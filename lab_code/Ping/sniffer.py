import socket
import os


"""
使用 rawsocket 作为嗅探器;
HINT: 需要管理员（root）权限！
"""


def get_host_ip():
    """
    查询本机 IP 地址
    :return: ip 地址 or None
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]

        return ip
    finally:
        s.close()


def sniffer_open(host, prot, win=False):
    """
    创建一个嗅探器
    :param host: 监听主机
    :param prot: 创建套接字使用的协议
    :param win: 是否设置网卡为混淆模式，要求操作系统为 windows
    """
    sniffer = socket.socket(socket.AF_INET, socket.SOCK_RAW, prot)
    sniffer.bind((host, 0))
    # 设置捕获的包中包含 IP 首部
    sniffer.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
    
    if win:
        # 设置网卡混淆模式（windows操作系统）
        sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)

    return sniffer


if __name__ == '__main__':
    host = get_host_ip()
    if os.name == 'nt':
        sniffer = sniffer_open(host, socket.IPPROTO_IP, True)
    else:
        sniffer = sniffer_open(host, socket.IPPROTO_ICMP, False)

    pkt = sniffer.recvfrom(65565)
    print(pkt)