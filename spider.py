#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/4/8 下12:11
# @Author  : Lewis
# @File    : spider.py
# @Desc    :
import re
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from requests.exceptions import RequestException
from config import *
import pymysql


browser = webdriver.PhantomJS(service_args=SERVICE_ARGS)
wait = WebDriverWait(browser, 10)

browser.set_window_size(1400, 900)

db = pymysql.connect(host='localhost',user='root', password='root', port=3306)
cursor = db.cursor()
cursor.execute('SELECT VERSION()')
data = cursor.fetchone()
print('Database version:', data)

sql = 'CREATE TABLE tender(id int(10) NOT NULL, titel varchar(100) NOT NULL, time varchar(20) NOT NULL, from varchar(100) NOT NULL,herf varchar(100) NOT NULL,content varchar(1500) NOT NULL,PRIMARY KEY (id)) '
cursor.execute(sql)
db.close()






def get_total():
    try:
        browser.get("http://deal.ggzy.gov.cn/ds/deal/dealList.jsp?HEADER_DEAL_TYPE=02")
        #等待页面加载完成-总页数加载出来
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > div.paging > span')))
        total = browser.find_element_by_xpath("/html/body/div[7]/span").text
        parse_list_url()
        return total
    except TimeoutException:
        return total()


def parse_list_url():
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'#publicl')))
    html = browser.page_source
    print(html)
    pattern = re.compile('<div class="publicont">.*?<h4>.*?<a href="(.*?)".*?title', re.S)
    detail_urls = re.findall(pattern, html)
    print(detail_urls)

    for detail_url in detail_urls:
        detail_tender(detail_url)

    return detail_urls


def detail_tender(detail_url):
    response = requests.get(detail_url)
    try:
        if response.status_code == 200:
            print('正在打开---------------URL',detail_url)
            print(response.text)
            print("打印 items-----------")
            for item in parse_detail_tender(response):
                print(item)
            return response.text
        return None
    except RequestException:
        return None



def parse_detail_tender(html):

    #标题，时间，来源，原文链接
    pattern =re.compile('detail">.*?h4_o.*?>(.*?)</h4>.*?class="p_o">(.*?)</span>.*?id="platformName">(.*?)</label>.*?class="detail_url">.*?href="(.*>)".*?',re.S)
    items = re.findall(pattern, str(html))
    for item in items:
        yield {
        'title':item[0],
        'time':item[1],
        'from':item[2],
        'herf':item[3],
        'content':item[4]
    }
    save_to_mysql(items)

def save_to_mysql(data):
    table = 'tender'
    keys = ', '.join(data.keys())
    values = ', '.join(['%s'] * len(data))

    sql = 'INSERT INTO {table}({keys}) VALUES ({values}) ON DUPLICATE KEY UPDATE'.format(table=table, keys=keys,
                                                                                         values=values)
    update = ','.join([" {key} = %s".format(key=key) for key in data])
    sql += update
    try:
        if cursor.execute(sql, tuple(data.values()) * 2):
            print('Successful')
            db.commit()
    except:
        print('Failed')
        db.rollback()
    db.close()


def next_page(page_number):
    try:
        #下一页按钮
        next_page_botton = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'body > div.paging > a:nth-child(10)')))
        next_page_botton.click()
        #高亮页码数等于 pagenumber ，说明翻页成功
        wait.until(EC.text_to_be_present_in_element((By.CLASS_NAME,'a_hover'),str(page_number)))
        parse_list_url()

    except TimeoutException:
        next_page(page_number)







def main():
    total = get_total()
    regex = re.compile('(\d*)')
    total = int(regex.findall(total)[1])
    for i in range(2, total + 1 ):
        print("正在翻页至：",i )
        next_page(i)


if __name__ == '__main__':
    main()