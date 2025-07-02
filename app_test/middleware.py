from django.utils.timezone import now
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from app_test.models import UserActivity


class UpdateLastActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_auth = JWTAuthentication()

    def __call__(self, request):
        try:
            authentication = self.jwt_auth.authenticate(request)
            if authentication is not None:
                user, _ = authentication
                if user:
                    if hasattr(user, 'useractivity'):
                        user.useractivity.last_activity = now()
                        user.useractivity.save()
                    else:
                        UserActivity.objects.create(user=user, last_activity=now())
        except InvalidToken:
            print('InvalidToken, error')
        response = self.get_response(request)
        return response
