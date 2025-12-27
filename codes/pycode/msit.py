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

# 1. 옵션 설정
chrome_options = Options()

# [핵심 수정 1] 최신 Headless 모드 사용
chrome_options.add_argument("--headless=new") 

# [핵심 수정 2] 화면 크기를 PC와 동일하게 고정 (반응형 웹 대응)
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--start-maximized")

# 리눅스 환경 설정 (CI/CD 필수)
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--allow-running-insecure-content')

# 봇 탐지 우회 User-Agent
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# 드라이버 실행
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

data = []

try:
    for i in range(1, 4):
        url = f"https://www.msit.go.kr/bbs/list.do?sCode=user&mId=307&mPid=208&pageIndex={i}&bbsSeqNo=94"
        driver.get(url)
        
        # [핵심 수정 3] 무작정 sleep 대신, 특정 요소가 뜰 때까지 최대 10초 대기
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".board_list .toggle:not(.thead)"))
            )
        except Exception:
            print(f"{i} 페이지 로딩 시간 초과 또는 데이터 없음")
            # 디버깅용: 페이지 소스를 파일로 저장해서 나중에 artifact로 확인 가능
            # with open("debug_page_source.html", "w", encoding="utf-8") as f:
            #     f.write(driver.page_source)

        # 게시글 요소 찾기
        items = driver.find_elements(By.CSS_SELECTOR, ".board_list .toggle:not(.thead)")
        
        if not items:
            print(f"{i} 페이지에서 게시글을 찾지 못했습니다.")
            continue

        for item in items:
            try:
                title_el = item.find_element(By.CSS_SELECTOR, "p.title")
                name = title_el.text.strip()
                
                date_el = item.find_element(By.CSS_SELECTOR, ".date")
                date = date_el.text.strip()
                date_temp = date.split(". ") 
                years = date_temp[0]
                month =  date_temp[1]
                day = date_temp[2]

                link_element = item.find_element(By.TAG_NAME, "a")
                onclick_text = link_element.get_attribute("onclick")
                
                code = re.search(r'\d+', onclick_text).group()
                
                link = f"https://www.msit.go.kr/bbs/view.do?sCode=user&mId=307&mPid=208&pageIndex=1&bbsSeqNo=94&nttSeqNo={code}&searchOpt=ALL&searchTxt="
                
                if name and years and month and day and link:
                    data.append([name, link, years, month, day])
            except Exception as e:
                # print(f"항목 추출 중 에러: {e}")
                continue

except Exception as e:
    print(f"전체 프로세스 중 치명적 에러 발생: {e}")

finally:
    driver.quit()

# 결과 확인
print(f"\n총 {len(data)} 건 추출 완료")

# --- (이하 JSON 저장 로직은 기존과 동일하므로 유지) ---
df15 = pd.DataFrame(data, columns=['기사명','링크','년','월','일'])
full_path = 'codes/msit.json'
new_data = df15.to_dict('records')

# 저장 폴더가 없으면 생성 (안전장치)
os.makedirs(os.path.dirname(full_path), exist_ok=True)

existing_data = []

if os.path.exists(full_path):
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if content:
                existing_data = json.loads(content)
    except Exception as e:
        print(f"기존 파일 로드 에러: {e}")
        existing_data = []

combined_data = existing_data + new_data
seen_links = set()
final_data = []

for item in combined_data:
    link = item.get('링크')
    if link and link not in seen_links:
        final_data.append(item)
        seen_links.add(link)
        
print(f"중복 제거 후 최종 데이터: {len(final_data)}개")

with open(full_path, 'w', encoding='utf-8') as f:
    json.dump(final_data, f, indent=4, ensure_ascii=False)
