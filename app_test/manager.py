from django.db import models
from django.db.models import Q, Sum, FloatField
from django.db.models.functions import Coalesce, Round


from django.db import models
from django.utils import timezone

class UserQuerySet(models.QuerySet):
    def online(self):
        """فیلتر کردن کاربران آنلاین (کاربرانی که فعالیت اخیرشان در 10 ثانیه گذشته بوده است)"""
        last_10_seconds = timezone.now() - timezone.timedelta(seconds=10)
        return self.filter(useractivity__last_activity__gt=last_10_seconds)

    def filter(self, *args, **kwargs):
        """پیاده‌سازی فیلتر برای بررسی فیلد آنلاین"""
        # چک کردن آیا فیلتر آنلاین بودن داده شده یا نه
        online = kwargs.pop('online', None)
        queryset = super().filter(*args, **kwargs)

        if online is not None:
            if online:
                # فیلتر کردن کاربران آنلاین
                return queryset.online()
            else:
                # فیلتر کردن کاربران آفلاین (فعالیت بیشتر از 10 ثانیه پیش بوده است)
                last_10_seconds = timezone.now() - timezone.timedelta(seconds=10)
                return queryset.filter(useractivity__last_activity__lte=last_10_seconds)

        return queryset


class UserManager(models.Manager):
    def with_active_test_score(self):
        return self.get_queryset().annotate(
            active_test_score=Round(
                Coalesce(Sum(
                    'useranswer__score',
                    filter=Q(useranswer__answer__question__test__status='active')
                ), 0, output_field=FloatField()
            ),
            3
        )
    )

    def get_queryset(self):
        """بازگرداندن QuerySet سفارشی"""
        return UserQuerySet(self.model, using=self._db)