import logging

import uuid, csv, io
import time

from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from rest_framework.exceptions import ValidationError
import requests
import datetime
from connector.utils import ConnectorWrapper
from lead.models import Lead
from unified_connector.sources.base import Source

from deep import settings
from io import BytesIO
from django.template.loader import render_to_string
from weasyprint import HTML

import hashlib
from django.core.files.base import ContentFile
import os
from boto3.session import Session
from botocore.exceptions import NoCredentialsError


logger = logging.getLogger(__name__)


@ConnectorWrapper
class Kobo(Source):

    URL = 'https://kf.kobotoolbox.org/api/v2/assets/'
    title = 'KoboToolbox Reports'
    key = 'kobo-toolbox'

    options = [
        {
            'key': 'project_id',
            'field_type': 'text',
            'title': 'Project ID',
        },
        {
            'key': 'token',
            'field_type': 'text',
            'title': 'Kobo API Token',
        }
    ]

    def get_content(self, project_id, token):
        api_url = f"{self.URL}{project_id}/data/?format=json"
        headers = {"Authorization": f"Token {token}"}

        try:
            with requests.get(api_url, headers=headers, stream=True) as response:
                if response.status_code == 200:
                    return response.json().get('results', [])
                else:
                    logger.error("Failed to fetch data from API, Status code: %d", response.status_code)
        except requests.RequestException as e:
            logger.critical("A critical error occurred while fetching data: %s", e)
        return []

    def fetch(self, params):
        logger.info(f'fetching for kobo commenced with params {params}')
        result = []
        project_id = params.get('project_id')
        if not project_id:
            return [], 0

        token = params.get('token')
        if not token:
            return [], 0


        try:
            records = self.get_content(project_id, token)
            if records:

                qualitative_columns, rows = accumulate_columns_and_rows(records)
                context = {
                    'columns': qualitative_columns,
                    'rows': rows,
                }

                html_string = render_to_string('connector/pdf.html', context)

                html = HTML(string=html_string)
                pdf_file = html.write_pdf()

                pdf_stream = BytesIO(pdf_file)

                file_path = save_file_remote(project_id, context, pdf_file=pdf_stream)
                print(f'the media url is {settings.MEDIA_URL} and the media files location is {settings.MEDIAFILES_LOCATION}')
                file_url = os.path.join(settings.MEDIA_URL, file_path)

                date = datetime.now()
                result = [{
                     'title': project_id,
                     'url': file_url,
                     'source': 'KoboToolbox',
                     'author': 'KoboToolbox',
                     'published_on': date.date(),
                     'source_type': Lead.SourceType.WEBSITE}
                ]

                logger.info(f'the resulted data of kobo is: {result}')
            return result, len(result)
        except Exception as e:
            logger.error("An error occurred: %s", e)
            return [], 0



def calculate_md5(file_content):
    """Calculate the MD5 checksum of a file-like object."""
    hash_md5 = hashlib.md5()
    for chunk in iter(lambda: file_content.read(4096), b""):
        hash_md5.update(chunk)
    file_content.seek(0)  # Reset file pointer
    return hash_md5.hexdigest()

def verify_checksum_s3(bucket_name, object_key, local_checksum, s3_client):
    """Verify the checksum of a file in S3."""
    try:
        response = s3_client.head_object(Bucket=bucket_name, Key=object_key)
        s3_etag = response['ETag'].strip('"')  # Remove quotes from ETag
        return s3_etag == local_checksum
    except NoCredentialsError:
        raise Exception("AWS credentials not found.")
    except Exception as e:
        raise Exception(f"Error verifying checksum: {e}")


def upload_to_s3_with_retry(bucket_name, object_key, file_content, local_checksum, max_retries=10,
                            retry_delay=1):
    """
    Upload a file to S3 with retry mechanism as a normal function.

    Args:
        bucket_name (str): S3 bucket name.
        object_key (str): S3 object key.
        encoded_pdf_content (str): Base64-encoded file content.
        local_checksum (str): MD5 checksum of the file.
        max_retries (int): Maximum number of retries.
        retry_delay (int): Delay (in seconds) between retries.

    Raises:
        Exception: If all retries fail.
    """
    session = Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )
    s3_client = session.client('s3')

    for attempt in range(max_retries):
        try:
            s3_client.put_object(Bucket=bucket_name, Key=object_key, Body=file_content)
            logger.info(f"File {object_key} uploaded successfully to bucket {bucket_name}. and is going to be verified")

            # Verify checksum
            if not verify_checksum_s3(bucket_name, object_key, local_checksum, s3_client):
                message = 'Checksum validation error'
                logger.warning(f'{message} retrying... Attempt {attempt + 1} of {max_retries}')
                raise ValidationError(message)  # Raise to trigger retry
            logger.info('checksum validation successful')
            return True
        except (BotoCoreError, ClientError, ValidationError) as exc:
            logger.error(f"Attempt {attempt + 1} failed: {exc}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error("All retry attempts failed.")
                raise


def save_file_remote(project_id, context, pdf_file):
    timestamp = datetime.now().strftime('%Y%m%dT%H%M%S')
    directory_path = os.path.join(str(project_id), str(timestamp))
    os.makedirs(directory_path, exist_ok=True)
    file_id = uuid.uuid4()
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME

    pdf_content = pdf_file.getvalue()
    def compose_file_path(file_type):
        file_path = os.path.join(file_type, directory_path, f"{file_id}.{file_type}")
        remote_file_path = os.path.join(settings.MEDIAFILES_LOCATION, file_path)
        return remote_file_path, file_path

    pdf_remote_path, pdf_path = compose_file_path('pdf')
    csv_remote_path, csv_path = compose_file_path('csv')

    def generate_csv_data(context):
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(context['columns'])
        for row in context['rows']:
            writer.writerow(row)
        csv_content = csv_buffer.getvalue().encode('utf-8')
        csv_file = ContentFile(csv_content)
        return csv_content, csv_file

    csv_content, csv_file = generate_csv_data(context)

    def remote_save_routine(file, file_content, remote_file_path):
        file_local_checksum = calculate_md5(file)
        upload_to_s3_with_retry(bucket_name, remote_file_path, file_content, file_local_checksum)

    remote_save_routine(pdf_file, pdf_content, pdf_remote_path)
    remote_save_routine(csv_file, csv_content, csv_remote_path)
    return pdf_path



# def pdf_save_path_and_url(project_id, context, pdf_file):
#     project_id = project_id
#     timestamp = datetime.now().strftime('%Y%m%dT%H%M%S')
#     import uuid, csv
#     directory_path = os.path.join(
#         str(project_id),
#         str(timestamp),
#     )
#     pdf_directory_path = os.path.join("pdf", directory_path)
#     os.makedirs(directory_path, exist_ok=True)
#     file_id = uuid.uuid4()
#     pdf_file_path = os.path.join(pdf_directory_path, f"{file_id}.pdf")
#     def save_pdf():
#
#         file_path = os.path.join(settings.MEDIAFILES_LOCATION, pdf_directory_path, f"{file_id}.pdf")
#         default_storage.save(file_path, ContentFile(pdf_file.getvalue()))
#     save_pdf()
#
#     csv_directory_path = os.path.join(settings.MEDIAFILES_LOCATION, "csv", directory_path)
#     csv_file_path = os.path.join(csv_directory_path, f"{file_id}.csv")
#
#     def save_csv():
#         import io
#         csv_buffer = io.StringIO()
#
#         writer = csv.writer(csv_buffer)
#         writer.writerow(context['columns'])
#         for row in context['rows']:
#             writer.writerow(row)
#
#         csv_content = ContentFile(csv_buffer.getvalue().encode('utf-8'))
#         default_storage.save(csv_file_path, csv_content)
#
#     save_csv()
#
#     return pdf_file_path
#

def accumulate_columns_and_rows(records):
    """Accumulate all columns from the records and filter qualitative columns."""
    all_columns_set = set()
    rows = []

    # Accumulate all unique columns across all records
    for record in records:
        all_columns_set.update(record.keys())

    all_columns = sorted(all_columns_set)

    # Filter qualitative columns based on values across all records
    qualitative_columns = []
    for col in all_columns:
        if all(is_qualitative(col, record.get(col, "N/A")) for record in records):
            qualitative_columns.append(col)

    # Build rows with qualitative data
    for record in records:
        row = [record.get(column, "N/A") for column in qualitative_columns]
        rows.append(row)

    return qualitative_columns, rows


import re
from datetime import datetime

BOOLEAN_TRUE_VALUES = {'true', 'yes', '1', 'on'}
BOOLEAN_FALSE_VALUES = {'false', 'no', '0', 'off'}


def is_uuid(value):
    """Check if a string is a valid UUID."""
    uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$', re.IGNORECASE)
    return bool(uuid_pattern.match(value))


def is_id_field(key, value):
    """Check if a field is likely to be an ID field."""
    if isinstance(key, str):
        # Check if the key contains 'id' or 'uuid'
        if 'id' in key.lower() or 'uuid' in key.lower():
            return True

    # Check if the value is a UUID
    if isinstance(value, str) and is_uuid(value):
        return True

    # Check if it's a numeric ID
    if isinstance(value, (int, str)):
        try:
            int(value)
            return len(str(value)) > 5  # Assume IDs are typically longer than 5 digits
        except ValueError:
            pass

    return False


def is_date(value):
    """Check if a string is a valid date."""
    try:
        datetime.fromisoformat(value.replace('Z', '+00:00'))
        return True
    except (ValueError, AttributeError):
        return False


def is_boolean(value):
    """Check if the value represents a boolean."""
    if isinstance(value, bool):
        return True  # Already a boolean

    if isinstance(value, str):
        normalized_value = value.strip().lower()
        if normalized_value in BOOLEAN_TRUE_VALUES or normalized_value in BOOLEAN_FALSE_VALUES:
            return True

    return False


def is_qualitative(key, value):
    """
    Helper function to determine if a value is qualitative based on its key, type, and content.
    """

    # Check if it's an ID field
    if isinstance(value, (dict, list)):
        return True

    if is_id_field(key, value):
        return False

    # Check if it's a boolean
    if is_boolean(value):
        return False

    if isinstance(value, str):
        # Check if it's a number or date disguised as a string
        try:
            float(value)
            return False  # It's a number
        except ValueError:
            if is_date(value):
                return False  # It's a date
            return True  # It's a regular string, consider it qualitative

    if isinstance(value, (int, float)):
        return False  # Numbers are quantitative

    # Consider everything else as qualitative
    return True