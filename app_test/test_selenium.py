"""
python manage.py test app_test.test_selenium
"""
import sys
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
from django.test import LiveServerTestCase
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from colorama import Fore, Style
import time
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import environ
from pathlib import Path
from datetime import timedelta
from app_test.models import Test


env = environ.Env()
environ.Env.read_env('.env')


PASSWORD = 'asdf@1234'
QUESTION_DURATION_TIME = 5

class MySeleniumTests(LiveServerTestCase):
    def init_db(self):
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
                    duration_time=QUESTION_DURATION_TIME,
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

    @classmethod
    def get_kwargs(cls, key, default_value):
        for arg in sys.argv:
            if arg.startswith(f"{key}="):
                return arg.split("=")[1]  # بازگرداندن URL
        return default_value

    @classmethod
    def setUpClass(cls):
        DEBUG = env('DEBUG', bool)
        if DEBUG:
            print(Fore.RED + "DEBUG is True! set to False" + Style.RESET_ALL)
        cls.port = 8000
        cls.frontend_url = env('FRONTEND_URL', str)
        super().setUpClass()
        
    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'browser') and cls.browser:
            cls.browser.quit()
        super().tearDownClass()

    def setUp(self):
        self.init_db()
        print(Fore.GREEN + "DB initiated!" + Style.RESET_ALL)
        self.browser = webdriver.Chrome()  # مرورگر را باز کنید
        super().setUp()  # فراخوانی متد والد (اختیاری)

    def tearDown(self):
        self.browser.quit()  # مرورگر را ببندید
        super().tearDown()  # فراخوانی متد والد (اختیاری)


        
    def login(self):
        username_field = self.browser.find_element(By.NAME, "email-username")
        username_field.send_keys("user1")
        username_field = self.browser.find_element(By.NAME, "password")
        username_field.send_keys("asdf@1234")
        login_button = self.browser.find_element(By.CSS_SELECTOR, "[data-selenium-id='btn-login']")
        login_button.click()

    def test_login_page_visibility_for_anonymous_user(self):
        """
        کاربر ناشناس باید به صفحه لاگین هدایت شود
        """
        self.browser.get(self.frontend_url)
        login_page_is_visible = WebDriverWait(self.browser, 10).until(
            EC.text_to_be_present_in_element((By.TAG_NAME, 'body'), 'به سامانه آزمون خوش آمدید!')
        )
        self.assertEqual(login_page_is_visible, True)  # جایگزین با عنوان واقعی صفحه

    def test_login_page_visibility_for_anonymous_user(self):
        """
        کاربری که لاگین کرده باید صفحه انتظار را ببیند
        """
        self.browser.get(self.frontend_url)
        login_page_is_visible = WebDriverWait(self.browser, 10).until(
            EC.text_to_be_present_in_element((By.TAG_NAME, 'body'), 'به سامانه آزمون خوش آمدید!')
        )
        if login_page_is_visible:
            self.login()
            please_wait = WebDriverWait(self.browser, 10).until(
                EC.text_to_be_present_in_element((By.CSS_SELECTOR, "[data-selenium-id='please wait']"), 'لطفا کمی صبر کنید تا شروع شود')
            )
            self.assertEqual(please_wait, True)

    def test_question(self):
        self.browser.get(self.frontend_url)
        # صبر میکنیم تا صفحه لاگین نمایش داده شود
        login_page_is_visible = WebDriverWait(self.browser, 10).until(
            EC.text_to_be_present_in_element((By.TAG_NAME, 'body'), 'به سامانه آزمون خوش آمدید!')
        )
        # اگر صفحه لاگین نمایش داده شد
        if login_page_is_visible:
            self.login()
            # صبر میکنیم تا صفحه انتظار ظاهر شود
            please_wait = WebDriverWait(self.browser, 10).until(
                EC.text_to_be_present_in_element((By.CSS_SELECTOR, "[data-selenium-id='please wait']"), 'لطفا کمی صبر کنید تا شروع شود')
            )
            self.assertEqual(please_wait, True)

            # چک میکنیم که فقط یک آزمون فعال باشد
            count = Test.objects.filter(status='active').count()
            self.assertEqual(count, 1)

            # اولین سوال از آزمون فعال را فعال میکنیم
            active_test = Test.objects.filter(status='active').first()
            first_question = active_test.question_set.first()
            first_question.start_datetime = timezone.now()
            first_question.save()

            # یک کمی بیشتز از یک ثانیه صبر میکنیم تا تایمر ظاهر شود
            WebDriverWait(self.browser, 1.5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-selenium-id="count-down-timer"]'))
            )
            
            remaining_time_element = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-selenium-id="remaining-time"]'))
            )

            answer = first_question.answer_set.get(is_answer=True).title
            answer_input = self.browser.find_element(By.XPATH, f"//*[contains(text(), '{answer}')]")
            answer_input.click()

            submit = self.browser.find_element(By.CSS_SELECTOR, '[data-selenium-id="submit"]')
            submit.click()
            
            please_wait = WebDriverWait(self.browser, QUESTION_DURATION_TIME + 1).until(
                EC.text_to_be_present_in_element((By.CSS_SELECTOR, "[data-selenium-id='please wait']"), 'لطفا کمی صبر کنید تا شروع شود')
            )

            # سه ثانیه صبر میکنیم تا مطمئن بشیم که دوباره به صفحه سوال برنمیگردیم
            element_still_visible = False
            for _ in range(3):
                # بررسی وجود المان
                is_displayed = self.browser.find_element(By.CSS_SELECTOR, "[data-selenium-id='please wait']").is_displayed()
                if is_displayed:
                    time.sleep(1)  # منتظر بمانید و دوباره بررسی کنید
                    element_still_visible = True
                    break
            self.assertEqual(element_still_visible, True)
