# 支持节点管理和监控的ServerStatus，它来了

原文地址：https://lidalao.com/archives/87
![img.png](../image/img.png)

## 介绍
项目地址：https://github.com/lidalao/ServerStatus  
项目基于cppla版本ServerStatus， 增加如下功能：

- 更方便的节点管理, 支持增删改查
- 上下线通知（telegram）
- Agent机器安装脚本改为systemd， 支持开机自启
## 安装
在服务端复制以下命令，一键到底。请记得替换成你自己的YOUR_TG_CHAT_ID和YOUR_G_BOT_TOKEN。

其中，Bot token可以通过@BotFather创建机器人获取， Chat id可以通过@getuserID获取。
```bash
wget --no-check-certificate https://raw.githubusercontent.com/jumploop/ServerStatus/master/shell/sss.sh && chmod +x ./sss.sh && sudo ./sss.sh YOUR_TG_CHAT_ID YOUR_TG_BOT_TOKEN
```

安装成功后，web服务地址：http://ip:8081

通过_sss.py脚本，可以很方便的进行节点的增删改查操作。特别的，添加新节点时，会有提示如何在新节点安装对应的agent服务。如果你想了解更多，可以看看进阶部分，不看也足够用。

## 进阶
由于没改动ServerStatus代码，理论上，任何版本的ServerStatus都可以用_sss.py来做管理， 都可以用bot-telegram.py来进行上下监控。

节点管理时，把_sss.py放到和config.json同一目录，运行python3 _sss.py即可,默认配置文件config.json和脚本在同一目录，ServerStatus服务重启命令为`docker-compose restart`。支持传入重启ServerStatus服务命令和config.json配置文件路径，改成你对应的服务启动方式和配置文件路径，例如用systemd,则传入`systemctl restart ServerStatus`。
```bash
python _sss.py -a 'systemctl restart ServerStatus' -c config.json
```

接下来是上下线监控服务，同样适用于任何版本的ServerStatus。 bot-telegram.py, 可以跑在任何机器上，不是必须在服务端，丢在家里nas上也成。

bot-telegram.py里面有三个配置信息，bot_token, cat_id和NODE_STATUS_URL, 改成你自己的对应信息，NODE_STATUS_URL需要改成你自己的探针web服务地址，例如，域名探针https://tz.test.com, 则改为https://tz.test.com/json/stats.json。配置修改完后，运行python3 bot-telegram.py即可开始监控
