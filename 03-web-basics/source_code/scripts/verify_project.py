"""Static validation of source asset paths and required structural components."""
from pathlib import Path
from html.parser import HTMLParser
import subprocess, shutil

class Inspector(HTMLParser):
    def __init__(self):
        super().__init__(); self.assets=[]; self.tags=[]; self.classes=[]; self.ids=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs);self.tags.append(tag)
        if 'class' in a:self.classes.extend(a['class'].split())
        if 'id' in a:self.ids.append(a['id'])
        if 'src' in a and not a['src'].startswith(('http://','https://','data:')):self.assets.append(a['src'])
        if 'href' in a and not a['href'].startswith(('#','http://','https://','mailto:','javascript:')):self.assets.append(a['href'].split('#')[0])

root=Path(__file__).resolve().parent.parent
failures=[]
for html in sorted(root.glob('*.html')):
    i=Inspector();i.feed(html.read_text(encoding='utf8'))
    bad=[a for a in i.assets if not (root/a).exists()]
    if bad:failures.append(f'{html.name}: 깨진 파일 링크 {bad}')
    print(f'[검사] {html.name}: 참조 {len(i.assets)}개, 이미지 {i.tags.count("img")}개, 깨진 링크 {len(bad)}개')
main=Inspector();main.feed((root/'06-main.html').read_text(encoding='utf8'))
for id_ in ['mainNav','bestsellerCarousel','genre','thread','logoutModal']:
    if id_ not in main.ids:failures.append(f'06-main.html 누락 요소: {id_}')
if main.classes.count('book-card')!=12:failures.append('베스트셀러 12권 없음')
if main.classes.count('genre-item')!=10:failures.append('장르 10개 없음')
if main.classes.count('thread-column')!=6:failures.append('쓰레드 6개 없음')
node=shutil.which('node')
if node:
    result=subprocess.run([node,'--check',str(root/'js/app.js')],capture_output=True,text=True)
    if result.returncode:failures.append('JS 구문 오류: '+result.stderr)
print('\n', '정적 파일/HTML 구조/JS 구문 검사 성공' if not failures else '검사 실패:\n'+'\n'.join(failures))
raise SystemExit(1 if failures else 0)
