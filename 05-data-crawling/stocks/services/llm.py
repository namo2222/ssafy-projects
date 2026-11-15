import json
import os

from django.conf import settings
from dotenv import load_dotenv
from openai import OpenAI

# 프로젝트 루트(manage.py 옆)의 .env 에서 GMS_KEY, GMS_BASE_URL, MODEL 불러오기
load_dotenv(settings.BASE_DIR / '.env')


def run_llm(prompt):
    """GMS Chat Completions API에 프롬프트를 보내 응답 텍스트를 반환한다.

    GMS 게이트웨이에서는 Responses API (/responses)가 허용되지 않을 수 있으므로
    Chat Completions (/chat/completions)를 사용한다.
    """
    api_key = os.getenv('GMS_KEY')
    base_url = os.getenv('GMS_BASE_URL')
    model = os.getenv('MODEL')

    if not api_key or not base_url or not model:
        raise ValueError('GMS 설정이 없습니다. .env의 GMS_KEY, GMS_BASE_URL, MODEL을 확인하세요.')

    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model,
        messages=[{'role': 'user', 'content': prompt}],
    )

    if not response.choices or not response.choices[0].message.content:
        raise ValueError('GMS에서 텍스트 응답을 받지 못했습니다.')
    return response.choices[0].message.content


def parse_json_array(response):
    """LLM 응답에서 JSON 배열을 꺼낸다. 형식이 틀리면 None"""
    text = response.strip()

    # ```json ... ``` 코드블럭으로 감싸 오는 경우 벗겨냄
    if text.startswith('```'):
        text = text.strip('`').removeprefix('json').strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        print('[파싱 실패] 응답이 JSON 형식이 아닙니다:', response[:100])
        return None

    if not isinstance(data, list):
        print('[파싱 실패] 응답이 리스트가 아닙니다:', response[:100])
        return None
    return data
