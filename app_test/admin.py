import nested_admin
from django.contrib import admin
from app_test.models import Test, Question, Answer, UserAnswer, UserActivity, UserTestResult


class AnswerInline(nested_admin.NestedTabularInline):
    model = Answer
    extra = 0


class QuestionInline(nested_admin.NestedTabularInline):
    model = Question
    extra = 0
    inlines = [AnswerInline]


@admin.register(Test)
class TestAdmin(nested_admin.NestedModelAdmin):
    search_fields = ['title']
    list_display = ['title', 'status']
    list_editable = ['status']
    list_filter = ['status']
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_filter = ['test']


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    pass


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'last_activity']


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ['user', 'answer', 'answer__is_answer', 'score']
    list_filter = ['answer__question__test']


@admin.register(UserTestResult)
class UserTestResultAdmin(admin.ModelAdmin):
    list_display = ['test', 'user', 'score']

