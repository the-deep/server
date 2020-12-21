from rest_framework import exceptions

from deep import error_codes


class EntryValidationVersionMismatchError(exceptions.ValidationError):
    status_code = 400
    code = error_codes.ENTRY_VALIDATION_VERSION_MISMATCH
    default_detail = 'Version Mismatch'
