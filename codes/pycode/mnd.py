import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import os
import json

data = []
for i in range(3,8):    
    if i > 6:
        response = requests.get("https://www.mnd.go.kr/user/newsInUserRecord.action?siteId=mnd&handle=I_669&id=mnd_020500000000")
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        items=soup.select(".post")
        #name = soup.select_one(".wrap_title >div > a").text
        category = "국방부 보도자료"
        for item in items:
            name = item.select_one(".post > div").text.strip()
            code_temp = item.select_one(".title > a").attrs['href']
            pattern = r"_(.*?)&"
            # re.findall()을 사용하여 패턴과 일치하는 모든 캡처 그룹(Group 1)의 내용을 리스트로 추출
            code_list = re.findall(pattern, code_temp)
            link = f'https://www.mnd.go.kr/user/newsInUserRecord.action?siteId=mnd&page=1&newsId=I_669&newsSeq=I_{code_list[1]}&command=view&id=mnd_020500000000&findStartDate=&findEndDate=&findType=title&findWord=&findOrganSeq='
            date = item.select_one(".post_info > dl").select_one('dd').text.strip()
            date1 = date.split('-')
            years, month, day = date1
            hour = ""
            minute =""
            data.append([name,category,link,years,month,day,hour,minute])
    else:
        response = requests.get(f"https://www.mnd.go.kr/cop/kookbang/kookbangIlboList.do?handle=dema000{i}&siteId=mnd&id=mnd_020104000000")
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        items=soup.select(".post")
        #name = soup.select_one(".wrap_title >div > a").text
        if i ==3:
            category = "국방부"
        if i == 4:
            category = "육군"
        if i == 5:
            category = "해군"
        if i == 6:
            category = "공군"

        for item in items:
            name = item.select_one(".post > div").text.strip()
            code_temp = item.select_one(".title > a").attrs['href']
            pattern = r"'(.*?)'"
            # re.findall()을 사용하여 패턴과 일치하는 모든 캡처 그룹(Group 1)의 내용을 리스트로 추출
            code_list = re.findall(pattern, code_temp)
            link = f'https://www.mnd.go.kr/cop/kookbang/kookbangIlboView.do?siteId=mnd&pageIndex=1&findType=&findWord=&categoryCode={code_list[0]}&boardSeq={code_list[1]}&startDate=&endDate=&id=mnd_020101000000'
            date = item.select_one(".post_info > dl").select_one('dd').text.strip()
            date1 = date.split('.')
            years, month, day = date1
            hour = ""
            minute =""
            
            data.append([name,category,link,years,month,day,hour,minute])
# .attrs['alt']
#form_list > div > ul > li:nth-child(2) > div.thumb > a > img
# 
    # data.append([name,category,link,year,month,day,])


df5 = pd.DataFrame(data, columns=['기사명','분류','링크','년','월','일','시','분'])

full_path = 'codes/mnd.json'
new_data = df5.to_dict('records') # 새 DataFrame을 리스트 오브 딕셔너리 형태로 변환

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
