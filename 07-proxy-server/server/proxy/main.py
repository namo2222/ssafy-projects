"""
FastAPI Proxy 서버. 이 파일 하나가 서버 전부입니다. (Django 만 이 서버를 호출하고, GMS_KEY 는 여기서만 씁니다)

실행: uvicorn main:app --port 8081 --reload   (이 폴더 안에서)
문서: http://localhost:8081/docs
"""
import base64
import json
import os

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from schemas import (
    ChatGuardrailRequest,
    ChatGuardrailResponse,
    ChatRequest,
    ChatResponse,
    ChatScoreRequest,
    ChatScoreResponse,
    DecideRouteRequest,
    DecideRouteResponse,
    GenerateSpeechRequest,
    GenerateSpeechResponse,
    ImageAnalysisRequest,
    ImageAnalysisResponse,
    ImageGenerationRequest,
    ImageGenerationResponse,
)

load_dotenv(".env")
GMS_KEY = os.getenv("GMS_KEY")
GMS_URL = os.getenv("GMS_URL")
HEADERS = {"Authorization": f"Bearer {GMS_KEY}"}

MODEL_NANO = "gpt-5-nano"       # 가볍고 저렴한 모델
MODEL_MINI = "gpt-5-mini"       # 더 성능 좋은 모델
MODEL_IMAGE = "gpt-image-2"  # gpt-image-1-mini 는 GMS 에서 400 (not available) 이 나서 변경
MODEL_TTS = "gpt-4o-mini-tts"   # F711

app = FastAPI(title="Book Recommend Proxy (FastAPI)")


# ######################################################################
# 제공 — 그대로 사용합니다. 수정하지 않습니다.
# ######################################################################

def ask_gms(messages, model=MODEL_NANO, response_format=None):
    """채팅 모델에 messages 를 보내고, 답변 문자열만 돌려줍니다."""
    payload = {"model": model, "messages": messages}
    if response_format:
        payload["response_format"] = response_format
    # gms_post 는 아래 F706 에 있음 (파이썬은 호출 시점에 함수를 찾으므로 순서는 상관없다)
    response = gms_post("/chat/completions", payload)
    return response.json()["choices"][0]["message"]["content"]


# ######################################################################
# 구현
# ######################################################################

# ---------------------------------------------------------------- F702 텍스트 추천 생성 (+F703, F710)
@app.post("/api/v1/chat/completions", response_model=ChatResponse)
def chat_completions(request: ChatRequest):
    # 생성 전에 guardrail 먼저 (부적절하면 여기서 403)
    user_text = request.messages[-1]["content"]
    ensure_appropriate(user_text)

    # F710 - 체크박스를 켰을 때만 난이도에 따라 모델을 고른다
    model = MODEL_NANO
    if request.use_tier_routing and decide_model_tier(user_text) == "complex":
        model = MODEL_MINI

    content = ask_gms(request.messages, model)
    return {"content": content, "model_used": model}


# ---------------------------------------------------------------- F703 Guardrail
GUARDRAIL_PROMPT = """
너는 도서 추천 서비스로 들어온 사용자 요청이 적절한지 판단하는 검사기이다.
아래에 해당하는 경우에만 is_appropriate 를 false 로 답한다.
- 폭력, 자해, 혐오 표현, 성인(선정적) 콘텐츠를 만들어 달라고 요구하는 경우
- 마약 제조, 해킹, 무기 제작처럼 명백히 불법인 행위의 방법을 묻는 경우
- 다른 사람의 주소, 전화번호, 주민번호 같은 개인정보를 요구하는 경우
위 경우가 아니면 true 로 답한다.
범죄 소설, 전쟁사, 심리학 책처럼 주제가 무거워도 책을 찾는 요청이면 true 이다.
판단이 애매하면 true 로 답한다.
"""


@app.post("/api/v1/chat/guardrail", response_model=ChatGuardrailResponse)
def chat_guardrail(request: ChatGuardrailRequest):
    messages = [
        {"role": "developer", "content": GUARDRAIL_PROMPT},
        {"role": "user", "content": request.prompt},
    ]
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "guardrail_response",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {"is_appropriate": {"type": "boolean"}},
                "required": ["is_appropriate"],
                "additionalProperties": False,
            },
        },
    }
    answer = ask_gms(messages, MODEL_NANO, response_format)
    result = json.loads(answer)
    return {"is_appropriate": result["is_appropriate"]}


def ensure_appropriate(prompt):
    """생성 함수들이 맨 먼저 호출합니다. 부적절하면 403 오류를 냅니다."""
    result = chat_guardrail(ChatGuardrailRequest(prompt=prompt))
    if not result["is_appropriate"]:
        raise HTTPException(status_code=403, detail="inappropriate request")


# ---------------------------------------------------------------- F704 라우트 결정
ROUTE_PROMPT = """
너는 도서 추천 서비스의 요청을 어느 기능으로 보낼지 정하는 분류기이다.
- 책 추천, 책 소개, 줄거리 질문처럼 글로 답하면 되는 요청이면 "/chat/completions"
- 책 표지를 그려 달라, 만들어 달라, 이미지로 보여 달라는 요청이면 "/images/generations"
둘 중 하나만 고른다. 애매하면 "/chat/completions" 를 고른다.
"""


@app.post("/api/v1/decide-route", response_model=DecideRouteResponse)
def decide_route(request: DecideRouteRequest):
    messages = [
        {"role": "developer", "content": ROUTE_PROMPT},
        {"role": "user", "content": request.prompt},
    ]
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "route_response",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "route": {"type": "string", "enum": ["/chat/completions", "/images/generations"]},
                },
                "required": ["route"],
                "additionalProperties": False,
            },
        },
    }
    answer = ask_gms(messages, MODEL_NANO, response_format)
    result = json.loads(answer)
    return {"route": result["route"]}


# ---------------------------------------------------------------- F705 이미지 생성 (+F703)
@app.post("/api/v1/images/generations", response_model=ImageGenerationResponse)
def image_generations(request: ImageGenerationRequest):
    ensure_appropriate(request.prompt)

    # quality, output_format 은 토큰과 파일 크기를 줄이려고 지정
    payload = {
        "model": MODEL_IMAGE,
        "prompt": request.prompt,
        "size": "1024x1024",
        "quality": "low",
        "output_format": "jpeg",
    }
    response = gms_post("/images/generations", payload)
    image_base64 = response.json()["data"][0]["b64_json"]
    return {"image_base64": image_base64}


# ---------------------------------------------------------------- F706 공통 에러 처리
def gms_post(path, payload):
    """GMS 에 POST 요청을 보냅니다. 모든 GMS 호출이 이 함수를 거칩니다."""
    response = requests.post(GMS_URL + path, headers=HEADERS, json=payload, timeout=120)
    if response.status_code != 200:
        print("[GMS 호출 실패]", path, response.status_code, response.text[:200])
        raise HTTPException(status_code=503, detail="model server error")
    return response


# ---------------------------------------------------------------- F707 이미지 분석 (+F703)
ANALYSIS_PROMPT = """
너는 책 표지 사진을 보고 책을 알아보는 도서 추천 도우미이다.
1. 표지의 글자, 그림, 분위기를 보고 책 제목과 저자를 추정한다. 확실하지 않으면 추정이라고 밝힌다.
2. 장르를 추정하고 그렇게 본 이유를 한 문장으로 쓴다.
3. 비슷한 분위기나 장르의 도서를 2~3권 추천하고, 각 책마다 제목, 저자, 추천 이유를 한두 문장으로 쓴다.
사용자의 질문이 있으면 그 질문에 맞춰 답한다. 한국어로 답한다.
"""


@app.post("/api/v1/images/analysis", response_model=ImageAnalysisResponse)
def image_analysis(request: ImageAnalysisRequest):
    # 이미지는 guardrail 에 보내지 않고 질문만 검사한다
    ensure_appropriate(request.question)

    image_url = "data:image/png;base64," + request.image_base64
    messages = [
        {"role": "developer", "content": ANALYSIS_PROMPT},
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": image_url}},
                {"type": "text", "text": request.question},
            ],
        },
    ]
    content = ask_gms(messages, MODEL_NANO)
    return {"content": content}


# ---------------------------------------------------------------- F709 텍스트 응답 점수 계산 (심화)
SCORE_PROMPT = """
너는 도서 추천 답변을 채점하는 평가자이다.
사용자의 요청과 마지막에 주어지는 추천 답변을 비교해서, 답변이 요청한 취향과 조건에 얼마나 맞는지 0~100 점으로 매긴다.
- 요청한 장르, 분위기, 상황, 분량 같은 조건을 지켰는지
- 실제로 있는 책을 추천했는지, 추천 이유가 요청과 연결되는지
reason 에는 점수를 준 이유를 한두 문장으로 한국어로 쓴다.
"""


@app.post("/api/v1/chat/score", response_model=ChatScoreResponse)
def chat_score(request: ChatScoreRequest):
    messages = (
        [{"role": "developer", "content": SCORE_PROMPT}]
        + request.messages
        + [{"role": "user", "content": "답변: " + request.answer}]
    )
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "score_response",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "score": {"type": "integer"},
                    "reason": {"type": "string"},
                },
                "required": ["score", "reason"],
                "additionalProperties": False,
            },
        },
    }
    answer = ask_gms(messages, MODEL_NANO, response_format)
    result = json.loads(answer)
    return {"score": result["score"], "reason": result["reason"]}


# ---------------------------------------------------------------- F710 모델 등급 라우팅 (심화)
TIER_PROMPT = """
너는 도서 추천 요청의 난이도를 분류한다.
- "소설 추천해줘", "SF 책 알려줘" 처럼 조건이 하나뿐인 단순한 요청이면 "simple"
- 상황, 기분, 분량, 분위기 등 여러 조건을 함께 고려해야 하거나 감정과 사정을 헤아려야 하는 요청이면 "complex"
"""


def decide_model_tier(prompt):
    messages = [
        {"role": "developer", "content": TIER_PROMPT},
        {"role": "user", "content": prompt},
    ]
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "tier_response",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "tier": {"type": "string", "enum": ["simple", "complex"]},
                },
                "required": ["tier"],
                "additionalProperties": False,
            },
        },
    }
    answer = ask_gms(messages, MODEL_NANO, response_format)
    tier = json.loads(answer)["tier"]
    print("[Tier]", tier, ":", prompt[:50])
    return tier


# ---------------------------------------------------------------- F711 TTS (심화)
@app.post("/api/v1/generate-speech", response_model=GenerateSpeechResponse)
def generate_speech(request: GenerateSpeechRequest):
    # TTS 는 guardrail 을 적용하지 않는다 (추천 결과를 읽어 주는 용도)
    payload = {"model": MODEL_TTS, "input": request.text, "voice": "nova", "response_format": "mp3"}
    response = gms_post("/audio/speech", payload)
    # 응답이 json 이 아니라 mp3 바이트라서 .content 를 base64 로 바꿔서 보낸다
    audio_data = base64.b64encode(response.content).decode("utf-8")
    return {"audio_data": audio_data}
