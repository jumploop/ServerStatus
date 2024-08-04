#!/usr/bin/env bash
set -x
#========================================================
#   System Required: CentOS 7+ / Debian 8+ / Ubuntu 16+ /
#     Arch 未测试
#   Description: Server Status 监控安装脚本
#   Github: https://github.com/lidalao/ServerStatus
#========================================================

GITHUB_RAW_URL="https://raw.githubusercontent.com/jumploop/ServerStatus/master"
WORKDIR=/root/serverstatus
[ ! -d $WORKDIR ] && mkdir -p $WORKDIR

# 拉取 ServerStatus
red='\033[0;31m'
green='\033[0;32m'
yellow='\033[0;33m'
plain='\033[0m'
export PATH=$PATH:/usr/local/bin

pre_check() {
    command -v systemctl >/dev/null 2>&1
    if [[ $? != 0 ]]; then
        echo "不支持此系统：未找到 systemctl 命令"
        exit 1
    fi

    # check root
    [[ $EUID -ne 0 ]] && echo -e "${red}错误: ${plain} 必须使用root用户运行此脚本！\n" && exit 1
}

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

install_docker() {
    install_base
    command -v docker >/dev/null 2>&1
    if [[ $? != 0 ]]; then
        install_base
        echo -e "正在安装 Docker"
        bash <(curl -sL https://get.docker.com) >/dev/null 2>&1
        if [[ $? != 0 ]]; then
            echo -e "${red}下载Docker失败${plain}"
            exit 1
        fi
        systemctl enable docker.service
        systemctl start docker.service
        echo -e "${green}Docker${plain} 安装成功"
    else
        echo -e "${green}Docker${plain} 已安装"

    fi

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

modify_config() {
    if [[ $# -lt 2 ]]; then
        echo -e "${red}参数错误，未能正确提供tg bot信息，请手动修改docker-compse.yml中的bot信息 ${plain}"
        exit 1
    fi

    tg_chat_id=$1
    tg_bot_token=$2
    sss_adder="$(curl -s https://api.ipify.org | head -n 1):8080"

    echo -e "
    ${green}> 修改 docker-compose.yml${plain}
    ${green}1.${plain}  使用基于debian和nginx镜像的Server Status服务
    ${green}2.${plain}  使用基于debian和caddy镜像的Server Status服务
    ${green}3.${plain}  使用基于ubuntu和nginx镜像的Server Status服务
    ${green}4.${plain}  使用基于ubuntu和caddy镜像的Server Status服务
    ${green}0.${plain}  退出脚本
    "
    echo && read -erp "请输入选择 [0-4]:(默认: 1) " num
    num=${num:-1}
    case "${num}" in
    0)
        exit 0
        ;;

    1)
        sed -i "s/serverstatus_server$/&:latest/" docker-compose.yml
        ;;
    2)
        sed -i "s/serverstatus_server$/&:caddy/" docker-compose.yml
        ;;
    3)
        sed -i "s/serverstatus_server$/&:ubuntu-latest/" docker-compose.yml
        ;;
    4)
        sed -i "s/serverstatus_server$/&:ubuntu-caddy/" docker-compose.yml
        ;;
    *)
        echo -e "${red}请输入正确的数字 [0-2]${plain}"
        ;;
    esac
    sed -i "s/context: ../context: ./" docker-compose.yml
    sed -i "s#../server/config.json#./server/config.json#" docker-compose.yml
    sed -i "s#../web/json#./web/json#" docker-compose.yml
    sed -i "s/\${TG_CHAT_ID}/${tg_chat_id}/" docker-compose.yml
    sed -i "s/\${TG_BOT_TOKEN}/${tg_bot_token}/" docker-compose.yml
    sed -i "s/\${SERVER_DOMAIN}/${sss_adder}/" docker-compose.yml
    echo -e "> 修改config.json"
    sed -i "s#yourSMSurl#api.telegram.org/bot${tg_bot_token}/sendMessage?parse_mode=HTML\&disable_web_page_preview=true\&chat_id=${tg_chat_id}\&text=#g" server/config.json
}

clean_images() {
    echo -e "> 清理 Docker 镜像"
    if [ "$(docker ps -q -f name=bot4sss)" ]; then
        docker stop "$(docker ps -qa -f name=bot4sss)" && docker rm "$(docker ps -qa -f name=bot4sss)"
        echo -e "${green}bot4sss${plain} 已停止"
    fi
    if [ "$(docker ps -q -f name=serverstatus)" ]; then
        docker stop "$(docker ps -qa -f name=serverstatus)" && docker rm "$(docker ps -qa -f name=serverstatus)"
        echo -e "${green}serverstatus${plain} 已停止"
    fi
    if [ "$(docker network ls -f name=serverstatus -q)" ]; then
        docker network rm "$(docker network ls -f name=serverstatus -q)"
        echo -e "${green}network serverstatus-network${plain} 已删除"
    fi
    docker system prune -f --all
}

install_dashboard() {

    install_docker
    clean_images

    echo -e "> 安装面板"
    cd $WORKDIR || exit
    [ ! -d server ] && mkdir server
    [ ! -d web ] && mkdir web
    wget --no-check-certificate -O docker-compose.yml ${GITHUB_RAW_URL}/docker-compose/docker-compose-telegram.yml >/dev/null 2>&1
    wget --no-check-certificate -O Dockerfile ${GITHUB_RAW_URL}/Dockerfile >/dev/null 2>&1
    wget --no-check-certificate -O Dockerfile-telegram ${GITHUB_RAW_URL}/docker-compose/Dockerfile-telegram >/dev/null 2>&1
    wget --no-check-certificate -O bot-telegram.py ${GITHUB_RAW_URL}/plugin/bot-telegram.py >/dev/null 2>&1
    wget --no-check-certificate -O node_manager.py ${GITHUB_RAW_URL}/plugin/node_manager.py >/dev/null 2>&1
    [[ ! -e server/config.json ]] && wget --no-check-certificate -O server/config.json ${GITHUB_RAW_URL}/server/config.json >/dev/null 2>&1
    modify_config "$@"
    echo -e "> 启动面板"
    (docker-compose up -d) >/dev/null 2>&1
}

nodes_mgr() {
    python3 node_manager.py -c server/config.json
}

pre_check
install_dashboard "$@"
nodes_mgr
