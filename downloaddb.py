#coding=utf-8
import time
import os
import sqlite3
import requests
import threading

class Mydb:
    def __init__(self,dbname):#链接数据库
        self.conn = sqlite3.connect(dbname)
        self.cursor = self.conn.cursor()

    def createtable(self,name):#创建表
        command = 'CREATE TABLE IF NOT EXISTS %s(picname message_text ,link message_text )'%name
        self.cursor.execute(command)
        #self.conn.commit()

    def insertdt(self,name,mes):
        command = 'INSERT INTO %s (picname,link) VALUES (?,?)'%name
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

class Down:
    def __init__(self,db,table):
        self.db = sqlite3.connect(db,10)
        self.table = table
        print("连接成功")
        self.cu = self.db.cursor()
        self.thtead = []
        self.path = 'F:\\%s\\'%self.table

    def readdb(self):
        str = "SELECT * from %s"%self.table
        mes = self.cu.execute(str)
        self.listdict = []
        for row in mes:
            dic = {}
            dic[row[0]] = row[1]
            self.listdict.append(dic)

        num = int(len(self.listdict)/8)
        for i in range(0,8):
            pica = i*num
            picb = num * (i+1) - 1
            if i == 7:
                picb = len(self.listdict)-1
            print("线程",pica,picb)
            mythr = threading.Thread(target=self.thrfx,args=(pica,picb))
            self.thtead.append(mythr)
        for item in range(0,8):
            threading.Thread.start(self.thtead[item])
            print("线程开始",item)
            #os.system("pause")

        for item in range(0,8):
            threading.Thread.join(self.thtead[item])
            print("线程%s结束"%str(item))

    def thrfx(self,pica,picb):
        print(pica,picb)
        time.sleep(1)
        listdict = self.listdict[pica:picb+1]
        j= 0
        for i in range(pica,picb+1):
            print("正在下载第%s张"%str(i))
            self.savepath = self.path + str(i)+r'.jpg'
            #print(list((self.listdict[i]).values())[0])
            # self.savepic(row[1],row[0])
            self.savepic(list((listdict[j]).values())[0],list(dict(listdict[j]).keys())[0])
            j+=1
            print("第%s张下载完成"%str(i))

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


obj = Mydb('jd')
listt = obj.alltable()
for tb in listt:
    if tb[-1] == '1':
        if not os.path.exists('F:\\%s'%tb):
            os.mkdir('F:\\'+tb)
        print(tb)
        obj = Down('jd',tb)
        obj.readdb()

