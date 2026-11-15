from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # 성별 선택자: 왼족은 DB 저장값, 오른쪽은 화면 표시값
    GENDER_CHOICES = [
        ('M', '남성'),
        ('F', '여성'),
        ('O', '기타'),
    ]

    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        blank=True,
    )

    age = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    # 주간 평균 독서 시간: 소수점 한 자리까지 지정
    weekly_reading_hours = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=0,
    )

    # 연간 독서량
    annual_reading_count = models.PositiveIntegerField(default=0)

    # 사진 파일은 media/profiles/에 저장
    profile_image = models.ImageField(
        upload_to='profiles/',
        blank=True,
    )

    # 내가 팔로우하는 사람들
    followings = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='followers',
        blank=True,
    )