from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import pandas as pd
import os
import json

# ==========================================
# 1. 옵션 설정
# ==========================================
chrome_options = Options()

# [디버깅 핵심 1] Headless 모드 끄기 (화면을 직접 확인하기 위함)
# 문제가 해결되면 다시 주석을 해제하세요.
# chrome_options.add_argument("--headless") 

chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--allow-running-insecure-content')

# 2. 드라이버 실행
print(">>> 브라우저를 실행합니다...")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.maximize_window() # 화면 크게 보기

data = []

try:
    for i in range(1, 4):
        print(f"\n[INFO] {i} 페이지로 이동 중...")
        url = f"https://www.msit.go.kr/bbs/list.do?sCode=user&mId=307&mPid=208&pageIndex={i}&bbsSeqNo=94"
        driver.get(url)
        
        # [디버깅 핵심 2] 로딩 대기 (단순 sleep 대신, 특정 요소가 뜰 때까지 대기 시도)
        try:
            # 게시판 리스트가 뜰 때까지 최대 10초 대기
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".board_list"))
            )
            print("   -> 페이지 로딩 완료 (게시판 요소 감지됨)")
        except:
            print("   -> [경고] 게시판 요소를 찾을 수 없습니다. (타임아웃)")

        time.sleep(2) # 추가 안정화 대기

        # [디버깅 핵심 3] 현재 페이지 제목 출력 (차단 여부 확인용)
        print(f"   -> 현재 페이지 제목: {driver.title}")

        # 게시글 요소 찾기
        items = driver.find_elements(By.CSS_SELECTOR, ".board_list .toggle:not(.thead)")
        
        print(f"   -> 발견된 게시글 수: {len(items)}개")

        if not items:
            print(f"   -> [ERROR] {i} 페이지에서 게시글을 찾지 못했습니다.")
            # HTML 구조가 바뀌었거나 차단되었을 수 있음. HTML 일부 출력
            print("   -> [HTML 소스 앞부분 확인]\n", driver.page_source[:500])
            continue

        count = 0
        for item in items:
            try:
                # 제목 추출 시도
                title_el = item.find_element(By.CSS_SELECTOR, "p.title")
                name = title_el.text.strip()
                
                # 날짜 추출 시도
                date_el = item.find_element(By.CSS_SELECTOR, ".date")
                date = date_el.text.strip()
                
                # 날짜 파싱
                if ". " in date:
                    date_temp = date.split(". ") 
                    years = date_temp[0]
                    month = date_temp[1]
                    day = date_temp[2]
                else:
                    # 날짜 형식이 다를 경우 대비
                    years, month, day = "0000", "00", "00"

                # 링크(onclick) 추출 시도
                link_element = item.find_element(By.TAG_NAME, "a")
                onclick_text = link_element.get_attribute("onclick")
                
                if onclick_text:
                    code_match = re.search(r'\d+', onclick_text)
                    if code_match:
                        code = code_match.group()
                        link = f"https://www.msit.go.kr/bbs/view.do?sCode=user&mId=307&mPid=208&pageIndex=1&bbsSeqNo=94&nttSeqNo={code}&searchOpt=ALL&searchTxt="
                        
                        if name:
                            data.append([name, link, years, month, day])
                            count += 1
                            # 정상 추출 확인용 로그 (너무 많으면 주석 처리)
                            # print(f"      - 추출 성공: {name[:10]}...")
            except Exception as e:
                print(f"      - [항목 에러] 개별 항목 추출 실패: {e}")
                continue
        
        print(f"   -> {count}개 항목 데이터 리스트에 추가 완료")

finally:
    driver.quit()
    print("\n>>> 브라우저를 종료했습니다.")

# 결과 확인
print(f"\n=============================")
print(f"총 {len(data)} 건 추출 완료")
print(f"=============================")

# ----------------- 저장 로직 (기존과 동일) -----------------
if len(data) > 0:
    df15 = pd.DataFrame(data, columns=['기사명','링크','년','월','일'])
    full_path = 'codes/msit.json'
    
    # 폴더가 없으면 생성
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    new_data = df15.to_dict('records')

    existing_data = []
    if os.path.exists(full_path):
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if content:
                    existing_data = json.loads(content)
        except Exception as e:
            print(f"기존 JSON 로드 에러: {e}")

    combined_data = existing_data + new_data
    
    # 중복 제거
    seen_links = set()
    final_data = []
    for item in combined_data:
        link = item.get('링크')
        if link and link not in seen_links:
            final_data.append(item)
            seen_links.add(link)

    with open(full_path, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=4, ensure_ascii=False)

    print(f"저장 완료: {len(final_data)}개 항목 (경로: {full_path})")
else:
    print("추출된 데이터가 없어 파일을 저장하지 않았습니다.")
