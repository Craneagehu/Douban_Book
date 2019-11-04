#-*- coding:utf-8 -*-
import re
import sys
import threading
import time
import pandas as pd
import requests
from queue import Queue
from lxml import etree
from fake_useragent import UserAgent

'''
需要使用代理IP，否则要被禁
'''
class douban_Book():
    def __init__(self):
        self.url_queue = Queue()
        self.html_queue = Queue()
        self.content_queue = Queue()
        self.base_url = 'https://book.douban.com/tag/%E5%B0%8F%E8%AF%B4?start={}&type=T'
        self.headers = {
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
                            #'Accept-Encoding': 'gzip, deflate, br',  #出现乱码
                            'Accept-Language': 'zh-CN,zh;q=0.9',
                            'Connection': 'keep-alive',
                            'Cookie': 'bid=SBVxkOaeD9c; douban-fav-remind=1; __yadk_uid=S4wvYIkkHQ5d6VkBPSLma0ndaRHO7mZS; trc_cookie_storage=taboola%2520global%253Auser-id%3Dd9d67e7b-a465-442e-b2e9-c936dc1be4f5-tuct453c2ba; gr_user_id=77b0633b-6fe6-4a7e-b5c1-edbbab86cc23; _vwo_uuid_v2=D127FFD80B626B42863CF0D67AF7D86BF|ac8ef622b56b7788c3cd752e38d79db4; __gads=ID=43ad771f732af4e2:T=1571880571:S=ALNI_MbuMKrrEJoVTnC0Tk_l3ZpJw8_x6Q; __utmc=30149280; viewed="1057244_25862578_27604025"; push_noty_num=0; push_doumail_num=0; douban-profile-remind=1; ct=y; apiKey=; dbcl2="205817541:/s46cQgsiR4"; ck=x07H; _pk_ref.100001.8cb4=%5B%22%22%2C%22%22%2C1571974725%2C%22https%3A%2F%2Faccounts.douban.com%2Fpassport%2Fregister%22%5D; _pk_ses.100001.8cb4=*; __utma=30149280.1251086817.1566195004.1571969951.1571974725.12; __utmz=30149280.1571974725.12.7.utmcsr=accounts.douban.com|utmccn=(referral)|utmcmd=referral|utmcct=/passport/register; __utmt=1; __utmv=30149280.20581; _pk_id.100001.8cb4=59fce4201d371ea4.1566195000.6.1571974749.1571971038.; __utmb=30149280.6.10.1571974725',
                            'Host': 'book.douban.com',
                            #'Referer': 'https://book.douban.com/tag/%E5%B0%8F%E8%AF%B4?start=20&type=T',
                            'Upgrade-Insecure-Requests': '1',
                            'User-Agent': UserAgent().random
        }
        self.bookname_list = []
        self.author_list=[]
        self.translator_list = []
        self.publish_house_list = []
        self.publish_date_list = []
        self.price_list = []
        self.rating_num_list = []
        self.comment_num_list=[]
        self.intro_list = []

    def get_url_list(self):
        for i in range(1,5):
            self.url_queue.put(self.base_url.format(20*(i-1)))

    def parse_url(self):
        while True:
            url = self.url_queue.get()
            time.sleep(1)
            response = requests.get(url,headers=self.headers)
            response.encoding = 'utf-8'

            self.html_queue.put(response.text)
            self.url_queue.task_done()

    #提取数据
    def get_content_list(self):
        html_str = self.html_queue.get()
        html = etree.HTML(html_str)
        content_list = html.xpath('//*[@id="subject_list"]/ul/li')
        for content in content_list:
            #书名
            bookname = content.xpath('.//div[2]/h2/a/text()')[0].strip()

            #书籍信息
            info = content.xpath('.//div[2]/div[1]/text()')[0].strip()
            info_list = info.split('/')
            #作者
            author = info_list[0].strip()
            #译者
            translator = info_list[1].strip() if len(info_list)==5 else ''
            #出版社
            publish_house = info_list[-3].strip()
            #出版日期
            publish_date = info_list[-2].strip()
            #图书价格
            price = info_list[-1].strip()

            #评分
            rating_num = content.xpath('.//div[2]/div[2]/span[2]/text()')[0].strip()

            #评论数
            comment_num = content.xpath('.//div[2]/div[2]/span[3]/text()')[0].strip()
            comment_num = re.findall('\d+',comment_num)[0]

            #简介
            intro = content.xpath('.//div[2]/p/text()')
            intro = intro[0].strip().replace('\n','') if intro else ''

            self.bookname_list.append(bookname)
            self.author_list.append(author)
            self.translator_list.append(translator)
            self.publish_house_list.append(publish_house)
            self.publish_date_list.append(publish_date)
            self.price_list.append(price)
            self.rating_num_list.append(rating_num)
            self.comment_num_list.append(comment_num)
            self.intro_list.append(intro)

        self.html_queue.task_done()

    def save_csv(self):
        df = pd.DataFrame({'书名': self.bookname_list, '作者': self.author_list, '译者': self.translator_list,
                           '出版社': self.publish_house_list, '出版时间': self.publish_date_list, '价格': self.price_list,
                           '评分': self.rating_num_list, '评论人数': self.comment_num_list, '简介': self.intro_list})
        df.to_csv('C:/Users/MSI1/Desktop/douban_Book/book.csv', index=False, encoding='utf-8-sig', sep=',')

    def run(self):
        thread_list = []
        t_url = threading.Thread(target=self.get_url_list)
        thread_list.append(t_url)

        for i in range(5):
            t_html = threading.Thread(target=self.parse_url)
            thread_list.append(t_html)

        for j in range(5):
            t_content = threading.Thread(target=self.get_content_list)
            thread_list.append(t_content)

        for t in thread_list:
            t.setDaemon(True)
            t.start()

        for q in [self.url_queue, self.html_queue]:
            q.join()

if __name__ == "__main__":
    t1 = time.time()
    db = douban_Book()
    db.run()
    db.save_csv()
    t2 = time.time()
    print(f'耗时: {t2-t1}')




























































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































