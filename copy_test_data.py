"""
Script to prepare test data.

This script takes the following parameters:
- start_time: ISO8601 or epoch string, start of time window (inclusive)
- end_time: ISO8601 or epoch string, end of time window (inclusive)
- new_time: ISO8601 or epoch string, timestamp to rewrite first file to
- delay: (optional, seconds, default 0) how much to wait before copying each file
- source_dir: directory with original files
- dest_dir: directory to copy files to

It copies files from source_dir to dest_dir whose names are within the time window,
renaming the first file's timestamp to new_time, and optionally waits between copies.
"""

import os
import sys
import time
import shutil
import argparse
from datetime import datetime

def parse_time(ts):
    """Parse ISO8601 or epoch string to datetime."""
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        try:
            return datetime.utcfromtimestamp(float(ts))
        except Exception:
            raise ValueError(f"Invalid timestamp: {ts}")

def extract_timestamp_from_filename(filename):
    # Assumes filename like: message_2025-07-21T10-40-00.json
    try:
        base = os.path.basename(filename)
        ts_str = base.replace('message_', '').replace('.json', '')
        # Convert T10-40-00 to T10:40:00 for ISO8601
        # convert last two '-' to ':'
        parts = ts_str.split('T')
        if len(parts) != 2:
            return None
        date_part, time_part = parts
        time_part = time_part.replace('-', ':', 2)
        ts_str = f"{date_part}T{time_part}"
        # Now ts_str is like 2025-07-21T10:40:00
        return datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S")
    except Exception:
        return None

def main():
    parser = argparse.ArgumentParser(description="Copy and rewrite test data files.")
    parser.add_argument('--start_time', required=True, help='Start time (ISO8601 or epoch)')
    parser.add_argument('--end_time', required=True, help='End time (ISO8601 or epoch)')
    parser.add_argument('--new_time', required=True, help='New timestamp for first file (ISO8601 or epoch)')
    parser.add_argument('--delay', type=float, default=0, help='Delay between copies (seconds)')
    parser.add_argument('--source_dir', required=True, help='Source directory')
    parser.add_argument('--dest_dir', required=True, help='Destination directory')
    args = parser.parse_args()

    start_dt = parse_time(args.start_time)
    end_dt = parse_time(args.end_time)
    new_dt = parse_time(args.new_time)

    time_offset = new_dt - start_dt
    print(f"Time offset to apply: {time_offset}")

    files = sorted([
        f for f in os.listdir(args.source_dir)
        if f.startswith('message_') and f.endswith('.json')
    ])

    # Filter files in time window
    selected = []
    for fname in files:
        ts = extract_timestamp_from_filename(fname)
        if ts and start_dt <= ts <= end_dt:
            selected.append((ts, fname))
    selected.sort()

    if not selected:
        print("No files found in the given time window.")
        sys.exit(1)

    #print(selected)

    os.makedirs(args.dest_dir, exist_ok=True)

    for idx, (ts, fname) in enumerate(selected):
        src = os.path.join(args.source_dir, fname)

        # Apply time offset to filename timestamp
        new_file_ts = ts + time_offset
        new_fname = f"message_{new_file_ts.strftime('%Y-%m-%dT%H-%M-%S')}.json"
        dst = os.path.join(args.dest_dir, new_fname)

        # Apply time offset inside file as well
        import json
        with open(src, 'r') as f:
            data = json.load(f)
        if 'telemetry' in data:
            for entry in data['telemetry']:
                ts = parse_time(entry['time'])
                print(ts)
                entry['time'] = (ts + time_offset).strftime('%Y-%m-%dT%H:%M:%SZ')
        with open(dst, 'w') as f:
            json.dump(data, f, indent=4)

        print(f"Copied {src} -> {dst}")
        if args.delay and idx < len(selected) - 1:
            time.sleep(args.delay)

if __name__ == "__main__":
    main()

