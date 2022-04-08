import os
import random
import time
import requests
import logging as log
import json
import frozen_dir

log.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',
    level=log.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

os.chdir(os.path.dirname(__file__))
fileList = os.listdir(os.getcwd())

config = """\
user_id = ''
clazz_course_id = ''
# 完成所需秒数
total_time = ''
# 作业id列表,格式为['id1','id2',...]
cid_list = []
token = ''
cookie = ''"""

if 'config.py' not in fileList:
    log.info('未发现配置文件,即将创建配置文件')
    
    file = frozen_dir.app_path()+'./config.py'
    dirname = os.path.dirname(file)
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    
    with open(file, 'w', encoding='utf8') as f:
        f.write(config)
    log.info('配置文件创建完成,请到当前文件夹下的config文件夹下的config.py进行配置后重启程序,程序将在5秒后退出')
    time.sleep(5)
    exit()
else:
    from config import *
    if user_id == '' or clazz_course_id == '' or total_time == '' or cid_list == [] or token == '' or cookie == '':
        log.error('请将配置文件填写完成,程序将在5秒后退出')
        time.sleep(5)
        exit()

class YunClass(object):
    def __init__(self, user_id, clazz_course_id, id, token, cookie):
        self.user_id = user_id
        self.clazz_course_id = clazz_course_id
        self.act_id = self.id = id
        self.token = token
        self.cookie = cookie
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language':'zh-CN,zh;q=0.9,en-CN;q=0.8,en;q=0.7,ja-CN;q=0.6,ja;q=0.5',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': self.cookie,
            'Host': 'www.mosoteach.cn',
            'Origin': 'https://www.mosoteach.cn',
            'Pragma': 'no-cache',
            'Referer': 'https://www.mosoteach.cn/web/index.php?c=interaction_quiz&m=reply&clazz_course_id={}&id={}&order_item=group'.format(self.clazz_course_id,self.id),
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="100", "Google Chrome";v="100"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': "Windows",
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'X-token': self.token
        }

        self.resultDict = {}
        self.submitList = []

    # 获取答案解析
    def person_result(self):
        log.info('开始获取答案')
        url = 'https://www.mosoteach.cn/web/index.php?c=interaction_quiz&m=person_result'
        data = {
            'id': self.id,
            'user_id': self.user_id
        }
        r = requests.post(url, data=data,headers=self.headers).json()
        if 'data' not in r:
            log.error('cookie失效了,请重新填写,程序将在5秒后退出')
            time.sleep(5)
            exit()
        resultList = r['data']['rows']
        for result in resultList:
            self.resultDict[result['id']] = result['answers']
        log.info('答案获取完成,总共有{}道题被记录'.format(len(self.resultDict)))

    # 获取作答题目
    def start_quiz(self):
        log.info('开始获取作答题目')
        self.headers['Content-Length'] = '43'
        url = 'https://www.mosoteach.cn/web/index.php?c=interaction_quiz&m=start_quiz'
        data = {
            'act_id':self.act_id,
        }
        r = requests.post(url,data=data,headers=self.headers).json()
        quiz_topic_list = r['quiz_topic_list']
        log.info('总共有{}道题需作答'.format(len(quiz_topic_list)))
        for i in quiz_topic_list:
            self.submitList.append(
                {
                    "id": i['id'],
                    "type": i['create_type'],
                    "proof_attachments":[],
                    "answers": self.resultDict[i['id']]
                }
            )
        log.info('作答完成')

    # 提交答案
    def save_answer(self):
        url = 'https://www.mosoteach.cn/web/index.php?c=interaction_quiz&m=save_answer'
        data = {
            "id": self.id,
            "clazz_course_id": self.clazz_course_id,
            "data": json.dumps(self.submitList)
        }
        r = requests.post(url,data=data,headers=self.headers).json()
        try:
            log.info('本次成绩: {}, 最好成绩: {}'.format(r['data']['score'], r['data']['best_score']))
        except:
            log.error(r)

    # 获取排名
    def get_quiz_ranking(self):
        url = 'https://www.mosoteach.cn/web/index.php?c=interaction_quiz&m=get_quiz_ranking'
        data = {
            'id': self.id
        }
        r = requests.post(url,data=data,headers=self.headers).json()
        try:
            log.info('当前排名: {}'.format(r['data']['user_ranking']))
            log.info('分数: {}/{}'.format(r['data']['user_score'], r['data']['total_score']))
        except:
            log.error(r)

if __name__ == '__main__':
    try:
        sleep_time = int(total_time) + random.randint(1, 60)
    except ValueError:
        log.error('时间需要为纯数字哦,暂时为你设置8分钟咯')
        sleep_time = 480
    for cid in cid_list:
        yc = YunClass(user_id, clazz_course_id, cid, token, cookie)
        yc.person_result()
        yc.start_quiz()
        log.info('将在{}s后交卷'.format(sleep_time))
        time.sleep(sleep_time)
        yc.save_answer()
        yc.get_quiz_ranking()
        del yc
    input('按任意键退出程序...')
