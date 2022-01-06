from rest_framework.authentication import SessionAuthentication


class CSRFExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, _):
        # Enforce for all request
        return True
