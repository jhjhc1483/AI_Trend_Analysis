
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import json

url = "https://kookbang.dema.mil.kr/newsWeb/allToday.do"

response = requests.get(url)
html = response.text
soup = BeautifulSoup(html, 'html.parser')
data = []

# 모든 기사 li 기준으로 순회
for li in soup.select("li"):
    title_tag = li.select_one(".eps1")
    date_tag = li.select_one("span")
    link_tag = li.select_one("a")

    # 필수 요소가 없으면 건너뜀
    if not (title_tag and date_tag and link_tag):
        continue
    # 제목
    name = title_tag.get_text(strip=True)
    # 카테고리 (비워둠)
    category = ""
    # 링크
    link = "https://kookbang.dema.mil.kr/" + link_tag.get("href")
    # 날짜 (예: 2025. 12. 18. 17:42)
    date_text = date_tag.get_text(strip=True)
    date = date_text.split(". ")
    year = date[0]
    month = date[1]
    day = date[2]
    time = date[3].split(":")
    hour = time[0]
    minute = time[1]

    data.append([name, category, link, year, month, day, hour, minute])

df13 = pd.DataFrame(data, columns=['제목','분류','링크','년','월','일','시', '분'])
full_path = 'codes/kookbang.json'
new_data = df13.to_dict('records') # 새 DataFrame을 리스트 오브 딕셔너리 형태로 변환    

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

