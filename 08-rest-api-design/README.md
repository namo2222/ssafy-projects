# 도서 검색에서 감상글·댓글 작성으로 이어지는 독서 커뮤니티 API

제목이나 저자로 책을 검색하고, 도서별 감상글과 댓글을 JSON API로 조회·작성·수정·삭제합니다.

![Django](https://img.shields.io/badge/Django-092E20) ![Django REST Framework](https://img.shields.io/badge/Django_REST_Framework-A30000)

팀: 이남호 · 김현재

## 프로젝트 개요

읽을 책을 찾을 때는 간결한 도서 목록을, 책을 고른 뒤에는 감상글까지 포함한 상세 정보를 제공합니다. 감상글에 댓글을 남기고 목록과 개수를 함께 조회해 독서 대화를 이어가는 API입니다.

## 기술 스택

| 기술 | 사용한 곳 |
| --- | --- |
| Python · Django | [모델](books/models.py)에서 카테고리·도서·감상글·댓글 관계를 정의합니다. |
| Django REST Framework | [Serializer](books/serializers.py)에서 입력을 검증하고 목록·상세 응답 필드를 구성합니다. |
| Django ORM | [조회 뷰](books/views.py)에서 제목·저자 검색과 관련 데이터 조회를 처리합니다. |

## 핵심 구현

### 검색과 상세 조회에 맞춘 응답

`GET /api/v1/books/search/?q=검색어`는 제목 또는 저자에 검색어가 포함된 도서를 PK 순으로 반환하며 빈 검색어에는 400을 반환합니다. 목록에는 ID·제목·저자·ISBN·표지만 담고, 도서 상세에는 카테고리와 감상글 목록·개수를 추가합니다. 상세 조회에서 카테고리는 `select_related`, 감상글은 `prefetch_related`로 가져옵니다. [검색·상세 조회](books/views.py), [목록·상세 응답](books/serializers.py)

### 도서에 연결된 감상글 작성과 편집

`POST /api/v1/books/{book_id}/threads/`에 제목·본문·독서일을 보내면 URL의 도서와 연결해 저장하고 201을 반환합니다. 생성한 감상글은 `/api/v1/threads/{thread_id}/`에서 GET·PUT·DELETE로 조회·수정·삭제합니다. PUT은 필수 필드를 모두 요구하며 삭제 성공 시 본문 없이 204를 반환합니다. [감상글 처리](books/views.py)

### 댓글과 대화 상태 조회

`POST /api/v1/threads/{thread_id}/comments/`에 `content`를 보내 댓글을 작성합니다. `/api/v1/comments/{comment_id}/`에서 개별 댓글을 조회·수정·삭제하고, 감상글 상세에서 댓글 목록과 `num_of_comments`를 확인합니다. 부모 삭제 시 하위 데이터도 삭제되므로 감상글을 삭제하면 댓글이 함께 삭제됩니다. 제공 코드에는 작성자 연결과 소유권 검사가 없으며, 전체 API 접근 권한은 누락된 설정에서 별도로 확인해야 합니다. [댓글 처리](books/views.py), [관계와 삭제 규칙](books/models.py)

## 실행 방법

제공 자료에는 `mypjt/settings.py`, 의존성 파일, `pytest.ini`, 초기 데이터 fixture가 없습니다. 원본에서 복구하고 Python 환경과 Django·Django REST Framework를 준비합니다. 설정에는 `books`·`rest_framework` 앱과 DB 구성이 필요합니다.

의존성을 설치한 뒤 `manage.py`가 있는 저장소 루트에서 실행합니다. 아래 `loaddata`는 `categories`·`books`·`threads`·`comments` fixture를 복구했을 때 사용할 명령입니다.

```bash
python manage.py migrate
python manage.py loaddata categories books threads comments
python manage.py runserver
```

`http://127.0.0.1:8000/api/v1/books/`에서 도서 목록을 확인하고 반환된 ID로 `/api/v1/books/{book_id}/`를 조회합니다. fixture를 불러오지 않으면 도서를 조회하거나 감상글을 연결할 데이터가 없으며, 이 API는 도서 생성 엔드포인트를 제공하지 않습니다. 결과는 각 API의 JSON 응답으로 확인합니다.

`books/test_api.py`에는 검색·작성·수정·삭제·오류 응답을 검사하는 테스트가 있습니다. 실행하려면 pytest·pytest-django와 Django 테스트 설정, 위 fixture가 필요하며 이번 문서 작성에서는 서버와 테스트를 실행하지 않았습니다.
