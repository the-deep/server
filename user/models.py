from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    """
    User profile model

    Extra attributes for the user besides the django
    provided ones.
    """
    user = models.OneToOneField(User)
    organization = models.CharField(max_length=300, blank=True)
    # country = models.ForeignKey(Country)
    display_picture = models.FileField(upload_to='user_dp/',
                                       null=True, blank=True, default=None)

    def __str__(self):
        return str(self.user)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, created, **kwargs):
    """
    Signal to auto create or save user profile instance whenever
    the user is saved.
    """
    if created or Profile.objects.filter(user=instance).count() == 0:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()
