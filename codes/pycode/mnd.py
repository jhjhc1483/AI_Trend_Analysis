import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import os
import json
import time

# 1. 브라우저 헤더 설정 (User-Agent)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
}

# 타임아웃 설정 (초 단위)
TIMEOUT_SEC = 15

data = []

for i in range(3, 8):    
    if i > 6:
        url = "https://www.mnd.go.kr/user/newsInUserRecord.action?siteId=mnd&handle=I_669&id=mnd_020500000000"
        try:
            # timeout과 headers 적용
            response = requests.get(url, headers=headers, timeout=TIMEOUT_SEC)
            response.raise_for_status() # 200 OK가 아니면 에러 발생
            
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            items = soup.select(".post")
            category = "국방부 보도자료"
            
            for item in items:
                name = item.select_one(".post > div").text.strip()
                code_temp = item.select_one(".title > a").attrs['href']
                pattern = r"_(.*?)&"
                code_list = re.findall(pattern, code_temp)
                
                # 안전한 인덱싱 확인
                if len(code_list) > 1:
                    link = f'https://www.mnd.go.kr/user/newsInUserRecord.action?siteId=mnd&page=1&newsId=I_669&newsSeq=I_{code_list[1]}&command=view&id=mnd_020500000000&findStartDate=&findEndDate=&findType=title&findWord=&findOrganSeq='
                    date = item.select_one(".post_info > dl").select_one('dd').text.strip()
                    years, month, day = date.split('-')
                    data.append([name, category, link, years, month, day, "", ""])
        except Exception as e:
            print(f"보도자료 크롤링 중 오류: {e}")

    else:
        for p in range(1, 3):
            url = f"https://www.mnd.go.kr/cop/kookbang/kookbangIlboList.do?siteId=mnd&pageIndex={p}&findType=&findWord=&categoryCode=dema000{i}&boardSeq=&startDate=&endDate=&id=mnd_020101000000"
            try:
                response = requests.get(url, headers=headers, timeout=TIMEOUT_SEC)
                response.raise_for_status()
                
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                items = soup.select(".post")
                
                categories = {3: "국방부", 4: "육군", 5: "해군", 6: "공군"}
                category = categories.get(i, "기타")

                for item in items:
                    name = item.select_one(".post > div").text.strip()
                    code_temp = item.select_one(".title > a").attrs['href']
                    pattern = r"'(.*?)'"
                    code_list = re.findall(pattern, code_temp)
                    
                    if len(code_list) > 1:
                        link = f'https://www.mnd.go.kr/cop/kookbang/kookbangIlboView.do?siteId=mnd&pageIndex=1&findType=&findWord=&categoryCode={code_list[0]}&boardSeq={code_list[1]}&startDate=&endDate=&id=mnd_020101000000'
                        date = item.select_one(".post_info > dl").select_one('dd').text.strip()
                        years, month, day = date.split('.')
                        data.append([name, category, link, years, month, day, "", ""])
                
                # 서버 부하 방지를 위한 짧은 휴식
                time.sleep(0.5)
            except Exception as e:
                print(f"국방일보({category}) 크롤링 중 오류: {e}")

# 데이터프레임 생성
df5 = pd.DataFrame(data, columns=['기사명','분류','링크','년','월','일','시','분'])

# 폴더 생성 (없을 경우)
os.makedirs('codes', exist_ok=True)
full_path = 'codes/mnd.json'
new_data = df5.to_dict('records')

# ----------------- JSON 저장 및 중복 제거 -----------------
existing_data = []
if os.path.exists(full_path):
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if content:
                existing_data = json.loads(content)
    except Exception as e:
        print(f"기존 파일 로드 실패: {e}")

combined_data = existing_data + new_data
seen_links = set()
final_data = []

for item in combined_data:
    link = item.get('링크')
    if link and link not in seen_links:
        final_data.append(item)
        seen_links.add(link)

with open(full_path, 'w', encoding='utf-8') as f:
    json.dump(final_data, f, indent=4, ensure_ascii=False)

print(f"성공: 기존 {len(existing_data)}개 + 신규 {len(new_data)}개 -> 합계(중복제거 후) {len(final_data)}개 저장 완료.")