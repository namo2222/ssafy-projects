from datetime import datetime  # 날짜와 시간을 처리하기 위한 라이브러리
import json  # JSON 파일을 처리하기 위한 라이브러리
from pathlib import Path  # 파일 경로를 처리하기 위한 라이브러리

# 월별 책 정보 모아보고 평균 가격 계산하기
# 아래에 전체 코드 작성
file_path = Path('./data/books_2000.json')  # 파일 경로 설정 부분

# 파일 존재 여부 확인
if file_path.exists():  # 파일이 존재할 경우
    # 2. 파일 열기
    with file_path.open('r', encoding='utf-8') as file:
            books = json.load(file)

monthly_stats = {}

for book in books:
    month = int(book['pubDate'].split('-')[1])

    price = book['priceSales']

    if month not in monthly_stats:
        monthly_stats[month] = {'count': 0, 'total': 0}

    monthly_stats[month]['count'] += 1
    monthly_stats[month]['total'] += price

for month in sorted(monthly_stats.keys()):
    stats = monthly_stats[month]
    avg = stats['total'] / stats['count']
    print(f'{month}월: 평균 가격 {avg:.2f}원 (총 {stats["count"]}권)')

