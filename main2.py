#!/usr/bin/env python
# -*- coding:utf-8 -*-
from functools import wraps
from types import MethodType
import random
import time
import datetime
import requests
import json
import os

import tgpush


class TimeoutRetry:
    max_retry = 3

    def __init__(self, func):
        wraps(func)(self)

    def __call__(self, *args, **kwargs):
        retry_count = 0
        while retry_count < self.max_retry:
            try:
                return self.__wrapped__(*args, **kwargs)
            except requests.RequestException:
                print("请求超时，正在重试")
                retry_count += 1
        raise TimeoutError("重试三次，连接无效，请检查网络")

    def __get__(self, instance, cls):
        if instance is None:
            return self
        else:
            return MethodType(self, instance)


class YouthLearning:
    def __init__(self, open_id, nick_name, name, nid, tgbot: tgpush.TGBot = None):
        self.open_id = open_id
        self.nick_name = nick_name
        self.name = name
        self.nid = nid
        self.tgbot = tgbot

        self.headers = {
            'Host': 'qczj.h5yunban.com',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 11; M2012K11AC Build/RKQ1.200826.002; wv) AppleWebKit/537.36 ('
                          'KHTML, like Gecko) Version/4.0 Chrome/86.0.4240.99 XWEB/3185 MMWEBSDK/20220105 Mobile '
                          'Safari/537.36 MMWEBID/4365 MicroMessenger/8.0.19.2080(0x2800133D) Process/toolsmp '
                          'WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',

            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json;charset=UTF-8',

            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
        }
        self.session = requests.session()

        self.access_token = self._get_access_token()

    @staticmethod
    def time_sleep(a: float = 5, b: float = 10):
        """
        随机时间 [a, b] 秒
        """
        time.sleep(random.uniform(a, b))

    @staticmethod
    def random_probability(probability):
        return random.random() < probability

    @TimeoutRetry
    def _get_access_token(self):
        headers = {
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
        }
        temp_headers = self.headers.copy()
        temp_headers.update(headers)
        time_stamp = str(int(time.time()))
        url = f"https://qczj.h5yunban.com/qczj-youth-learning/cgi-bin/login/we-chat/callback?callback=https%3A%2F" \
              f"%2Fqczj.h5yunban.com%2Fqczj-youth-learning%2Findex.php&scope=snsapi_userinfo&appid=wx56b888a1409a2920" \
              f"&openid={self.open_id}&nickname={self.nick_name}&headimg=&time={time_stamp}&source=common&sign=&t=" \
              f"{time_stamp} "
        res = self.session.get(url, headers=temp_headers, timeout=3)
        return res.text[45:81]

    @TimeoutRetry
    def _get_current_course(self):
        headers = {
            'Referer': 'https://qczj.h5yunban.com/qczj-youth-learning/signUp.php?rom=1',
        }
        headers.update(self.headers)
        url = f"https://qczj.h5yunban.com/qczj-youth-learning/cgi-bin/common-api/course/current?" \
              f"accessToken={self.access_token}"
        res_json = self.session.get(url, headers=headers, timeout=3).json()
        if res_json["status"] == 200:
            return res_json["result"]["id"]
        else:
            return ""

    @TimeoutRetry
    def join_course(self, course_id, nid, name):
        headers = {
            'Content-Length': '80',
            'Origin': 'https://qczj.h5yunban.com',
            'Referer': 'https://qczj.h5yunban.com/qczj-youth-learning/signUp.php?rom=1',
        }
        headers.update(self.headers)
        data = {
            "course": course_id,  # 大学习期次
            "subOrg": None,  # 就是空的
            "nid": nid,  # 团组织编号
            "cardNo": name  # 打卡昵称
        }
        url = f"https://qczj.h5yunban.com/qczj-youth-learning/cgi-bin/user-api/course/join?" \
              f"accessToken={self.access_token}"
        res_json = self.session.post(url, json=data, headers=headers, timeout=3).json()  # json发送保证subOrg被转化为null
        return res_json["status"] == 200

    @TimeoutRetry
    def read_passage(self, passage_id):
        headers = {
            'Referer': 'https://qczj.h5yunban.com/qczj-youth-learning/learn.php',
            'Content-Length': '2',
            'Origin': 'https://qczj.h5yunban.com',
        }
        headers.update(self.headers)
        url = f'https://qczj.h5yunban.com/qczj-youth-learning/cgi-bin/user-api/course/study?' \
              f'accessToken={self.access_token}&id={passage_id}'
        res = self.session.post(url, json={}, headers=headers, timeout=3).json()
        return res['status'] == 200

    @TimeoutRetry
    def sign_in(self):
        headers = {
            'Content-Length': '2',
            'Origin': 'https://qczj.h5yunban.com',
            'Referer': 'https://qczj.h5yunban.com/qczj-youth-learning/mine.php',
        }
        url = f'https://qczj.h5yunban.com/qczj-youth-learning/cgi-bin/user-api/sign-in?accessToken={self.access_token}'
        res = self.session.post(url, json={}, headers=headers, timeout=3).json()
        return res["status"] == 200 and res['result']

    @TimeoutRetry
    def send_message(self, message):
        if self.tgbot:
            self.tgbot.send_message(message)

    def main(self, learn_course=False):
        # 随机顺序
        sequence = [1,2,3]
        random.shuffle(sequence)
        order = {1:'签到',2:'读文章',3:'学视频'}

        name = self.name if len(self.name)!=10 else self.name[:2]+"*****"+self.name[-3:]

        display_message = f"{name}开始学习\n"

        display_message += "学习顺序：{}".format(", ".join([order[i] for i in sequence]))

        push_message = f"{display_message}\n"

        print(display_message)

        for i in sequence:
            # 签到
            if i == 1:
                # 工作日签到
                if datetime.datetime.weekday(datetime.datetime.now()) in range(0, 5):
                    if self.sign_in():
                        display_message = f"{name}签到成功"
                    else:
                        display_message = f"{name}已签到或签到失败"
                    push_message += f"{display_message}\n"
                    print(display_message)

                    self.time_sleep()

            # 读文章
            if i == 2:
                # 工作日学习
                if datetime.datetime.weekday(datetime.datetime.now()) in range(0, 5):
                    passages = [f'C004700{random.randint(17, 26)}' for _ in range(4)]
                    for passage_id in passages:
                        if self.read_passage(passage_id):
                            display_message = f"{name}已学习{passage_id}"
                        else:
                            display_message = f"{name}学习失败{passage_id}"
                        push_message += f"{display_message}\n"
                        print(display_message)
                        self.time_sleep(8, 10)

            # 学视频
            if i == 3:
                if learn_course and self.random_probability(0.7):
                    new_course_id = self._get_current_course()
                    self.time_sleep()
                    if self.join_course(new_course_id, self.nid, name):
                        display_message = f"{name}已完成视频课程"
                    else:
                        display_message = f"{name}视频课程失败"
                    push_message += f"{display_message}\n"
                    print(display_message)
                    self.time_sleep()

        self.send_message(push_message)


if __name__ == "__main__":
    # from telebot import apihelper
    # apihelper.proxy = {'https': 'http://localhost:7890', 'http': 'http://localhost:7890'}

    tgbot = None

    if os.path.exists("tgpush.json"):
        try:
            f = open('tgpush.json')
            data = json.load(f)
            token = data['token']
            chat_id = data['chat_id']
            print("成功读取tg bot信息")
        except:
            print("未能成功从tgdata.json读取tg bot信息")
        finally:
            f.close()
        tgbot = tgpush.TGBot(token, chat_id)

    # 使用例 见data.json 批量多人完成
    with open("data.json", encoding="utf-8") as f:
        data_json = json.load(f)
    for nid_ in data_json.keys():
        for stu in data_json[nid_]:
            stu_learn = YouthLearning(**stu, nid=nid_, tgbot=tgbot)
            stu_learn.main(True)
