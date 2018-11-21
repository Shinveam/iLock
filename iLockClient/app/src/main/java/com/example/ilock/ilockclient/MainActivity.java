package com.example.ilock.ilockclient;

import android.os.Handler;
import android.os.Looper;
import android.os.Message;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetAddress;
import java.net.Socket;

public class MainActivity extends AppCompatActivity {

    EditText username, loginpwd, lockpwd;
    EditText againlpwd, newlockpwd, againnewlpwd;
    EditText ipaddr, port;
    TextView LoginRemind, LockRemind, ResetRemind;
    Button RegisterBtn, LoginBtn, conn;

    Socket socket = null;
    OutputStream outputStream = null;//定义输出流
    InputStream inputStream = null;//定义输入流

    String myMsg = null;//定义需要向服务器发送的字符串

    int ifconnect = 0;//网络连接标志，0为未连接，1为已连接
    int flag = 0;//定义标签，0为未登录，1为已登录

    Handler handler = new Handler(){
        @Override
        public void handleMessage(Message msg) {
            super.handleMessage(msg);
            String data = (String) msg.obj;
            switch (data){
                case "connected":
                    Toast.makeText(getApplicationContext(), "网络已连接", Toast.LENGTH_SHORT).show();
                    conn.setEnabled(false);  //按钮设置不可按
                    ifconnect = 1;
                    break;
                case "RegisterSuccess":
                    LoginRemind.setText("");
                    Toast.makeText(getApplicationContext(), "注册成功并已为您登录", Toast.LENGTH_SHORT).show();
                    username.setEnabled(false);
                    loginpwd.setEnabled(false);
                    RegisterBtn.setEnabled(false);
                    LoginBtn.setEnabled(false);
                    LoginBtn.setText("已登录");
                    flag = 1;
                    break;
                case "RegisterFault":
                    loginpwd.setText("");
                    LoginRemind.setText("已存在该用户！");
                    Toast.makeText(getApplicationContext(), "注册失败", Toast.LENGTH_SHORT).show();
                    break;
                case "LoginSuccess":
                    LoginRemind.setText("");
                    Toast.makeText(getApplicationContext(), "登录成功", Toast.LENGTH_SHORT).show();
                    username.setEnabled(false);
                    loginpwd.setEnabled(false);
                    RegisterBtn.setEnabled(false);
                    LoginBtn.setEnabled(false);
                    LoginBtn.setText("已登录");
                    flag = 1;
                    break;
                case "LoginFault":
                    loginpwd.setText("");
                    LoginRemind.setText("用户名或密码错了哦！");
                    Toast.makeText(getApplicationContext(), "登录失败", Toast.LENGTH_SHORT).show();
                    break;
                case "LockpwdSuccess":
                    LockRemind.setText("");
                    Toast.makeText(getApplicationContext(), "已开锁！", Toast.LENGTH_LONG).show();
                    break;
                case "LockpwdFault":
                    LockRemind.setText("密码错了哦！");
                    lockpwd.setText("");
                    Toast.makeText(getApplicationContext(), "开锁失败！", Toast.LENGTH_SHORT).show();
                    break;
                case "UpdateLockPwd Success":
                    ResetRemind.setText("");
                    Toast.makeText(getApplicationContext(), "开锁密码已更改！", Toast.LENGTH_LONG).show();
                    break;
                default:break;
            }
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        username = (EditText) findViewById(R.id.username);
        loginpwd = (EditText) findViewById(R.id.loginpwd);
        lockpwd = (EditText) findViewById(R.id.lockpwd);
        againlpwd = (EditText) findViewById(R.id.againlpwd);
        newlockpwd = (EditText) findViewById(R.id.newlockpwd);
        againnewlpwd = (EditText) findViewById(R.id.againnewlpwd);

        LoginRemind = (TextView) findViewById(R.id.LoginRemind);
        LockRemind = (TextView) findViewById(R.id.LockRemind);
        ResetRemind = (TextView) findViewById(R.id.ResetRemind);

        ipaddr = (EditText) findViewById(R.id.ipaddr);
        port = (EditText) findViewById(R.id.port);

        conn = (Button) findViewById(R.id.conn);
        RegisterBtn = (Button) findViewById(R.id.RegisterBtn);
        LoginBtn = (Button) findViewById(R.id.LoginBtn);
    }

    //连接网络
    public void connect(View v){
        String IP = ipaddr.getText().toString();  //获取IP出入框内容
        String PORT = port.getText().toString();  //获取端口号内容

        if (IP.isEmpty() || PORT.isEmpty()){  //判断IP输入框和端口号是否为空
            Toast.makeText(this,
                    "IP地址和端口号不能为空哦", Toast.LENGTH_LONG).show();
        }
        else {
            Connect_Thread connect_Thread = new Connect_Thread();
            connect_Thread.start();//开启连接线程
        }
    }


    //用户注册
    public void Register(View v){
        if (ifconnect == 1){  //判断网络是否连接，当前状态为已连接
            String usr, lgpwd;

            usr = username.getText().toString();//获取输入框中的用户名
            lgpwd = loginpwd.getText().toString();//获取登录密码

            if (usr.isEmpty() || lgpwd.isEmpty()){ //判断登录名输入框和登录密码输入框是否为空
                LoginRemind.setText("请将信息填写完整！");
            }

            else {
                myMsg = "2#iLock#" + usr + "#iLock#" + lgpwd;  //按协议组成需要发送的数据
                LoginRemind.setText("");
                SendMsg(myMsg);//向服务器发送字符串
            }
        }

        else{
            Toast.makeText(this, "请先连接网络", Toast.LENGTH_LONG).show();
        }
    }

    //用户登录
    public void Login(View v){
        if (ifconnect == 1){
            String usr, lgpwd;

            usr = username.getText().toString();//获取用户名
            lgpwd = loginpwd.getText().toString();//获取登录密码输入框的字符串

            if (usr.isEmpty() || lgpwd.isEmpty()){
                LoginRemind.setText("请将信息填写完整！");
            }

            else {
                LoginRemind.setText("");
                myMsg = "1#iLock#" + usr + "#iLock#" + lgpwd;
                SendMsg(myMsg);
            }
        }

        else {
            Toast.makeText(this, "请先连接网络", Toast.LENGTH_LONG).show();
        }
    }

    //开锁
    public void OpenLock(View v){
        if (ifconnect == 1) {
            if (flag == 1) {
                String lcpwd, usr;
                lcpwd = lockpwd.getText().toString();//获取开锁密码输入框的字符串
                usr = username.getText().toString();

                if (lcpwd.isEmpty()) {
                    LockRemind.setText("密码没有输入呦！");
                } else {
                    myMsg = "4#iLock#" + usr + "#iLock#" +lcpwd;
                    LockRemind.setText("");
                    SendMsg(myMsg);
                }
            }

            else {
                Toast.makeText(this, "请先登录！", Toast.LENGTH_SHORT).show();
            }
        }

        else {
            Toast.makeText(this, "请先连接网络", Toast.LENGTH_LONG).show();
        }
    }

    //确认更改密码
    public void Confirm(View v) {
        if (ifconnect == 1) {
            if (flag == 1) {
                String algpwd, nlcpwd, anlcpwd, usr;
                algpwd = againlpwd.getText().toString();
                nlcpwd = newlockpwd.getText().toString();
                anlcpwd = againnewlpwd.getText().toString();
                usr = username.getText().toString();

                if (nlcpwd.isEmpty() || algpwd.isEmpty() || anlcpwd.isEmpty()) {
                    ResetRemind.setText("没输入登录密码、新密码或者没确认密码");
                } else {
                    ResetRemind.setText("");

                    if (algpwd.equals(loginpwd.getText().toString())) {  //如果再次输入的开锁密码与登录的开锁密码相同

                        if (nlcpwd.equals(anlcpwd)) { // 如果新密码和确认密码相同
                            myMsg = "5#iLock#" + usr + "#iLock#" + nlcpwd;
                            SendMsg(myMsg);
                        } else {
                            againnewlpwd.setText("");
                            ResetRemind.setText("新密码错了，再确认一遍！");
                        }
                    } else {
                        ResetRemind.setText("登录密码不对，请再次输入！");
                        againlpwd.setText("");
                    }
                }
            } else {
                Toast.makeText(this, "请先登录！", Toast.LENGTH_SHORT).show();
            }
        }

        else {
            Toast.makeText(this, "请先连接网络", Toast.LENGTH_LONG).show();
        }
    }

    //退出App
    public void ExitApp(View v){
        if (ifconnect == 1){
            myMsg = "3#iLock##iLock#";
            SendMsg(myMsg);
            System.exit(0);//退出app
        }

        else {
            System.exit(0);//退出app
        }
    }

    //发送
    public void SendMsg(final String data) {
        try
        {
            Log.e("socket is conect", Boolean.toString(socket.isConnected()));//socket状态日志
            if (!socket.isConnected()){
                return;
            }
            //获取输出流
            outputStream = socket.getOutputStream();
            new Thread(new Runnable() {
                @Override
                public void run() {
                    try {
                        //发送数据
                        //outputStream.write(MsgEditText.getText().toString().getBytes());
                        outputStream.write(data.getBytes("utf-8"));
                        outputStream.flush();
                    }
                    catch (IOException e){
                        e.printStackTrace();
                    }
                }
            }).start();
        }
        catch (Exception e)
        {
            // TODO Auto-generated catch block
            e.printStackTrace();
        }
    }

    //连接线程
    class Connect_Thread extends Thread//继承Thread
    {
        public void run()//重写run方法
        {
            try
            {
                if (socket == null)
                {
                    String IP = ipaddr.getText().toString();  //获取IP地址
                    int PORT = Integer.parseInt(port.getText().toString());  //获取端口号
                    socket = new Socket(IP, PORT);//创建连接地址和端口
                    //ifconnect = 1;//网络连接标志，1为已连接，可进行下步操作

                    if (socket.isConnected()){
                        Log.e("socket is connected", Boolean.toString(socket.isConnected()));
                        //Toast.makeText(getApplicationContext(), "网络已连接", Toast.LENGTH_SHORT).show();
                    }
                    //在创建完连接后启动接收线程
                    Receive_Thread receive_Thread = new Receive_Thread();
                    receive_Thread.start();//开启接收线程
                }

//                else {
//                    Toast.makeText(getApplicationContext(),
//                            "网络无法连接，请检查IP地址是否输入正确", Toast.LENGTH_LONG).show();
//                }
            }
            catch (Exception e)
            {
                // TODO Auto-generated catch block
                e.printStackTrace();
            }
        }
    }

    //接收线程
	class Receive_Thread extends Thread
	{
		public void run()//重写run方法
		{
			try
			{
                final byte[] buffer = new byte[1024];//创建接收缓冲区
				while (true)
                {
					inputStream = socket.getInputStream();
					final int len = inputStream.read(buffer);//数据读出来，并且返回数据的长度
					runOnUiThread(new Runnable()//不允许其他线程直接操作组件，用提供的此方法可以
					{
						public void run()
						{
							// TODO Auto-generated method stub
                            String result = new String(buffer, 0, len);//获取从服务器接收的字符串
                            Message msg = Message.obtain();
                            msg.obj = result;
                            handler.sendMessage(msg);//线程间通信，向主线程发送接收到的字符串
						}
					});
				}
			}
			catch (IOException e)
			{
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
		}
	}

}