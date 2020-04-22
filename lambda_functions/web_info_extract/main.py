import json
from datetime import datetime
from utils.web_info_extractor default import DefaultWebInfoExtractor


def create_400_response(exc_data: str) -> dict:
    """Create 400 response from exception data"""
    timestamp = int(datetime.now().timestamp())
    if isinstance(exc_data, dict):
        exc_data['timestamp'] = timestamp
        return create_response(400, exc_data)
    resp_data = {
        'timestamp': timestamp,
        'errors': {
            'internal_non_field_errors': [exc_data],
            'non_field_errors': ['Something went wrong. Please try later or contact admin.']
        }
    }
    return create_response(400, resp_data)


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
        except Exception as e:
            # TODO: log
            if e.args:
                return create_400_response(e.args[0])
            return create_400_response('Something unexpected happened')
    return wrapped


def validate_params(params: dict):
    url = params.get('url')
    if not url or not is_valid_url(url):
        raise Exception({'url': 'Url must be present and valid'})


@auto_http_response
def main(api_input, *args, **kwargs):
    params = api_input.get('queryStringParameters') or {}
    validate_params(params)
    url = params.get('url') or ''
    extractor = DefaultWebInfoExtractor(url)
    return extractor.serialized_data()


if __name__ == '__main__':
    response_data = main({'queryStringParameters': {'url': 'https://www.bbc.com/news/world-us-canada-52377122'}})
    print(response_data)
