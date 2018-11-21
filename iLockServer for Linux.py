from socket import *
import sqlite3
import serial
import time
import select#不适合在windows上使用
import sys

HOST = '192.168.43.32'
PORT = 8888
BUFSIZ = 1024
ADDR = (HOST, PORT)

class iLockDataBase:  #数据库处理
    def __init__(self):  #初始化数据库
        self.conn = sqlite3.connect('iLock.db')  # 连接现有数据库，若不存在则会被创建
        print('数据库打开成功')
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE  IF NOT EXISTS iLock
                (USERNAME TEXT PRIMARY KEY  NOT NULL,
                LOGINPWD  CHAR(20)  NOT NULL,
                LOCKPWD  CHAR(20)  NOT NULL
                );''')
        print('表打开成功')
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
            print('以注册用户数据')
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

class SocketServer:  #网络通信
    def __init__(self):  #初始化网络
        self.s = socket(AF_INET, SOCK_STREAM)
        print('Socket已创建')
        self.s.bind(ADDR)
        self.s.listen(5)
        self.input = [self.s, sys.stdin]  # input是一个列表，初始有欢迎套接字以及标准输入

    def ClientMsgAccept(self):
        print('等待用户连接...')
        self.ClientMsg, addr = self.s.accept()
        print('连接服务器的对象：', addr)
        self.input.append(self.ClientMsg)  # 将服务套接字加入到input列表中

    def Msg_Send(self, data):  # 发送数据（网络）
        if data:
            self.ClientMsg.send(data.encode())
        else:
            self.ClientMsg.close()
            print('无数据')
            return 'n'

    def Msg_Recv(self):  # 接收数据（网络）
        data = self.ClientMsg.recv(1024).decode()
        if data:
            return data
        else:
            self.ClientMsg.close()
            print('没有接收到数据')
            return 'n'

    def Lockpwd_Send(self, data):  # 串口通信
        lock = serial.Serial('/dev/ttyUSB0', 9600)  #树莓派的usb端口文件为ttyUSB0-ttyUSB4
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

def domain():#对客户端指令操作
    while True:
        socketServer.ClientMsgAccept()
        socketServer.Msg_Send("connected")
        while True:
            # 从input中选择，轮流处理client的请求连接（tcpSerSock），
            # client发送来的消息(tcpCliSock)，及服务器端的发送消息(stdin)
            readyInput, readyOutput, readyException = select.select(socketServer.input, [], [])
            for indata in readyInput:
                if indata == socketServer.ClientMsg:  # 处理client发送来的消息
                    data = socketServer.Msg_Recv()
                    print(data)
                    model1 = int(data.split('#iLock#')[0])  # 注册或登录选择,1为登录，2为注册,3为用户退出客户端
                    username = data.split('#iLock#')[1]  # 获取用户名
                    loginpwd = data.split('#iLock#')[2]  # 获取登录密码

                    if model1 == 1:  # 登录
                        userlogin = MyiLockDataBase.LoginUser(username, loginpwd)  # 查询用户是否在数据库
                        if userlogin == 'y':
                            socketServer.Msg_Send('LoginSuccess')  # 向客户端反馈用户登录正确
                            print('登录成功')
                        elif userlogin == 'n':
                            socketServer.Msg_Send('LoginFault')  # 向客户端反馈用户登录错误
                            print('登录失败')

                    elif model1 == 2:  # 注册
                        userregister = MyiLockDataBase.RegisterUser(username, loginpwd)  # 向数据库添加用户名和登录密码
                        if userregister == 'y':
                            socketServer.Msg_Send('RegisterSuccess')  # 向客户端反馈用户注册成功
                            print('注册并登录成功')
                        elif userregister == 'n':
                            socketServer.Msg_Send('RegisterFault')  # 向客户端反馈用户注册失败
                            print('注册失败')

                    # 4或5，此时的loginpwd为开锁密码lockpwd
                    # 根据相同服务协议，客户端发送开锁密码的指令为
                    # “model1#iLock#username#iLock#lockpwd”
                    elif model1 == 4:  # 开锁
                        openlockstatus = MyiLockDataBase.OpenLock(username, loginpwd)  # 比对开锁密码
                        if openlockstatus == 'y':  # 如果是正确的开锁密码
                            socketServer.Lockpwd_Send(0)  # 打开usb串口，即开锁
                            socketServer.Msg_Send('LockpwdSuccess')  # 向客户端反馈开锁成功
                            time.sleep(2)  # 休眠2秒
                            socketServer.Lockpwd_Send(1)  # 关闭usb串口为下次开锁做准备
                        elif openlockstatus == 'n':
                            socketServer.Msg_Send('LockpwdFault')  # 向客户端反馈开锁失败

                    elif model1 == 5:  # 更改开锁密码
                        # lockpwd = clientdata.split('#iLock#')[2]  # 获取更改后的密码
                        updatelockpwd = MyiLockDataBase.UpdateData(username, loginpwd)  # 更改密码，此时的lockpwd为更新后的开锁密码
                        if updatelockpwd == 'y':
                            socketServer.Msg_Send('UpdateLockPwd Success')  # 向客户端反馈更改成功

                    elif model1 == 3:  # 退出
                        socketServer.input.remove(socketServer.ClientMsg)
                        break
                        socketServer.ClientMsg.close()

if __name__ == '__main__':
    MyiLockDataBase = iLockDataBase()  # 实例化对象，数据库初始化
    socketServer = SocketServer()  # 实例化对象，网络初始化
    domain()
