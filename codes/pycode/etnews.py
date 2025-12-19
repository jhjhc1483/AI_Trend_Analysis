import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import json
import os
import re

# 전자신문 검색어 '인공지능' 5페이지까지 크롤링
for i in range(1,6):
    response = requests.get(f"https://search.etnews.com/etnews/search.html?category=CATEGORY1&kwd=%EC%9D%B8%EA%B3%B5%EC%A7%80%EB%8A%A5&pageNum={i}&pageSize=20&reSrchFlag=false&sort=1&startDate=&endDate=&detailSearch=true&preKwd%5B0%5D=%EC%9D%B8%EA%B3%B5%EC%A7%80%EB%8A%A5", verify=False)

    html = response.text
    soup = BeautifulSoup(html, 'html.parser')


    data = []
    items=soup.select(".news_list li")
    for item in items:
        name = item.select_one(".text > strong").text.strip()
        numbers = re.sub(r'[^\d]', '',item.select_one(".text > strong > a").attrs['href'])
        # numbers = re.sub(r'[^\d]', '', link1)
        #summary = item.select_one(".summary").text
        link = f"https://www.etnews.com/{numbers}"
        response = requests.get(link)
        html2 = response.text
        soup2 = BeautifulSoup(html2, 'html.parser')   
        time = soup2.select_one("time").text
        parts = time.split(' ')
        date_part = parts[2]  
        time_part = parts[3] 
        d = date_part.split('-')
        years = d[0]
        month = d[1]
        day = d[2]
        d1 = time_part.split(':')
        hour = d1[0]
        minute = d1[1]
        data.append([name,link,years,month,day,hour,minute])

df2 = pd.DataFrame(data, columns=['기사명','링크','년','월','일','시','분'])
df2['기사명'] = df2['기사명'].fillna('').str.replace(r'\\', '', regex=True)
df2['기사명'] = df2['기사명'].str.replace('\'', '＇', regex=False)
df2['기사명'] = df2['기사명'].str.replace('\"', '〃', regex=False)
# #엑셀 저장
# #index=False 는 앞에 번호 없애기
# df2.to_excel('result.xlsx', index=False)
# full_path = 'D:/startcoding/python_crawling/04.기사 크롤링 사이트 만들기/etnews.json'
# df2.to_json(full_path, orient='records', indent=4, force_ascii=False)

# ... (기존 엑셀 저장 코드)
# df2.to_excel('result.xlsx', index=False)

full_path = 'codes/etnews.json'
new_data = df2.to_dict('records') # 새 DataFrame을 리스트 오브 딕셔너리 형태로 변환

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
