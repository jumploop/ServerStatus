#!/usr/bin/env bash

red='\033[0;31m'
green='\033[0;32m'
yellow='\033[0;33m'
plain='\033[0m'
export PATH=$PATH:/usr/local/bin

# check root
[[ $EUID -ne 0 ]] && echo -e "${red}错误: ${plain} 必须使用root用户运行此脚本！\n" && exit 1

install_soft() {
    (command -v yum >/dev/null 2>&1 && yum install "$*" -y) ||
        (command -v apt >/dev/null 2>&1 && apt install "$*" -y) ||
        (command -v pacman >/dev/null 2>&1 && pacman -Syu "$*") ||
        (command -v apt-get >/dev/null 2>&1 && apt-get install "$*" -y)

    if [[ $? != 0 ]]; then
        echo -e "${red}安装基础软件失败，稍等会${plain}"
        exit 1
    fi

    (command -v pip3 >/dev/null 2>&1 && pip3 install requests)
}

install_base() {
    (command -v curl >/dev/null 2>&1 && command -v wget >/dev/null 2>&1 && command -v pip3 >/dev/null 2>&1) || install_soft curl wget python3-pip python3
}

install_docker_compose() {
    install_base
    command -v docker-compose >/dev/null 2>&1
    if [[ $? != 0 ]]; then
        echo -e "正在安装 Docker Compose"
        wget --no-check-certificate -O /usr/local/bin/docker-compose "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" >/dev/null 2>&1
        if [[ $? != 0 ]]; then
            echo -e "${red}下载Compose失败${plain}"
            return 0
        fi
        chmod +x /usr/local/bin/docker-compose
        echo -e "${green}Docker Compose${plain} 安装成功"
    else
        echo -e "${green}Docker Compose${plain} 已安装"
    fi
}

install_docker_compose
