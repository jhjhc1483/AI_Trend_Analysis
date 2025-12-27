from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import pandas as pd
import os
import json

# 1. 옵션 설정 (봇 탐지 우회 및 화면 크기 설정)
# --- Headless 옵션 설정 ---
chrome_options = Options()
chrome_options.add_argument("--headless")  # 창 띄우지 않음
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
# [중요] 봇 탐지 우회 (일반 브라우저인 척 위장)
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
# [중요] 일부 보안 옵션 무시
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--allow-running-insecure-content')

# 2. 드라이버 실행
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

data = []

try:
    for i in range(1, 4):
        url = f"https://www.msit.go.kr/bbs/list.do?sCode=user&mId=307&mPid=208&pageIndex={i}&bbsSeqNo=94"
        driver.get(url)
    
        time.sleep(5) # 서버 부하 고려하여 대기 시간 약간 늘림
    
        # [디버깅] 접속 성공 여부 확인

        # 게시글 요소 찾기
        items = driver.find_elements(By.CSS_SELECTOR, ".board_list .toggle:not(.thead)")
        
        if not items:
            print(f"{i} 페이지에서 게시글을 찾지 못했습니다. (페이지 소스 확인 필요)")
            # 디버깅용: 페이지 소스 일부 출력 (차단되었는지 확인용)
            # print(driver.page_source[:500]) 
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

finally:
    driver.quit()

# 결과 확인
print(f"\n총 {len(data)} 건 추출 완료")

df15 = pd.DataFrame(data, columns=['기사명','링크','년','월','일'])
full_path = 'codes/msit.json'
new_data = df15.to_dict('records') # 새 DataFrame을 리스트 오브 딕셔너리 형태로 변환
# ----------------- JSON 이어 붙이기 및 중복 제거 로직 시작 -----------------

existing_data = []

# 1. 기존 JSON 파일 로드
if os.path.exists(full_path):
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            # 파일이 비어있지 않은지 확인 후 로드
            content = f.read()
            if content:
                existing_data = json.loads(content)
            else:
                print("기존 JSON 파일은 존재하지만 비어 있습니다. 새 데이터만 저장합니다.")
    except Exception as e:
        print(f"기존 JSON 파일 로드 중 오류 발생 ({e}). 새 데이터만 저장합니다.")
        existing_data = []

# 2. 새 데이터와 기존 데이터를 합치기
combined_data = existing_data + new_data

# 3. 중복 제거 (가장 중요한 단계)
# '링크'를 기준으로 중복 제거를 위한 Set을 생성합니다.
seen_links = set()
final_data = []

for item in combined_data:
    link = item.get('링크') # '링크' 컬럼 값을 가져옵니다.
    
    # '링크'가 None이거나 비어있지 않고, 아직 처리하지 않은 링크인 경우에만 추가
    if link and link not in seen_links:
        final_data.append(item)
        seen_links.add(link)
        
print(f"총 {len(existing_data)}개의 기존 데이터와 {len(new_data)}개의 새 데이터를 합쳤습니다.")
print(f"중복을 제거한 후 최종 데이터는 총 {len(final_data)}개입니다.")

# 4. 최종 데이터를 JSON 파일로 저장 (덮어쓰기)
# indent=4와 force_ascii=False 옵션을 유지하여 가독성 및 한글 보존
with open(full_path, 'w', encoding='utf-8') as f:
    json.dump(final_data, f, indent=4, ensure_ascii=False)

print(f"\n최종 데이터가 '{full_path}'에 성공적으로 저장되었습니다.")
