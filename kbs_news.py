# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import traceback
from datetime import datetime
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger()
logger.setLevel("INFO")
formatter = logging.Formatter('%(asctime)s %(process)d %(levelname)1.1s %(lineno)3s:%(funcName)-16.16s %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger = logging.getLogger(__file__)

MAX_PAGE = 10


def filter_01(row):
    title = row.select('a > span > em')[0].text

    content_url = 'http://news.kbs.co.kr' + row.select('a')[0].attrs['href'].strip()

    return title, content_url


def filter_02(content_html):
    reg_datetime = content_html.select('em.date')[0].text.replace('.', '-')
    reg_datetime = reg_datetime.replace('입력 ', '').replace('(', '').replace(')', '') + ':00'

    content = content_html.select("#cont_newstext")[0]
    center_tag_list = content.find_all('center')
    for center_tag in center_tag_list:
        center_tag.extract()
    content = content.text.strip()[0:10000]

    chul_cheo = 'KBS'

    return reg_datetime, content, chul_cheo


def crawling():
    start = datetime.now()
    list_url = None
    content_url = None

    try:
        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Safari/537.36'}

        for page in range(1, MAX_PAGE + 1):

            list_url = "http://news.kbs.co.kr/common/main.html?ref=pLogo"
            response = requests.get(list_url, headers=headers)
            response.raise_for_status()
            response.encoding = None

            if response.status_code == 200:
                html = BeautifulSoup(response.text, 'html.parser')
                rows = html.select("#content > div.m-section.main-col2 > div > div.fl.col-box.col-recent > ul > li")

                for row in rows:

                    title, content_url = filter_01(row)

                    response_content = requests.get(content_url, headers=headers)
                    response_content.raise_for_status()
                    response_content.encoding = None

                    if response_content.status_code == 200:
                        content_html = BeautifulSoup(response_content.text, 'html.parser')

                        if content_html.select('em.date') == []:
                            continue

                        reg_datetime, content, chul_cheo = filter_02(content_html)

                        if content is None or content == '':
                            continue

                        logger.info("{:<2}/{:>2} [NEW] {} {}".format(page, MAX_PAGE, reg_datetime, title))

                    else:
                        msg = "[본문 크롤링 오류] {} {}".format(response_content.status_code, content_url)
                        logger.warning(msg)
            else:
                msg = "[목록 크롤링 오류] {} {}".format(response.status_code, list_url)
                logger.warning(msg)
                break

    except Exception as e:
        msg = "list_url={}{}content_url={}{}{}".format(list_url, os.linesep, content_url, os.linesep, traceback.format_exc())
        logger.error(msg)

    finally:
        elapsed_time = (datetime.now() - start).total_seconds()
        logger.info("소요시간  {:5.2f}".format(elapsed_time))


if __name__ == '__main__':
    crawling()

