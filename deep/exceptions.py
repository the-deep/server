from rest_framework.exceptions import APIException


class NotImplementedException(APIException):
    status_code = 501
    default_detail = 'Not Implemented'
    default_code = 'not_implemented'
