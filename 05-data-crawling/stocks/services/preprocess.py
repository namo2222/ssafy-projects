import re

import pandas as pd

from .llm import parse_json_array, run_llm

# 명세 필수 : 길이 5 이상 ~ 76 이하
MIN_LEN = 5
MAX_LEN = 76

# 부적절 판단 기준 (basic = 명세 프롬프트 예시 기준)
CRITERIA = {
    'basic': '욕설, 혐오, 비방, 선정성, 과도한 비난',
    'strict': (
        '욕설, 혐오, 비방, 선정성, 과도한 비난, 조롱·비꼬기, '
        '다른 투자자를 깎아내리는 표현, 근거 없는 단정이나 매수·매도를 부추기는 선동'
    ),
}


# ------------------------------------------------------------
# 터미널 확인용 출력
# ------------------------------------------------------------
def show_changes(df, before_col, after_col):
    """정리 전과 후가 달라진 행만 나란히 출력한다"""
    changed = df[df[before_col] != df[after_col]]
    print(f'  바뀐 댓글 {len(changed)}개')
    for before, after in zip(changed[before_col], changed[after_col]):
        print(f'  - 전 : {before!r}')
        print(f'    후 : {after!r}')


def show_removed(title, removed_texts):
    """제거된 댓글 목록을 출력한다"""
    print(f'  {title} : {len(removed_texts)}개')
    for text in removed_texts:
        print(f'    - {text!r}')


# ------------------------------------------------------------
# 부적절 댓글 제거 (LLM)
# ------------------------------------------------------------
def build_filter_prompt(comments, criteria):
    """댓글에 번호를 붙이고, 기준에 해당하는 댓글의 번호만 돌려 달라는 프롬프트"""
    # 댓글 안의 줄바꿈을 공백으로 바꿔 "한 줄 = 댓글 하나"가 되도록 (번호 어긋남 방지)
    numbered = '\n'.join(f'{i}. {" ".join(c.split())}' for i, c in enumerate(comments))
    return f"""다음 댓글 목록에서 아래 기준에 해당하는 부적절한 댓글의 번호(0부터 시작)만 골라줘.
기준 : {criteria}
응답은 반드시 [0, 2, 5] 또는 [] 형식의 JSON 배열만 보내고, 설명이나 코드블럭은 쓰지 마.

댓글 목록:
{numbered}"""


def filter_inappropriate(comments, criteria):
    """LLM 이 고른 번호의 댓글을 제거하고 (남은 댓글, 제거된 댓글)을 돌려준다"""
    response = run_llm(build_filter_prompt(comments, criteria))
    print('[부적절 필터] LLM 응답:', response)

    numbers = parse_json_array(response)
    if numbers is None:
        # 해석 실패 시 아무것도 지우지 않음 (잘못 지우는 것보다 안전)
        return list(comments), []

    # 정수이면서 실제 번호 범위 안인 값만 사용
    to_remove = sorted(
        {n for n in numbers if type(n) is int and 0 <= n < len(comments)}
    )

    # 앞에서부터 지우면 번호가 밀리므로 뒤에서부터 제거
    kept = list(comments)
    removed = []
    for i in reversed(to_remove):
        removed.append(kept.pop(i))
    removed.reverse()

    return kept, removed


# ------------------------------------------------------------
# 정제 (pandas + 정규표현식)
# ------------------------------------------------------------
def to_dataframe(comments):
    """댓글 리스트를 DataFrame 으로 바꾸고, 비어 있는 댓글(결측치)을 제거한다"""
    df = pd.DataFrame(comments, columns=['comment'])
    df = df.dropna(subset=['comment'])
    df['comment'] = df['comment'].astype(str).str.strip()
    df = df[df['comment'] != '']
    print(f'[결측치] {len(comments)}개 -> {len(df)}개')
    return df


def remove_special_chars(df):
    """한글·영문·숫자·공백만 남기고, 연속된 공백을 한 칸으로 정리한다"""
    # ㅋㅋㅋ, ㅠㅠ 같은 자음·모음과 이모지·특수문자도 여기서 제거됨
    df['clean'] = df['comment'].apply(lambda x: re.sub(r'[^가-힣a-zA-Z0-9\s]', '', x))
    df['clean'] = df['clean'].str.replace(r'\s+', ' ', regex=True).str.strip()

    print('[특수문자 정리]')
    show_changes(df, 'comment', 'clean')
    return df


def remove_meaningless(df):
    """빈 문자열 / 숫자만 / 영어만 / 'none' 인 댓글을 제거한다"""
    cond_empty = df['clean'] == ''
    cond_numeric = df['clean'].str.match(r'^\d+$')
    cond_english = df['clean'].str.match(r'^[A-Za-z\s]+$')
    cond_none = df['clean'].str.lower() == 'none'
    cond_any = cond_empty | cond_numeric | cond_english | cond_none

    print('[의미 없는 댓글]')
    show_removed('제거 대상', df[cond_any]['comment'].tolist())
    return df[~cond_any]


def remove_length_outliers(df):
    """IQR 로 정상 길이 범위를 계산해 제거하고 (df, IQR 정보)를 돌려준다"""
    df['length'] = df['clean'].str.len()

    # 댓글이 너무 적으면 통계 의미가 없음 -> 명세 고정 범위만 적용
    if len(df) < 5:
        print(f'[길이 이상치] 댓글 5개 미만 -> {MIN_LEN}~{MAX_LEN}글자만 남김')
        iqr_info = {'q1': None, 'q3': None, 'iqr': None, 'lower': MIN_LEN, 'upper': MAX_LEN}
    else:
        q1 = float(df['length'].quantile(0.25))
        q3 = float(df['length'].quantile(0.75))
        iqr = q3 - q1
        # IQR 범위와 명세 범위(5~76) 중 더 좁은 쪽 사용
        lower = max(MIN_LEN, q1 - 1.5 * iqr)
        upper = min(MAX_LEN, q3 + 1.5 * iqr)
        iqr_info = {'q1': q1, 'q3': q3, 'iqr': iqr, 'lower': lower, 'upper': upper}
        print(f'[길이 이상치] Q1={q1}, Q3={q3}, IQR={iqr} -> 정상 범위 {lower} ~ {upper}글자')

    cond_outlier = (df['length'] < iqr_info['lower']) | (df['length'] > iqr_info['upper'])
    show_removed('제거 대상', df[cond_outlier]['clean'].tolist())
    return df[~cond_outlier], iqr_info


def clean_comments(comments):
    """정제 4단계 적용 후 (정제된 댓글 리스트, IQR 정보)를 돌려준다"""
    df = to_dataframe(comments)
    df = remove_special_chars(df)
    df = remove_meaningless(df)
    df, iqr_info = remove_length_outliers(df)
    return df['clean'].tolist(), iqr_info
