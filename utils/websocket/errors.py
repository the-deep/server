SN_NOT_PROVIDED = 40011

ACTION_INVALID = 40012
PERMISSION_DENIED = 403

CHANNEL_INVALID = 40021
EVENT_INVALID = 40022
FIELD_INVALID = 40023


class SnNotProvidedError(Exception):
    code = SN_NOT_PROVIDED
    message = 'Sequence number is not provided'


class ActionValueError(Exception):
    code = ACTION_INVALID
    message = 'Action is not provided or is invalid'


class PermissionDenied(Exception):
    code = PERMISSION_DENIED
    message = 'Permission denied'


class ChannelValueError(Exception):
    code = CHANNEL_INVALID
    message = 'Channel is not provided or is invalid'


class EventValueError(Exception):
    code = EVENT_INVALID
    message = 'Event is not provided or is invalid'


class FieldValueError(Exception):
    code = FIELD_INVALID

    def __init__(self, key):
        self.message = 'Value for {} is not provided or is invalid'.format(key)


# EOF
