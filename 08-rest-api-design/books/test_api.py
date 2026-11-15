import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from .models import Comment, Thread


@pytest.fixture
def client(db):
    call_command('loaddata', 'categories', 'books', 'threads', 'comments', verbosity=0)
    return APIClient()


@pytest.mark.parametrize(('path', 'size'), [('categories/', 7), ('books/', 70), ('threads/', 9)])
def test_lists(client, path, size):
    response = client.get('/api/v1/' + path)
    assert response.status_code == 200
    assert len(response.json()) == size


def test_book_detail(client):
    data = client.get('/api/v1/books/1/').json()
    assert data['category']['name'] == '소설/시/희곡'
    assert data['num_of_threads'] == len(data['threads']) > 0
    assert set(data['threads'][0]) == {'id', 'title', 'content', 'reading_date'}


def test_discussion(client):
    fields = {'title': '기억에 남은 장면', 'content': '인물의 선택을 다시 읽었다.', 'reading_date': '2026-11-13'}
    created = client.post('/api/v1/books/1/threads/', fields)
    assert created.status_code == 201
    pk = created.json()['id']
    url = f'/api/v1/threads/{pk}/'
    fields['title'] = '두 번째 독서'
    assert client.put(url, fields).json()['title'] == fields['title']
    reply = client.post(url + 'comments/', {'content': '저도 공감해요.'})
    assert reply.status_code == 201
    comment_url = f"/api/v1/comments/{reply.json()['id']}/"
    assert client.get(comment_url).json()['thread'] == fields['title']
    assert client.put(comment_url, {'content': '다시 읽어 봤어요.'}).json()['content'] == '다시 읽어 봤어요.'
    assert client.get(url).json()['num_of_comments'] == 1
    assert client.delete(comment_url).status_code == 204
    assert client.get(url).json()['comments'] == []
    client.post(url + 'comments/', {'content': '함께 삭제될 댓글'})
    assert client.delete(url).status_code == 204
    assert not Comment.objects.filter(thread_id=pk).exists()
    assert not Thread.objects.filter(pk=pk).exists()


@pytest.mark.parametrize(('method', 'path', 'code'), [
    ('get', 'books/1/threads/', 405), ('get', 'threads/1/comments/', 405),
    ('post', 'books/', 405), ('post', 'books/1/threads/', 400),
    ('put', 'threads/1/', 400), ('post', 'threads/1/comments/', 400),
    ('get', 'books/9999/', 404), ('get', 'books/search/?q=%20', 400),
])
def test_error_responses(client, method, path, code):
    response = getattr(client, method)('/api/v1/' + path)
    assert response.status_code == code


@pytest.mark.parametrize('query', ['데미안', '한강'])
def test_search(client, query):
    rows = client.get('/api/v1/books/search/', {'q': query}).json()
    assert rows
    for row in rows:
        assert query in row['title'] or query in row['author']
