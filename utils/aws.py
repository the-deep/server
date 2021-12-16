import boto3
from botocore.exceptions import ClientError
import json
import logging

logger = logging.getLogger(__name__)


def get_db_cluster_secret(cluster_secret, cluster_secret_ref):
    try:
        # Try for databaseSecret json
        return json.loads(cluster_secret)
    except json.decoder.JSONDecodeError:
        logger.info(f'Fetching db cluster secret using ARN: {cluster_secret_ref}')

    # the passed secret is the aws arn instead
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        # region_name='us-east-1',
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=cluster_secret_ref
        )
    except ClientError as e:
        logger.info(f"Got client error {e.response['Error']['Code']} for {cluster_secret_ref}")
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
    raise Exception('Failed to parse/fetch secret')
