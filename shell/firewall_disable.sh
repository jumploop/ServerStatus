#!/usr/bin/env bash

set -x

# 检查系统是否使用firewalld
if [ -x "$(command -v firewall-cmd)" ]; then
    # CentOS/RHEL 使用firewalld
    systemctl stop firewalld
    systemctl disable firewalld
    echo "Firewalld 已关闭"
fi

# 检查系统是否使用ufw
if [ -x "$(command -v ufw)" ]; then
    # Debian/Ubuntu 使用ufw
    ufw disable
    echo "UFW 已关闭"
fi

# 检查是否还有其他防火墙在运行
if [ -x "$(command -v iptables)" ]; then
    # 检查iptables状态，若有规则则清空
    iptables -F
    echo "iptables 防火墙规则已清空"
fi

echo "防火墙已关闭"
