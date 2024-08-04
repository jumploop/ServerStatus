#!/usr/bin/env python3
# coding: utf-8
# Create by : https://github.com/lidalao/ServerStatus
# 版本：0.0.1, 支持Python版本：2.7 to 3.9
# 支持操作系统： Linux, OSX, FreeBSD, OpenBSD and NetBSD, both 32-bit and 64-bit architectures

import json
import logging
import shlex
import sys
import os
import requests
import random
import string
import subprocess
import uuid
import argparse
from six.moves import input
from threading import Timer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(filename)s:%(lineno)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)


class NodesManager(object):

    def __init__(self, args):
        logging.info('received args: %s', args)
        self.github_raw_url = (
            "https://raw.githubusercontent.com/jumploop/ServerStatus/master"
        )
        self.ip_url = "https://api.ipify.org"
        self.port_file = "port.json"
        self.config_file = args.config
        self.restart_cmd = args.action
        if not os.path.isfile(self.config_file):
            logging.error("请在当前目录创建config.json!")
            sys.exit(1)
        self.servers = self.get_config()
        self.server_port = self.get_server_port()
        self.ip = self.get_ip()

    def run(self):
        actions = {
            '0': self.exit,
            '1': self.show,
            '2': self.add,
            '3': self.delete,
            '4': self.update,
        }
        print("\n")
        print('- - - 欢迎使用最简洁的探针: Server Status - - -')
        print(
            '详细教程请参考：https://github.com/jumploop/ServerStatus/blob/master/doc/sss插件.md'
        )
        print("\n")
        self._show()
        print("\n")

        print('>>>请输入操作标号：1.查看, 2.添加, 3.删除, 4.更新, 0.退出')
        x = input()
        if not is_number(x):
            print('无效输入, 退出')
            self.exit()
        if x in actions:
            actions.get(x)()
        else:
            print('无效输入, 退出')
            self.exit()

    def exit(self):
        """Exit the program"""
        logging.info("感谢您的使用!")
        sys.exit(0)

    def get_config(self):
        """get the config from config.json"""
        with open(self.config_file, "r") as f:
            data = unicode_convert(json.load(f))
        return data

    def get_ip(self):
        """get the ip address"""
        ip = requests.get(self.ip_url).content.decode('utf8')
        return ip

    def restart_server(self):
        """Restart the server"""
        exe_command(self.restart_cmd, shell=True)

    def get_server_port(self):
        """获取探针服务端端口"""
        if os.path.isfile(self.port_file):
            with open(self.port_file, 'r') as file:
                data = unicode_convert(json.load(file))
            return data.get('server_port')
        return 35601

    def add(self):
        """添加节点配置"""
        print('>>>请输入节点名字：')
        node_name = input()
        if node_name == "":
            print("输入有误")
            self._back()
            self.exit()

        print('>>>请输入{0}位置：[{1}]'.format(node_name, "us"))
        node_location = input()
        if node_location == "":
            node_location = "us"

        print('>>>请输入{0}类型：[{1}]'.format(node_name, "kvm"))
        node_type = input()
        if node_type == "":
            node_type = "kvm"

        item = {}
        item['monthstart'] = "1"
        item['location'] = node_location
        item['type'] = node_type
        item['name'] = node_name
        item['username'] = uuid.uuid4().hex
        item['host'] = node_name
        item['password'] = get_passwd()
        self.servers['servers'].append(item)
        self.save_config()

        logging.info("操作完成，等待服务重启")
        self.restart_server()
        logging.info("添加成功!")
        self._show()
        print('>>>请复制以下命令在机器{0}安装agent服务'.format(item['name']))
        self.how2agent(item['username'], item['password'])
        self._back()

    def update(self):
        """更新节点信息"""
        print("请输入需要更新的节点标号：")
        idx = input()
        if not is_number(idx):
            print('无效输入,退出')
            self._back()
            self.exit()
        index = int(idx)
        if len(self.servers['servers']) <= index:
            print('输入无效')
            self._back()
            self.exit()

        item = self.servers['servers'][index]
        print(
            '--- 面板更换ip时，请复制以下命令在机器{0}安装agent服务 ---'.format(
                item['name']
            )
        )
        self.how2agent(item['username'], item['password'])

        print(
            '>>>请输入{0}新名字：[{1}] *中括号内为原值，按回车表示不做修改*'.format(
                item['name'], item['name']
            )
        )
        node_name = input()
        if "" != node_name:
            self.servers['servers'][int(idx)]['name'] = node_name

        print('>>>请输入{0}新位置：[{1}]'.format(item['name'], item['location']))
        node_location = input()
        if "" != node_location:
            self.servers['servers'][int(idx)]['location'] = node_location

        print('>>>请输入{0}新类型：[{1}]'.format(item['name'], item['type']))
        node_type = input()
        if "" != node_type:
            self.servers['servers'][int(idx)]['type'] = node_type

        print(
            '>>>请输入{0}新的月流量起始日：[{1}]'.format(
                item['name'], item['monthstart']
            )
        )
        node_monthstart = input()
        if "" != node_monthstart:
            self.servers['servers'][index]['monthstart'] = node_monthstart

        if (
            "" == node_name
            and "" == node_location
            and "" == node_type
            and "" == node_monthstart
        ):
            print('未做任何更新，直接返回')
            self._back()
            self.exit()
        self.save_config()
        logging.info("操作完成，等待服务重启")
        self.restart_server()
        logging.info("更新成功!")
        self._show()
        self._back()

    def delete(self):
        """删除节点信息"""
        print(">>>请输入需要删除的节点标号：")
        idx = input()
        if not is_number(idx):
            print('无效输入,退出')
            self._back()
            self.exit()
        index = int(idx)
        if len(self.servers['servers']) <= index:
            print('输入无效')
            self._back()
            self.exit()

        print(
            '>>>请确认你需要删除的节点：{0}？ [Y/n]'.format(
                self.servers['servers'][index]['name']
            )
        )
        confirm = input()
        if confirm in "nN":
            print("取消删除")
            self._back()
            self.exit()

        del self.servers['servers'][index]
        self.save_config()
        logging.info("操作完成，等待服务重启")
        self.restart_server()
        logging.info("删除成功!")
        self._show()
        self._back()

    def save_config(self):
        """Save the configuration"""
        self.servers['servers'] = sorted(
            self.servers['servers'], key=lambda d: d['name']
        )
        with open(self.config_file, "w") as file:
            file.write(
                json.dumps(self.servers, ensure_ascii=False, indent=2, sort_keys=True)
            )

    def how2agent(self, user, passwd):
        """返回安装agent的命令"""
        print('```')
        print("\n")
        print(
            'curl -L {0}/shell/sss-agent.sh  -o sss-agent.sh && chmod +x sss-agent.sh && sudo ./sss-agent.sh {1} {2} {3} {4}'.format(
                self.github_raw_url, self.ip, user, passwd, self.server_port
            )
        )
        print("\n")
        print('```')

    def _show(self):
        """展示现有的监控节点"""
        print("---你的监控节点如下---")
        print("\n")
        if len(self.servers['servers']) == 0:
            print('>>> 你好, 暂时没发现你有任何监控节点! <<<')
            print("\n")
            print("-----------------")
            self.exit()

        for idx, item in enumerate(self.servers['servers']):
            print(
                "{0}. name: {1}, loc: {2}, type: {3}".format(
                    idx, item['name'], item['location'], item['type']
                )
            )

        print("\n")
        print("-----------------")

    def show(self):
        self._show()
        self._back()

    def _back(self):
        print(">>>按任意键返回上级菜单")
        input()
        self.run()


def exe_command(cmdstr, timeout=1800, shell=False):
    if shell:
        command = cmdstr
    else:
        command = shlex.split(cmdstr)
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell
    )
    timer = Timer(timeout, process.kill)
    try:
        timer.start()
        stdout, stderr = process.communicate()
        retcode = process.poll()
        result = (stdout + stderr).strip()
        shellresult = (
            result if isinstance(result, str) else str(result, encoding='utf-8')
        )
        logging.info('execute shell [%s], shell result is\n%s', cmdstr, shellresult)
        return retcode, shellresult
    finally:
        timer.cancel()


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


def is_number(value):
    if hasattr(value, 'isnumeric'):
        return value.isnumeric()
    return value.isdigit()


def get_passwd():
    passwd = []
    # all = string.digits + string.ascii_letters + string.punctuation
    all = string.digits + string.ascii_letters
    m1 = random.choice(string.digits)
    m2 = random.choice(string.ascii_lowercase)
    m3 = random.choice(string.ascii_uppercase)
    # m4 = random.choice(string.punctuation)
    m5 = "".join(random.sample(all, 12))
    passwd.append(m1)
    passwd.append(m2)
    passwd.append(m3)
    # mima.append(m4)
    passwd.append(m5)
    random.shuffle(passwd)
    return "".join(passwd)


def get_parser():
    parser = argparse.ArgumentParser(description='管理探针服务端配置')
    parser.add_argument(
        '-c', '--config', default='config.json', help='Server config file path'
    )
    parser.add_argument(
        '-a', '--action', default='docker-compose restart', help='Server restart method'
    )
    args = parser.parse_args()
    return args


def main():
    args = get_parser()
    manager = NodesManager(args)
    manager.run()


if __name__ == '__main__':
    main()
