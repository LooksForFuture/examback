from django.utils.timezone import now, timedelta
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model


def get_online_users():
    User = get_user_model()
    active_sessions = Session.objects.filter(expire_date__gte=now())
    online_users = []
    for session in active_sessions:
        data = session.get_decoded()
        last_activity = data.get('last_activity')
        if last_activity:
            last_activity_time = datetime.datetime.strptime(last_activity, '%Y-%m-%d %H:%M:%S')
            if now() - timedelta(minutes=1) <= last_activity_time:  # 1 دقیقه اخیر
                user_id = data.get('_auth_user_id')
                if user_id:
                    online_users.append(User.objects.get(id=user_id))
    return online_users
