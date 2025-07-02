from django.utils import timezone
from rest_framework import serializers
from app_test.models import CustomUser
from app_test.models import Test, Question, Answer, UserAnswer, UserTestResult


class ManagerTestSerializer(serializers.ModelSerializer):
    question_set = serializers.SerializerMethodField()

    def get_question_set(self, obj):
        return QuestionSerializer(obj.question_set.all(), many=True).data

    class Meta:
        model = Test
        fields = ['id', 'title', 'status', 'question_set']
        

class TestSerializer(serializers.ModelSerializer):

    class Meta:
        model = Test
        fields = ['id', 'title', 'status']


class MyTestSerializer(serializers.ModelSerializer):

    class Meta:
        model = Test
        fields = ['id', 'title', 'status']


class FinishedTestSerializer(serializers.ModelSerializer):

    usertestresult_set = serializers.SerializerMethodField()

    def get_usertestresult_set(self, obj):
        return QuestionSerializer(obj.usertestresult_set.all(), many=True).data

    class Meta:
        model = Test
        fields = ['title', 'status', 'usertestresult_set']


class ManagerQuestionSerializer(serializers.ModelSerializer):
    number = serializers.IntegerField(required=False)
    answer_set = serializers.SerializerMethodField()

    def get_answer_set(self, obj):
        return AnswerSerializer(obj.answer_set.all(), many=True).data

    class Meta:
        model = Question
        fields = '__all__'




class QuestionSerializer(serializers.ModelSerializer):
    number = serializers.IntegerField(required=False)
    answer_set = serializers.SerializerMethodField()

    def get_answer_set(self, obj):
        return AnswerSerializer(obj.answer_set.all(), many=True).data

    class Meta:
        model = Question
        fields = '__all__'


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'question', 'title']


class UserAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAnswer
        fields = ['answer']


class UserSerializer(serializers.ModelSerializer):
    is_online = serializers.SerializerMethodField()

    def get_is_online(self, obj):
        if hasattr(obj, 'useractivity'):
            last_60_seconds = timezone.now() - timezone.timedelta(seconds=3)
            return obj.useractivity.last_activity > last_60_seconds
        return False

    active_test_score = serializers.FloatField()

    def get_active_test_score(self, obj):
        return obj.active_test_score

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'username', 'is_online', 'active_test_score']


class UserProfileSerializer(UserSerializer):
    
    test_result_list = serializers.SerializerMethodField()

    def get_test_result_list(self, obj):
        return MyUserTestResultSerializer(obj.usertestresult_set.all(), many=True).data

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'username', 'is_online', 'active_test_score', 'test_result_list']


class MyUserTestResultSerializer(serializers.ModelSerializer):
    test = serializers.SerializerMethodField()

    def get_test(self, obj):
        return MyUserTestResultTestSerializer(obj.test).data
    
    class Meta:
        model = UserTestResult
        exclude = ('user', )

class MyUserTestResultTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Test
        fields = '__all__'


class UserTestResultSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    def get_user(self, obj):
        return {
            'username': obj.user.username
        }

    class Meta:
        model = UserTestResult
        fields = '__all__'