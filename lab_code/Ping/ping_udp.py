import time
import struct
import socket
import select
import random
import settings
import sniffer


"""
如何发送udp分组，并接受服务端返回的icmp分组：
1. 使用udp套接字接收
    若使用udp套接字接收，一般情况下udp分组会忽略icmp错误，故要接收icmp分组的错误，
    有两种方式：
    (1) 使用 connect，将udp套接字与远端连接，可以使用send进行数据发送，之后使用
    recvfrom时，若收到icmp错误信息，会直接返回-1，这时通过获取errno可以判断错误
    的类型。
    (2) 使用setsockopt，将IP_RECVERR设为1，之后使用sendto发送数据，并在recvfrom
    时，若收到icmp错误信息，会直接返回-1，通过获取errno可以判断错误类型。
2. 使用两个套接字
    使用udp套接字发送，使用rawsocket接收，此时rawsocket相当于嗅探器的功能，需要进
    行一定的设置（包含IP头、设置网卡混淆模式）并需要提升权限。
"""


HOST = sniffer.get_host_ip()


def udp_open_socket(ttl):
    """
    创建具有特定 TTL 的 UDP 套接字
    :param ttl: 需要设置的 IP TTL 数
    :return: socket 对象，使用 UDP 协议
    """
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0) # UDP 套接字
    udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl) # 设置 TTL 值

    return udp_socket


def icmp_open_socket(host):
    """
    创建嗅探 ICMP 分组的套接字
    :param host: 监听本地的ip地址
    :return: socket 对象，使用 ICMP 协议
    """
    icmp_socket = sniffer.sniffer_open(host, socket.IPPROTO_ICMP, True)

    return icmp_socket


def udp_request_ping(send_socket, dst_addr, dst_port, payload):
    """
    发送探测包
    :param send_socket: 用来发送的套接字，使用 UDP 协议
    :param dst_addr: 发送探测包的目的 IP 地址
    :param dst_port: 发送探测包的目的端口号
    :param payload: 发送的数据负载
    :return: 发送时的时间
    """
    send_request_ping_time = time.time()
    # 向套接字中发送数据
    send_socket.sendto(payload,(dst_addr,dst_port))
    return send_request_ping_time


def reply_ping(recv_socket, dst_addr, time_sent, timeout = 5):
    """
    接收 Ping 回复
    :param recv_socket: 用来接收回复分组的套接字
    :param dst_addr: 回复分组的源 IP 地址（ping发送的目的 IP 地址）
    :param time_sent: ping 探测包发送的时间
    :param timeout: 等待的最大超时时间
    :return: tuple or None，None 代表超时，否则(flag, delay, ttl/addr [, recv_length])
        当遇到 ttl 超时分组时，flag = False，返回内容 (flag, delay, addr)，delay为rtt，
        addr 为发送超时分组的地址；
        当遇到目的地不可达分组时，flag = True，返回内容 (flag, delay, ttl, recv_length)，
        delay 为 rtt，ttl 为收到的分组的 IP ttl 字段，recv_length 为收到的分组长度。
    """
    timeleft = timeout
    
    while True:
        started_select = time.time()
        what_ready = select.select([recv_socket], [], [], timeleft)
        wait_for_time = (time.time() - started_select)
        if what_ready[0] == []:
            # Timeout
            return

        timeleft = timeleft - wait_for_time
        time_received = time.time()
        delay = time_received - time_sent # 计算 rtt

        # 接收并解析包
        recv_pkt, addr = recv_socket.recvfrom(65535)
        icmp_header = recv_pkt[20:28]
        icmp_type, icmp_code, checksum, packetID, sequence = struct.unpack('!bbHHh', icmp_header)
        # 判断 ICMP 包类型
        if icmp_type == settings.ICMP_TYPE_UNREACHABLE and icmp_code == settings.ICMP_CODE_PORT_UNREACHABLE and addr[0] == dst_addr:
            # 返回不可达，说明到达目的地
            tot_length = struct.unpack('!H', recv_pkt[2:4])[0] # 总长度
            recv_length = tot_length - 56 # tot-2*ip_hdr-2*udp/icmp_hdr=data length
            ttl = ord(struct.unpack('!c', recv_pkt[8: 9])[0]) # 获取ttl
            return (True, delay, ttl, recv_length)
        elif icmp_type == settings.ICMP_TYPE_TTL_EXCEEDED and icmp_code == settings.ICMP_CODE_TTL_EXCEEDED_TRANSIT:
            # TTL 过期
            old_dest = socket.inet_ntoa(recv_pkt[44:48])
            if old_dest == dst_addr:
                # 发送到目标的过期包
                return (False, delay, addr[0])

        # 其他类型错误无视
        if timeleft <= 0:
            return


def udp_ping_once(dst_addr, dst_port, pkt_size, ttl, timeout):
    """
    进行一次 ping 探测，使用 UDP 协议
    :param dst_addr: 探测的目的 IP 地址
    :param dst_port: 探测的目的 UDP 端口
    :param pkt_size: 探测包的大小
    :param ttl: 探测包的 IP ttl 数
    :param timeout: 等待响应的超时时间
    :return: tuple or None，None 代表超时，否则(flag, delay, ttl/addr [, recv_length])
        当遇到 ttl 超时分组时，flag = False，返回内容 (flag, delay, addr)，delay为rtt，
        addr 为发送超时分组的地址；
        当遇到目的地不可达分组时，flag = True，返回内容 (flag, delay, ttl, recv_length)，
        delay 为 rtt，ttl 为收到的分组的 IP ttl 字段，recv_length 为收到的分组长度。
    """
    if pkt_size == 0 or ttl == 0 or timeout <= 0:
        return

    icmp_socket = icmp_open_socket(HOST) # 创建接收套接字
    udp_socket = udp_open_socket(ttl) # 创建发送套接字

    payload = b'a'*pkt_size # 可变长度payload

    send_time = udp_request_ping(udp_socket, dst_addr, dst_port, payload) # 发送 UDP 探测包
    result = reply_ping(icmp_socket, dst_addr, send_time, timeout) # 捕获 ICMP 响应
    
    # 关闭套接字
    udp_socket.close()
    icmp_socket.close()

    return result


def udp_ping(host, pkt_num=settings.PING_PKT_NUM, pkt_size=settings.PING_PKT_SIZE,
             ttl=settings.PING_PKT_TTL, timeout=settings.PING_TIMEOUT):
    """
    ping 命令，使用 UDP 包探测
    :param host: 探测的目的主机
    :param pkt_num: 总共发送的探测包数量
    :param pkt_size: 探测包的大小
    :param ttl: 探测包的 IP ttl 数
    :param timeout: 等待响应的超时时间
    """
    if pkt_num <= 0 or pkt_size <= 0 or ttl <= 0:
        return

    dst_addr = socket.gethostbyname(host) # 获取主机 IP

    # 准备开始
    print("now Ping {0} [{1}] with {2} bytes of data:".format(host, dst_addr, pkt_size))

    loss = 0 # 损失包数
    tot_rtt = 0 # 延迟之和
    min_rtt = 0x7fffffff # 最小的rtt
    max_rtt = -1 # 最大的rtt
    for i in range(pkt_num):
        rand_port = random.randint(settings.UDP_PING_PORT_LOWER, settings.UDP_PING_PORT_HIGHER)
        # 发起一次 ping 探测
        result = udp_ping_once(dst_addr, rand_port, pkt_size, ttl, timeout)
        
        if not result or not result[0]:
            # 超时或 ttl 到期
            print("request timed out.")
            loss += 1
        else:
            # 收到不可达分组
            delay = int(result[1]*1000)
            TTL = result[2]
            bytes = result[3]
            print("reply from {0}: byte(s)={1} deley={2}ms TTL={3}".format(dst_addr, bytes, delay, TTL))
            
            # 记录 rtt
            tot_rtt += delay
            if delay < min_rtt:
                min_rtt = delay
            if delay > max_rtt:
                max_rtt = delay

        time.sleep(1) # 隔一秒

    # 统计
    print()
    print('-'*60)
    print("Packet: sent = {0} received = {1} lost = {2}".format(pkt_num, pkt_num-loss, loss))
    if loss != pkt_num:
        print("RTT(ms): min = {0}ms avg = {1}ms max = {2}ms".format(min_rtt, int(tot_rtt/(pkt_num-loss)), max_rtt))


if __name__ == "__main__":
    # 测试 ping 程序
    udp_ping("www.pingplotter.com")