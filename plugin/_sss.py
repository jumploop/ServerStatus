#!/usr/bin/env python3
# coding: utf-8
# Create by : https://github.com/lidalao/ServerStatus
# 版本：0.0.1, 支持Python版本：2.7 to 3.9
# 支持操作系统： Linux, OSX, FreeBSD, OpenBSD and NetBSD, both 32-bit and 64-bit architectures

import json
import sys
import os
import requests
import random, string
import subprocess
import uuid
import argparse
from six.moves import input


CONFIG_FILE = "config.json"
PORT_FILE = "port.json"
GITHUB_RAW_URL = "https://raw.githubusercontent.com/jumploop/ServerStatus/master"
IP_URL = "https://api.ipify.org"
RESTART_SSS = "docker-compose restart"
jjs = {}
ip = ""
PORT = 35601


def get_server_port():
    if os.path.isfile(PORT_FILE):
        with open(PORT_FILE, 'r') as file:
            pjs = unicode_convert(json.load(file))
        return pjs.get('server_port')
    return PORT


def how2agent(user, passwd):
    port = get_server_port()
    print('```')
    print("\n")
    print(
        'curl -L {0}/shell/sss-agent.sh  -o sss-agent.sh && chmod +x sss-agent.sh && sudo ./sss-agent.sh {1} {2} {3} {4}'.format(
            GITHUB_RAW_URL, getIP(), user, passwd, port
        )
    )
    print("\n")
    print('```')


def unicode_convert(data, encode="utf-8"):
    """
    python2 json.loads会默认将字符串解析成unicode，因此需要自行转换为想要的格式
    https://stackoverflow.com/questions/956867/how-to-get-string-objects-instead-of-unicode-from-json
    """
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        return {
            unicode_convert(key, encode): unicode_convert(value)
            for key, value in data.items()
        }
    if isinstance(data, list):
        return [unicode_convert(element, encode) for element in data]
    # Python 3 compatible duck-typing
    # If this is a Unicode string, return its string representation
    if str(type(data)) == "<type 'unicode'>":
        return data.encode('utf-8')

    # If it's anything else, return it in its original form
    return data


def getIP():
    global ip
    if ip == "":
        ip = requests.get(IP_URL).content.decode('utf8')
    return ip


def restartSSS():
    p = subprocess.Popen(RESTART_SSS, stdout=subprocess.PIPE, shell=True)
    for line in p.stdout:
        print(line)
    p.wait()


def is_number(value):
    if hasattr(value, 'isnumeric'):
        return value.isnumeric()
    return value.isdigit()


def getPasswd():
    mima = []
    sz = '123456789'
    xzm = 'abcdefghijklmnopqrstuvwxyz'
    dzm = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    # tzf = '~!#@$%^&*?'
    # all = sz + xzm + dzm + tzf
    all = sz + xzm + dzm
    m1 = random.choice(sz)

    m2 = random.choice(xzm)
    m3 = random.choice(dzm)
    # m4 = random.choice(tzf)
    m5 = "".join(random.sample(all, 12))
    mima.append(m1)
    mima.append(m2)
    mima.append(m3)
    # mima.append(m4)
    mima.append(m5)
    random.shuffle(mima)
    a = "".join(mima)
    return a


def saveJJs():
    jjs['servers'] = sorted(jjs['servers'], key=lambda d: d['name'])
    with open(CONFIG_FILE, "w") as file:
        file.write(json.dumps(jjs, ensure_ascii=False, indent=2, sort_keys=True))


def _show():
    print("---你的jjs如下---")
    print("\n")
    if len(jjs['servers']) == 0:
        print('>>> 你好MJJ, 暂时没发现你有任何jj! <<<')
        print("\n")
        print("-----------------")
        return

    for idx, item in enumerate(jjs['servers']):
        print(
            "{0}. name: {1}, loc: {2}, type: {3}".format(
                idx, item['name'], item['location'], item['type']
            )
        )

    print("\n")
    print("-----------------")


def show():
    _show()
    _back()


def _back():
    print(">>>按任意键返回上级菜单")
    input()
    cmd()


def add():
    print('>>>请输入jj名字：')
    jjname = input()
    if jjname == "":
        print("输入有误")
        _back()
        return

    print('>>>请输入{0}位置：[{1}]'.format(jjname, "us"))
    jjloc = input()
    if jjloc == "":
        jjloc = "us"

    print('>>>请输入{0}类型：[{1}]'.format(jjname, "kvm"))
    jjtype = input()
    if jjtype == "":
        jjtype = "kvm"

    item = {}
    item['monthstart'] = "1"
    item['location'] = jjloc
    item['type'] = jjtype
    item['name'] = jjname
    item['username'] = uuid.uuid4().hex
    item['host'] = jjname
    item['password'] = getPasswd()
    jjs['servers'].append(item)
    saveJJs()

    print("操作完成，等待服务重启")
    restartSSS()

    print("添加成功!")
    _show()
    print('>>>请复制以下命令在机器{0}安装agent服务'.format(item['name']))
    how2agent(item['username'], item['password'])
    _back()


def update():
    print("请输入需要更新的jj标号：")
    idx = input()
    if not is_number(idx):
        print('无效输入,退出')
        _back()
        return

    if len(jjs['servers']) <= int(idx):
        print('输入无效')
        _back()
        return

    jj = jjs['servers'][int(idx)]
    print(
        '--- 面板更换ip时，请复制以下命令在机器{0}安装agent服务 ---'.format(jj['name'])
    )
    how2agent(jj['username'], jj['password'])

    print(
        '>>>请输入{0}新名字：[{1}] *中括号内为原值，按回车表示不做修改*'.format(
            jj['name'], jj['name']
        )
    )
    jjname = input()
    if "" != jjname:
        jjs['servers'][int(idx)]['name'] = jjname

    print('>>>请输入{0}新位置：[{1}]'.format(jj['name'], jj['location']))
    jjloc = input()
    if "" != jjloc:
        jjs['servers'][int(idx)]['location'] = jjloc

    print('>>>请输入{0}新类型：[{1}]'.format(jj['name'], jj['type']))
    jjtype = input()
    if "" != jjtype:
        jjs['servers'][int(idx)]['type'] = jjtype

    print('>>>请输入{0}新的月流量起始日：[{1}]'.format(jj['name'], jj['monthstart']))
    jjms = input()
    if "" != jjms:
        jjs['servers'][int(idx)]['monthstart'] = jjms

    if "" == jjname and "" == jjloc and "" == jjtype and "" == jjms:
        print('未做任何更新，直接返回')
        _back()
        return
    saveJJs()
    print("操作完成，等待服务重启")
    restartSSS()
    print("更新成功!")
    _show()
    _back()


def remove():
    print(">>>请输入需要删除的jj标号：")
    idx = input()
    if not is_number(idx):
        print('无效输入,退出')
        _back()
        return

    if len(jjs['servers']) <= int(idx):
        print('输入无效')
        _back()
        return

    print(
        '>>>请确认你需要删除的节点：{0}？ [Y/n]'.format(
            jjs['servers'][int(idx)]['name']
        )
    )
    yesOrNo = input()
    if yesOrNo == "n" or yesOrNo == "N":
        print("取消删除")
        _back()
        return

    del jjs['servers'][int(idx)]
    saveJJs()
    print("操作完成，等待服务重启")
    restartSSS()
    print("删除成功!")
    _show()
    _back()


def cmd():
    print("\n")
    print('- - - 欢迎使用最简洁的探针: Server Status - - -')
    print('详细教程请参考：https://lidalao.com/archives/87')
    print("\n")
    _show()
    print("\n")

    print('>>>请输入操作标号：1.查看, 2.添加, 3.删除, 4.更新, 0.退出')
    x = input()
    if not is_number(x):
        print('无效输入, 退出')
        return

    if 1 == int(x):
        show()
    elif 2 == int(x):
        add()
    elif 3 == int(x):
        remove()
    elif 4 == int(x):
        update()
    elif 0 == int(x):
        return
    else:
        print('无效输入, 退出')
        return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='管理探针服务端配置')
    parser.add_argument(
        '-c', '--config', default=CONFIG_FILE, help='Server config file path'
    )
    parser.add_argument(
        '-a', '--action', default=RESTART_SSS, help='Server restart method'
    )
    args = parser.parse_args()
    CONFIG_FILE = args.config
    RESTART_SSS = args.action
    file_exists = os.path.isfile(CONFIG_FILE)
    if file_exists is False:
        print("请在当前目录创建config.json!")
        sys.exit(1)

    with open(CONFIG_FILE, "r") as f:
        jjs = unicode_convert(json.load(f))
    cmd()
