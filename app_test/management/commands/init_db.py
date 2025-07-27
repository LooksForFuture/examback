from django.db.models import Q
import random
from django.core.management.base import BaseCommand
from faker import Faker
from app_test.models import Test, Question, Answer, UserAnswer, UserTestResult
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate fake data for Test, Question, Answer, and UserAnswer models'

    def handle(self, *args, **kwargs):
        fake = Faker()
        admin = User.objects.get(username='admin')
        User.objects.filter(~Q(username='admin')).delete()
        Test.objects.all().delete()
        Question.objects.all().delete()
        Answer.objects.all().delete()
        UserAnswer.objects.all().delete()
        UserTestResult.objects.all().delete()

        # Generate fake users
        users = [admin]
        for _ in range(10):
            user = User.objects.create_user(
                username=fake.user_name(),
                email=fake.email(),
                password=''
            )
            users.append(user)
        self.stdout.write(self.style.SUCCESS(f'Created {len(users)} fake users.'))

        # Generate fake tests
        tests = []
        for _ in range(5):
            test = Test.objects.create(
                title=fake.sentence(nb_words=4),
                status='inactive'
            )
            tests.append(test)
        random_test = random.choice(tests)
        random_test.status = 'active'
        random_test.save()
        self.stdout.write(self.style.SUCCESS(f'Created {len(tests)} fake tests.'))

        # Generate fake questions
        questions = []
        for test in tests:
            for _ in range(10):
                question = Question.objects.create(
                    test=test,
                    title=fake.sentence(nb_words=6),
                )
                questions.append(question)
        self.stdout.write(self.style.SUCCESS(f'Created {len(questions)} fake questions.'))

        # Generate fake answers
        answers = []
        for question in questions:
            for _ in range(4):
                answer = Answer.objects.create(
                    question=question,
                    title=fake.sentence(nb_words=5),
                    is_answer=random.choice([True, False])
                )
                answers.append(answer)
        self.stdout.write(self.style.SUCCESS(f'Created {len(answers)} fake answers.'))

        # Generate fake user answers
        user_answers = []
        for user in users:
            for _ in range(5):
                answer = random.choice(answers)
                user_answer = UserAnswer.objects.create(
                    user=user,
                    answer=answer,
                    create_datetime=timezone.now() - timedelta(days=random.randint(1, 30)),
                    score=1
                )
                user_answers.append(user_answer)
        self.stdout.write(self.style.SUCCESS(f'Created {len(user_answers)} fake user answers.'))

        for user in users:
            user_test_ids = user.useranswer_set.values_list('answer__question__test', flat=True)
            for test in Test.objects.filter(id__in=user_test_ids):
                score = sum(user.useranswer_set.filter(answer__question__test=test).values_list('score', flat=True))
                user_answer = UserTestResult.objects.create(
                    user=user,
                    test=test,
                    score=score
                )
                user_answers.append(user_answer)
        self.stdout.write(self.style.SUCCESS(f'Created {len(user_answers)} fake user answers.'))