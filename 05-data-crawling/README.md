# 회사명으로 모은 토스증권 댓글을 정제·증강·요약하는 웹 서비스

회사명을 입력하면 매칭된 종목의 커뮤니티 댓글을 수집하고 원본·정제·AI 증강 결과와 요청 시 생성한 요약을 확인합니다.

![Django](https://img.shields.io/badge/Django-092E20) ![Selenium](https://img.shields.io/badge/Selenium-43B02A) ![pandas](https://img.shields.io/badge/pandas-150458)

팀: 이남호 · 최원준

## 프로젝트 개요

종목 커뮤니티의 여러 댓글을 모아 어떤 의견이 있는지 살펴보는 서비스입니다. 수집한 글과 가공한 글을 구분해 비교하고, 필요할 때 저장된 원본 댓글을 바탕으로 요약을 생성합니다.

## 기술 스택

| 기술 | 사용한 곳 |
| --- | --- |
| Python · Django | [분석 뷰](stocks/views.py)에서 수집·가공·저장과 결과 조회를 연결합니다. |
| Selenium | [크롤러](stocks/services/crawler.py)에서 Chrome을 제어하고 댓글 영역을 스크롤합니다. |
| pandas · re (Python 표준 라이브러리) | [전처리](stocks/services/preprocess.py)에서 문자와 길이 조건을 적용합니다. |
| GMS API · OpenAI Python 클라이언트 | [LLM 연결](stocks/services/llm.py)에서 환경변수로 지정한 모델을 호출합니다. |
| HTML · CSS · JavaScript | [결과 템플릿](stocks/templates/stocks/index.html)에서 처리 결과와 요청 상태를 표시합니다. |

## 핵심 구현

### 회사 검색에서 댓글 수집까지

회사명을 검색해 진입한 종목의 커뮤니티에서 동일 텍스트를 제외한 댓글을 최대 20개 수집합니다. 댓글이 들어 있는 내부 스크롤 영역을 찾아 추가 내용을 읽고, 수집 종료 후 브라우저를 닫습니다. 검색어와 원하는 종목이 정확히 일치하는지 별도로 검증하지 않으며, 사이트 화면 구조가 바뀌면 수집에 실패할 수 있습니다. [검색·스크롤 수집](stocks/services/crawler.py), [수집 예외와 종료 처리](stocks/views.py)

### 댓글 정제와 AI 증강 결과 비교

LLM의 엄격한 부적절 표현 기준을 적용한 뒤 문자 정리와 길이 필터를 수행합니다. 길이는 5~76자 범위와 IQR 기준을 함께 적용하되 댓글이 5개 미만이면 고정 범위만 사용합니다. 정제 댓글을 AI로 확장하고 입력과 같은 개수의 비어 있지 않은 문자열인지 검사한 후 원본·정제·증강·부적절 판단 제거 목록을 저장합니다. 필터 응답을 JSON 배열로 해석하지 못하면 댓글을 제거하지 않고 다음 단계로 진행합니다. [필터·정제](stocks/services/preprocess.py), [증강 응답 검증](stocks/services/augment.py), [저장 모델](stocks/models.py)

### 저장된 원본 댓글의 요청형 요약

‘AI 요약 생성’ 버튼의 POST 요청에서 저장된 원본 댓글을 요약하고 결과를 DB에 반영합니다. 이미 요약이 있거나 댓글이 없으면 API 호출을 건너뛰며, 결과 조회는 재크롤링 없이 저장된 분석을 사용합니다. 요약이 실패하면 안내 메시지를 보여주고 기존 댓글 데이터를 보존합니다. [요약 생성·조회](stocks/views.py), [원본 기반 요약](stocks/services/summary.py)

## 실행 방법

Python 환경과 Chrome, ChromeDriver 다운로드 및 토스증권·GMS에 접근할 네트워크가 필요합니다. 제공 자료에는 `config/settings.py`와 의존성 파일이 없으므로 원본에서 복구해야 합니다. 설정에는 `stocks` 앱, DB, 템플릿 및 messages 관련 구성이 필요합니다. 기존 README는 Django 5.2와 SQLite를 명시하지만 실제 설치 버전과 DB 설정은 확인하지 못했습니다.

원본 의존성을 설치한 뒤 `manage.py`가 있는 저장소 루트에 `.env`를 만들고 유효한 `GMS_KEY`, `GMS_BASE_URL`, `MODEL` 값을 설정합니다. 설정의 `BASE_DIR`가 이 위치를 가리키는지 확인하고 실행합니다.

```bash
python manage.py migrate
python manage.py runserver
```

`http://127.0.0.1:8000/`에서 회사명을 입력합니다. 기본 수집 경로는 Chrome 창을 띄우므로 브라우저 실행이 가능한 환경에서 사용합니다. 결과와 요약은 웹 화면에서 확인하며 저장된 분석은 `/analysis/<분석 ID>/`로 조회합니다. 제공된 테스트는 Selenium·GMS를 mock으로 대체하지만 이번 문서 작성에서는 테스트·실제 수집·API 호출을 실행하지 않았습니다.
