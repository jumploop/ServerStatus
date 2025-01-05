#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function
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

# Python 2/3 兼容
try:
    # Python 2
    STRING_TYPES = (str, unicode)
except NameError:
    # Python 3
    STRING_TYPES = (str,)

# 基础配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(filename)s:%(lineno)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

# 常量定义
DEFAULTS = {'port': 35601, 'type': 'kvm', 'location': 'us', 'monthstart': '1'}

ACTIONS = {
    '0': ('退出', 'exit'),
    '1': ('查看', 'show'),
    '2': ('添加', 'add'),
    '3': ('删除', 'delete'),
    '4': ('更新', 'update'),
}


class ConfigManager(object):
    def __init__(self, args):
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

        self.servers = self._load_json(self.config_file)
        self.server_port = self._get_port()
        self.ip = self._get_ip()

    def _load_json(self, file_path):
        """安全加载JSON文件"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f, object_hook=unicode_convert)
        except Exception as e:
            logging.error("读取文件失败: %s", e)
            raise

    def _get_port(self):
        """获取服务端口"""
        try:
            if os.path.isfile(self.port_file):
                data = self._load_json(self.port_file)
                return data.get('server_port', DEFAULTS['port'])
        except Exception:
            pass
        return DEFAULTS['port']

    def _get_ip(self):
        """获取IP地址"""
        try:
            return requests.get(self.ip_url, timeout=5).text.strip()
        except Exception as e:
            logging.error("获取IP失败: %s", e)
            raise

    def _save_config(self):
        """保存配置"""
        self.servers['servers'].sort(key=lambda x: x['name'])
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.servers, f, ensure_ascii=False, indent=2, sort_keys=True)
        except Exception as e:
            logging.error("保存配置失败: %s", e)
            raise

    def _get_input(self, prompt, default=None, validator=None):
        """获取用户输入"""
        while True:
            value = input(prompt).strip()
            if not value and default is not None:
                return default
            if not validator or validator(value):
                return value
            print("输入无效，请重试")

    def show(self):
        """展示现有的监控节点"""
        print("---你的监控节点如下---\n")
        if len(self.servers['servers']) == 0:
            print('>>> 你好, 暂时没发现你有任何监控节点! <<<\n')
            print("-----------------")
            return

        for idx, item in enumerate(self.servers['servers']):
            print(
                "{0}. name: {1}, loc: {2}, type: {3}".format(
                    idx, item['name'], item['location'], item['type']
                )
            )

        print("\n")
        print("-----------------")

    def add(self):
        """添加节点"""
        try:
            # 获取节点名
            name = self._get_input(
                '>>>请输入节点名字：\n',
                validator=lambda x: x
                                    and not any(s['name'] == x for s in self.servers['servers']),
            )

            # 创建节点
            node = {
                'name': name,
                'type': self._get_input(
                    '>>>请输入{0}类型：[{1}]\n'.format(name, DEFAULTS['type']),
                    default=DEFAULTS['type'],
                ),
                'host': self._get_input(
                    '>>>请输入{0}主机名：[{1}]\n'.format(name, name), default=name
                ),
                'location': self._get_input(
                    '>>>请输入{0}位置：[{1}]\n'.format(name, DEFAULTS['location']),
                    default=DEFAULTS['location'],
                ),
                'monthstart': DEFAULTS['monthstart'],
                'username': uuid.uuid4().hex,
                'password': get_passwd(),
            }

            # 保存并重启
            self.servers['servers'].append(node)
            self._save_and_restart()

            # 显示安装命令
            print('>>>请复制以下命令在机器{0}安装agent服务'.format(node['name']))
            self._show_agent_cmd(node)

        except Exception as e:
            logging.error("添加节点失败: %s", e)

    def update(self):
        """更新节点"""
        try:
            # 获取节点索引
            idx = self._get_node_index()
            if idx is None:
                return

            node = self.servers['servers'][idx]
            self._show_agent_cmd(node)

            # 获取更新
            updates = {}
            fields = {
                'name': '名字',
                'location': '位置',
                'type': '类型',
                'monthstart': '月流量起始日',
            }

            for field, desc in fields.items():
                value = self._get_input(
                    '>>>请输入{0}新{1}：[{2}]\n'.format(node['name'], desc, node[field])
                )
                if value:
                    updates[field] = value

            if updates:
                self.servers['servers'][idx].update(updates)
                self._save_and_restart()
            else:
                print('未做任何更新')

        except Exception as e:
            logging.error("更新节点失败: %s", e)

    def delete(self):
        """删除节点"""
        try:
            idx = self._get_node_index()
            if idx is None:
                return

            node = self.servers['servers'][idx]
            if (
                    self._get_input(
                        '>>>请确认删除节点{0}？[y/N]\n'.format(node['name']), default='n'
                    ).lower()
                    != 'y'
            ):
                print("取消删除")
                return

            del self.servers['servers'][idx]
            self._save_and_restart()

        except Exception as e:
            logging.error("删除节点失败: %s", e)

    def _get_node_index(self):
        """获取有效的节点索引"""
        try:
            idx = self._get_input(
                "请输入节点标号：\n",
                validator=lambda x: x.isdigit()
                                    and 0 <= int(x) < len(self.servers['servers']),
            )
            return int(idx)
        except Exception:
            return None

    def _save_and_restart(self):
        """保存配置并重启"""
        self._save_config()
        self._restart_server()
        logging.info(">>>配置已保存，服务已重启")

    def _restart_server(self):
        """重启服务"""
        try:
            exe_command(self.restart_cmd, shell=True)
        except Exception as e:
            logging.error("重启服务失败: %s", e)

    def _show_agent_cmd(self, node):
        """显示agent安装命令"""
        print('```')
        print(
            'curl -L {0}/shell/serverstatus-agent.sh -o serverstatus-agent.sh && '
            'chmod +x serverstatus-agent.sh && '
            './serverstatus-agent.sh {1} {2} {3} {4}'.format(
                self.github_raw_url,
                self.ip,
                node['username'],
                node['password'],
                self.server_port,
            )
        )
        print('```')

    def run(self):
        """运行主程序"""
        while True:
            print("\n")
            print('- - - 欢迎使用最简洁的探针: Server Status - - -')
            print(
                '详细教程请参考：https://github.com/jumploop/ServerStatus/blob/master/doc/sss_plugin.md'
            )
            print("\n")
            self.show()
            action = self._get_input(
                '>>>请输入操作标号：'
                + ', '.join(
                    '{0}.{1}'.format(k, v[0]) for k, v in sorted(ACTIONS.items())
                )
                + '\n',
                validator=lambda x: x in ACTIONS,
            )

            if action == '0':
                break

            method = getattr(self, ACTIONS[action][1])
            method()

        logging.info("感谢使用!")


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
        logging.info('execute shell [%s]\n%s', cmdstr, shellresult)
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
    manager = ConfigManager(args)
    manager.run()


if __name__ == '__main__':
    main()
