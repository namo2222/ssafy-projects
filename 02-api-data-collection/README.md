# 도서 검색에서 가격 분석과 음성 소개까지

알라딘 API로 도서를 검색하고 주제별 통계, 가격별 JSON 분류, 한국어 MP3 소개 파일을 만듭니다.

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white) ![Aladin API](https://img.shields.io/badge/Aladin-API-blue) ![gTTS](https://img.shields.io/badge/gTTS-TTS-green)

참여자: 안소현 · 이남호

## 프로젝트 개요

주제별 도서의 판매가와 출판 연도를 비교하고, 할인 여부에 따라 검색 결과를 나누어 저장합니다. 도서 소개를 듣고 싶은 경우에는 API가 제공한 소개문과 제목을 음성 파일로 변환합니다.

## 기술 스택

| 기술 | 사용한 곳 |
| --- | --- |
| Python | [주제별 가격·출판 연도 집계](source_code/problem_B1.py) |
| 알라딘 Open API · requests | [키워드 검색 HTTP 요청과 JSON 응답 처리](source_code/problem_B1.py) |
| python-dotenv | [환경 변수에서 API 키 로드](source_code/problem_B2.py) |
| gTTS | [한국어 텍스트를 MP3로 변환](source_code/problem_B3.py) |
| json · pathlib (표준 라이브러리) | [출력 폴더 생성과 한글 JSON 저장](source_code/problem_B2.py) |

## 핵심 구현

### 주제별 판매가·출판 연도 분석

자연·예술·기술을 각각 최대 30건 요청합니다. 판매가와 출판 연도를 정수로 변환하고, 변환 가능한 값의 개수를 각각 분모로 삼아 주제별·전체 평균을 콘솔에 출력합니다. 유효한 값이 없으면 평균을 0으로 표시하며, 주제 사이의 중복 도서는 제거하지 않습니다. [통계 계산 코드](source_code/problem_B1.py)

### 판매가와 정가 비교로 도서 분류

경제 도서를 최대 50건 요청하고 판매가가 정가보다 낮으면 할인 목록에, 나머지는 일반 가격 목록에 저장합니다. 두 가격 중 하나라도 없으면 제외하며, 숫자형 가격을 전제로 비교합니다. 일반 가격 목록에는 정가보다 비싼 도서도 포함될 수 있습니다. [가격 비교와 JSON 저장](source_code/problem_B2.py)

### 소개문이 있는 도서를 골라 음성 생성

한국문학 검색 결과에서 공백을 제거한 `description`이 있는 도서를 순서대로 최대 5건 저장하고, 제목과 소개문을 합쳐 한국어 MP3로 변환합니다. JSON의 `요약` 필드는 API 소개문을 그대로 사용합니다. `description`은 문자열이어야 하며, 유효한 도서가 적으면 출력도 5건보다 적습니다. [소개문 선별과 음성 변환](source_code/problem_B3.py)

## 실행 방법

Python 3, 알라딘 API 키, 알라딘 API와 gTTS 서비스에 접속 가능한 네트워크가 필요합니다. 원본 프로젝트의 `source_code/`가 있는 루트에서 다음을 실행합니다.

```powershell
python -m pip install requests python-dotenv gTTS
# 같은 위치의 .env 파일에 MY_TTBKEY=<발급받은 키>를 설정합니다.
python source_code/problem_B1.py
python source_code/problem_B2.py
python source_code/problem_B3.py
```

음성 변환 실행 전 `problem_B3.py`의 검색 파라미터 오타 `SearchTraget`을 `SearchTarget`으로 수정해야 합니다. API·TTS 요청 실패 시 실행이 중단될 수 있습니다.

통계는 콘솔에 표시됩니다. 실행 위치를 기준으로 분류 결과는 `output/discounted_books.json`, `output/regular_priced_books.json`에, 음성 소개는 `output/korean_literature_books.json`과 `output/book_1.mp3`부터 저장됩니다. 제공 자료에는 실제 결과 파일과 의존성 버전 정보가 없으며, API·음성 변환 실행은 검증하지 않았습니다.
