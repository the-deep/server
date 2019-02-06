# from django.contrib.auth.models import User
# from django.db import models


# class RefreshToken(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     token = models.TextField()
#     blacklisted = models.BooleanField(default=False)

#     def __str__(self):
#         return '{} ({}) {}'.format(
#             self.user,
#             self.token,
#             'BLACKLISTED' if self.blacklisted else None
#         )
