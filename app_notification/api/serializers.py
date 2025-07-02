from rest_framework import serializers
from app_notification.models import Notification


class MyNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        exclude = ['receiver']