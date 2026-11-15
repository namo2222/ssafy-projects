from django import forms
from .models import Book, Thread


# 도서 등록·수정용 Form
class BookForm(forms.ModelForm):
    class Meta:
        model = Book

        fields = (
            'title',
            'description',
            'rating',
            'author',
        )

        labels = {
            'title': '도서 제목',
            'description': '도서 설명',
            'rating': '평점',
            'author': '저자',
        }


# 쓰레드 작성·수정용 Form
class ThreadForm(forms.ModelForm):
    class Meta:
        model = Thread

        fields = (
            'title',
            'content',
            'reading_date',
        )

        labels = {
            'title': '쓰레드 제목',
            'content': '내용',
            'reading_date': '독서일',
        }

        widgets = {
            'reading_date': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date'},
            ),
        }