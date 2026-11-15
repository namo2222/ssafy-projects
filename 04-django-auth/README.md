# 기분을 입력하면 등록 도서를 추천하는 도서 관리 서비스

도서를 등록·검색하고 현재 기분이나 상황에 맞는 책과 추천 이유를 확인합니다.

![Django](https://img.shields.io/badge/Django-5.2-092E20) ![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.3-7952B3)

## 프로젝트 개요

읽을 책을 고를 때 현재 상황을 문장으로 입력하면 등록된 도서 안에서 추천을 받습니다. Django 도서 관리와 회원 인증을 연결하고, 저장한 도서 정보를 GMS API의 추천 후보로 활용합니다.

## 기술 스택

| 기술 | 사용한 곳 |
| --- | --- |
| Python · Django | [도서 뷰](mypjt/books/views.py)에서 ORM 조회와 폼 검증을 처리합니다. |
| GMS API · OpenAI Python 클라이언트 | [추천 요청](mypjt/books/views.py)에서 `gpt-5-nano`를 호출합니다. |
| HTML · Django Template · Bootstrap 5.3.3 | [공통 템플릿](mypjt/templates/base.html)에서 화면과 인증 메뉴를 구성합니다. |
| json (Python 표준 라이브러리) | [추천 응답 처리](mypjt/books/views.py)에서 JSON을 파싱합니다. |

## 핵심 구현

### 등록 도서에 한정한 AI 추천

로그인 사용자가 기분이나 상황을 300자 이내로 입력하면 PK 내림차순 최대 30권의 제목·저자·설명 앞 200자를 API에 전달합니다. 응답의 ID를 후보 도서와 대조하고 중복과 빈 추천 이유를 제외해 최대 3권을 표시합니다. 추천 이유는 AI가 생성하므로 실제 책 내용과 다를 수 있습니다. [추천 요청·응답 검증](mypjt/books/views.py), [추천 카드와 상세 링크](mypjt/books/templates/books/recommend.html)

### 제목 검색과 도서 편집

검색어가 제목에 포함된 도서를 조회하고 상세 화면에서 설명·평점·저자를 확인합니다. 등록·수정은 같은 `BookForm`을 사용하며 수정 시 `instance`로 기존 도서를 갱신합니다. 편집은 로그인이 필요하고 삭제는 POST만 허용합니다. 사용자별 소유권 제한은 없으며, 목록의 정렬 선택 UI에 대응하는 서버 정렬 처리는 없습니다. [도서 조회·편집](mypjt/books/views.py), [도서 입력 폼](mypjt/books/forms.py)

### 회원 인증과 계정 관리

회원가입 후 자동 로그인하며 이름·이메일 수정, 비밀번호 변경, 탈퇴를 제공합니다. 비밀번호 변경 후에는 세션 인증 정보를 갱신하고 로그아웃·탈퇴는 로그인한 사용자의 POST 요청으로 처리합니다. [회원 처리](mypjt/accounts/views.py), [수정 가능 필드](mypjt/accounts/forms.py)

## 실행 방법

제공 자료에는 `mypjt/mypjt/settings.py`, 의존성 파일, DB·초기 도서 데이터가 없어 그대로 실행할 수 없습니다. 원본 프로젝트의 설정과 의존성 목록을 복구하고 해당 의존성이 지원하는 Python 환경을 준비해야 합니다. Django 5.2는 마이그레이션 생성 주석과 기존 README에 기재된 버전이며, 설치 버전은 검증하지 않았습니다. DB는 기존 README에 SQLite로 적혀 있지만 실제 설정은 확인할 수 없습니다.

설정에서 `accounts`·`books` 앱, 사용자 모델 `accounts.User`, 공통 템플릿 경로와 DB 연결을 확인합니다. AI 추천에는 유효한 GMS 접속 정보가 필요하며 Django settings에 `GMS_API_KEY`와 `GMS_BASE_URL`을 제공해야 합니다. 기존 README는 `manage.py` 옆 `.env` 사용을 안내하지만 이를 로드하는 코드는 자료에 없어 별도 확인이 필요합니다.

원본 의존성을 설치한 뒤 저장소 루트의 `mypjt` 폴더에서 실행합니다.

```bash
cd mypjt
python manage.py migrate
python manage.py runserver
```

서버 실행 후 `http://127.0.0.1:8000/books/`에서 목록을 확인합니다. `/accounts/signup/`에서 가입한 뒤 도서를 등록하고 `/books/recommend/`에서 추천을 요청합니다. 결과는 추천 화면에 표시됩니다. 서버와 외부 API를 실행한 검증은 수행하지 않았습니다.
