# coding=utf-8
import time
import os
import sqlite3
import re
import threading
import requests
from bs4 import BeautifulSoup
from selenium import webdriver

SIZE = "1920x1080"
kv = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}

class Mydb:
    def __init__(self,dbname):#链接数据库
        self.conn = sqlite3.connect(dbname,check_same_thread = False)
        self.cursor = self.conn.cursor()

    def createtable(self,name):#创建表
        command = 'CREATE TABLE IF NOT EXISTS %s(title message_text ,link message_text ,hot message_text )'%name
        self.cursor.execute(command)
        self.conn.commit()

    def insertdt(self,name,mes):
        command = 'INSERT INTO %s(title,link,hot) VALUES (?,?,?)'%name
        self.cursor.execute(command,mes)
        self.conn.commit()

    def alltable(self):
        listtable = []
        mes = self.cursor.execute('SELECT name FROM sqlite_master')
        for row in mes:
            #print(row[0])
            listtable.append(row[0])
        return listtable

    def closedb(self):
        self.conn.close()

class Picture(object):
    def __init__(self):
        self.option = webdriver.ChromeOptions()
        self.option.add_argument('--no-sandbox')
        self.option.add_argument('--headless')
        self.driver = webdriver.Chrome()  # options=option
        self.rooturl = 'http://desk.zol.com.cn/'
        self.taglist = []
        self.sizelist = []
        self.url = ''

        self.db = Mydb('zol_bizhi')
        self.cu = self.db.cursor
        self.tbnm = ''
        self.mutex = threading.Lock()

    def gettags(self):
        self.driver.get(self.rooturl)
        soup = BeautifulSoup(self.driver.page_source,'html.parser')
        tagdd = soup.find('dd',{'class':['filter-item','first','clearfix']})#main > dl.filter-item.first.clearfix
        for tag in BeautifulSoup.find_all(tagdd,'a'):
            tagdic = {}
            tagdic[tag.text] = tag.get('href')
            self.taglist.append(tagdic)
        print("****************************************************")
        for i in range(len(self.taglist)):
            print(str(i),list(dict(self.taglist[i]).keys())[0],list(dict(self.taglist[i]).values())[0],sep=":")
        print("****************************************************")
##############################################################################################################################
        tagdd = soup.find_all('dd', {'class': ['brand-sel-box','clearfix']})#main > dl:nth-child(2)
        for tag in BeautifulSoup.find_all(tagdd[1], 'a'):
            tagdic = {}
            tagdic[tag.text] = tag.get('href')
            self.sizelist.append(tagdic)
        print("****************************************************")
        for i in range(len(self.sizelist)):
            print(str(i), list(dict(self.sizelist[i]).keys())[0], list(dict(self.sizelist[i]).values())[0], sep=":")
        print("****************************************************")

    def getitem(self,flag=True,inp='2 4'):
        if flag:
            inse = inp
        else:
            inse = input('输入:')
        print(inse.split(' ')[0])
        url = self.rooturl + list(dict(self.taglist[int(inse.split(' ')[0])]).values())[0][1:] +\
              list(dict(self.sizelist[int(inse.split(' ')[1])]).values())[0][1:]
        print(url)
        self.tbnm = list(dict(self.taglist[int(inse.split(' ')[0])]).keys())[0]
        if self.mutex.acquire(True):
            self.db.createtable(self.tbnm)
            self.mutex.release()
        return url

    def getlistcha(self,hot = True,page = 30):
        myth = []
        for p in range(1,page+1,int(page/4)):
            pag = p + int(page/4)-1
            if pag + int(page/4)-1 > page:
                pag = page
            th = threading.Thread(target=self.thr,args=(hot,p,pag))
            myth.append(th)
            print("线程%s-%s"%(str(p),str(pag)))
            th.start()
        for t in myth:
            t.join()
            print("线程结束")

    def thr(self,hot,pagea,pageb):
        driver = webdriver.Chrome(options=self.option)#
        for p in range(pagea,pageb+1):
            print("正在加载第%s页"%str(p))
            if hot:
                url = self.url + 'hot_%s.html' % str(p)
            else:
                url = self.url + 'good_%s.html' % str(p)
            print(url)
            driver.get(url)
            soup = BeautifulSoup(driver.page_source,"html.parser")
            ul = soup.find('ul',{'class':['pic-list2','clearfix']})
            for taga in BeautifulSoup.find_all(ul,'li'):
                print(taga.find('a').text)
                print(self.rooturl[:-1]+taga.find('a').get('href'))
                print(taga.find('ins').text)
                if self.mutex.acquire(True):
                    print("正在写入数据")
                    self.db.insertdt(self.tbnm,(taga.find('a').text,self.rooturl[:-1]+taga.find('a').get('href'),taga.find('ins').text))
                    print("写入成功")
                    self.mutex.release()
            print("第%s页加载成功" % str(p))

    def auto(self):
        self.gettags()
        for i in range(0,len(self.taglist)):
            inp = '%s 4'%str(i)
            self.url = self.getitem(inp=inp)
            self.getlistcha(page=20)

class Downloadpic(object):
    def __init__(self):
        self.savpath = r'F:\\bz\\'
        self.filedir = ''
        self.option = webdriver.ChromeOptions()
        self.option.add_argument('--no-sandbox')
        self.option.add_argument('--headless')
        self.driver = webdriver.Chrome()  # options=option

        self.rooturl ='http://desk.zol.com.cn/showpic/1920x1080_%s_%s.html'

        self.db = Mydb('zol_bizhi')
        self.cu = self.db.cursor
        self.alltb = self.db.alltable()
        self.mutex = threading.Lock()

        self.allpurl = []


    def readtb(self,name):
        self.allpurl.clear()
        self.filedir = name
        path = self.savpath + name
        if not os.path.exists(path):
            try:
                os.mkdir(path)
                print(path,'创建成功')
            except Exception as e:
                print(e)
                return
        print("开始读取数据库")
        if self.mutex.acquire(True):
            rows = self.cu.execute('SELECT * FROM %s'%name)
            self.mutex.release()
        for row in rows:
            print(row[0],row[1])
            dic = {}
            dic[row[0]] = row[1]
            self.allpurl.append(dic)
        print("数据库读取完毕")

    def thrdiv(self):
        myth = []
        print(len(self.allpurl))
        for p in range(0,len(self.allpurl),int((len(self.allpurl)+1)/4)):
            pag = p + int((len(self.allpurl)+1)/4)-1
            if pag >= len(self.allpurl):
                pag = len(self.allpurl)-1
            th = threading.Thread(target=self.thr,args=(p,pag))
            print("线程%s-%s"%(str(p),str(pag)))
            th.start()
            myth.append(th)
        for t in myth:
            t.join()
            print("线程结束")

    def thr(self,paga,pagb):
        driver = webdriver.Chrome(options=self.option)
        for p in range(paga,pagb+1):
            path = self.savpath + self.filedir +'\\'+ list(dict(self.allpurl[p]).keys())[0]
            if not os.path.exists(path):
                os.mkdir(path)
                print(path,"创建成功")
            url = list(dict(self.allpurl[p]).values())[0]
            savepth = self.savpath
            driver.get(url)
            soup = BeautifulSoup(driver.page_source,'html.parser')
            ul = soup.find('ul',{'id':'showImg','class':'clearfix'})#
            dd = soup.find('a',{'target':'_blank','id':SIZE})
            picwebid = dd.get('href')
            picwebid = picwebid[re.search('_\d+\.',picwebid).span()[0]+1:re.search('_\d+\.',picwebid).span()[1]-1]
            for taga in BeautifulSoup.find_all(ul,'a'):
                picid = taga.get('href')
                picid = picid[re.search('_\d+_',picid).span()[0]+1:re.search('_\d+_',picid).span()[1]-1]
                try :
                    req =requests.get(self.rooturl%(str(picid),str(picwebid)),headers = kv)
                    if not req.status_code == 200:
                        continue
                except Exception as e:
                    print(e)
                    continue
                souppic = BeautifulSoup(req.text,'html.parser')
                print(souppic.find('img').get('src'))
                self.savepic(path,souppic.find('img').get('src'))

    def savepic(self,path, url):
        savepath = path + '\\'+ url.split('/')[-1]
        try:
            pic = requests.get(url, timeout=10, headers=kv)
            if pic.status_code == 200:
                with open(savepath, 'wb') as f:
                    f.write(pic.content)
                    print(savepath, "图片保存成功！")
            else:
                pic = requests.get(url, timeout=10)
                if pic.status_code == 200:
                    with open(savepath, 'wb') as f:
                        f.write(pic.content)
                        print(savepath, "图片保存成功！")
                else:
                    print("图片不存在")
        except:
            print("savepic requests请求错误")

    def auto(self):
        for t in self.alltb:
            self.readtb(t)
            self.thrdiv()
            print(t,"保存成功")




###############################
#obj = Picture()
#obj.auto()

#obj.gettags()
#obj.url=obj.getitem()
#obj.getlistcha(page=4)
###################################
objd = Downloadpic()
objd.auto()