"""F606: 전처리된 댓글을 GMS LLM으로 의미를 유지하며 확장한다."""
import json

from .llm import parse_json_array, run_llm


def augment_comments(comments):
    """정제 댓글 목록을 받아 같은 순서·개수의 증강 댓글을 돌려준다.

    API 응답의 개수나 형식이 틀리면 오류를 발생시켜 잘못된 결과가
    정상 데이터로 DB에 저장되는 일을 막는다.
    """
    if not comments:
        return []

    prompt = f"""다음은 주식 커뮤니티에서 수집한 댓글이야.
각 댓글의 원래 의미, 의견, 말투를 유지하면서 더 자연스럽고 명확한 문장으로 확장해 줘.

반드시 지킬 규칙:
1. 입력 댓글마다 확장 댓글을 정확히 하나씩 생성하고, 순서를 바꾸지 마.
2. 원문에 없는 숫자, 뉴스, 실적, 주가 전망 등의 새로운 사실을 지어내지 마.
3. 원문의 긍정·부정·중립 의미를 바꾸거나 투자 권유를 추가하지 마.
4. 각 결과는 비어 있지 않은 하나의 문자열이어야 해.
5. 응답은 JSON 문자열 배열만 반환해. 마크다운이나 설명을 붙이지 마.

입력 댓글(JSON 배열):
{json.dumps(comments, ensure_ascii=False)}"""

    response = run_llm(prompt)
    augmented = parse_json_array(response)

    if (
        augmented is None
        or len(augmented) != len(comments)
        or any(not isinstance(item, str) or not item.strip() for item in augmented)
    ):
        raise ValueError(
            'AI 증강 응답 형식이 올바르지 않습니다. '
            '정제 댓글과 동일한 개수의 JSON 문자열 배열이 필요합니다.'
        )

    return [item.strip() for item in augmented]
