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
- Attach the following permissions policy to the user: ```
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

``` 
export AWS_ACCESS_KEY_ID=your_access_key_id
export AWS_SECRET_ACCESS_KEY=your_secret_access_key
export AWS_DEFAULT_REGION=your_aws_region
```

## Installing the uploader script

## Testing

