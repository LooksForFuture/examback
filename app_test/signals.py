import threading
from django.utils import timezone
from datetime import timedelta, datetime, timezone
from django.db.models import Sum
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from app_test.models import Question, Answer, UserAnswer, Test
from django.contrib.auth import get_user_model
from app_notification.models import Notification
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from json import dumps

User = get_user_model()
channel_layer = get_channel_layer()

def reset_question_start_datetime(question):
    question.start_datetime = None
    question.save()

def notify_about_question(question):
    answers = Answer.objects.filter(question=question)
    answer_set = []
    for answer in answers:
        answer_set.append({
            "id":answer.id,
            "question":question.id,
            "title":answer.title,
        })

    group_name = str(question.test.id)
    message_data = {
        "type": "question_started",
        "message": {
            "id":question.id,
            "number":question.number,
            "answer_set":answer_set,
            "title":question.title,
            "start_datetime":str(question.start_datetime),
            "duration_time":question.duration_time,
            "test":question.test.id,
        },
    }
    async_to_sync(channel_layer.group_send)(group_name, message_data)

@receiver(pre_save, sender=Question, weak=False)
def pre_save_question(sender, instance, *args, **kwargs):
    if instance.start_datetime:
        instance.start_datetime += timedelta(seconds=13)

@receiver(post_save, sender=Question, weak=False)
def post_save_question(sender, instance, created, **kwargs):
    if not instance.start_datetime or instance.test.status != "active":
        return

    time_to_start = (instance.start_datetime - datetime.now(instance.start_datetime.tzinfo)).total_seconds() - 10
    if time_to_start >= 0:
        threading.Timer(
            time_to_start,
            notify_about_question,
            args=(instance, )
        ).start()


@receiver(post_save, sender=UserAnswer, weak=False)
def post_save_user_answer(sender, instance, created, **kwargs):
    if instance.result:
        total_score = instance.result.useranswer_set.aggregate(total_score=Sum('score')).get('total_score')
        instance.result.score = total_score
        instance.result.save()


@receiver(pre_save, sender=Test, weak=False)
def pre_save_test(sender, instance, *args, **kwargs):
    if instance.pk:
        old_instance = Test.objects.get(pk=instance.pk)
        if old_instance.status != instance.status and instance.status == 'active':
            Notification.objects.bulk_create([
                Notification(
                    title=instance.title,
                    description="برای شرکت در آزمون لطفا کلیک کنید",
                    receiver=user,
                    url='/'
                )
            for user in User.objects.filter(is_active=True)])

@receiver(post_save, sender=Test, weak=False)
def post_save_test(sender, instance, *args, **kwargs):
    if instance.status == "finished":
        group_name = str(instance.id)
        message_data = {
            "type": "simple_broadcast",
            "message_type":"finished",
            "message": "finished"
        }
        async_to_sync(channel_layer.group_send)(group_name, message_data)
