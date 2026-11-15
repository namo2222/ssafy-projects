import os                       # 운영 체제와 상호작용하기 위한 라이브러리
import requests                 # HTTP 요청을 보내기 위한 라이브러리
from gtts import gTTS           # 텍스트를 음성으로 변환하기 위한 라이브러리
from dotenv import load_dotenv  # 환경 변수 로드를 위한 라이브러리


load_dotenv()  # .env 파일을 읽어 환경 변수로 설정합니다.

# 1. [ dotenv를 활용하여 알라딘 API 키 가져오기 ]
MY_TTBKEY = os.getenv('MY_TTBKEY')

# 2. [ 공식 문서를 참고하여 알라딘 API 검색 URL 설정하기 ]
ALADIN_SEARCH_URL = 'https://www.aladin.co.kr/ttb/api/ItemSearch.aspx'


# 3. 도서 제목 가져오는 함수 정의
def fetch_book_title(keyword):
    url = ALADIN_SEARCH_URL

    params = {
        "TTBKey": MY_TTBKEY,
        "Query": keyword,
        "output": "js",
        "Version": "20131101",
    }

    # 3.1 HTTP GET 요청
    response = requests.get(url, params=params, timeout=5)

    # 3.2 응답 데이터를 Python dict 타입으로 변환
    data = response.json()

    # 3.3 첫 번째 도서 제목 추출
    books = data.get('item', [])

    if books:
        title = books[0].get('title')
    else:
        title = None

    return title


# 4. TTS 파일 생성 함수 정의
def create_tts_file(keyword, output_file):

    # 4.1 첫 번째 도서 제목 가져오기
    title = fetch_book_title(keyword)

    if title:
        # 4.2 gTTS를 사용해 title의 내용으로 음성 파일 생성
        tts = gTTS(text=title, lang='ko')

        tts.save(output_file)

        print(f"음성 파일이 {output_file}로 저장되었습니다.")
    else:
        print("도서 제목을 가져오는데 실패했습니다.")


# 함수 실행
if __name__ == '__main__':
    os.makedirs('output', exist_ok=True)

    create_tts_file("자격증", "output/book_title.mp3")