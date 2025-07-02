from rest_framework.routers import DefaultRouter
from django.urls import path
from app_test.api.views import (
    TestViewSet,
    QuestionViewSet,
    UserAnswerViewSet,
    UserViewSet,
    UserProfileView,
    ActiveQuestionView,
    result
)

# router.register(r'manager-test', ManagerTestViewSet, basename='manager-test')
# router.register(r'manager-question', ManagerQuestionViewSet, basename='manager-question')
# router.register(r'question', QuestionViewSet, basename='question')
# router.register(r'answer', AnswerViewSet, basename='answer')
router = DefaultRouter()
router.register(r'test', TestViewSet, basename='test')
router.register(r'user-answer', UserAnswerViewSet, basename='user-answer')
router.register(r'user', UserViewSet, basename='user')
urlpatterns = router.urls

urlpatterns += [
    path('result/<int:test_id>/', result),
    path('profile/me/', UserProfileView.as_view({'get': 'retrieve'})),
    path('get-active-question/', ActiveQuestionView.as_view({'get': 'retrieve'}))
]