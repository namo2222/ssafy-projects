"""Take actual Chromium screenshots for the SSAFY UI submission (optional dependency)."""
from pathlib import Path
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    raise SystemExit('설치 필요: pip install playwright && python -m playwright install chromium')

root = Path(__file__).resolve().parent.parent
out = root / 'screenshots'
out.mkdir(exist_ok=True)
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    for width, height, suffix in [(1440,900,'desktop'),(390,844,'mobile')]:
        context = browser.new_context(viewport={'width':width,'height':height},device_scale_factor=1)
        page = context.new_page()
        page.goto((root / '06-main.html').as_uri(), wait_until='domcontentloaded')
        page.locator('img.hero-img').wait_for(state='visible')
        page.screenshot(path=str(out / f'main-{suffix}.png'), full_page=True, animations='disabled')
        if suffix=='desktop':
            page.locator('[data-bs-target="#logoutModal"]').click()
            page.locator('#logoutModal.show').wait_for(state='visible')
            page.screenshot(path=str(out / 'logout-modal.png'))
        page.goto((root / '04-genre_list.html').as_uri(), wait_until='domcontentloaded')
        page.screenshot(path=str(out / f'genre-{suffix}.png'), full_page=True, animations='disabled')
        page.goto((root / '07-book_detail.html').as_uri(), wait_until='domcontentloaded')
        page.screenshot(path=str(out / f'book-detail-{suffix}.png'), full_page=True, animations='disabled')
        context.close()
    browser.close()
print('완료: screenshots 폴더에서 캡처 파일 7개를 확인하세요.')
