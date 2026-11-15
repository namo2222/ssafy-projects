# 취향과 표지 요청을 책 추천·이미지·음성으로 바꾸는 AI 도서 서비스

독서 취향으로 책을 추천받고 표지 생성·분석과 입력 텍스트의 음성 변환을 이용합니다.

![Django](https://img.shields.io/badge/Django-092E20) ![FastAPI](https://img.shields.io/badge/FastAPI-009688)

팀: 최성민 · 이남호

## 프로젝트 개요

읽고 싶은 책의 분위기를 문장으로 설명하거나 표지 사진에 관해 질문하는 서비스입니다. Django가 폼과 결과 화면을 담당하고 FastAPI 프록시가 GMS 인증·요청 검사·모델 호출을 처리합니다.

## 기술 스택

| 기술 | 사용한 곳 |
| --- | --- |
| Python · Django | [웹 뷰](server/web/recommend/views.py)에서 입력 검증과 결과 저장·표시를 처리합니다. |
| FastAPI · Pydantic | [프록시 API](server/proxy/main.py)와 [요청·응답 모델](server/proxy/schemas.py)을 구성합니다. |
| GMS API · requests | [모델 호출](server/proxy/main.py)에서 텍스트·이미지·음성 요청을 보냅니다. |
| python-dotenv | [프록시 초기화](server/proxy/main.py)에서 API 접속 환경변수를 읽습니다. |
| HTML · Django Templates | [결과 템플릿](server/web/recommend/templates/recommend/result_text.html)에서 생성 결과를 표시합니다. |

## 핵심 구현

### 한 번의 입력으로 추천 또는 표지 생성

300자 이내 요청을 검증한 뒤 모델이 텍스트 추천과 이미지 생성 중 경로를 선택하고 Django가 해당 API를 실행합니다. 생성 전 프록시에서 요청 적절성을 판단해 거부 시 403 안내를 표시합니다. 텍스트 추천은 모델 자동 선택 옵션을 켠 경우에만 난이도를 분류해 `gpt-5-nano` 또는 `gpt-5-mini`를 사용합니다. 별도 텍스트 추천 화면은 답변의 LLM 점수·이유도 요청하지만, 이 점수는 정확성을 검증한 지표가 아닙니다. [분기 실행](server/web/recommend/views.py), [요청 검사와 모델 선택](server/proxy/main.py)

### 표지 이미지 생성과 업로드 분석

이미지는 `gpt-image-2`에 JPEG 생성을 요청해 화면에 직접 표시합니다. 생성 이미지의 파일 저장은 TODO 상태이며 영구 보관하지 않습니다. 업로드 분석은 사진과 질문을 함께 전달해 제목·저자·장르 추정과 유사 도서 추천을 요청합니다. 적절성 검사는 질문에만 적용하며, 이미지 분석 결과의 정확성은 검증하지 않았습니다. [생성·분석 API](server/proxy/main.py), [이미지 표시](server/web/recommend/templates/recommend/result_image.html)

### 입력 텍스트를 음성으로 듣기

최대 2,000자의 텍스트를 받아 `gpt-4o-mini-tts`의 `nova` 음성으로 MP3 변환을 요청합니다. 반환 오디오를 같은 결과 화면에서 재생하며 파일로 보관하지 않습니다. 추천 결과를 자동으로 넘기는 흐름은 없으므로 읽을 내용을 직접 입력합니다. [음성 요청 처리](server/web/recommend/views.py), [오디오 재생](server/web/recommend/templates/recommend/result_audio.html)

## 실행 방법

제공 자료에는 `server/requirements.txt`, `server/web/web/settings.py`, `.env.example`과 실제 DB가 없습니다. 원본 의존성과 설정을 복구하고 Python 환경을 준비해야 합니다. Django 설정에는 `recommend` 앱, 템플릿·DB·미디어 구성 및 `PROXY_URL = 'http://127.0.0.1:8081/api/v1'`이 필요하며 이미지 필드용 Pillow도 준비합니다.

`server/proxy/.env`에 유효한 `GMS_KEY`와 `GMS_URL`을 설정합니다. `GMS_URL`은 `/chat/completions` 등의 경로가 이어질 API 기본 주소이며 끝의 슬래시를 제외합니다. 코드에 지정된 모델을 사용할 권한과 네트워크 연결도 필요합니다.

의존성을 설치한 동일 가상환경의 터미널 두 개에서 저장소 루트 기준으로 각각 실행합니다.

```bash
# 터미널 1
cd server/proxy
uvicorn main:app --port 8081 --reload
```

```bash
# 터미널 2
cd server/web
python manage.py migrate
python manage.py runserver 8080
```

`http://127.0.0.1:8080/flow/`에서 통합 생성 결과를 확인합니다. 표지 분석은 `/analyze/`, 음성 변환은 `/tts/`, 프록시 API 문서는 `http://127.0.0.1:8081/docs`입니다. GMS의 비정상 HTTP 응답은 503 안내로 연결하지만 연결 단절·타임아웃 예외는 별도로 처리하지 않습니다. 서버·API·테스트 실행 검증은 수행하지 않았습니다.
