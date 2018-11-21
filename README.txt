毕设项目--基于Linux的智能门锁。
功能--使用继电器，设计一个服务端程序和客户端程序，使用Android设备进行远程控制门锁的开启。
*注：应付毕业设计做的，别指望能有多好的功能和效果。哈哈哈~~~

iLockServer.py为服务端程序，适用于windows系统-->不能进行多用户操作；python版本为3.6。
IlockServer for Linux也是服务端程序，适用于Linux系统-->可以多线程，python版本为3.6。
iLockClient文件为Android项目，作为Android客户端软件，与iLock服务端通信-->适用于Android4.0.3及以上系统