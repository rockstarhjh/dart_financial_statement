# -*- coding: utf-8 -*-
from os import path
from os.path import join
import requests
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

start_dt = '20081231'  # 검색시작일
# end_dt = '20031231'  # 검색종료일
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
    fs_find3 = re.compile('\d\.\s연결재무제표에 관한 사항["]')
    fs_find4 = re.compile('\.\s재무제표 등["]')
    head_lines = bsObj.find('head').text.split("\n")  # 리스트데이터타입
    line_num = 0   # head_lines 리스트에서 정규표현식에 일치하는 인덱스 찾기위한 변수 초기화
    line_find = 0  # 일치하는 인덱스를 저장하는 변수 초기화
    # 보고서 페이지 텍스트(head_lines)에서 일치하는 표현식 찾기
    for head_line in head_lines:
        if fs_find1.search(head_line):
            line_find = line_num     # 일치하는 항목이 있으면 그 위치의 인덱스 저장
            break
        elif fs_find2.search(head_line):   # 문제점, 재무제표항목이 연결재무제표보다 앞에 있으면 뒤의 연결재무제표를 검색을 안함. 일단 for문을 하나더 만듬
            line_find = line_num
            break
        elif fs_find3.search(head_line):
            line_find = line_num
            break
        elif fs_find4.search(head_line):
            line_find = line_num
            break
        line_num = line_num + 1    # 리스트의 다음인덱스로 변경하여 루프 순환

    line_num2 = 0
    for head_line in head_lines:
        if fs_find1.search(head_line):
            line_find = line_num2
            break
        line_num2 = line_num2 + 1

    if line_find != 0:  # 만약 일치하는 항목이 있으면
        line_words = head_lines[line_find+4].split("'")   # 그 위치를 기준으로 rcp_No 등을 찾음
        rcpNo = line_words[1]
        dcmNo = line_words[3]
        eleId = line_words[5]
        offset = line_words[7]
        length = line_words[9]
        dtd = line_words[11]
        fs_baseurl = "http://dart.fss.or.kr/report/viewer.do?rcpNo="
        fs_url = fs_baseurl+rcpNo+"&dcmNo="+dcmNo+"&eleId="+eleId+"&offset="+offset+"&length="+length+"&dtd="+dtd
        print(fs_url)

    fs_data = requests.get(fs_url)   # 최종얻은 재무제표url에서 페이지 데이터 요청하기
    bsObj_fs = BeautifulSoup(fs_data.content, "html.parser")   # 요청한 데이터를 html 인코딩?해서 객체에 담기
    tables = bsObj_fs.findAll("table")   # 페이지안에서 table 태그 찾기

    # 대차대조표, 손익계산서, 현금흐름표에 대한 테이블을 찾기위한 정규표현식 설정
    re_income_find = re.compile("법[ \s]*인[ \s]*세[ \s]*비[ \s]*용(\(이익\))*[ \s]*차[ \s]*감[ \s]*전[ \s]*순[ \s]*((이[ \s]*익)|(손[ \s]*실))|법[ \s]*인[ \s]*세[ \s]*차[ \s]*감[ \s]*전[ \s]*계[ \s]*속[ \s]*영[ \s]*업[ \s]*순[ \s]*이[ \s]*익|법인세[ \s]*차감전[ \s]*순이익|법인세차감전계속영업이익|법인세비용차감전이익|법인세비용차감전계속영업[순]*이익|법인세비용차감전당기순이익|법인세(비용차감|손익가감)전순이익|법인세비용차감전[ \s]*계속사업이익|법인세비용차감전순손익")
    re_cashflow_find = re.compile("영업활동[ \s]*현금[ \s]*흐름|영업활동으로[ \s]*인한[ \s]*[순]*현금[ \s]*흐름|영업활동으로부터의[ \s]*현금흐름|영업활동으로 인한 자산부채의 변동")
    re_balance_sheet_find = re.compile("현[ \s]*금[ \s]*및[ \s]*현[ \s]*금[ \s]*((성[ \s]*자[ \s]*산)|(등[ \s]*가[ \s]*물))")   #  [ \s]* 은 빈공백이 0개이상 있다는 의미, 따라서 공백이 있거나 없거나 임.

    # 정규표현식과 일치하는 테이블 찾기
    cnt = 0  #테이블 변수 초기화
    table_balance_num = 0
    # 대차대조표 찾기
    for table in tables:
        if re_balance_sheet_find.search(table.text):  # 만약 전체 재무제표테이블안에서 대차대조표의 정규표현식과 일치하는 테이블이 있다면
            table_balance_num = cnt
            break
        cnt += 1
    balance_table = bsObj_fs.findAll("table")[table_balance_num]

    # 손익계산서 찾기
    cnt = 0
    table_income_num = 0
    for table in tables:
        if re_income_find.search(table.text):  # 만약 전체 재무제표테이블안에서 손익계산서의 정규표현식과 일치하는 테이블이 있다면
            table_income_num = cnt
            break
        cnt += 1
    income_table = bsObj_fs.findAll("table")[table_income_num]
    # 현금흐름표 테이블 찾기
    cnt = 0
    table_cashflow_num = 0
    for table in tables:
        if re_cashflow_find.search(table.text):  # 만약 전체 재무제표테이블안에서 손익계산서의 정규표현식과 일치하는 테이블이 있다면
            table_cashflow_num = cnt
            break
        cnt += 1
    cashflow_table = bsObj_fs.findAll("table")[table_cashflow_num]

    table_num = [table_balance_num, table_income_num, table_cashflow_num]
    # 단위 검색 및 설정
    re_unit1 = re.compile('단위[ \s]*:[ \s]*원')
    re_unit2 = re.compile('단위[ \s]*:[ \s]*백만원')
    re_unit3 = re.compile('단위[ \s]*:[ \s]*천원')

    i = 0
    unit = []
    for num in table_num:
        # 원
        if len(bsObj_fs.findAll("table")[num - 1](string=re_unit1)) != 0:
            unit.append(100000000.0)
            unit_find = 1
        # 백만원
        elif len(bsObj_fs.findAll("table")[num - 1](string=re_unit2)) != 0:
            unit.append(100.0)
            unit_find = 1
        # 천원
        elif len(bsObj_fs.findAll("table")[num - 1](string=re_unit3)) != 0:
            unit.append(100000.0)
            unit_find = 1
        i += 1
    print(unit)
