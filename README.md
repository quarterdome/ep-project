# ElectriqPower Power Pod 1 Metrics Uploader

This project provides a Python script to upload metrics from JSON files to AWS CloudWatch. It is designed to work with data collected from the ElectriqPower Power Pod 1 device.

In spring 2024, ElectriqPower went out of business as a company. While Power Pod 1 is design to work completely autonomously without cloud connectivity, the device owners lost access to their telemetry data. Fortunately, the PP1 data logger is nothing but a Raspberry Pi running Linux, and the data is stored in easily parsable JSON files. This project aims to help PP1 owners regain access to their telemetry data by uploading it to AWS CloudWatch.

You would have to be fairly technical to use this project, but it should be doable for anyone with basic Python and Linux skills.


## Getting access to data logger

- Physical access to the device
- Resetting `root` / `pi` account password

## Finding the right file locations

On my device the telemetry JSON is written in a file called `/home/pi/der-firmware/messages`. Metrics are sampled every 10 seconds, and stored in the files named something like `message_2025-07-21T10-40-00.json`. 

Warning, if you data logger has been running for multiple months/years without cloud connectivity, you may have thousands of these files. You may want to clear the folder before running the uploader script.

## Installing the uploader script

## Setting up AWS

- Credentials
- CloudWatch Namespace

## Testing

