from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from gallery.models import File
from project.models import Project


class Profile(models.Model):
    """
    User profile model

    Extra attributes for the user besides the django
    provided ones.
    """
    user = models.OneToOneField(User)
    organization = models.CharField(max_length=300, blank=True)
    hid = models.TextField(default=None, null=True, blank=True)
    # country = models.ForeignKey(Country)
    display_picture = models.ForeignKey(File, on_delete=models.SET_NULL,
                                        null=True, blank=True, default=None)

    last_active_project = models.ForeignKey(Project,
                                            null=True, blank=True,
                                            default=None)

    login_attempts = models.IntegerField(default=0)

    def __str__(self):
        return str(self.user)

    def get_display_name(self):
        return self.user.get_full_name() if self.user.first_name \
            else self.user.username


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
