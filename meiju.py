# -*- coding: utf-8 -*-
# @Time    : 2019-11-25 19:02
# @Author  : wuhao
# @Email   : 15392746632@qq.com
# @File    : meiju.py
import base64
import re
import threading
import urllib.parse

import requests
from bs4 import BeautifulSoup
from faker import Faker
from pick import pick

_faker = Faker()

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def search_video(keyword):
    all_video = []
    url = f'https://91mjw.com/?s={keyword}'
    resp = requests.get(url, headers={'user_agent': _faker.user_agent()}, verify=False)
    soup = BeautifulSoup(resp.text, 'html.parser')
    for article in soup.find_all('article'):
        link = article.find('a').get('href')
        title = article.find('h2').get_text()
        all_video.append({'link': link, 'name': title})
    return all_video


def total_count(url):
    resp = requests.get(url, headers={'user_agent': _faker.user_agent()}, verify=False)
    return int(re.findall(r'<strong>集数:</strong> (\d+)<br />', resp.text)[0])


def video_parse(url, video_num):
    vid = re.findall(r'(\d+)\.htm', url)[0]
    url = 'https://91mjw.com/vplay/{}.html'.format(
        base64.b64encode((vid + '-1-' + str(video_num)).encode()).decode())
    resp = requests.get(url, headers={'user_agent': _faker.user_agent()}, verify=False)
    vid = re.findall(r'vid="(.*?)\.m3u8"', resp.text)
    return vid[0]


def download(url, name):
    index = 1
    while True:
        segment = '-{:0>5}.ts'.format(index)
        resp = requests.get(urllib.parse.unquote(url + segment), headers={'user_agent': _faker.user_agent()},
                            verify=False)
        if resp.status_code != 200:
            return
        with open(name + '.mp4', 'ab') as fd:
            chunk = resp.content
            fd.write(chunk)
        index += 1


def get_description_for_display(option):
    return '{:30}\t{:30}'.format(option.get('name'), option.get('link'))


def main():
    name = input('输入影片名：')
    all_video = search_video(name)
    video = pick(all_video, '选择影片', indicator='=>', options_map_func=get_description_for_display)[0]
    count = total_count(video['link'])
    options = [f'第{i+1}集' for i in range(count)]
    video_list = pick(options, '选集按空格', indicator='=>', default_index=0, multi_select=True)
    video_list = [i[1] for i in video_list]
    t_list = []
    for i in video_list:
        i = int(i)
        url = video_parse(video['link'], i)
        print(video['link'])
        t = threading.Thread(target=download, args=(url, video['name'] + str(i + 1)))
        t_list.append(t)
    print('下载中......')
    [t.start() for t in t_list]
    [t.join() for t in t_list]


if __name__ == '__main__':
    main()
