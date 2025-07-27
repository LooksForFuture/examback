from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from app_test.models import CustomUser
from app_test.models import Test, Question, Answer, UserAnswer, UserTestResult
from app_test.api.serializers import (
    TestSerializer,
    QuestionSerializer,
    UserSerializer,
    UserProfileSerializer,
    ManagerTestSerializer,
    ManagerQuestionSerializer,
    UserAnswerSerializer,
    UserTestResultSerializer,
)


class TestViewSet(viewsets.ModelViewSet):
    queryset = Test.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']

    def get_serializer_class(self):
        if self.request.user.is_superuser:
            return ManagerTestSerializer
        return TestSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    permission_classes = [IsAdminUser]
    serializer_class = ManagerQuestionSerializer


class UserAnswerViewSet(viewsets.ModelViewSet):
    queryset = UserAnswer.objects.all()
    serializer_class = UserAnswerSerializer

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def get_queryset(self):
        if self.request.user.is_superuser:
            return super().get_queryset()
        return super().get_queryset().filter(user=self.request.user)

    def perform_create(self, serializer):
        answer = serializer.validated_data.get('answer', None)
        if answer is not None:
            is_before_answered = UserAnswer.objects.filter(answer__question=answer.question, user=self.request.user).count()
            if is_before_answered:
                raise PermissionDenied('مجاز به پاسخ مجدد نیستید')
        serializer.save(user=self.request.user)
        return super().perform_create(serializer)


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CustomUser.with_score.with_active_test_score().filter(online=True).union(
            CustomUser.with_score.with_active_test_score().filter(active_test_score__gt=0)
        ).order_by('-active_test_score')

    def get_permissions(self):
        if self.action == 'list':
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()


class UserProfileView(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        user = CustomUser.with_score.with_active_test_score().get(
            username=self.request.user.username
        )
        return user


class ActiveQuestionView(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return Question.objects.filter(start_datetime__isnull=False).first()


@api_view(['GET'])
def result(request, test_id):
    queryset = UserTestResult.objects.filter(test__id=test_id).order_by('-score')
    data = UserTestResultSerializer(queryset, many=True).data
    return Response(data)