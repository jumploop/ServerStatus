# ServerStatus中文版：   

* ServerStatus中文版是一个酷炫高逼格的云探针、云监控、服务器云监控、多服务器探针~。
* 在线演示：https://tz.cloudcpp.com    

[![Python Support](https://img.shields.io/badge/python-3.6%2B%20-blue.svg)](https://github.com/cppla/ServerStatus)
[![C++ Compiler](http://img.shields.io/badge/C++-GNU-blue.svg?style=flat&logo=cplusplus)](https://github.com/cppla/ServerStatus)
[![License](https://img.shields.io/badge/license-MIT-4EB1BA.svg?style=flat-square)](https://github.com/cppla/ServerStatus)
[![Version](https://img.shields.io/badge/Version-Build%201.1.4-red)](https://github.com/cppla/ServerStatus)

![Latest Host Version](https://dl.cpp.la/Archive/serverstatus_1.1.2_host.png)
![Latest Server Version](https://dl.cpp.la/Archive/serverstatus_1.1.2_server.png)

`Watchdog触发式告警，interval只是为了防止频繁收到报警信息造成的骚扰，并不是探测间隔。值得注意的是，Exprtk库默认使用窄字符类型，中文等Unicode字符无法解析计算，等待修复。 `    

# 目录：

* clients       	客户端文件
* server       	 	服务端文件  
* web           	网站文件

* server/config.json	探针配置文件                                
* web/json      	探针月流量        

# Linux部署

支持操作系统：Debian/Ubuntu,Centos/Redhat,archlinux
#### 一键脚本安装:
支持的
```bash
wget -N --no-check-certificate https://raw.githubusercontent.com/jumploop/ServerStatus/master/status.sh && chmod +x status.sh && bash status.sh
```
部署成功后，web服务地址：http://ip:8888

# 容器部署：

【服务端】：
```bash

`Docker`:     

wget --no-check-certificate -qO ~/serverstatus-config.json https://raw.githubusercontent.com/cppla/ServerStatus/master/server/config.json && mkdir ~/serverstatus-monthtraffic    
docker run -d --restart=always --name=serverstatus -v ~/serverstatus-config.json:/ServerStatus/server/config.json -v ~/serverstatus-monthtraffic:/usr/share/nginx/html/json -p 80:80 -p 35601:35601 cppla/serverstatus:latest     

`Docker-compose(推荐)`: docker-compose up -d
```
服务端一键脚本容器部署：
```bash
wget -N --no-check-certificate https://raw.githubusercontent.com/jumploop/ServerStatus/master/shell/serverstatus_deploy.sh && chmod +x serverstatus_deploy.sh && bash serverstatus_deploy.sh
```

【客户端】：
```bash
wget --no-check-certificate -qO client-linux.py 'https://raw.githubusercontent.com/cppla/ServerStatus/master/clients/client-linux.py' && nohup python3 client-linux.py SERVER={$SERVER} USER={$USER} PASSWORD={$PASSWORD} >/dev/null 2>&1 &

eg:
wget --no-check-certificate -qO client-linux.py 'https://raw.githubusercontent.com/cppla/ServerStatus/master/clients/client-linux.py' && nohup python3 client-linux.py SERVER=45.79.67.132 USER=s04  >/dev/null 2>&1 &
```
部署成功后，web服务地址：http://ip:8080
# 主题：            

* layui：https://github.com/zeyudada/StatusServerLayui ，预览：https://sslt.8zyw.cn            
<img src=https://dl.cpp.la/Archive/serverstatus_layui.png width=200 height=100 />

* light：https://github.com/orilights/ServerStatus-Theme-Light ，预览：https://tz.cloudcpp.com/index3.html    
<img src=https://dl.cpp.la/Archive/serverstatus_light.png width=200 height=100 />  


# 手动安装教程：     
   
**【服务端配置】**           
          
#### 一、生成服务端程序              
```
`Debian/Ubuntu`: apt-get -y install gcc g++ make libcurl4-openssl-dev
`Centos/Redhat`: yum -y install gcc gcc-c++ make libcurl-devel

cd ServerStatus/server && make
./sergate
```
如果没错误提示，OK，ctrl+c关闭；如果有错误提示，检查35601端口是否被占用    

#### 二、修改配置文件         
```diff
! watchdog rule 可以为任何已知字段的表达式。注意Exprtk库默认使用窄字符类型，中文等Unicode字符无法解析计算，等待修复       
! watchdog interval 最小通知间隔
! watchdog callback 可自定义为Post方法的URL，告警内容将拼接其后并发起回调 

! watchdog callback Telegram: https://api.telegram.org/bot你自己的密钥/sendMessage?parse_mode=HTML&disable_web_page_preview=true&chat_id=你自己的标识&text=
! watchdog callback Server酱: https://sctapi.ftqq.com/你自己的密钥.send?title=ServerStatus&desp=
! watchdog callback PushDeer: https://api2.pushdeer.com/message/push?pushkey=你自己的密钥&text=
! watchdog callback BasicAuth: https://用户名:密码@你自己的域名/api/push?message=
```
关于Server酱的具体使用可以查看[Server酱使用方法](https://zhuanlan.zhihu.com/p/713331404)

```
{
        "servers":
	[
		{
			"username": "s01",
			"name": "vps-1",
			"type": "kvm",
			"host": "chengdu",
			"location": "🇨🇳",
			"password": "USER_DEFAULT_PASSWORD",
			"monthstart": 1
		}
	],
	"monitors": [
		{
			"name": "监测网站以及MySQL、Redis，默认为七天在线率",
			"host": "https://www.baidu.com",
			"interval": 60,
			"type": "https"
		}
	],
	"watchdog":
	[
	        {
			"name": "服务器负载高监控，排除内存大于32G物理机，同时排除node1机器",
			"rule": "cpu>90&load_1>4&memory_total<33554432&name!='node1'",
			"interval": 600,
			"callback": "https://yourSMSurl"
		},
		{
                        "name": "服务器内存使用率过高监控",
                        "rule": "(memory_used/memory_total)*100>90",
                        "interval": 600,
                        "callback": "https://yourSMSurl"
                },
                {
                        "name": "服务器宕机告警",
                        "rule": "online4=0&online6=0",
                        "interval": 600,
                        "callback": "https://yourSMSurl"
                },
		{
                        "name": "DDOS和CC攻击监控",
                        "rule": "tcp_count>600",
                        "interval": 300,
                        "callback": "https://yourSMSurl"
                },
		{
			"name": "服务器月出口流量999GB告警",
			"rule": "(network_out-last_network_out)/1024/1024/1024>999",
			"interval": 3600,
			"callback": "https://yourSMSurl"
		},
		{
			"name": "你可以组合任何已知字段的表达式",
			"rule": "(hdd_used/hdd_total)*100>95",
			"interval": 1800,
			"callback": "https://yourSMSurl"
		}
	]
}       
```

#### 三、拷贝ServerStatus/web到你的网站目录        
例如：
```
sudo cp -r ServerStatus/web/* /home/wwwroot/default
```

#### 四、运行服务端：             
web-dir参数为上一步设置的网站根目录，务必修改成自己网站的路径   
```
./sergate --config=config.json --web-dir=/home/wwwroot/default   
```

**【客户端配置】**    

客户端有两个版本，client-linux为普通linux，client-psutil为跨平台版，普通版不成功，换成跨平台版即可。        

#### 一、client-linux版配置：       
1、vim client-linux.py, 修改SERVER地址，username帐号， password密码        
2、python3 client-linux.py 运行即可。      

#### 二、client-psutil版配置:                
1、安装psutil跨平台依赖库       
```
`Debian/Ubuntu`: apt -y install python3-pip && pip3 install psutil    
`Centos/Redhat`: yum -y install python3-pip gcc python3-devel && pip3 install psutil      
`Windows`: https://pypi.org/project/psutil/    
```
2、vim client-psutil.py, 修改SERVER地址，username帐号， password密码       
3、python3 client-psutil.py 运行即可。    

服务器和客户端自行加入开机启动，或进程守护，或后台方式运行。 例如： nohup python3 client-linux.py &    

`extra scene (run web/ssview.py)`
![Shell View](https://dl.cpp.la/Archive/serverstatus-shell.png?version=2023)

## 集成新功能
1. https://github.com/lidalao/ServerStatus

#### 介绍
项目基于cppla版本ServerStatus， 增加如下功能：

更方便的节点管理, 支持增删改查
上下线通知（telegram）
Agent机器安装脚本改为systemd， 支持开机自启
由于未改动cppla版的任何代码，所以，我愿意把这个项目称为ServerStatus的小插件, 理论上它可以为任何版本的ServerStatus服务

#### 安装
在服务端复制以下命令，一键到底。请记得替换成你自己的YOUR_TG_CHAT_ID，YOUR_TG_BOT_TOKEN

其中，Bot token可以通过@BotFather创建机器人获取， Chat id可以通过@getuserID获取。
```bash
wget --no-check-certificate -O sss.sh https://raw.githubusercontent.com/jumploop/ServerStatus/master/shell/sss.sh && chmod +x ./sss.sh && ./sss.sh YOUR_TG_CHAT_ID YOUR_TG_BOT_TOKEN
```

安装成功后，web服务地址：http://ip:8081

# Make Better        

* BotoX：https://github.com/BotoX/ServerStatus
* mojeda: https://github.com/mojeda 
* mojeda's ServerStatus: https://github.com/mojeda/ServerStatus
* BlueVM's project: http://www.lowendtalk.com/discussion/comment/169690#Comment_169690
* lidalao：https://github.com/lidalao/ServerStatus

# Jetbrains    

<a href="https://www.jetbrains.com/?from=ServerStatus"><img src="https://resources.jetbrains.com/storage/products/company/brand/logos/jb_square.png" width="100px"></a>
