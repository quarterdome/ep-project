"""
Script to prepare test data.

This script takes the following parameters:
- start_time: ISO8601 or epoch string, start of time window (inclusive)
- end_time: ISO8601 or epoch string, end of time window (inclusive, defaults to all files after start_time)
- new_time: ISO8601 or epoch string, timestamp to rewrite first file to (defaults to now)
- delay: (optional, seconds) a fixed delay before copying each file; if omitted, uses the original source spacing between files
- source_dir: directory with original files
- dest_dir: directory to copy files to

It copies files from source_dir to dest_dir whose names are within the time window,
renaming the first file's timestamp to new_time, and waits between copies to simulate realtime playback.
"""

import os
import sys
import time
import shutil
import argparse
from datetime import datetime

def parse_time(ts):
    """Parse ISO8601, filename-style, or epoch string to datetime."""
    s = ts.strip()
    if s.endswith('Z'):
        s = s[:-1] + '+00:00'

    if 'T' in s:
        date_part, time_part = s.split('T', 1)
        if ':' not in time_part:
            time_part = time_part.replace('-', ':', 2)
            s = f"{date_part}T{time_part}"

    try:
        return datetime.fromisoformat(s)
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
    parser.add_argument('--end_time', help='End time (ISO8601 or epoch). Defaults to all files after start_time.')
    parser.add_argument('--new_time', help='New timestamp for first file (ISO8601 or epoch). Defaults to now.')
    parser.add_argument('--delay', type=float, default=None, help='Delay between copies (seconds). If omitted, uses source file spacing.')
    parser.add_argument('--source_dir', required=True, help='Source directory')
    parser.add_argument('--dest_dir', required=True, help='Destination directory')
    args = parser.parse_args()

    start_dt = parse_time(args.start_time)
    end_dt = parse_time(args.end_time) if args.end_time else None
    new_dt = parse_time(args.new_time) if args.new_time else datetime.now().replace(microsecond=0)

    time_offset = new_dt - start_dt

    print(f"Start time: {start_dt}")
    print(f"End time: {end_dt}")
    print(f"New time for first file: {new_dt}")
    print(f"Time offset to apply: {time_offset}")

    files = sorted([
        f for f in os.listdir(args.source_dir)
        if f.startswith('message_') and f.endswith('.json')
    ])
    print(f"Found {len(files)} files in source directory.")

    # Filter files in time window
    selected = []
    for fname in files:
        ts = extract_timestamp_from_filename(fname)
        if ts and ts >= start_dt and (end_dt is None or ts <= end_dt):
            selected.append((ts, fname))
    selected.sort()

    if not selected:
        print("No files found in the given time window.")
        sys.exit(1)

    print(f"Selected {len(selected)} files in the time window.")

    os.makedirs(args.dest_dir, exist_ok=True)

    if args.delay is None and len(selected) > 1:
        source_delays = [
            max(0.0, (selected[i][0] - selected[i-1][0]).total_seconds())
            for i in range(1, len(selected))
        ]
        print("Simulating realtime playback using source file timestamp spacing.")
    else:
        source_delays = []

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
                entry['time'] = (ts + time_offset).strftime('%Y-%m-%dT%H:%M:%SZ')
        with open(dst, 'w') as f:
            json.dump(data, f, indent=4)

        print(f"Copied {src} -> {dst}")
        if idx < len(selected) - 1:
            sleep_seconds = args.delay if args.delay is not None else source_delays[idx]
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

if __name__ == "__main__":
    main()

