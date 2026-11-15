from pathlib import Path
import json


file_path = Path('./data/books_2000.json')  # 파일 경로 설정 부분

# 파일 존재 여부 확인
if file_path.exists():  # 파일이 존재할 경우
    # 2. 파일 열기
    with file_path.open('r', encoding='utf-8') as file:
            books = json.load(file)


series_data = {}
series_dir = Path('./data/series_items')

for json_path in series_dir.rglob('*.json'):
    with json_path.open('r', encoding='utf-8') as file:
        book = json.load(file)

    info = book.get('seriesInfo')
    if not info:
        continue

    series_id = str(info['seriesId'])

    if series_id not in series_data:
        series_data[series_id] = {
            'seriesId': info['seriesId'],
            'seriesName': info['seriesName'],
            'books': []
        }

    series_data[series_id]['books'].append(book)

if not series_dir.exists():
    print('data/series_items 디렉토리가 존재하지 않습니다.')
else:
    # 위 로직 실행

    with open('./data/series.json', 'w', encoding='utf-8') as file:
        json.dump(series_data, file, ensure_ascii=False, indent=4)

    print('모든 시리즈 데이터가 series.json 파일로 병합되었습니다.')

