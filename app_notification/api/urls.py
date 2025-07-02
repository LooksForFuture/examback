from rest_framework.routers import DefaultRouter
from app_notification.api.views import NotificationViewSet


router = DefaultRouter()
router.register(r'notification', NotificationViewSet, basename='notification')
urlpatterns = router.urls
