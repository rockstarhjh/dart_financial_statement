# -*- coding: utf-8 -*-
from os import path
from os.path import join
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

from lxml import html

# 테이블 내의 수치를 int 타입으로 변환
def find_value(text, unit):
    return int(text.replace(" ", "").replace("△", "-").replace("(-)", "-").replace("(", "-").replace(")", "").replace(",", "").replace("=", "")) / unit

# 대차대조표 크롤링 함수
def scrape_balance_sheet(balance_table, year, unit):

    #  원하는 테이블(대차대조표, 손익계산서, 현금흐름표)에서 찾고자하는 항목 설정(정규표현식 리스트) 및 검색 기능
    re_balance_list = []
    # 대차대조표
    # 유동자산 정규표현식
    re_asset_current = re.compile("^((.)*\.)*[\ s]*유[ \s]*동[ \s]*자[ \s]*산([ \s]*합[ \s]*계)*|\.[ \s]*유[ \s]*동[ \s]*자[ \s]*산([ \s]*합[ \s]*계)*")
    re_asset_current_sub1 = re.compile("^((.)*\.)*[\ s]*현[ \s]*금[ \s]*및[ \s]*현[ \s]*금[ \s]*((성[ \s]*자[ \s]*산)|(등[ \s]*가[ \s]*물))")
    re_asset_current_sub2 = re.compile("^((.)*\.)*[\ s]*매[ \s]*출[ \s]*채[ \s]*권([ \s]*및[ \s]*기[ \s]*타[ \s]*유[ \s]*동[ \s]*채[ \s]*권[ \s]*|[ \s]*및[ \s]*기[ \s]*타[ \s]*채[ \s]*권[ \s])*")
    re_asset_current_sub3 = re.compile("^((.)*\.)*[\ s]*재[ \s]*고[ \s]*자[ \s]*산")
    # re_asset_current_sub4 = re.compile("단[ \s]*기[ \s]*금[ \s]*융[ \s]*자[ \s]*산|기[ \s]*타[ \s]*유[ \s]*동[ \s]*금[ \s]*융[ \s]*자[ \s]*산|단[ \s]*기[ \s]*금[ \s]*융[ \s]*상[ \s]*품")
    # re_asset_current_sub5 = re.compile("당[ \s]*기[ \s]*법[ \s]*인[ \s]*세[ \s]*자[ \s]*산")
    # re_asset_current_sub6 = re.compile("기[ \s]*타[ \s]*유[ \s]*동[ \s]*자[ \s]*산")
    # 비유동자산 정규표현식
    re_asset_non_current = re.compile("^((.)*\.)*[\ s]*비[ \s]*유[ \s]*동[ \s]*자[ \s]*산|고[ \s]*정[ \s]*자[ \s]*산([ \s]*합[ \s]*계)*")
    re_asset_non_current_sub1 = re.compile("^((.)*\.)*[\ s]*유[ \s]*형[ \s]*자[ \s]*산")
    re_asset_non_current_sub2 = re.compile("^((.)*\.)*[\ s]*무[ \s]*형[ \s]*자[ \s]*산")
    # re_asset_non_current_sub3 = re.compile("투[ \s]*자[ \s]*부[ \s]*동[ \s]*산")
    # re_asset_non_current_sub4 = re.compile("기[ \s]*타[ \s]([ \s]*의[ \s])*비[ \s]*유[ \s]*동[ \s]*금[ \s]*융[ \s]*자[ \s]*산|기[ \s]*타[ \s]*금[ \s]*융[ \s]*자[ \s]*산")
    # re_asset_non_current_sub5 = re.compile("기[ \s]*타[ \s]*비[ \s]*유[ \s]*동[ \s]*자[ \s]*산")

    re_asset_sum = re.compile("^((.)*\.)*[\ s]*자[ \s]*산[ \s]*총[ \s]*계([ \s]*합[ \s]*계)*")
    # 유동부채 정규표현식
    re_liability_current = re.compile("^((.)*\.)*[\ s]*유[ \s]*동[ \s]*부[ \s]*채([ \s]*합[ \s]*계)*|\.[ \s]*유[ \s]*동[ \s]*부[ \s]*채([ \s]*합[ \s]*계)*")
    re_liability_current_sub1 = re.compile("^((.)*\.)*[\ s]*(단[ \s]*기[ \s])*매[ \s]*입[ \s]*채[ \s]*무([ \s]*및[ \s]*기[ \s]*타([ \s]*유[ \s]*동[ \s])*채[ \s]*무)*")
    re_liability_current_sub2 = re.compile("^((.)*\.)*[\ s]*단[ \s]*기[ \s]*차[ \s]*입[ \s]*금([ \s]*및[ \s]*유[ \s]*동[ \s]*성[ \s]*장[ \s]*기[ \s]*부[ \s]*채[ \s])*|단[ \s]*기[ \s]*금[ \s]*융[ \s]*부[ \s]*채")
    # re_liability_current_sub3 = re.compile("(유[ \s]*동[ \s]*성[ \s])*충[ \s]*당[ \s]*부[ \s]*채[ \s]")
    # re_liability_current_sub4 = re.compile("기[ \s]*타[ \s]*유[ \s]*동[ \s]*부[ \s]*채")
    # 비유동부채 정규표현식
    re_liability_non_current = re.compile("^((.)*\.)*[\ s]*비[ \s]*유[ \s]*동[ \s]*부[ \s]*채|\.[ \s]*비[ \s]*유[ \s]*동[ \s]*부[ \s]*채|고[ \s]*정[ \s]*부[ \s]*채")
    re_liability_non_current_sub1 = re.compile("^((.)*\.)*[\ s]*사[ \s]*채[ \s]*")
    re_liability_non_current_sub2 = re.compile("^((.)*\.)*[\ s]*장[ \s]*기[ \s]*차[ \s]*입[ \s]*금")
    re_liability_non_current_sub3 = re.compile("^((.)*\.)*[\ s]*장[ \s]*기[ \s]*매[ \s]*입[ \s]*채[ \s]*무([ \s]*및[ \s]*기[ \s]*타[ \s]*채[ \s]*무)*|^((.)*\.)*[\ s]*장[ \s]*기([ \s]*성)*미[ \s]*지[ \s]*급[ \s]*금")
    re_liability_non_current_sub4 = re.compile("^((.)*\.)*[\ s]*이[ \s]*연[ \s]*법[ \s]*인[ \s]*세[ \s]*부[ \s]*채")
    # re_liability_non_current_sub5 = re.compile("확[ \s]*정[ \s]*급[ \s]*여[ \s]*부[ \s]*채")
    re_liability_sum = re.compile("^((.)*\.)*[\ s]*부[ \s]*채[ \s]*총[ \s]*계([ \s]*합[ \s]*계)*|\.[ \s]*부[ \s]*채[ \s]*총[ \s]*계([ \s]*합[ \s]*계)*")
    # 자본 정규표현식
    re_equity_parent = re.compile("^((.)*\.)*[\ s]*지[ \s]*배[ \s]*기[ \s]*업([ \s]*의)*[ \s]*소[ \s]*유|지[ \s]*배[ \s]*회[ \s]*사[ \s]*지[ \s]*분")
    re_equity_non_parent = re.compile("^((.)*\.)*[\ s]*비[ \s]*지[ \s]*배[ \s]*지[ \s]*분")
    re_equity_sub1 = re.compile("^((.)*\.)*[\ s]*자[ \s]*본[ \s]*금")
    re_equity_sub2 = re.compile("^((.)*\.)*[\ s]*주[ \s]*식[ \s]*발[ \s]*행[ \s]*초[ \s]*과[ \s]*금")
    re_equity_sub3 = re.compile("^((.)*\.)*[\ s]*자[ \s]*본[ \s]*잉[ \s]*여[ \s]*금")
    re_equity_sub4 = re.compile("^((.)*\.)*[\ s]*이[ \s]*익[ \s]*잉[ \s]*여[ \s]*금")
    re_equity_sum = re.compile("^((.)*\.)*[\ s]*자[ \s]*본[ \s]*총[ \s]*계([ \s]*합[ \s]*계)*|\.[ \s]*자[ \s]*본[ \s]*총[ \s]*계([ \s]*합[ \s]*계)*")

    re_balance_list.append(re_asset_current)
    re_balance_list.append(re_asset_current_sub1)
    re_balance_list.append(re_asset_current_sub2)
    re_balance_list.append(re_asset_current_sub3)
    # re_balance_list.append(re_asset_current_sub4)
    # re_balance_list.append(re_asset_current_sub5)
    # re_balance_list.append(re_asset_current_sub6)
    re_balance_list.append(re_asset_non_current)
    re_balance_list.append(re_asset_non_current_sub1)
    re_balance_list.append(re_asset_non_current_sub2)
    # re_balance_list.append(re_asset_non_current_sub3)
    # re_balance_list.append(re_asset_non_current_sub4)
    # re_balance_list.append(re_asset_non_current_sub5)
    re_balance_list.append(re_asset_sum)
    re_balance_list.append(re_liability_current)
    re_balance_list.append(re_liability_current_sub1)
    re_balance_list.append(re_liability_current_sub2)
    # re_balance_list.append(re_liability_current_sub3)
    # re_balance_list.append(re_liability_current_sub4)
    re_balance_list.append(re_liability_non_current)
    re_balance_list.append(re_liability_non_current_sub1)
    re_balance_list.append(re_liability_non_current_sub2)
    re_balance_list.append(re_liability_non_current_sub3)
    re_balance_list.append(re_liability_non_current_sub4)
    # re_balance_list.append(re_liability_non_current_sub5)
    re_balance_list.append(re_liability_sum)
    re_balance_list.append(re_equity_parent)
    re_balance_list.append(re_equity_non_parent)
    re_balance_list.append(re_equity_sub1)
    re_balance_list.append(re_equity_sub2)
    re_balance_list.append(re_equity_sub3)
    re_balance_list.append(re_equity_sub4)
    re_balance_list.append(re_equity_sum)


    # 대차대조표의 항목 리스트 만들기
    balance_sheet_key_list = []
    balance_sheet_key_list.append("asset_current")
    balance_sheet_key_list.append("asset_current_sub1")
    balance_sheet_key_list.append("asset_current_sub2")
    balance_sheet_key_list.append("asset_current_sub3")
    balance_sheet_key_list.append("asset_non_current")
    balance_sheet_key_list.append("asset_non_current_sub1")
    balance_sheet_key_list.append("asset_non_current_sub2")
    balance_sheet_key_list.append("asset_sum")
    balance_sheet_key_list.append("liability_current")
    balance_sheet_key_list.append("liability_current_sub1")
    balance_sheet_key_list.append("liability_current_sub2")
    # balance_sheet_key_list.append("liability_current_sub3")
    balance_sheet_key_list.append("liability_non_current")
    balance_sheet_key_list.append("liability_non_current_sub1")
    balance_sheet_key_list.append("liability_non_current_sub2")
    balance_sheet_key_list.append("liability_non_current_sub3")
    balance_sheet_key_list.append("liability_non_current_sub4")
    balance_sheet_key_list.append("liability_sum")
    balance_sheet_key_list.append("equity_parent")
    balance_sheet_key_list.append("equity_non_parent")
    balance_sheet_key_list.append("equity_sub1")
    balance_sheet_key_list.append("equity_sub2")
    balance_sheet_key_list.append("equity_sub3")
    balance_sheet_key_list.append("equity_sub4")
    balance_sheet_key_list.append("equity_sum")

    # 대차대조표의 항목에 대한 값을 저장할 딕셔너리 만들기(항목리스트에서 키값을 가져옴)
    balance_sheet_sub_list = {}
    balance_sheet_sub_list["asset_current"] = 0.0
    balance_sheet_sub_list["asset_current_sub1"] = 0.0
    balance_sheet_sub_list["asset_current_sub2"] = 0.0
    balance_sheet_sub_list["asset_current_sub3"] = 0.0
    balance_sheet_sub_list["asset_non_current"] = 0.0
    balance_sheet_sub_list["asset_non_current_sub1"] = 0.0
    balance_sheet_sub_list["asset_non_current_sub2"] = 0.0
    balance_sheet_sub_list["asset_sum"] = 0.0
    balance_sheet_sub_list['year'] = year+"년"
    balance_sheet_sub_list["liability_current"] = 0.0
    balance_sheet_sub_list["liability_current_sub1"] = 0.0
    balance_sheet_sub_list["liability_current_sub2"] = 0.0
    # balance_sheet_sub_list["liability_current_sub3"] = 0.0
    balance_sheet_sub_list["liability_non_current"] = 0.0
    balance_sheet_sub_list["liability_non_current_sub1"] = 0.0
    balance_sheet_sub_list["liability_non_current_sub2"] = 0.0
    balance_sheet_sub_list["liability_non_current_sub3"] = 0.0
    balance_sheet_sub_list["liability_non_current_sub4"] = 0.0
    balance_sheet_sub_list["liability_sum"] = 0.0
    balance_sheet_sub_list["equity_parent"] = 0.0
    balance_sheet_sub_list["equity_non_parent"] = 0.0
    balance_sheet_sub_list["equity_sub1"] = 0.0
    balance_sheet_sub_list["equity_sub2"] = 0.0
    balance_sheet_sub_list["equity_sub3"] = 0.0
    balance_sheet_sub_list["equity_sub4"] = 0.0
    balance_sheet_sub_list["equity_sum"] = 0.0


    # 대차대조표의 테이블 텍스트 가져와서 정규표현식과 비교하기
    trs = balance_table.findAll("tr")

    # 대차대조표

    # 대차대조표 테이블 안에서 정규표현식 항목에 맞는 것을 찾고 그 금액값 입력하기
    for tr in trs:
        tds = tr.findAll("td")  # 각 행마다 루프를 돌면서 각 열의 데이터 찾기

        if len(tds) != 0:  # 각 행마다 열이 존재한다면,
            value = 0.0
            for i in range(len(re_balance_list)):  # 찾고자하는 정규표현식 리스트의 개수만큼 루프돌리기
                # print(i)
                if re_balance_list[i].search(tds[0].text.strip()):  # 정규표현식 리스트의 내용과 일치하는 행(첫열)이 있다면
                    if len(tds) > 4:
                        if (tds[1].text.strip() != "") and (tds[1].text.strip() != "-"):  # 열이 4열이상이면 값이 있는 것을 찾아 넣기
                            value = find_value(tds[1].text.strip(), unit)
                            # print(value)
                            break
                        elif (tds[2].text.strip() != "") and (tds[2].text.strip() != "-"):  # 빈 공백이거나 "-"로 표시하지 않았다면
                            value = find_value(tds[2].text.strip(), unit)
                            # print(value)
                            break
                    else:
                        if (tds[1].text.strip() != "") and (tds[1].text.strip() != "-"):  # 두번째 열부터 금액이므로 두번째 열이 비어있지 않다면 값을 변수에 저장
                            value = find_value(tds[1].text.strip(), unit)
                            # print(value)
                            break
            if value != 0.0 and balance_sheet_sub_list[balance_sheet_key_list[i]] == 0.0:
                balance_sheet_sub_list[balance_sheet_key_list[i]] = value  # balance_sheet_key_list[i]랑 re_balance_list 를 일치시켜 year는 상관없음
    return balance_sheet_sub_list

def scrape_income_sheet(income_table, year, unit):
    # 손익계산서
    re_income_list = []
    # 수익(매출액) / 매출액 / 영업수익 / I. 영업수익 / 매출
    # 매출원가 / 영업비용
    # 매출총이익
    # 판매비와관리비
    # 영업이익(손실) / 영업이익
    # 기타수익 / 기타영업외수익 / 영업외수익 / 기타이익
    # 기타비용 / 기타영업외비용 /영업외비용 / 기타손실
    # 금융수익
    # 금융비용
    # 법인세비용차감전순이익(손실) / 법인세비용차감전순이익
    # 법인세비용 / 법인세비용(수익)
    # # 계속영업이익(손실) / 계속영업당기순이익(손실)
    # 당기순이익(손실) / 연결당기순이익 / 당기순이익
    # 기본주당이익(손실)(단위:원) / 기본주당이익(단위 : 원) / 기본주당이익(손실) / 기본주당이익
    # 보통주 기본주당이익 / 보통주 기본및희석주당이익(손실)
    # 1우선주 기본주당이익 / 우선주 기본및희석주당이익(손실)

    # 항목별 정규표현식
    re_sales = re.compile("^((.)*\.)*[\s]*매[ \s]*출([\s]*$|[\s]*액)|^((.)*\.)*[\s]*수[ \s]*익[ \s]*\([ \s]*매[ \s]*출[ \s]*액[ \s]*\)*|^((.)*\.)*[\s]*영[ \s]*업[ \s]*수[ \s]*익[ \s]*")
    re_cost = re.compile("^((.)*\.)*[\s]*매[ \s]*출[ \s]*원[ \s]*가[ \s]*")
    re_gross_profit = re.compile("^((.)*\.)*[\s]*매[ \s]*출[ \s]*총[ \s]*이[ \s]*익[ \s]*")
    re_selling_cost = re.compile("^((.)*\.)*[\s]*판[ \s]*매[ \s]*비[ \s]*와[ \s]*관[ \s]*리[ \s]*비[ \s]*")
    re_op_income = re.compile("^((.)*\.)*[\s]*영[ \s]*업[ \s]*이[ \s]*익[ \s]*(\([ \s]*손[ \s]*실[ \s]*\))*")
    re_income_sub1 = re.compile("^((.)*\.)*[\s]*기[ \s]*타[ \s]*((영[ \s]*업[ \s]*외[ \s]*)*수[ \s]*익[ \s]*|이[ \s]*익[ \s]*)|^((.)*\.)*[\s]*영[ \s]*업[ \s]*외[ \s]*수[ \s]*익[ \s]*")
    re_cost_sub1 = re.compile("^((.)*\.)*[\s]*기[ \s]*타[ \s]*((영[ \s]*업[ \s]*외[ \s]*)*비[ \s]*용[ \s]*|손[ \s]*실[ \s]*)|^((.)*\.)*[\s]*영[ \s]*업[ \s]*외[ \s]*비[ \s]*용[ \s]*")
    re_income_sub2 = re.compile("^((.)*\.)*[\s]*금[ \s]*융[ \s]*수[ \s]*익[ \s]*")
    re_cost_sub2 = re.compile("^((.)*\.)*[\s]*금[ \s]*융[ \s]*비[ \s]*용[ \s]*")
    re_income_sub3 = re.compile("^((.)*\.)*[\s]*법[ \s]*인[ \s]*세[ \s]*비[ \s]*용[ \s]*차[ \s]*감[ \s]*전[ \s]*순[ \s]*이[ \s]*익[ \s]*(\([ \s]*손[ \s]*실[ \s]*\))*")
    re_cost_sub3 = re.compile("^((.)*\.)*[\s]*법[ \s]*인[ \s]*세[ \s]*비[ \s]*용[ \s]*(\([ \s]*수[ \s]*익[ \s]*\))*[\s]*$")
    re_net_income =re.compile("^((.)*\.)*[\s]*(연[ \s]*결[ \s]*)*당[ \s]*기[ \s]*순[ \s]*이[ \s]*익[ \s]*(\([ \s]*손[ \s]*실[ \s]*\))*$")
    re_stock_income = re.compile("^((.)*\.)*[\s]*기[ \s]*본[ \s]*주[ \s]*당[ \s]*이[ \s]*익[ \s]*")
    # re_stock_income_unit = re.compile("주[ \s]*당[ \s]*이[ \s]*익[ \s]*(\([ \s]*손[ \s]*실[ \s]*\))*\([ \s]*단[ \s]*위[ \s]*\:[ \s]*원[ \s]*\)*")  # eps는 다 원 단위라 의미 없을듯
    re_stock_income_sub1 =re.compile("^((.)*\.)*[\s]*(보[ \s]*통[ \s]*주[ \s]*)*(기[ \s]*본[ \s]*)*주[ \s]*당[ \s]*(순[ \s]*)*이[ \s]*익[ \s]*|^((.)*\.)*[\s]*(보[ \s]*통[ \s]*주[ \s]*)*기[ \s]*본[ \s]*및[ \s]*희[ \s]*석[ \s]*주[ \s]*당[ \s]*이[ \s]*익[ \s]*")
    re_stock_income_sub2 = re.compile("^((.)*\.)*[\s]*(1*[\s]*)*우[ \s]*선[ \s]*주[ \s]*기[ \s]*본[ \s]*주[ \s]*당[ \s]*이[ \s]*익[ \s]*|^((.)*\.)*[\s]*우[ \s]*선[ \s]*주[ \s]*기[ \s]*본[ \s]*및[ \s]*희[ \s]*석[ \s]*주[ \s]*당[ \s]*이[ \s]*익[ \s]*")

    # 리스트에 정규표현식 담기
    re_income_list.append(re_sales)
    re_income_list.append(re_cost)
    re_income_list.append(re_gross_profit)
    re_income_list.append(re_selling_cost)
    re_income_list.append(re_op_income)
    re_income_list.append(re_income_sub1)
    re_income_list.append(re_cost_sub1)
    re_income_list.append(re_income_sub2)
    re_income_list.append(re_cost_sub2)
    re_income_list.append(re_income_sub3)
    re_income_list.append(re_cost_sub3)
    re_income_list.append(re_net_income)
    re_income_list.append(re_stock_income)
    # re_income_list.append(re_stock_income_unit)
    re_income_list.append(re_stock_income_sub1)
    re_income_list.append(re_stock_income_sub2)

    # 딕셔너리 타입에 값을 저장하기 위해 키 값 만들기
    income_sheet_key_list = []
    income_sheet_key_list.append("sales")
    income_sheet_key_list.append("cost")
    income_sheet_key_list.append("gross_profit")
    income_sheet_key_list.append("selling_cost")
    income_sheet_key_list.append("op_income")
    income_sheet_key_list.append("income_sub1")
    income_sheet_key_list.append("cost_sub1")
    income_sheet_key_list.append("income_sub2")
    income_sheet_key_list.append("cost_sub2")
    income_sheet_key_list.append("income_sub3")
    income_sheet_key_list.append("cost_sub3")
    income_sheet_key_list.append("net_income")
    income_sheet_key_list.append("stock_income")
    # income_sheet_key_list.append("stock_income_unit")
    income_sheet_key_list.append("stock_income_sub1")
    income_sheet_key_list.append("stock_income_sub2")

    # 손익계산서의 항목에 대한 값을 저장할 딕셔너리 만들기(항목리스트에서 키값을 가져옴)
    income_sheet_sub_list = {}
    income_sheet_sub_list["sales"] = 0.0
    income_sheet_sub_list["cost"] = 0.0
    income_sheet_sub_list["gross_profit"] = 0.0
    income_sheet_sub_list["selling_cost"] = 0.0
    income_sheet_sub_list["op_income"] = 0.0
    income_sheet_sub_list["income_sub1"] = 0.0
    income_sheet_sub_list["cost_sub1"] = 0.0
    income_sheet_sub_list["income_sub2"] = 0.0
    income_sheet_sub_list["cost_sub2"] = 0.0
    income_sheet_sub_list["income_sub3"] = 0.0
    income_sheet_sub_list["cost_sub3"] = 0.0
    income_sheet_sub_list["net_income"] = 0.0
    income_sheet_sub_list["stock_income"] = 0.0
    # income_sheet_sub_list["stock_income_unit"] = 0.0
    income_sheet_sub_list["stock_income_sub1"] = 0.0
    income_sheet_sub_list["stock_income_sub2"] = 0.0
    income_sheet_sub_list['year'] = year + "년"

    # 손익계산서의 테이블 텍스트 가져와서 정규표현식과 비교하기
    trs = income_table.findAll("tr")

    # 손익계산서 테이블 안에서 정규표현식 항목에 맞는 것을 찾고 그 금액값 입력하기
    for tr in trs:
        tds = tr.findAll("td")  # 각 행마다 루프를 돌면서 각 열의 데이터 찾기
        if len(tds) != 0:  # 각 행마다 열이 존재한다면,
            value = 0.0
            for i in range(len(re_income_list)):  # 찾고자하는 정규표현식 리스트의 개수만큼 루프돌리기

                if re_income_list[i].search(tds[0].text.strip()):  # 정규표현식 리스트의 내용과 일치하는 행(첫열)이 있다면
                    # print("i : ",  i,  "result : ", bool(re_income_list[i].search(tds[0].text.strip())), re_income_list[i], tds[0].text.strip())  # 정규표현식 에러(실수) 확인용
                    if len(tds) > 4:
                        if (tds[1].text.strip() != "") and (tds[1].text.strip() != "-"):  # 열이 4열이상이면 값이 있는 것을 찾아 넣기
                            value = find_value(tds[1].text.strip(), unit)
                            # print(value)
                            break
                        elif (tds[2].text.strip() != "") and (tds[2].text.strip() != "-"):  # 빈 공백이거나 "-"로 표시하지 않았다면
                            value = find_value(tds[2].text.strip(), unit)
                            # print(value)
                            break
                    else:
                        if (tds[1].text.strip() != "") and (tds[1].text.strip() != "-"):  # 두번째 열부터 금액이므로 두번째 열이 비어있지 않다면 값을 변수에 저장
                            value = find_value(tds[1].text.strip(), unit)
                            # print(value)
                            break
            if value != 0.0 and income_sheet_sub_list[income_sheet_key_list[i]] == 0.0:
                income_sheet_sub_list[income_sheet_key_list[i]] = value  # income_sheet_key_list[i]랑 re_income_list 를 일치시켜 year는 상관없음
    if income_sheet_sub_list["stock_income_sub1"] != 0:
        income_sheet_sub_list["stock_income_sub1"] = income_sheet_sub_list["stock_income_sub1"] * unit  # 기본주당이익은 단위가 원이므로
    return income_sheet_sub_list



#main 함수
# def main():
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

start_dt = '20171201'  # 검색시작일 20081231 20010101
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
    year = name.split('(')[1].split('.')[0]  # 년도만 뽑기
    # [기재정정][첨부추가][첨부정정] 등 보고서 앞에 붙은 이름을 제거
    if name.find('[') != -1:  # 문자내에 '[' 문자열이 있다면 없으면 -1 리턴
        name = name.split(']')[1]    # [첨부추가]사업보고서(0000.00.00)이라면 ]를 기준으로 앞의 [첨부추가] 와 사업보고서(0000.00.00)으로 분리 1번째 값이므로 뒤의 사업보고서를 이름으로 할당
    urldict[name] = url2+row['rcp_no']
    print(name+": " + url2 + row['rcp_no'])
    report_url = url2+row['rcp_no']  # 이 url 이 보고서 조회 가능한 url
    report_data = requests.get(report_url)  # 보고서 조회가능한 url을 요청하여 해당 페이지 데이터를 가져옴
    bsObj = BeautifulSoup(report_data.content, "html.parser")  # 해당 페이지 데이터는 html 인코딩? 을 통해 beautifulsoup 객체로 가져옴
    fs_find1 = re.compile('(\d\.\s)*연[\s]*결[\s]*재[\s]*무[\s]*제[\s]*표["]')   # 정규표현식(re모듈)으로 해당 객체안에서 원하는 텍스트 정보를 얻기위해 정규표현식을 설정
    fs_find2 = re.compile('(\d\.\s)*재[\s]*무[\s]*제[\s]*표["]')
    fs_find3 = re.compile('(\d\.\s)*연[\s]*결[\s]*재[\s]*무[\s]*제[\s]*표[\s]*에[\s]*관[\s]*한[\s]*사[\s]*항["]')
    fs_find4 = re.compile('(\.\s)*재[\s]*무[\s]*제[\s]*표[\s]*등["]')
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
    # 각기 다른 단위를 억 단위로 만들기
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

balance_sheet_list = scrape_balance_sheet(balance_table, year, unit[0])
income_sheet_list = scrape_income_sheet(income_table, year, unit[1])



# 우선 마지막 데이터 url 만 저장되어서 검색하는것을 전부로 변경, main 함수 마지막에 저장관련 기능 넣으면 될듯




