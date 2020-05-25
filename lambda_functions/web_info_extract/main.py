import os
import json
import jwt
from datetime import datetime
from utils.web_info_extractor import get_web_info_extractor


class UnauthorizedException(Exception):
    pass


def create_error_response_body(exc_data: str = None, non_field_error: str = None) -> dict:
    """Create 400 response from exception data"""
    timestamp = int(datetime.now().timestamp())
    if isinstance(exc_data, dict):
        exc_data['timestamp'] = timestamp
        return create_response(400, exc_data)
    resp_data = {
        'timestamp': timestamp,
        'errors': {
            'non_field_errors': [non_field_error or 'Something went wrong. Please try later or contact admin.']
        }
    }
    if exc_data:
        resp_data['errors']['internal_non_field_errors'] = [exc_data]
    return resp_data


def create_response(status: int, data: dict) -> dict:
    """Create response from given data and status code"""
    return {
        'body': json.dumps(data),
        'isBase64Encoded': False,
        'statusCode': status,
        'headers': {}
    }


def is_valid_url(url: str) -> bool:
    """Check if the url is valid"""
    # TODO: implement this
    return True


def auto_http_response(func):
    """This is a decorator that automatically send 200 json response when the
    wrapped function returns a dict data. If exception is raised, 400 is returned
    """
    def wrapped(*args, **kwargs):
        try:
            serialized_data = func(*args, **kwargs)
            return create_response(200, serialized_data)
        except UnauthorizedException as e:
            if e.args:
                return create_response(401, create_error_response_body(None, e.args[0]))
        except Exception as e:
            # TODO: log
            if e.args:
                return create_response(400, create_error_response_body(e.args[0]))
            return create_response(400, create_error_response_body('Something unexpected happened'))
    return wrapped


def validate_params(params: dict):
    url = params.get('url')
    if not url or not is_valid_url(url):
        raise Exception({'url': 'Url must be present and valid'})


def authorize(bearer_token: str):
    if not bearer_token:
        raise UnauthorizedException("You are unauthorized")
    token = bearer_token.replace('Bearer ', '')
    secret = os.environ['JWT_SECRET']
    try:
        jwt.decode(
            token,
            secret,
            algorithms=['HS256'],
            verify=True,
        )
    except jwt.exceptions.InvalidSignatureError:
        raise UnauthorizedException("Invalid token")
    except jwt.exceptions.ExpiredSignatureError:
        raise UnauthorizedException("Expired token")


@auto_http_response
def main(api_input, *args, **kwargs):
    params = api_input.get('queryStringParameters') or {}
    headers = api_input.get('headers') or {}

    authorize(headers.get('Authorization'))
    validate_params(params)

    url = params.get('url') or ''
    extractor = get_web_info_extractor(url)
    return extractor.serialized_data()


if __name__ == '__main__':
    request_data = {
        'queryStringParameters': {
            'url': 'https://redhum.org/documento/123212'
        },
        'headers': {
            'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE1ODg5MTY5NzcsInRva2VuVHlwZSI6ImFjY2VzcyIsInVzZXJJZCI6NDc2fQ.QQjb_EBUtbC1t5avo6Wwj3qIjipg'
        }
    }
    response_data = main(request_data)
    print(response_data)
