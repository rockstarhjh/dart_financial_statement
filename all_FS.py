from os import path

import requests
from astropy.utils.data import download_file
from bs4 import BeautifulSoup
import pandas as pd
import re

from lxml import html


# 전자공시 dart의 API 키를 텍스트 파일에서 읽기
basepath = "F:\study\coding\python\crawling\dart_financial_statement"  # api_key 파일 경로
filepath = path.abspath(path.join(basepath,  "api_key.txt"))
with open(filepath, 'r') as f:
    API_KEY = f.read()

# print(API_KEY)

# 종목코드 저장한 엑셀파일 불러오기(엑셀출처:[한국거래소 전자공시 홈페이지](http://kind.krx.co.kr/corpgeneral/corpList.do?method=loadInitPage))

file_path = "F:\study\coding\python\crawling\dart_financial_statement"   # 종목코드 엑셀파일 경로
file_name_kospi = "company_codes_kospi.xlsx"
file_name_kosdaq = "company_codes_kosdaq.xlsx"

df1 = pd.read_excel(join(file_path, file_name_kospi), dtype=str)  # 코스피 종목코드 불러오기
df2 = pd.read_excel(join(file_path, file_name_kosdaq), dtype=str)  # 코스닥 종목코드 불러오기

# 코스피인지 코스닥인지 구분하는 열 추가
df1.insert(0, '분류', '코스피')
df2.insert(0, '분류', '코스닥')

# 코스피 코스닥 종목코드 합치기
company_codes = pd.concat([df1, df2], ignore_index=True)

# 합친 종목코드 엑셀로 저장하기
company_codes.to_excel(file_path+'company_codes.xlsx')

# crp_cd = [] #종목코드 리스트 변수 만들기
# for item in company_codes['종목코드']:
#     crp_cd.append(item)

company_data = company_codes[['분류', '회사명', '종목코드']]  # 분류, 회사명, 종목코드만 가져오기


# 회사이름 입력하면 그 이름이 있는지와 있다면 종목코드 가져오기
company_name = input('회사명을 입력해주세요 : ')

while len(company_data[company_data['회사명'] == company_name]) == 0:  # 회사이름이 완전히 같지않으면 즉, 없거나 일부포함하면 0을 리턴
    print('해당 이름의 회사가 존재하지 않습니다. 다시 입력해주세요')
    print('아래에 회사목록이 있다면 아래 회사중 하나를 찾으시나요? 다시 입력해주세요.')
    for row in company_data['회사명']:
        if row.find(company_name) != -1:  # 일부포함하는 회사명이 있는지 확인
            print(row)
    company_name = input('회사명을 입력해주세요 : ')

code = company_data[company_data.회사명 == company_name].종목코드.iloc[0]   # 입력한 회사명과 일치하는 종목코드 리턴
print("회사명: "+company_name+"\n종목코드: "+code)


# dart 사이트의 보고서 목록 url 생성, 여기서 crp_no 가져와야함

start_dt = '20010101'  # 검색시작일
bsn_tp = 'A001'  # 검색할 보고서 종류, A001 = 사업보고서
fin_rpt = "Y"  # 최종보고서만 검색할 시 Y
page_set = '100'  # 페이지당 건수(1~100) 기본값 : 10, 최대값 : 100

url = "http://dart.fss.or.kr/api/search.json?auth="+API_KEY+"&crp_cd="+code+"&start_dt="+start_dt+"&bsn_tp="+bsn_tp+"&fin_rpt="+fin_rpt+"&page_set="+page_set  # dart사이트 api 요청 url
ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36"
headers = {'User-Agent': ua}
a = requests.get(url, headers=headers).json()  # 조건에 따른 공시결과 조회(사업보고서), 여기서 rcp_no 값을 뽑아내서 url에 연결하여 각 보고서를 조회해야함
# print(a['list'])

# 검색조건 url에 맞는 보고서 목록 url중에서 각각의 보고서정보 rcp_no를 가져와야함

urldict = {}
for row in a['list']:  # list 키 안에 rcp_no, rpt_nm 등의 값들이 들어있음
    url2 = "http://dart.fss.or.kr/dsaf001/main.do?rcpNo="  # rcp_no 값만 넣으면 보고서 조회가능한 url이 됨
    name = row['rpt_nm']  # rpt_nm은 보고서의 이름 여기서는 '사업보고서(0000.00.00)'
    # [기재정정][첨부추가][첨부정정] 등 보고서 앞에 붙은 이름을 제거
    if name.find('[') != -1:
        name = name.split(']')[1]    # [첨부추가]사업보고서(0000.00.00)이라면 ]를 기준으로 앞의 [첨부추가] 와 사업보고서(0000.00.00)으로 분리 1번째 값이므로 뒤의 사업보고서를 이름으로 할당
    urldict[name] = url2+row['rcp_no']
    print(name+": " + url2 + row['rcp_no'])
    report_url = url2+row['rcp_no']  # 이 url 이 보고서 조회 가능한 url
    report_data = requests.get(report_url)  # 보고서 조회가능한 url을 요청하여 해당 페이지 데이터를 가져옴
    bsObj = BeautifulSoup(report_data.content, "html.parser")  # 해당 페이지 데이터는 html 인코딩? 을 통해 beautifulsoup 객체로 가져옴
    fs_find1 = re.compile('\d\.\s연결재무제표["]')   # 정규표현식(re모듈)으로 해당 객체안에서 원하는 텍스트 정보를 얻기위해 정규표현식을 설정
    fs_find2 = re.compile('\d\.\s재무제표["]')
    head_lines = bsObj.find('head').text.split("\n")  # 리스트데이터타입
    print(head_lines)
    # result = fs_find1.search(head_lines)  # 오류남, re의 search 함수는 인자로 str 타입을 받으나 인자로 리스트(head_lines)를 줬기 때문




# #카운터 선정
# n = 1
# for key, value in urldict.items():
#     # dcm_no 값을 알아야 다운로드 링크에 접근할 수 있는데, 알 방법이 링크에서 바로 가져오는 방법밖에 없으므로 xpath을 활용해서 알아봅시다
#     test = requests.get(value, headers=headers)
#     tree = html.fromstring(test.content)
#     testpath = tree.xpath('//*[@id="north"]/div[2]/ul/li[1]/a/@onclick')[0]
#     print(testpath)
#     dcm_no = testpath.split(", '")[1].split("')")[0]
#     # print(dcm_no)
#
#     # 다운로드를 위한 url은 보고서 url과 차이점이 몇 가지 있는데, replace를 통해 추가할 수 있어요
#     download_url = value.replace('dsaf001', 'pdf/download').replace('rcpNo', 'rcp_no') + "&dcm_no=" + dcm_no
#     print(key + " " + download_url + " Downloading... " + str(n) + " out of " + str(len(urldict)))
#
#     # dcm_no를 구했던 것과 같은 방법으로 첨부파일 다운로드 url을 추출합니다
#     dtest = requests.get(download_url, headers=headers)
#     dtree = html.fromstring(dtest.text)

    # \d\.\s연결재무제표["]


    # # 각 보고서 당 복수의 첨부파일이 존재하는데, 첨부파일 이름과 함께 저장하기 위해 downloadpath라는 dict를 사용했습니다
    # downloadpath = {}
    # keys = dtree.xpath('/html/body/div/div/table/tr/td[1]/text()')
    # key_links = dtree.xpath('/html/body/div/div/table/tr/td/a/@href')
    # for key2, link in zip(keys, key_links):
    #     l = "http://dart.fss.or.kr" + link
    #     k = key2.replace(")", "").replace("(", "_")
    #     downloadpath[k] = l
    #     # print(k)
    #
    # # utils에 있는 download_file을 이용해 디렉토리를 만들고 그 안에다가 파일을 집어넣습니다
    # for key2, link in downloadpath.items():
    #     # download_file(link, filename=key2, directory="dart_" + company_name + "/" + key)
    #     requests.urlretrieve(url, key2)
    #
    # n += 1




