# ElectriqPower Power Pod 1 Metrics Uploader

This project provides a Python script to upload metrics from JSON files to AWS CloudWatch. It is designed to work with data collected from the ElectriqPower Power Pod 1 device.

In spring 2024, ElectriqPower went out of business as a company. While Power Pod 1 is design to work completely autonomously without cloud connectivity, the device owners lost access to their telemetry data. Fortunately, the PP1 data logger is nothing but a Raspberry Pi running Linux, and the data is stored in easily parsable JSON files. This project aims to help PP1 owners regain access to their telemetry data by uploading it to AWS CloudWatch.

You would have to be fairly technical to use this project, but it should be doable for anyone with basic Python and Linux skills.


## Getting access to data logger

### Physical access to the device

In my case that involved opening up the case, finding the Raspberry Pi inside, finding the power supply, disconnecting the power supply, unmounting the Raspberry Pi, disconnecting it from ethernet and from the USB, and finally taking it out. I had to do it very carefully not to touch any hight voltage wires inside battery enclosrue -- it was not hard, but severely cramped the working space.

However, every installer mounts the PP1 data logger differently. I heard that in some cases it is mounted externally, and not inside the battery enclosure.

### Resetting `root` / `pi` account password

The Raspberry Pi inside the PP1 data logger has a microSD card that contains the operating system and data. You need to take out the microSD card, put it into a microSD-to-USB adapter, and plug it into your computer. You have to switch the boot configuration to boot into singkle-user mode in order to reset the password for the `root` or `pi` user. Then you have to switch the boot configuration back to normal.

The detailed instructions for root password reset are available here: https://www.raspberrypi.com/documentation/computers/configuration.html#changing-the-root-password

## Finding the right file locations

On my device the telemetry JSON files are written in a directlry called `/home/pi/der-firmware/messages`. Metrics are sampled every 10 seconds, and stored in the files named something like `message_2025-07-21T10-40-00.json`. 

_Warning_: If you data logger has been running for multiple months/years without cloud connectivity, you may have thousands of these files. You may want to clear the folder before running the uploader script.

## Setting up AWS

The uploaded script uploads metrics to AWS CloudWatch. You need to have an AWS account, and set up the following:

- IAM User. I namesd mine `pp1`. 
- CloudWatch namespace. I used `pp1_telemetry`. 
- Attach the following permissions policy to the user: 
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublishCustomMetrics",
            "Effect": "Allow",
            "Action": [
                "cloudwatch:PutMetricData"
            ],
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "cloudwatch:namespace": "pp1_telemetry"
                }
            }
        }
    ]
}
```
- Configure the following environment variables before running the uploader script:

```bash
export AWS_ACCESS_KEY_ID=your_access_key_id
export AWS_SECRET_ACCESS_KEY=your_secret_access_key
export AWS_DEFAULT_REGION=your_aws_region
```

## Installing the uploader script

On the Raspberry Pi that collects telemetry:

1. Install system dependencies (Python 3.9+ is already present on Raspberry Pi OS). Then install the Python packages:
   ```bash
   pip3 install --user -r /home/pi/ep-project/requirements.txt
   ```
2. Create the `env` file and fill in your AWS credentials. This file is sourced when the uploader starts.

3. (Optional) Edit the `WATCH_DIR` variable in the `env` file. On my device the telemetry JSON files are written in a directlry called `/home/pi/der-firmware/messages`. If you don't edit the variable, the uploader will look for JSON files in `./test` relative to where it is started.

## Testing


## Running the uploader on boot (systemd service)

The repository contains a ready-to-use systemd unit under `scripts/pp1-uploader.service`. It assumes you cloned this project to `/home/pi/ep-project/` and that the uploader should run as the `pi` user. If your setup differs, edit the file before installing it.

1. Mark the helper script as executable (only required the first time, already done in the repository):
   ```bash
   chmod +x /home/pi/ep-project/scripts/run-uploader.sh
   ```
2. Copy the service file into systemd and reload units:
   ```bash
   sudo cp /home/pi/ep-project/scripts/pp1-uploader.service /etc/systemd/system/pp1-uploader.service
   sudo systemctl daemon-reload
   ```
3. Enable the service so it starts at boot and start it immediately:
   ```bash
   sudo systemctl enable --now pp1-uploader.service
   ```
4. Check the status or logs if you need to troubleshoot:
   ```bash
   sudo systemctl status pp1-uploader.service
   journalctl -u pp1-uploader.service -n 50
   ```

The service launches `scripts/run-uploader.sh`, which sources the `env` file for AWS credentials and then executes `uploader.py`. Updates to the repository will take effect on the next restart (`sudo systemctl restart pp1-uploader.service`).
