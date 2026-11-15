import time

from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

MAIN_URL = 'https://www.tossinvest.com/'


def get_driver(headless=False):
    """옵션을 적용한 크롬 브라우저를 실행해 돌려준다"""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    if headless:
        # 창 없이 백그라운드로 실행 (웹 서비스 안에서 실행할 때)
        chrome_options.add_argument('--headless=new')
        # 창 크기를 지정하지 않으면 작은 화면(모바일) 배치로 그려질 수 있음
        chrome_options.add_argument('--window-size=1920,1080')
    # webdriver-manager 로 크롬 버전에 맞는 ChromeDriver 자동 설치
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


def open_main(driver):
    """토스증권 메인 페이지에 접속하고, 화면이 그려질 때까지 기다린다"""
    driver.get(MAIN_URL)
    # 왼쪽 메뉴(#ts-lnb)가 나타나면 화면이 그려진 것으로 판단
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '#ts-lnb'))
    )
    print('[접속] 토스증권 메인 페이지 로딩 완료')


def close_popups(driver):
    """첫 진입 시 뜨는 안내 팝업의 닫기 버튼을 모두 누른다"""
    time.sleep(1)  # 팝업이 조금 늦게 뜨는 경우 대비
    for close_btn in driver.find_elements(By.XPATH, "//button[@aria-label='닫기']"):
        try:
            if close_btn.is_displayed():
                # 다른 요소에 가려진 버튼도 클릭되도록 JS 로 클릭
                driver.execute_script('arguments[0].click();', close_btn)
                time.sleep(0.5)
        except Exception:
            pass


def search_company(driver, company_name):
    """'/' 단축키로 검색창을 열고 회사명을 검색한다 (최상단 회사 자동 선택)"""
    close_popups(driver)

    # 단축키는 페이지 전체(body)에 포커스가 있어야 동작
    driver.execute_script('document.activeElement.blur(); document.body.focus();')
    ActionChains(driver).send_keys('/').perform()

    search_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//input[@placeholder='검색어를 입력해주세요']")
        )
    )
    search_input.send_keys(company_name)
    search_input.send_keys(Keys.ENTER)
    print(f'[검색] {company_name}')

def get_stock_code(driver):
    """종목 페이지 주소에서 종목 코드를 꺼낸다 (이동 못 하면 None = 검색 결과 없음)"""
    try:
        WebDriverWait(driver, 15).until(EC.url_contains('/order'))
    except TimeoutException:
        print('[검색 실패] 종목 페이지로 이동하지 못했습니다.')
        return None

    # https://www.tossinvest.com/stocks/A005930/order -> 'A005930'
    parts = driver.current_url.split('/')
    stock_code = parts[parts.index('stocks') + 1]
    print(f'[종목 코드] {stock_code} ({driver.current_url})')
    return stock_code


def get_stock_name(driver):
    """탭 제목 '220,250원 -5.06% | 삼성전자' 에서 실제 종목명을 꺼낸다"""
    WebDriverWait(driver, 10).until(lambda d: '|' in d.title)
    stock_name = driver.title.split('|')[-1].strip()
    print(f'[종목명] {stock_name}')
    return stock_name


def open_community(driver, stock_code):
    """종목 코드로 커뮤니티 페이지 주소를 만들어 바로 이동한다"""
    community_url = f'https://www.tossinvest.com/stocks/{stock_code}/community'
    driver.get(community_url)

    # 댓글 영역(#stock-content)이 나타날 때까지 대기 (시간 초과 시 안내만 출력)
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#stock-content'))
        )
        print('[커뮤니티] 댓글 영역 로딩 완료')
    except TimeoutException:
        print('[커뮤니티] 10초 안에 댓글 영역을 찾지 못했습니다. 화면을 확인하세요.')


# 댓글 본문 선택자 : 배포마다 바뀌는 클래스명 대신 "역할" 속성 기준
#   style 안의 --fold-after-lines(N줄까지만 보이고 접기)는 게시글 본문에만 있음
COMMENT_SELECTOR = "span[style*='--fold-after-lines']"


def read_visible_comments(driver, comments):
    """지금 화면에 보이는 댓글을 comments 리스트에 추가한다 (중복 제외)"""
    for span in driver.find_elements(By.CSS_SELECTOR, COMMENT_SELECTOR):
        try:
            text = span.text.strip()
        except StaleElementReferenceException:
            # 읽는 사이에 화면이 다시 그려져 사라진 요소 -> 다음 스크롤 때 다시 읽힘
            continue
        if text and text not in comments:
            comments.append(text)


def find_scroll_container(driver):
    """댓글 목록을 감싼 내부 스크롤 영역을 찾는다 (없으면 None)"""
    # base-ui-...-viewport 상자가 여러 개 있으므로 "댓글이 들어 있는" 상자만 고름
    return driver.execute_script(
        """
        const boxes = document.querySelectorAll("div[data-id^='base-ui-'][data-id$='-viewport']");
        for (const box of boxes) {
            if (box.querySelector(arguments[0])) return box;
        }
        return null;
        """,
        COMMENT_SELECTOR,
    )


def collect_comments(driver, limit=20, max_scroll=30):
    """스크롤을 반복하며 댓글을 최대 limit 개까지 모아 돌려준다"""
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, COMMENT_SELECTOR))
        )
    except TimeoutException:
        print('[수집] 댓글을 찾지 못했습니다. 선택자가 바뀌었는지 확인하세요.')
        return []

    scroll_container = find_scroll_container(driver)
    comments = []
    prev_count = -1      # 직전 반복의 댓글 개수
    stagnant_rounds = 0  # 댓글 개수가 그대로인 횟수

    for scroll in range(max_scroll):
        read_visible_comments(driver, comments)
        print(f'[수집] 스크롤 {scroll + 1}회 -> 누적 {len(comments)}개')

        # 목표 개수 도달 또는 스크롤 상자가 없으면 종료
        if len(comments) >= limit or scroll_container is None:
            break

        # 5번 연속 개수가 늘지 않으면 더 이상 댓글이 없다고 판단
        if len(comments) == prev_count:
            stagnant_rounds += 1
            if stagnant_rounds >= 5:
                break
        else:
            stagnant_rounds = 0
        prev_count = len(comments)

        # 스크롤 상자는 화면이 다시 그려지면 바뀌므로 매번 새로 찾음
        scroll_container = find_scroll_container(driver)
        if scroll_container is None:
            break
        try:
            # 스크롤 상자를 맨 아래로 이동 -> 다음 댓글 자동 로딩
            driver.execute_script(
                'arguments[0].scrollTop = arguments[0].scrollHeight;', scroll_container
            )
        except StaleElementReferenceException:
            # 이번 회차는 건너뛰고 다음 반복에서 다시 시도
            pass
        time.sleep(1.5)  # 새 댓글을 불러올 시간

    return comments[:limit]
