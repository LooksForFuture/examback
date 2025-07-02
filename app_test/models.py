from django.db import models
from django.db.models import Sum
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from app_test.manager import UserManager
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


TEST_STATUS_CHOICES = (
    ('active', 'Active'),
    ('inactive', 'Inactive'),
    ('finished', 'Finished'),
)

class Test(models.Model):
    title = models.CharField(max_length=250, null=True)
    status = models.CharField(choices=TEST_STATUS_CHOICES, max_length=8, null=True, default='inactive')

    def __str__(self):
        return self.title


class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=250, null=True)
    start_datetime = models.DateTimeField(null=True, blank=True)
    duration_time = models.PositiveSmallIntegerField(default=30)

    def save(self, *args, **kwargs):
        if self.start_datetime:
            self.start_datetime += timedelta(seconds=6)
        super().save(*args, **kwargs)

    @property
    def number(self):
        return tuple(
            self.test.question_set.values_list('id', flat=True)
        ).index(self.id) + 1

    def __str__(self):
        return self.title


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=250, null=True)
    is_answer = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class CustomUser(User):
    
    with_score = UserManager()

    @property
    def is_online(self):
        if hasattr(self, 'useractivity'):
            last_60_seconds = timezone.now() - timezone.timedelta(seconds=3)
            return self.useractivity.last_activity > last_60_seconds
        return False
    
    class Meta:
        proxy = True


class UserActivity(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    last_activity = models.DateTimeField(null=True)

    def __str__(self):
        return str(self.last_activity)


class UserAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, null=True)
    create_datetime = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    score = models.FloatField(null=True, blank=True)
    result = models.ForeignKey('UserTestResult', on_delete=models.CASCADE, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.answer and self.answer.question and self.answer.question.start_datetime:
            if self.answer.is_answer:
                self.score = (abs(self.answer.question.duration_time * 1000 - (now() - self.answer.question.start_datetime).total_seconds() * 1000)) / 1000
            else:
                self.score = 0
            result = UserTestResult.objects.filter(test__question__answer=self.answer, user=self.user)
            if result.exists():
                result = result.first()
                self.result = result
            elif self.answer:
                result, created = UserTestResult.objects.get_or_create(test=self.answer.question.test, user=self.user)
                self.result = result
            super().save(*args, **kwargs)

    def __str__(self):
        if hasattr(self.answer, 'title'):
            return self.answer.title
        return '-'


class UserTestResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, null=True)
    score = models.FloatField(null=True, default=0, blank=True)

    def __str__(self):
        return self.test.title