import boto3
import datetime
import os
import subprocess

KILO = 1024
MEGA = 1048576
GIGA = 1073741824

# Create CloudWatch client

cloudwatch = boto3.client(
    'cloudwatch',
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
    region_name=os.environ['DEPLOYMENT_REGION'],
)


class MemInfo():
    def __init__(self, path='/proc/meminfo'):
        self.path = path

    def fileobj(self):
        return open(self.path, 'r')

    def dict(self):
        with self.fileobj() as f:
            d = dict(x.strip().split(None, 1) for x in f)
            d = {
                key.strip(':'): (float(item.strip('kB')) * KILO)
                for key, item in d.items()
            }
        return d


class DiskInfo():
    def __init__(self):
        self.pull_info()

    def pull_info(self):
        process = subprocess.Popen(
            '/bin/df -k -l -P /',
            stdout=subprocess.PIPE,
            shell=True
        )
        output = process.communicate()[0].decode('ascii').splitlines()[1]\
            .strip().split()
        self.info = {
            'disk_total': float(output[1]) * KILO,
            'disk_used': float(output[2]) * KILO,
            'disk_avail': float(output[3]) * KILO,
            'fsystem': output[0],
            'mount': output[5],
        }

    def dict(self):
        return self.info


class CPUInfo():
    def __init__(self):
        self.pull_info()

    def pull_info(self):
        process = subprocess.Popen(
            """
mpstat 1 1 |\
awk '/%idle/ \
{for (i=1;i<=NF;i++) {if ($i=="%idle") col=i-1}} /^Average:/ {print $col}'
            """,
            stdout=subprocess.PIPE,
            shell=True
        )
        idle = float(process.communicate()[0].decode('ascii').strip())
        self.info = {
            'idle': idle,
            'usage': 100 - idle,
        }

    def dict(self):
        return self.info


# Common info
current_timestamp = int(datetime.datetime.now().timestamp())
instance_id = 'DEEP-CERN'  # i-00013f1f

# meminfo values are in bytes
meminfo = MemInfo().dict()

mem_total = meminfo['MemTotal']
mem_free = meminfo['MemFree']
mem_avail = meminfo['MemAvailable']
mem_used = mem_total - mem_avail
mem_util = (100 * mem_used / mem_total) if mem_total > 0 else 0

# Swap info
swap_total = meminfo['SwapTotal']
swap_free = meminfo['SwapFree']
swap_used = swap_total - swap_free
swap_util = (100 * swap_used / swap_total) if swap_total > 0 else 0

# Disk Info
diskinfo = DiskInfo().dict()
disk_total = diskinfo['disk_total']
disk_used = diskinfo['disk_used']
disk_avail = diskinfo['disk_avail']
disk_util = (100 * disk_used / disk_total) if disk_total > 0 else 0

# CPU Info
cpuinfo = CPUInfo().dict()
cpu_usage = cpuinfo['usage']


def get_dimensions(dimensions=[]):
    return [
        {
            'Name': 'InstanceId',
            'Value': instance_id
        },
        {
            'Name': 'Instance Name',
            'Value': instance_id
        },
    ] + dimensions


def get_memory_utilization():
    return {
        'MetricName': 'MemoryUtilization',
        'Value': mem_util,
        'Unit': 'Percent',
        'Timestamp': current_timestamp,
        'Dimensions': get_dimensions()
    }


def get_memory_used():
    return {
        'MetricName': 'MemoryUsed',
        'Value': mem_used,
        'Unit': 'Bytes',
        'Timestamp': current_timestamp,
        'Dimensions': get_dimensions()
    }


def get_memory_available():
    return {
        'MetricName': 'MemoryAvailable',
        'Value': mem_avail,
        'Timestamp': current_timestamp,
        'Unit': 'Bytes',
        'Dimensions': get_dimensions()
    }


def get_swap_utilization():
    return {
        'MetricName': 'SwapUtilization',
        'Value': swap_util,
        'Timestamp': current_timestamp,
        'Unit': 'Percent',
        'Dimensions': get_dimensions()
    }


def get_swap_used():
    return {
        'MetricName': 'SwapUsed',
        'Value': swap_used,
        'Unit': 'Bytes',
        'Timestamp': current_timestamp,
        'Dimensions': get_dimensions()
    }


def get_diskspace_utilization():
    return {
        'MetricName': 'DiskSpaceUtilization',
        'Value': disk_util,
        'Timestamp': current_timestamp,
        'Unit': 'Percent',
        'Dimensions': get_dimensions()
    }


def get_swap_available():
    return {
        'MetricName': 'SwapAvailable',
        'Value': swap_free,
        'Unit': 'Bytes',
        'Timestamp': current_timestamp,
        'Dimensions': get_dimensions()
    }


def get_diskspace_used():
    return {
        'MetricName': 'DiskSpaceUsed',
        'Value': disk_used / GIGA,
        'Unit': 'Gigabytes',
        'Timestamp': current_timestamp,
        'Dimensions': get_dimensions()
    }


def get_diskspace_available():
    return {
        'MetricName': 'DiskSpaceAvailable',
        'Value': disk_avail / GIGA,
        'Unit': 'Gigabytes',
        'Timestamp': current_timestamp,
        'Dimensions': get_dimensions()
    }


def get_cpu_usage():
    return {
        'MetricName': 'CpuUtilization',
        'Value': cpu_usage,
        'Unit': 'Percent',
        'Timestamp': current_timestamp,
        'Dimensions': get_dimensions()
    }


metrics = [
    get_memory_utilization(),
    get_memory_used(),
    get_memory_available(),

    get_swap_utilization(),
    get_swap_used(),
    get_swap_available(),

    get_diskspace_utilization(),
    get_diskspace_used(),
    get_diskspace_available(),

    get_cpu_usage(),
]

# print(json.dumps(metrics))

cloudwatch.put_metric_data(
    Namespace='CERN',
    MetricData=metrics,
)
