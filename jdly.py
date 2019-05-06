# encoding=utf-8
import re
import threading
import os
import requests
from bs4 import BeautifulSoup
from selenium import webdriver

import sqlite3

TAGALL = 0


class Mydb:
    def __init__(self, dbname):  # 链接数据库
        self.conn = sqlite3.connect(dbname)
        self.cursor = self.conn.cursor()

    def alltable(self):
        listtable = []
        mes = self.cursor.execute('SELECT name FROM sqlite_master')
        for row in mes:
            #print(row[0])
            listtable.append(row[0])
        return listtable

    def createtable(self, name):  # 创建表
        command = 'CREATE TABLE IF NOT EXISTS %s(picname message_text ,link message_text )' % name
        self.cursor.execute(command)
        # self.conn.commit()

    def insertdt(self, name, mes):
        command = 'INSERT INTO %s (picname,link) VALUES (?,?)' % name
        self.cursor.execute(command, mes)
        self.conn.commit()

    def closedb(self):
        self.conn.close()


mutex = threading.Lock()
numpic = 0
numtb = 0


class Jdlypar(object):  # 基类
    def __init__(self, url):
        option = webdriver.ChromeOptions()
        option.add_argument('--no-sandbox')
        option.add_argument('--headless')
        # 获得无界面google
        self.driver = webdriver.Chrome(options=option)
        self.driver.get(url)

    def end(self):
        self.driver.quit()


class Checkedtag(Jdlypar):  # 项目选择
    def __init__(self):
        # 初始化基类
        super().__init__('http://www.jder.net/')
        # 获得页面soup
        self.soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        # 保存 标签--链接 字典信息
        self.listu_n = []

    def gethottag(self, divclass):  # 读取保存标签信息
        div = self.soup.find('div', {'class': divclass})
        for taga in div.find_all('a'):
            dictu_n = {}
            dictu_n[taga.text] = taga.get('href')
            self.listu_n.append(dictu_n)

    def getinput(self, inputnum=0):  # 显示标签和链接信息 并获得输入
        print("*******************************绅士*************************************")
        global TAGALL
        TAGALL = len(self.listu_n)
        for i in range(len(self.listu_n)):
            print(str(i + 1) + ".", list(dict(self.listu_n[i]).keys())[0], list(dict(self.listu_n[i]).values())[0])
        print("*******************************END*************************************")
        if inputnum == 0:
            select = input("Please Make Your Choose:")
        else:
            select = inputnum
        listm = [list(dict(self.listu_n[int(select) - 1]).values())[0],
                 list(dict(self.listu_n[int(select) - 1]).keys())[0]]
        # 返回【标签--链接 】
        return listm


class Picjdly(Jdlypar):
    def __init__(self, url, tbname):
        self.url = url
        super().__init__(url)
        self.refer = []  # 保存链接
        self.pathname = []  # 保存存储路径
        self.tablename = tbname  # 数据库表名

    # 打开数据库并创建对应表
    def database(self, table):
        self.db = Mydb('jd')
        self.db.createtable(table)

    # 获得指定页面的项目信息
    def allpage(self, pages, pagee):
        for page in range(int(pages), int(pagee) + 1):
            print("开始加载第%s页" % str(page))
            self.driver.get(self.url + 'page/%s/' % str(page))
            print("开始读取页面")
            self.getpage()
            # self.db.closedb()
            print("开始加载图片")
            self.getpic(True)  #######################################################################################
            # self.db.closedb()
            print("第%s页下载完成！" % str(page))
        self.db.closedb()
        print("数据库关闭")

    def getpage(self):
        self.refer.clear()
        self.pathname.clear()
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        # soup=soup.find_all('section')
        soup = soup.find('main', {'id': 'main'})
        soup = soup.find_all('a')
        for item in soup:
            if item.find('img') != None:
                # print(item.get('href'))
                print(item.find('img').get('alt'))
                self.refer.append(item.get('href'))
                dirname = re.sub(r'[\\:：/]', '.', item.find('img').get('alt'))
                ########################################################################################################################
                lockflag = mutex.acquire(True)
                if lockflag:
                    self.database(self.tablename + '0')
                    self.db.insertdt(self.tablename + '0', (dirname, item.get('href')))
                    mutex.release()
                    global numtb
                    numtb += 1
                #############################################################################################################333
                self.pathname.append(dirname)

    def getpic(self, table=False):
        for i in range(0, len(self.refer)):
            if not table:
                if not os.path.exists(self.pathname[i]):
                    try:
                        os.mkdir(self.pathname[i])
                    except:
                        print("创建目录失败")
                        continue
                    print(self.pathname[i], "创建成功!")
            for j in range(1, 3):
                try:
                    r = requests.get(self.refer[i] + '/' + str(j), timeout=10)
                except:
                    print("gepic requests请求错误")
                    # os.rmdir(self.pathname[i])
                    continue
                if not r.status_code == 200:
                    print(self.refer[i], "链接不存在")
                    break
                soup = BeautifulSoup(r.text, 'html.parser')
                for item in soup.find_all('div'):
                    if item.get('class') == ['single-content']:
                        for img in item.find_all('img'):
                            picurl = img.get('src')
                            # print(picurl)
                            if re.match(r'^http:', picurl) == None:
                                picurl = 'http:' + picurl
                                # print(picurl)
                            ###########################################################################################
                            lockflag = mutex.acquire(True)
                            if lockflag:
                                self.database(self.tablename + '1')
                                self.db.insertdt(self.tablename + '1', (self.refer[i], picurl))
                                mutex.release()
                                global numpic
                                numpic += 1
                            ##########################################################################################
                            # print(img.get('src'))
                            # print(re.match(r'^http',img.get('src')))
                            self.savepath = './' + self.pathname[i] + '/' + picurl.split('/')[-1]
                            if not table:
                                self.savepic(picurl, self.refer[i])

    def savepic(self, url, refer=""):
        kv = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
        kv['Referer'] = refer
        try:
            pic = requests.get(url, timeout=10, headers=kv)
            if pic.status_code == 200:
                with open(self.savepath, 'wb') as f:
                    f.write(pic.content)
                    print(self.savepath, "图片保存成功！")
            else:
                pic = requests.get(url, timeout=10)
                if pic.status_code == 200:
                    with open(self.savepath, 'wb') as f:
                        f.write(pic.content)
                        print(self.savepath, "图片保存成功！")
                else:
                    print("图片不存在")
        except:
            print("savepic requests请求错误")


class Alltest(object):
    def __init__(self, mode):
        self.mode = mode

    def start(self, pages, pagee):
        obj = Checkedtag()
        if self.mode == 0:
            print("按类别获取")
            obj.gethottag('menu-%e8%8f%9c%e5%8d%952-container')
        else:
            print("按热门标签获取")
            obj.gethottag('tagcloud')
        obj.end()
        if not self.mode == 0:
            global TAGALL
            for i in range(1,
                           TAGALL + 1):  ##############################################################################
                me = obj.getinput(i)
                print(me)
                self.url = me[0]
                self.tbname = me[1]
                self.pages = pages
                self.pagee = pagee
                self.thread()
        else:
            me = obj.getinput()
            print(me)
            self.url = me[0]
            self.tbname = me[1]
            self.pages = pages
            self.pagee = pagee
            self.thread()

    def thr(self, tbname, pages, pagee):
        obj = Picjdly(self.url, tbname)
        obj.allpage(pages, pagee)

    def thread(self):
        thre = []
        nump = self.pagee - self.pages + 1
        thone = int(nump / 4)
        for t in range(self.pages, self.pagee + 1, thone):
            pagea = t
            if (t + thone - 1) > self.pagee:
                pageb = self.pagee
            else:
                pageb = t + thone - 1
            print("线程", pagea, pageb)
            myt = threading.Thread(target=self.thr, args=(self.tbname, pagea, pageb))
            thre.append(myt)
        for i in range(0, len(thre)):
            print("线程%s开始" % str(i))
            thre[i].start()
        for i in range(0, len(thre)):
            thre[i].join()
            print("线程%s结束" % str(i))


if __name__ == '__main__':
    a = Alltest(1)
    a.start(1, 30)
    print("共%s张标签" % str(numtb))
    print("共%s张图片" % str(numpic))
