from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from django.urls import reverse
from app_test.models import Question
from app_test.models import Test, Question, Answer
from django.utils import timezone
from datetime import timedelta
from freezegun import freeze_time


PASSWORD = ''


class QuestionViewSetTests(APITestCase):
    
    def setUp(self):
        fake = Faker()
        
        # create superuser
        self.admin = User.objects.create_superuser(username='admin', password=PASSWORD)
        
        # create staff user
        self.staff_user = User.objects.create_user(username='staff', password=PASSWORD, is_staff=True)

        # create user1, ..., user10
        users = []
        for i in range(1, 11):
            user = User.objects.create_user(
                username=f'user{i}',
                email=fake.email(),
                password=PASSWORD
            )
            users.append(user)

        # Generate fake tests
        tests = []
        for _ in range(5):
            test = Test.objects.create(
                title=fake.sentence(nb_words=4),
                status='inactive'
            )
            tests.append(test)
        
        # make first test as active
        random_test = tests[0]
        random_test.status = 'active'
        random_test.save()

        # Generate fake questions
        questions = []
        for test in tests:
            for _ in range(10):
                question = Question.objects.create(
                    test=test,
                    title=fake.sentence(nb_words=6),
                )
                questions.append(question)

        # Generate fake answers
        answers = []
        for question in questions:
            for i in range(4):
                answer = Answer.objects.create(
                    question=question,
                    title=fake.sentence(nb_words=5),
                    is_answer=False
                )
                answers.append(answer)
                # make first answer correct
                if i == 0:
                    answer.is_answer = True
                    answer.save()

    def test_swagger_superuser_access(self):
        """
        دسترسی به Swagger برای سوپریوزر
        """
        self.client.login(username='admin', password=PASSWORD)
        response = self.client.get('/api/swagger/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_swagger_staff_user_access(self):
        """
        عدم دسترسی به Swagger برای استف یوزر
        """
        self.client.login(username='staff', password=PASSWORD)
        response = self.client.get('/api/swagger/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_swagger_logged_in_user_access(self):
        """
        عدم دسترسی به Swagger برای کاربر لاگین کرده
        """
        self.client.login(username='user1', password=PASSWORD)
        response = self.client.get('/api/swagger/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_swagger_anonymous_user_access(self):
        """
        عدم دسترسی به Swagger برای کاربر ناشناس
        """
        response = self.client.get('/api/swagger/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_redoc_superuser_access(self):
        """
        دسترسی به Redoc برای سوپریوزر
        """
        self.client.login(username='admin', password=PASSWORD)
        response = self.client.get('/api/redoc/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_redoc_staff_user_access(self):
        """
        عدم دسترسی به Redoc برای استف یوزر
        """
        self.client.login(username='staff', password=PASSWORD)
        response = self.client.get('/api/redoc/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_redoc_logged_in_user_access(self):
        """
        عدم دسترسی به Redoc برای کاربر لاگین کرده
        """
        self.client.login(username='user1', password=PASSWORD)
        response = self.client.get('/api/redoc/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_redoc_anonymous_user_access(self):
        """
        عدم دسترسی به Redoc برای کاربر ناشناس
        """
        response = self.client.get('/api/redoc/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_anonymous_user_can_login(self):
        """
        کاربر ناشناس باید بتواند با اطلاعات ldap اش لاگین کند
        """
        data = {
            'username': '',
            'password': ''
        }
        response = self.client.post('/api/token/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_anonymous_user_can_login(self):
        """
        کاربر ناشناس باید بتواند با یوزرنیم و پسوردی که در جنگو ادمین برایش ساخته شده لاگین کند
        """
        data = {
            'username': 'user1',
            'password': PASSWORD
        }
        response = self.client.post('/api/token/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_logged_in_user_can_login_again_with_token(self):
        """
        کاربری که لاگین کرده باید بتواند دوباره لاگین کند؟
        """
        data = {
            'username': 'user1',
            'password': PASSWORD
        }

        # First login to get the token
        response = self.client.post('/api/token/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        access_token = response.data['access']

        # Set the token in the headers for the next login attempt
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Attempt to login again
        response = self.client.post('/api/token/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_anonymous_user_cannot_refresh_token(self):
        """
        کاربر ناشناس نباید بتواند توکنش را تازه سازی کند
        """
        data = {
            'refresh': 'invalid-refresh-token'
        }
        response = self.client.post('/api/token/refresh/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logged_in_user_can_refresh_token(self):
        """
        کاربری که لاگین کرده باید بتواند توکنش را رفرش کند
        """
        login_data = {
            'username': 'user1',
            'password': PASSWORD
        }
        # Login to get tokens
        response = self.client.post('/api/token/', login_data)
        refresh_token = response.data['refresh']
        
        # Refresh the token
        response = self.client.post('/api/token/refresh/', {'refresh': refresh_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_token_validation_before_one_hour(self):
        """
        توکن قبل از یک ساعت باید معتبر باشد
        """
        protected_url = '/api/test/get-active-question/'
        # اطلاعات ورود کاربر
        data = {
            'username': 'user1',
            'password': PASSWORD
        }
        
        # ورود و دریافت توکن
        response = self.client.post('/api/token/', data)
        access_token = response.data['access']
        
        # ارسال درخواست با توکن تازه دریافت شده
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        initial_response = self.client.get(protected_url)
        self.assertEqual(initial_response.status_code, status.HTTP_200_OK)
        
        # شبیه‌سازی گذشت یک ساعت
        with freeze_time(timedelta(hours=0.99)):
            # ارسال درخواست به یک endpoint محافظت‌شده با توکن بعد از گذشت یک ساعت
            response = self.client.get(protected_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_token_expires_after_one_hour(self):
        """
        توکن پس از یک ساعت باید منقضی شود
        """
        protected_url = '/api/test/get-active-question/'
        # اطلاعات ورود کاربر
        data = {
            'username': 'user1',
            'password': PASSWORD
        }
        
        # ورود و دریافت توکن
        response = self.client.post('/api/token/', data)
        access_token = response.data['access']
        
        # ارسال درخواست با توکن تازه دریافت شده
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        initial_response = self.client.get(protected_url)
        self.assertEqual(initial_response.status_code, status.HTTP_200_OK)
        
        # شبیه‌سازی گذشت یک ساعت
        with freeze_time(timedelta(hours=1)):
            # ارسال درخواست به یک endpoint محافظت‌شده با توکن بعد از گذشت یک ساعت
            response = self.client.get(protected_url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_refresh_token_expires_after_one_day(self):
        """
        رفرش توکن قبل از یک روز نباید منقضی شود
        """
        login_data = {
            'username': 'user1',
            'password': PASSWORD
        }
        response = self.client.post('/api/token/', login_data)
        refresh_token = response.data['refresh']
        
        # شبیه‌سازی گذشت یک ساعت
        with freeze_time(timedelta(days=0.99)):
            # ارسال درخواست به یک endpoint محافظت‌شده با توکن بعد از گذشت یک ساعت
            response = self.client.post('/api/token/refresh/', {'refresh': refresh_token})
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_refresh_token_expires_after_one_day(self):
        """
        رفرش توکن پس از یک روز باید منقضی شود
        """
        login_data = {
            'username': 'user1',
            'password': PASSWORD
        }
        response = self.client.post('/api/token/', login_data)
        refresh_token = response.data['refresh']
        
        # شبیه‌سازی گذشت یک ساعت
        with freeze_time(timedelta(days=1)):
            # ارسال درخواست به یک endpoint محافظت‌شده با توکن بعد از گذشت یک ساعت
            response = self.client.post('/api/token/refresh/', {'refresh': refresh_token})
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_anonymous_user_cannot_see_user_list(self):
        """
        کاربر ناشناس نباید بتواند لیست کاربران را ببیند
        """
        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # def test_logged_in_user_can_see_users_in_exam(self):
    #     """
    #     کاربری که لاگین کرده باید بتواند لیست کاربرانی که در حال شرکت در آزمون هستند را ببیند
    #     """
    #     # TODO: این تست را هنوز ننوشته ایم چون هنوز نمیتوانیم لیست کاربران فعال در یک ازمون را در یک ای پی آی داشته باشیم

    # def test_superuser_can_see_users_in_exam(self):
    #     """
    #     سوپر یوزر باید بتواند لیست کاربرانی که در حال شرکت در آزمون هستند را ببیند
    #     """
    #     # TODO: این تست را هنوز ننوشته ایم چون هنوز نمیتوانیم لیست کاربران فعال در یک ازمون را در یک ای پی آی داشته باشیم







    # def test_anonymous_user_cannot_see_user_details(self):
    #     """
    #     کاربر ناشناس نباید بتواند جزئیات کاربر را ببیند
    #     """
    #     response = self.client.get(f'/api/users/{self.user1.id}/')
    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # def test_logged_in_user_cannot_see_other_user_details(self):
    #     """
    #     کاربری که لاگین کرده نباید بتواند جزئیات کاربر دیگری را ببیند
    #     """
    #     self.client.login(username='user1', password=PASSWORD)
    #     response = self.client.get(f'/api/users/{self.user2.id}/')
    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # def test_superuser_can_see_user_details(self):
    #     """
    #     سوپر یوزر نباید بتواند جزئیات یک کاربر را ببیند
    #     """
    #     self.client.login(username='admin', password=PASSWORD)
    #     response = self.client.get(f'/api/users/{self.user1.id}/')
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)

    # def test_anonymous_user_cannot_edit_user(self):
    #     """
    #     کاربر ناشناس نباید بتواند کاربر را ویرایش کند
    #     """
    #     response = self.client.patch(f'/api/users/{self.user1.id}/', {'username': 'newuser'})
    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # def test_logged_in_user_cannot_edit_other_user(self):
    #     """
    #     کاربری که لاگین کرده نباید بتواند کاربر را ویرایش کند
    #     """
    #     self.client.login(username='user1', password=PASSWORD)
    #     response = self.client.patch(f'/api/users/{self.user2.id}/', {'username': 'newuser'})
    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # def test_superuser_can_edit_user(self):
    #     """
    #     سوپر یوزر نباید بتواند کاربر را ویرایش کند
    #     """
    #     self.client.login(username='admin', password=PASSWORD)
    #     response = self.client.patch(f'/api/users/{self.user1.id}/', {'username': 'newuser'})
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)

    # def test_anonymous_user_cannot_delete_user(self):
    #     """
    #     کاربر ناشناس نباید بتواند کاربر را حذف کند
    #     """
    #     response = self.client.delete(f'/api/users/{self.user1.id}/')
    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # def test_logged_in_user_cannot_delete_other_user(self):
    #     """
    #     کاربری که لاگین کرده نباید بتواند کاربر را حذف کند
    #     """
    #     self.client.login(username='user1', password=PASSWORD)
    #     response = self.client.delete(f'/api/users/{self.user2.id}/')
    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # def test_superuser_can_delete_user(self):
    #     """
    #     سوپر یوزر نباید بتواند کاربر را حذف کند
    #     """
    #     self.client.login(username='admin', password=PASSWORD)
    #     response = self.client.delete(f'/api/users/{self.user1.id}/')
    #     self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # def test_user_goes_offline_after_10_seconds(self):
    #     """
    #     وضعیت آنلاین بودن هر کاربر پس از گذشت ۱۰ ثانیه باید آفلاین شود
    #     """
    #     self.client.login(username='user1', password=PASSWORD)
    #     response = self.client.get('/api/users/online-status/')
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)

    #     # Simulate passing of time (10 seconds)
    #     import time
    #     time.sleep(10)

    #     # Check if user is offline
    #     response = self.client.get('/api/users/online-status/')
    #     self.assertEqual(response.data['online'], False)











    # تست هایی که کلا از قبل داشته ایم و درست هستند
    # def test_anonymous_user_can_not_see_test_list(self):
    #     """تست اینکه کاربران ناشناس نباید بتوانند لیست آزمون ها را ببینند"""
    #     test_list_url = reverse('test-list')
    #     response = self.client.get(test_list_url)
    #     self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    #     pass

    # def test_authenticated_user_can_see_test_list(self):
    #     """تست اینکه کاربران عادی بتوانند لیست سوالات را مشاهده کنند"""
    #     self.client.login(username='user1', password=PASSWORD)
    #     test_list_url = reverse('test-list')
    #     response = self.client.get(test_list_url)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    # def test_superuser_can_see_test_list(self):
    #     """تست اینکه سوپر یوزر بتواند لیست تست ها را ببیند"""
    #     self.client.login(username='admin', password=PASSWORD)
    #     test_list_url = reverse('test-list')
    #     response = self.client.get(test_list_url)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)

    # def test_anonymous_user_can_not_see_test_detail(self):
    #     """تست اینکه کاربر ناشناس نباید بتواند جزئیات تست را ببیند"""
    #     test_detail_url = reverse('test-detail', args=(1, ))
    #     response = self.client.get(test_detail_url)
    #     self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # def test_authenticated_user_can_see_test_detail(self):
    #     """تست اینکه سوپریوزر بتواند جزئیات یک تست را ببیند"""
    #     self.client.login(username='admin', password=PASSWORD)
    #     test_detail_url = reverse('test-detail', args=(1, ))
    #     response = self.client.get(test_detail_url)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    # def test_superuser_can_see_test_detail(self):
    #     """تست اینکه سوپریوزر بتواند جزئیات یک تست را ببیند"""
    #     self.client.login(username='admin', password=PASSWORD)
    #     test_detail_url = reverse('test-detail', args=(1, ))
    #     response = self.client.get(test_detail_url)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    # پایان تست هایی که از قبل داشته ایم و درست هستند
#####################################3
    # این تست ها رو اصلا نمیدونم درست هستند یا نه
    # def test_non_admin_cannot_create_question(self):
    #     """تست اینکه کاربران عادی نتوانند سوال جدیدی ایجاد کنند"""
    #     self.client.login(username='testuser', password='testpass')
    #     data = {'text': 'Unauthorized Question'}
    #     response = self.client.post(self.question_list_url, data)
    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # def test_admin_can_update_question(self):
    #     """تست اینکه فقط ادمین بتواند سوال را ویرایش کند"""
    #     self.client.login(username='adminuser', password='adminpass')
    #     data = {'text': 'Updated Question'}
    #     response = self.client.put(self.question_detail_url, data)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.question.refresh_from_db()
    #     self.assertEqual(self.question.text, 'Updated Question')

    # def test_non_admin_cannot_update_question(self):
    #     """تست اینکه کاربران عادی نتوانند سوال را ویرایش کنند"""
    #     self.client.login(username='testuser', password='testpass')
    #     data = {'text': 'Attempted Update'}
    #     response = self.client.put(self.question_detail_url, data)
    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # def test_admin_can_delete_question(self):
    #     """تست اینکه فقط ادمین بتواند سوال را حذف کند"""
    #     self.client.login(username='adminuser', password='adminpass')
    #     response = self.client.delete(self.question_detail_url)
    #     self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # def test_non_admin_cannot_delete_question(self):
    #     """تست اینکه کاربران عادی نتوانند سوال را حذف کنند"""
    #     self.client.login(username='testuser', password='testpass')
    #     response = self.client.delete(self.question_detail_url)
    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
