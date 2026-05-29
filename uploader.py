#!/usr/bin/env python3
import os
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Tuple
import pprint

import boto3
from botocore.exceptions import ClientError, ConnectionError


CLOUDWATCH_NAMESPACE = "pp1_telemetry"    # your CloudWatch namespace
WATCH_DIR = os.environ.get("WATCH_DIR")   # directory where new JSON files appear
POLL_INTERVAL_SEC = 10
RETRY_INTERVAL_SEC = 30
RETRY_MAX_ATTEMPTS = 100


def create_cloudwatch_client(region_name: str = "us-west-1"):
    return boto3.client("cloudwatch", region_name=region_name)


def _iso_to_datetime(iso_str: str) -> datetime:
    # supports "…Z" or offset formats
    return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))

def build_metric_data(records: List[dict]) -> List[dict]:
    """
    Input 'records' are your JSON 'telemetry' items.
    Output is a list of CloudWatch MetricData dicts.
    For each numeric field, we emit one metric sample:
      MetricName = field_name
      Dimensions = der_id, measurement
      Timestamp  = parsed ISO time
      Value      = numeric value
      Unit       = from FIELD_UNITS or "None"
    """
    metric_data = []
    for it in records:
        meas = it.get("measurement")
        t = _iso_to_datetime(it.get("time")).timestamp()

        if meas == 'grid':
            metric_data.append({
                "MetricName": "grid_voltage",
                "Timestamp": t,
                "Value": it.get('fields', {}).get('voltage', 0.0),
                "Unit": "None",
            })
            metric_data.append({
                "MetricName": "grid_frequency",
                "Timestamp": t,  
                "Value": it.get('fields', {}).get('frequency', 0.0),
                "Unit": "None"
            })
            metric_data.append({
                "MetricName": "grid_power",
                "Timestamp": t,  
                "Value": it.get('fields', {}).get('power', 0.0),
                "Unit": "None"
            })
            metric_data.append({
                "MetricName": "grid_current",
                "Timestamp": t,  
                "Value": it.get('fields', {}).get('current', 0.0),
                "Unit": "None"
            })
        elif meas == 'inverter':
            metric_data.append({
                "MetricName": "inverter_voltage",
                "Timestamp": t,
                "Value": it.get('fields', {}).get('voltage', 0.0),
                "Unit": "None",
            })
            metric_data.append({
                "MetricName": "load_power",
                "Timestamp": t,  
                "Value": it.get('fields', {}).get('load_power', 0.0),
                "Unit": "None"
            })
            metric_data.append({
                "MetricName": "whole_home_power",
                "Timestamp": t,  
                "Value": it.get('fields', {}).get('whole_home_power', 0.0),
                "Unit": "None"
            })
            metric_data.append({
                "MetricName": "inverter_current",
                "Timestamp": t,  
                "Value": it.get('fields', {}).get('current', 0.0),
                "Unit": "None"
            })
            metric_data.append({
                "MetricName": "inverter_temperature",
                "Timestamp": t,  
                "Value": it.get('fields', {}).get('temperature', 0.0),
                "Unit": "None"
            })
        elif meas == 'battery':
            metric_data.append({
                "MetricName": "battery_voltage",
                "Timestamp": t,
                "Value": it.get('fields', {}).get('voltage', 0.0),
                "Unit": "None",
            })
            metric_data.append({
                "MetricName": "battery_power_charge",
                "Timestamp": t,  
                "Value": it.get('fields', {}).get('power_charge', 0.0),
                "Unit": "None"
            })
            metric_data.append({
                "MetricName": "battery_power_discharge",
                "Timestamp": t,  
                "Value": it.get('fields', {}).get('power_discharge', 0.0),
                "Unit": "None"
            })
            metric_data.append({
                "MetricName": "battery_current",
                "Timestamp": t,  
                "Value": it.get('fields', {}).get('current', 0.0),
                "Unit": "None"
            })
            metric_data.append({
                "MetricName": "battery_charge_state",
                "Timestamp": t,  
                "Value": it.get('fields', {}).get('charge_state', 0.0),
                "Unit": "None"
            })
            metric_data.append({
                "MetricName": "battery_temperature",
                "Timestamp": t,  
                "Value": it.get('fields', {}).get('temperature', 0.0),
                "Unit": "None"
            })
    
    return metric_data

def put_metric_data_batched(cw_client, namespace: str, metric_data: List[dict]) -> None:
    """
    CloudWatch limit: 20 MetricData per PutMetricData call.
    """
    CHUNK = 20
    for i in range(0, len(metric_data), CHUNK):
        chunk = metric_data[i:i + CHUNK]
        cw_client.put_metric_data(Namespace=namespace, MetricData=chunk)


def process_one_json_file(path: str, cw_client=None, namespace: str = CLOUDWATCH_NAMESPACE) -> Tuple[bool, str, bool]:
    """
    Returns (success, message, retryable).
    On success, caller should delete the file.
    """
    try:
        with open(path, "r") as f:
            data = json.load(f)
    except Exception as e:
        return (False, f"JSON load error: {e}", False)

    telemetry = data.get("telemetry", [])
    if not isinstance(telemetry, list):
        return (False, "Invalid JSON: 'telemetry' is not a list", False)

    metric_data = build_metric_data(telemetry)
    if not metric_data:
        return (True, "No matching numeric fields; nothing to publish", False)

    if cw_client is None:
        cw_client = create_cloudwatch_client()

    try:
        #pprint.pprint(metric_data)
        put_metric_data_batched(cw_client, namespace, metric_data)
        return (True, f"Published {len(metric_data)} metric samples", False)
    except ConnectionError as e:
        return (False, f"CloudWatch transient network error: {e}", True)
    except ClientError as e:
        return (False, f"CloudWatch error: {e}", False)
    except Exception as e:
        return (False, f"Unexpected error: {e}", False)


def process_one_json_file_with_retry(path: str, cw_client=None, namespace: str = CLOUDWATCH_NAMESPACE) -> Tuple[bool, str]:
    """Wrap process_one_json_file with retry logic for network errors."""
    attempts = 0
    while True:
        success, msg, retryable = process_one_json_file(path, cw_client=cw_client, namespace=namespace)
        if success:
            return True, msg

        if not retryable:
            return False, msg

        attempts += 1
        if attempts >= RETRY_MAX_ATTEMPTS:
            return False, msg

        print(f"RETRY {os.path.basename(path)}: {msg} (attempt {attempts}/{RETRY_MAX_ATTEMPTS}, waiting {RETRY_INTERVAL_SEC}s)")
        time.sleep(RETRY_INTERVAL_SEC)


def ensure_dirs():
    os.makedirs(WATCH_DIR, exist_ok=True)
    os.makedirs(os.path.join(WATCH_DIR, "failed"), exist_ok=True)

def main():

    print("Starting uploader...")
    print(f"Using CloudWatch namespace: {CLOUDWATCH_NAMESPACE}")
    print(f"Watching directory: {WATCH_DIR}")
    print(f"Poll interval: {POLL_INTERVAL_SEC} seconds")

    ensure_dirs()
    print(f"Watching {WATCH_DIR} (poll {POLL_INTERVAL_SEC}s) for .json files…")

    cw_client = create_cloudwatch_client()

    while True:
        try:
            names = sorted(os.listdir(WATCH_DIR))
        except FileNotFoundError:
            time.sleep(POLL_INTERVAL_SEC)
            continue

        for name in names:
            if not name.endswith(".json"):
                continue
            full = os.path.join(WATCH_DIR, name)

            if not os.path.isfile(full):
                continue

            success, msg = process_one_json_file_with_retry(full, cw_client=cw_client)
            if success:
                try:
                    os.remove(full)
                    print(f"OK {name}: {msg} (file deleted)")
                except Exception as e:
                    print(f"OK {name}: {msg} (delete failed: {e})")
            else:
                # move to failed/ to avoid re-processing loop
                dst = os.path.join(WATCH_DIR, "failed", name)
                try:
                    os.replace(full, dst)
                    print(f"FAIL {name}: {msg} (moved to failed/)")
                except Exception as e:
                    print(f"FAIL {name}: {msg} (could not move: {e})")

        time.sleep(POLL_INTERVAL_SEC)

if __name__ == "__main__":
    main()