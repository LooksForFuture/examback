from rest_framework import viewsets
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from app_notification.api.serializers import MyNotificationSerializer
from app_notification.models import Notification


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = MyNotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(receiver=self.request.user).order_by('-create_datetime')
    
    def create(self, request, *args, **kwargs):
        return Response({'detail': 'عدم دسترسی'}, status=status.HTTP_403_FORBIDDEN)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        # serializer = self.get_serializer(instance, data=request.data)
        serializer = self.get_serializer(instance, data={'is_seen': True})
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)