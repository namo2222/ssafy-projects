# 독서 감상을 나누고 후속 질문 두 개를 받는 커뮤니티

도서에 감상글을 남기고 다른 독자와 교류하며, 내가 쓴 감상을 이어 쓸 AI 질문을 받습니다.

![Django](https://img.shields.io/badge/Django-092E20) ![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.3-7952B3)

팀: 이남호 · 최성민

## 프로젝트 개요

같은 책을 읽은 회원들이 각자의 감상을 남기고 서로의 독서 기록을 살펴보는 서비스입니다. 감상을 더 쓰고 싶을 때는 작성한 글을 바탕으로 후속 질문 두 개를 요청할 수 있습니다.

## 기술 스택

| 기술 | 사용한 곳 |
| --- | --- |
| Python · Django | [도서·감상글 뷰](books/views.py)에서 폼 검증, 작성자 권한 검사와 저장을 처리합니다. |
| GMS API | [질문 생성](books/ai.py)에서 환경변수로 지정한 모델에 감상글을 전달합니다. |
| urllib.request · json (Python 표준 라이브러리) | [API 통신](books/ai.py)에서 HTTP 요청과 JSON 직렬화를 처리합니다. |
| Django Templates · Bootstrap 5.3.3 · JavaScript | [감상글 상세](books/templates/books/thread_detail.html)에서 질문 결과와 생성 대기 상태를 표시합니다. |

## 핵심 구현

### 같은 책에 감상글을 남기고 작성자별로 편집

로그인한 회원은 다른 회원이 등록한 책에도 제목·본문·독서일을 담은 감상글을 작성합니다. 도서와 감상글은 각각의 작성자만 수정·삭제할 수 있도록 서버에서 권한을 검사합니다. 도서 평점은 등록자가 입력한 값이며 회원 평점의 집계는 아닙니다. 도서 등록자가 탈퇴하면 그 도서에 다른 회원이 쓴 감상글도 함께 삭제됩니다. [등록·편집과 권한 검사](books/views.py), [도서·감상글 관계](books/models.py)

### 내 감상을 이어 쓰는 AI 질문

감상글 작성자가 버튼을 누르면 책 제목과 감상글 제목·본문을 GMS API로 보내고, 비어 있지 않은 응답 줄이 정확히 두 개인지 확인합니다. 질문이나 오류 안내는 세션에 보관하여 상세 화면을 새로고침할 때 재호출하지 않습니다. 다른 글에서 질문을 생성하면 이전 세션 결과를 덮어쓰며, 감상글 수정 후 기존 질문을 자동으로 갱신하지는 않습니다. 요청 중에는 버튼을 비활성화하고 대기 상태를 표시합니다. [질문 생성·응답 검사](books/ai.py), [세션 저장과 작성자 제한](books/views.py), [질문 화면](books/templates/books/thread_detail.html)

### 독서 프로필과 회원 간 교류

프로필에서 사진·독서 시간·연간 독서량·작성한 감상글을 확인합니다. 로그인한 회원은 자신을 제외한 다른 회원의 팔로우를 추가·취소하고 감상글에 좋아요를 누르거나 취소할 수 있습니다. 프로필은 로그인 없이도 조회할 수 있으며 이메일 등 등록 정보가 표시됩니다. [프로필·팔로우 처리](accounts/views.py), [프로필 표시](accounts/templates/accounts/profile.html), [좋아요 처리](books/views.py)

## 실행 방법

제공 자료에는 `mypjt/settings.py`와 프로젝트 의존성 파일, 초기 데이터가 없어 그대로 실행할 수 없습니다. 원본 설정·의존성을 복구하고 Python 환경을 준비합니다. 설정에서 `accounts`·`books` 앱, `AUTH_USER_MODEL = 'accounts.User'`, 공통 템플릿·세션·DB 및 `MEDIA_ROOT`·`MEDIA_URL`을 확인해야 합니다. 이미지 필드에는 Pillow도 필요합니다. 기존 README는 SQLite를 명시하지만 DB 설정은 자료에 없습니다.

AI 요청은 환경변수 `GMS_KEY`, `GMS_BASE_URL`, `MODEL`을 읽습니다. 기존 README는 `manage.py` 옆 `.env`를 안내하지만 제공 코드에는 `.env` 로더가 없어, 환경변수를 직접 설정하거나 복구한 설정의 로딩 처리를 확인해야 합니다. 접속 주소와 모델은 사용 가능한 GMS 값으로 준비합니다.

원본 의존성을 설치한 뒤 `manage.py`가 있는 저장소 루트에서 실행합니다.

```bash
python manage.py migrate
python manage.py runserver
```

`http://127.0.0.1:8000/books/`에서 도서를 확인합니다. `/accounts/signup/`에서 가입한 뒤 도서와 감상글을 작성하고, 본인 감상글 상세의 ‘질문 생성’을 누르면 결과가 같은 화면에 표시됩니다. 서버·API·테스트를 실행한 검증은 수행하지 않았습니다.
