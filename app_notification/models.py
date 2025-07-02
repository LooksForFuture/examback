from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Notification(models.Model):
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=250, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    url = models.CharField(max_length=250, null=True, blank=True)
    create_datetime = models.DateTimeField(auto_now_add=True)
    is_seen = models.BooleanField(default=False)

    def __str__(self):
        return self.title