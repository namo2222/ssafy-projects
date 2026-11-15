# 도서 탐색과 관심 도서 보관 웹페이지

베스트셀러를 둘러보고 도서 상세와 독서 이야기를 확인하며, 관심 도서를 브라우저에 보관합니다.

![HTML5](https://img.shields.io/badge/HTML5-E34F26) ![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3) ![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E)

SSAFY 16기 Python 관통 프로젝트 3회차입니다.

## 프로젝트 개요

읽을 책을 고르고 책에 관한 이야기를 살펴보는 장면을 정적 웹 UI로 구성합니다. 메인 화면에서 베스트셀러·장르·인기 쓰레드를 탐색하고, 채식주의자 상세 화면에서 도서 담기와 관련 콘텐츠를 확인합니다. AI 추천 영역은 소개 화면이며 실제 추천 모델이나 도서 검색 API는 연동하지 않습니다.

## 기술 스택

| 기술 | 사용한 곳 |
|---|---|
| HTML5 | [통합 메인](source_code/06-main.html)의 도서·장르·쓰레드 구조를 구성합니다. |
| CSS3 | [공통 스타일](source_code/css/style.css)에서 Grid·Flexbox와 미디어 쿼리로 반응형 배치를 정의합니다. |
| Bootstrap 5.3 | [상세 화면](source_code/07-book_detail.html)의 탭과 공통 메뉴·모달·캐러셀을 구성합니다. |
| JavaScript | [화면 동작](source_code/js/app.js)에서 페이지 전환과 localStorage 기반 도서 담기를 처리합니다. |
| Google Maps | [도서 상세](source_code/07-book_detail.html)에 도서관 위치 예시를 iframe으로 표시합니다. |

## 핵심 구현

### 베스트셀러 탐색과 상세 화면 연결

도서 12권을 네 권씩 세 슬라이드로 구성하고, 5초 간격 자동 전환과 다음 버튼을 설정합니다. 채식주의자 카드는 상세 화면으로 연결하며 다른 도서 카드의 링크는 베스트셀러 영역에 머뭅니다. [캐러셀 구성](source_code/02-bestseller.html)

### 세 카드씩 전환하는 인기 쓰레드

페이지 번호를 누르면 카드 인덱스를 세 개 단위로 나눠 해당 페이지의 카드만 표시합니다. 활성 페이지 스타일과 `aria-current`도 함께 갱신합니다. 서버 조회 없이 준비된 카드 여섯 개의 표시를 전환합니다. [페이지 전환 처리](source_code/js/app.js)

### 도서 담기와 상세 탭

도서 담기를 누르면 버튼 상태를 바꾸고 `localStorage`에 저장하여 같은 브라우저에서 다시 읽습니다. 저장소 접근이 허용되어야 상태가 유지됩니다. [담기 상태 처리](source_code/js/app.js)

상세 탭은 도서관 지도와 관련 쓰레드를 구분합니다. 지도는 위치 예시이며 실제 소장·대여 가능 여부를 제공하지 않습니다. 관련 쓰레드와 좋아요는 정적 콘텐츠이고, 쓰레드 작성·마이 페이지·로그아웃은 안내 동작만 제공합니다. [상세 탭과 지도](source_code/07-book_detail.html)

## 실행 방법

원본 프로젝트의 HTML, `css/`, `js/`, `assets/`, `vendor/`가 함께 필요합니다. 제공된 소스 자료에는 이미지·폰트와 Bootstrap 배포 파일이 포함되어 있지 않으므로 원본 파일을 준비해야 합니다. 지정 폰트는 원본 `skeleton.zip`의 `skeleton/assets/fonts/`에서 `assets/fonts/`로 복사하며, 없으면 시스템 글꼴을 사용합니다.

원본 프로젝트 루트에서 Chrome으로 `06-main.html` 또는 `index.html`을 엽니다. Python이 있으면 같은 위치에서 다음 명령으로 로컬 서버를 실행할 수도 있습니다.

```bash
python -m http.server 8000
```

`http://localhost:8000/06-main.html`에서 메인 화면을 확인합니다. 도서 담기 상태는 브라우저 저장소에 남으며 지도에는 인터넷 연결이 필요합니다. 이 문서는 소스 검토를 바탕으로 작성했으며 브라우저 실행과 화면 캡처는 검증하지 않았습니다.
