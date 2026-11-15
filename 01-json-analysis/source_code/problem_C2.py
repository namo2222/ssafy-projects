import json
from pathlib import Path


file_path = Path('./data/books_2000.json')

if file_path.exists():

    with file_path.open('r', encoding='utf-8') as file:
        books = json.load(file)

    category_books = {}

    for book in books:
        category_id = str(book['categoryId'])
        category_name = book['categoryName']

        if category_id not in category_books:
            category_books[category_id] = {
                'name': category_name,
                'books': []
            }
     
        book_info = {
            'title': book['title'],
            'author': book['author'],
            'publisher': book['publisher'],
            'pubDate': book['pubDate'],
            'isbn': book['isbn'],
            'price': book['priceSales']
        }

        category_books[category_id]['books'].append(book_info)

    output_path = Path('./data/category_books.json')

    with output_path.open('w', encoding='utf-8') as file:
        json.dump(
            category_books,
            file,
            ensure_ascii=False,
            indent=4
        )

    print('JSON 파일이 생성되었습니다: category_books.json')

else:
    print('books_2000.json 파일이 존재하지 않습니다.')