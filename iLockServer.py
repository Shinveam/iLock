'''
***********************************
* Author        : Wei Deping
* Last modified : 2018-4-21  20:10
* Email         : 980432822@qq.com
* Filename      : iLockServer
***********************************
'''
from socket import *
import sqlite3
import serial
#import binascii
import time
import threading
#from multiprocessing import Process  #Windows系统下使用该模块创建子进程
#import os  #Unix和Linux系统下使用该模块os.fork（）创建子进程

class SocketServer:  #网络通信
    def __init__(self):  #初始化网络
        host = '192.168.43.32'
        port = 8888
        #self.s = socket.socket()
        self.s = socket(AF_INET, SOCK_STREAM)  #创建一个服务，socket里不写参数则默认为IPv4协议
        print('Socket 创建成功')
        self.s.bind((host, port))  # 绑定
        self.s.listen(5)  #监听连接，如果系统提供的线程（或资源）满了，则挂起5个线程，后面连接的客户端则无法连接
        print('Socket 正在监听')

    def ClientMsgAccept(self):
        print('等待用户连接...')
        self.ClientMsg, self.addr = self.s.accept()
        print('连接服务器的对象：', self.addr)

    def Msg_Send(self, data):  # 发送数据（网络）
        if data:
            self.ClientMsg.send(data.encode())
        else:
            self.ClientMsg.close()
            print('not data!')
            return 'n'

    def Msg_Recv(self):  # 接收数据（网络）
        data = self.ClientMsg.recv(1024).decode()
        if data:
            return data
        else:
            print('没有接收到数据')
            return 'n'

    def Lockpwd_Send(self, data):  # 串口通信
        lock = serial.Serial('com3', 9600)  #树莓派的usb端口文件为ttyUSB0-ttyUSB4
        #1、openlock = binascii.b2a_hex('A0 01 01 A2')  # 以16进制发送，打开usb串口
        #2、openlock = '\x41\x30 \x30\x31 \x30\x31 \x41\x32'

        # 1、closeserial = binascii.b2a_hex('A0 01 00 A1')  # 以16进制发送，关闭usb串口
        # 2、closeserial = '\x41\x30 \x30\x31 \x30\x30 \x41\x31'
        '''
        发送十六进制指令先将十六进制数转化为十进制值，然后通过ser.write()发送。
        在python中，只有bytes类型能通过串口收发，
        转化的实质是将十六进制代码逐字节转化为bytes类型，就是字节流。
        '''
        openlock = bytes([160, 1, 1, 162])  #定义开锁(打开串口)指令，差分连续单通道模式（A0 01 01 A2）
        closeserial = bytes([160, 1, 0, 161])  #定义关闭串口指令（A0 01 00 A1）

        if data == 0:  #开串口
            #1、pwd = openlock.decode('hex')
            #2、pwd = openlock.encode(encoding="utf-8")
            lock.write(openlock)
        elif data == 1:  #关串口
            #1、pwd = closelock.decode('hex')
            #2、pwd = closelock.encode(encoding="utf-8")
            lock.write(closeserial)

class iLockDataBase:  #数据库处理
    def __init__(self):  #初始化数据库
        self.conn = sqlite3.connect('iLock.db')  # 连接现有数据库，若不存在则会被创建
        print('数据库 打开成功')
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE  IF NOT EXISTS iLock
                (USERNAME TEXT PRIMARY KEY  NOT NULL,
                LOGINPWD  CHAR(20)  NOT NULL,
                LOCKPWD  CHAR(20)  NOT NULL
                );''')
        print('数据表 打开成功')
        self.conn.commit()
        #self.conn.close()

    def RegisterUser(self, username, loginpwd, lockpwd='123456'):  #用户注册
        #查询表内是否存在该用户
        self.c.execute("SELECT * FROM iLock WHERE USERNAME = '%s'" % username)
        value = self.c.fetchall()
        if len(value) == 0:  #表内不存在则插入数据
            self.c.execute("INSERT INTO iLock (USERNAME, LOGINPWD, LOCKPWD) \
                           VALUES('%s', '%s', '%s')" % (username, loginpwd, lockpwd) )
            self.conn.commit()
            print('用户数据已插入')
            return 'y'
        else:
            return 'n'
        #self.conn.close()

    def LoginUser(self, username, loginpwd):  #用户登录
        self.c.execute("SELECT * FROM iLock WHERE USERNAME = '%s' AND LOGINPWD = '%s'" % (username, loginpwd))
        value = self.c.fetchall()
        if len(value) == 0:
            return 'n'
        else:
            return 'y'

    def OpenLock(self, username, lockpwd):  #开锁密码比对
        self.c.execute("SELECT * FROM iLock WHERE USERNAME = '%s' AND LOCKPWD = '%s'" % (username, lockpwd))
        value = self.c.fetchall()
        if len(value) == 0:
            print('开锁失败')
            return 'n'
        else:
            print('开锁成功')
            return 'y'

    def UpdateData(self, username, nlockpwd):  #更改开锁密码
        # self.c.execute("SELECT * FROM iLock WHERE USERNAME = '%s' AND LOGINPWD = '%s'" % username)
        # value = self.c.fetchall()
        # if len(value) == 0:
        #     print('loginpwd error')
        #     return 'n'

        self.c.execute("UPDATE iLOCK SET LOCKPWD = '%s' where USERNAME = '%s'" % (nlockpwd, username))
        self.conn.commit()
        print('Total password updated : ', self.conn.total_changes)
        return 'y'
        #self.conn.close()

def ClientCommand():  #对客户端的指令进行操作  ClientMsg
    while True:
        socketServer.ClientMsgAccept()
        socketServer.Msg_Send("connected")  # 告知客户端已经连接

    #服务协议
    # 用户名以及登录密码和开锁密码的数据接收和登录或
    # 者注册使用“ ‘model#iLock#用户名#iLock#密码’ ”的格式
    #当model为1和2时，lglcpwd为登录密码，model为4和5时lglcpwd为开锁密码
        while True:  #循环获取用户信息
            data = socketServer.Msg_Recv()  # 获取用户名及登录密码
            model = int(data.split('#iLock#')[0])  # 注册或登录选择,1为登录，2为注册,3为用户退出客户端
            username = data.split('#iLock#')[1]  # 获取用户名
            lglcpwd = data.split('#iLock#')[2]  # 获取登录密码

            if model == 1:  # 登录模式
                userlogin = MyiLockDataBase.LoginUser(username, lglcpwd)  # 查询用户是否在数据库
                if userlogin == 'y':
                    socketServer.Msg_Send('LoginSuccess')  # 向客户端反馈用户登录正确
                    print('登录成功')

                elif userlogin == 'n':
                    socketServer.Msg_Send('LoginFault')  # 向客户端反馈用户登录错误
                    print('登录失败')

            elif model == 2:  # 注册模式，注册成功后默认已登录
                userregister = MyiLockDataBase.RegisterUser(username, lglcpwd)  # 向数据库添加用户名和登录密码
                if userregister == 'y':
                    socketServer.Msg_Send('RegisterSuccess')  # 向客户端反馈用户注册成功
                    print('注册并登录成功')

                elif userregister == 'n':
                    socketServer.Msg_Send('RegisterFault')  # 向客户端反馈用户注册失败
                    print('注册失败')

            elif model == 3:  #用户退出
                break  #退出循环，停止接收信息

            elif model == 4:  # 开锁模式
                openlockstatus = MyiLockDataBase.OpenLock(username, lglcpwd)  # 比对开锁密码
                if openlockstatus == 'y':  # 如果是正确的开锁密码
                    socketServer.Lockpwd_Send(0)  # 打开usb串口，即开锁
                    socketServer.Msg_Send('LockpwdSuccess')  # 向客户端反馈开锁成功
                    time.sleep(2)  # 休眠2秒
                    socketServer.Lockpwd_Send(1)  # 关闭usb串口为下次开锁做准备
                elif openlockstatus == 'n':
                    socketServer.Msg_Send('LockpwdFault')  # 向客户端反馈开锁失败

            elif model == 5:  # 更改开锁密码
                # lockpwd = clientdata.split('#iLock#')[2]  # 获取更改后的密码
                updatelockpwd = MyiLockDataBase.UpdateData(username, lglcpwd)  # 更改密码，此时的lockpwd为更新后的开锁密码
                if updatelockpwd == 'y':
                    socketServer.Msg_Send('UpdateLockPwd Success')  # 向客户端反馈更改成功
                # elif updatelockpwd == 'n':
                #     socketServer.Msg_Send('UpdateLockPwd Fault')  # 向客户端反馈更改失败

        socketServer.ClientMsg.close()
        print('用户退出')

if __name__ == '__main__':
    MyiLockDataBase = iLockDataBase()  # 实例化对象，数据库初始化
    socketServer = SocketServer()  # 实例化对象，网络初始化

    while True:
        # socketServer.ClientMsgAccept()
        # t = threading.Thread(target=ClientCommand, args=(socketServer.ClientMsg))
        # t.start()

        ClientCommand()
        # #Unix和Linux的多进程操作
        # pid = os.fork()
        # if pid == 0:   #子进程创建成功
        #     ClientCommand()
        # elif pid < 0:  #子进程创建失败
        #     print('Fail to fork')
        # else:
        #     SocketServer.ClientMsg.close()  #关闭父进程对应客户端的网络通信

        #Windows下的多进程操作
        # p = Process(target=ClientCommand, args=(socketServer.ClientMsg, socketServer.addr))
        # p.start()  #开启子进程
        #p.join()  #该方法可以等待子进程结束后执行下一步指令
        #print('Child process end')  #向控制台反应子进程结束
