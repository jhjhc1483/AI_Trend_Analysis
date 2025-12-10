from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service # Service 클래스 임포트
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import os
import json


# --- Options 설정 부분 수정 ---
chrome_options = webdriver.ChromeOptions()

# 1. Headless 모드 설정 (GUI 없이 백그라운드에서 실행)
chrome_options.add_argument('--headless')

# 2. 샌드박스 비활성화 (GitHub Actions/Docker 환경에서 필수)
chrome_options.add_argument('--no-sandbox')

# 3. /dev/shm 사용 비활성화 (리소스 제한 환경에서 충돌 방지)
chrome_options.add_argument('--disable-dev-shm-usage')

# 4. 기타 유용한 옵션들
chrome_options.add_argument('--window-size=1920,1080')
chrome_options.add_argument('--disable-gpu') # GPU 사용 비활성화
# ------------------------------

# service와 options를 사용하여 브라우저 초기화
# 예시: service = Service(ChromeDriverManager().install())
# browser = webdriver.Chrome(service=service, options=chrome_options)


# 1. 드라이버 실행 파일 경로 지정
CHROME_DRIVER_PATH = 'C:/chromedriver.exe'

# 2. Service 객체 생성 시 경로 전달

service = Service(executable_path=ChromeDriverManager().install())
chrome_options = Options()
chrome_options.add_experimental_option("detach",True)

#불필요한 에러 메시지 없애기
chrome_options.add_experimental_option("excludeSwitches",["enable=logging"])
# 3. Service 객체를 사용하여 WebDriver 초기화
# 이제 webdriver.Chrome()에는 Service 객체를 keyword argument로 전달합니다.
browser = webdriver.Chrome(service=service, options=chrome_options)

# 웹사이트 열기
browser.get('https://www.aitimes.com/news/articleList.html?page=1&total=29543&sc_section_code=&sc_sub_section_code=&sc_serial_code=&sc_area=&sc_level=&sc_article_type=&sc_view_level=&sc_sdate=&sc_edate=&sc_serial_number=&sc_word=&sc_andor=&sc_word2=&box_idxno=&sc_multi_code=&sc_is_image=&sc_is_movie=&sc_user_name=&sc_order_by=E')
browser.implicitly_wait(10)

driver = None # 드라이버 객체를 try/finally 외부에서 선언
more_button = browser.find_element(By.CSS_SELECTOR, '.button.expanded.nd-white.list-btn-more')
# more_button.click()
# more_button.click()
# more_button.click()
# more_button.click()
#more_button.click()
#more_button.click()
#more_button.click()
#more_button.click()

items = browser.find_elements(By.CSS_SELECTOR, '.altlist-text-item')
data = []
for item in items:
    name=item.find_element(By.CSS_SELECTOR,'.altlist-subject').text
    link = str(item.find_element(By.CSS_SELECTOR,'.altlist-subject > a').get_attribute('href'))
    print(link)
    if link == "":
        break
    response = requests.get(link)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')   
    date = soup.select_one(".breadcrumbs > li:nth-child(2)").text.strip() 
    parts = date.split(' ')
    date_part = parts[1]  
    time_part = parts[2] 
    d = date_part.split('.')
    years = d[0]
    month = d[1]
    day = d[2]
    d1 = time_part.split(':')
    hour = d1[0]
    # print(hour)
    #minute_temp = d1[1].split('"\"')
    minute_with_extras = d1[1].strip()
    minute = re.sub(r'[^0-9]', '', minute_with_extras)
    # print(name)
    # print(minute)
    data.append([name,link,years,month,day,hour,minute])
    

df1 = pd.DataFrame(data, columns=['기사명','링크','년','월','일','시','분'])
df1['기사명'] = df1['기사명'].fillna('').str.replace(r'\\', '', regex=True)
df1['기사명'] = df1['기사명'].str.replace('\'', '＇', regex=False)
df1['기사명'] = df1['기사명'].str.replace('\"', '〃', regex=False)



# =============================================================
# 셀 6: JSON 파일 이어 붙이기 및 저장 로직 (경로 수정됨)
# =============================================================

# 💡 현재 스크립트와 동일한 디렉토리(code 폴더)에 저장됩니다.
full_path = 'codes/aitimes.json' 
new_data = df1.to_dict('records')

existing_data = []

# 1. 기존 JSON 파일 로드
if os.path.exists(full_path):
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
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

# 3. 중복 제거
seen_links = set()
final_data = []

for item in combined_data:
    link = item.get('링크')
    if link and link not in seen_links:
        final_data.append(item)
        seen_links.add(link)
        
print(f"총 {len(existing_data)}개의 기존 데이터와 {len(new_data)}개의 새 데이터를 합쳤습니다.")
print(f"중복을 제거한 후 최종 데이터는 총 {len(final_data)}개입니다.")

# 4. 최종 데이터를 JSON 파일로 저장
with open(full_path, 'w', encoding='utf-8') as f:
    json.dump(final_data, f, indent=4, ensure_ascii=False)

print(f"\n최종 데이터가 '{full_path}'에 성공적으로 저장되었습니다.")

