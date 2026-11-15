from django.db import models

# Create your models here.
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class Book(models.Model):
    # 도서를 등록한 사용자
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='books',
    )

    title = models.CharField(max_length=200)
    description = models.TextField()

    # 예: 4.5점
    rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(5),
        ],
    )

    # 실제 책의 작가 이름
    author = models.CharField(max_length=100)

    def __str__(self):
        return self.title


class Thread(models.Model):
    # 감상글을 작성한 사용자
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='threads',
    )

    # 감상글의 대상 도서
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='threads',
    )

    title = models.CharField(max_length=200)
    content = models.TextField()
    reading_date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 이 감상글을 좋아요 한 사용자들
    like_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='liked_threads',
        blank=True,
    )

    def __str__(self):
        return self.title