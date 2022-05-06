import boto3
import requests
from botocore.exceptions import ClientError
import json
import logging

logger = logging.getLogger(__name__)


def fetch_db_credentials_from_secret_arn(cluster_secret_arn, ignore_error=False):
    logger.warning(f'Fetching db cluster secret using ARN: {cluster_secret_arn}')

    # the passed secret is the aws arn instead
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        # region_name='us-east-1',
    )

    try:
        get_secret_value_response = client.get_secret_value(SecretId=cluster_secret_arn)
    except ClientError as e:
        logger.error(f"Got client error {e.response['Error']['Code']} for {cluster_secret_arn}")
    else:
        logger.info('Found secret...')
        # Secrets Manager decrypts the secret value using the associated KMS CMK
        # Depending on whether the secret was a string or binary, only one of these fields will be populated
        if 'SecretString' in get_secret_value_response:
            text_secret_data = get_secret_value_response['SecretString']
            return json.loads(text_secret_data)
        else:
            # binary_secret_data = get_secret_value_response['SecretBinary']
            logger.error("Secret should be decrypted to string but found binary instead")
    if ignore_error:
        return
    raise Exception('Failed to parse/fetch secret')


def get_internal_ip(name):
    try:
        resp = requests.get('http://169.254.170.2/v2/metadata', timeout=1).json()
        return [
            container['Networks'][0]['IPv4Addresses'][0]
            for container in resp['Containers']
            # 'web' is from Dockerfile + web manifest
            if container['DockerName'] == name
        ][0]
    except Exception:
        logger.error(f"Failed to retrieve AWS internal ip, {locals().get('resp')}", exc_info=True)
