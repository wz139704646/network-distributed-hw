import tcp_settings
import random
from enum import Enum


# TODO: 考虑将 cwnd 的增长封装，及时对其大小与 ssthresh 比较，及时进入 CA 状态
# Congestion Control State
class CCState(Enum):
    SS = 1      # Slow Start 慢启动
    CA = 2      # Congestion Avoiding 拥塞避免
    FR = 3      # Fast Recovery 快恢复


# TCP reno
class SimpleTCPSender:
    def __init__(self):
        self.__estimate_rtt = 0             # 预估RTT
        self.__dev_rtt = None               # 偏差估计
        self.timeout_interval = 10          # 初始默认超时时间10s

        self.dup_ack = 0                                # 重复 ACK 个数
        self.cwnd = tcp_settings.MSS                    # 初始窗口大小 1MSS
        self.ssthresh = tcp_settings.ini_ssthresh       # 初始门限
        self.ccstate = CCState.SS                       # 初始状态 Slow Start


    # 状态转变
    def set_state(self, new_stat):
        print(f'状态 {self.ccstate.name} -> {new_stat.name}')
        self.ccstate = new_stat


    # 更新预估RTT
    def update_estimate(self, sample_rtt):
        alpha = tcp_settings.alpha
        self.__estimate_rtt = (1-alpha)*self.__estimate_rtt + alpha*sample_rtt


    # 更新偏差
    def update_dev(self, sample_rtt):
        beta = tcp_settings.beta
        self.__dev_rtt = (1-beta)*self.__dev_rtt + beta*abs(self.__estimate_rtt-sample_rtt)


    # 更新超时时间
    def update_timeout(self, sample_rtt):
        print(f'sample RTT {sample_rtt}')
        if self.__estimate_rtt == 0:
            self.__estimate_rtt = sample_rtt
        else:
            self.update_estimate(sample_rtt)

        if self.__dev_rtt is None:
            self.__dev_rtt = 0.125 * self.__estimate_rtt  # 初始时安全余量设置为 50% 的预估时间
        else:
            self.update_dev(sample_rtt)

        self.timeout_interval = self.__estimate_rtt + 4*self.__dev_rtt
        print(f'timeout interval 更新为 {self.timeout_interval}')

    # 超时事件发生
    def on_timeout(self):
        print('发生超时')
        self.ssthresh = self.cwnd / 2
        self.cwnd = tcp_settings.MSS
        self.dup_ack = 0

        if self.ccstate != CCState.SS:
            self.set_state(CCState.SS)       # 回到慢启动


    def on_3dupACK(self):
        print('收到3个重复ACK')
        self.ssthresh = self.cwnd / 2
        self.cwnd = self.ssthresh + 3 * tcp_settings.MSS

        self.set_state(CCState.FR)       # 进入快速回复阶段


    def on_dupACK(self, err_prob):
        """
        收到重复 ACK 的动作
        :param err_prob: ACK受损概率
        """
        if random.random() < err_prob:
            print('重复ACK受损')
            return
        
        print('收到重复的ACK')
        if self.ccstate == CCState.SS or self.ccstate == CCState.CA:
            # 处于慢启动 或 拥塞避免阶段
            self.dup_ack += 1
        else:
            # 处于快速恢复阶段
            self.cwnd += tcp_settings.MSS

        if self.ccstate != CCState.FR and self.dup_ack == 3:
            # 产生3重复ACK
            self.on_3dupACK()


    def on_newRTT(self, sample_RTT, newACKs, dupACKs, err_prob):
        """
        新的一轮回复事件对应动作
        :param sample_RTT: 采样到的 RTT 时间
        :param newACKs: 收到的新的ACK数量
        :param dupACKs: 收到的重复ACK数量
        :param err_prob: ACK损坏的概率
        """
        if sample_RTT > self.timeout_interval:
            # 采样RTT超过超时时间
            print(f'当前超时时间 {self.timeout_interval}')
            print(f'sample RTT {sample_RTT}')
            self.on_timeout()
            # 更新超时时间
            self.update_timeout(sample_RTT)
            return
        
        # 更新超时时间
        self.update_timeout(sample_RTT)

        sent = self.cwnd // tcp_settings.MSS    # 收到回复前发送的数量
        # 先收到 newACKs 个新的 ACK
        for i in range(newACKs):
            if random.random() < err_prob:
                # ACK 受损
                if i < newACKs - 1 or dupACKs == 0:
                    print('中间的新ACK受损，或最后的ACK受损且无重复ACK')
                    # 中间的ACK损坏，直接超时
                    self.on_timeout()
                    return
                else:
                    print('最后的新ACK受损且无重复ACK')
                    # 最后一个新ACK损坏，之后重复的 ACK 中的一个被当作新的 ACK
                    i -= 1
                    dupACKs -= 1
                    continue
            if self.ccstate == CCState.SS:
                # 处于慢启动阶段
                self.cwnd += tcp_settings.MSS       # 每一ACK加 1MSS，整个RTT翻倍
                self.dup_ack = 0
                if self.cwnd >= self.ssthresh:
                    self.set_state(CCState.CA)       # 超过阈值，进入拥塞避免阶段
            elif self.ccstate == CCState.CA:
                # 处于拥塞避免状态
                self.cwnd += tcp_settings.MSS * (tcp_settings.MSS / self.cwnd)      # 整个RTT后增加约 1MSS
                self.dup_ack = 0
            else:
                # 处于快速恢复阶段
                self.cwnd = self.ssthresh
                self.dup_ack = 0
                self.set_state(CCState.CA)      # 进入拥塞避免阶段
        
        # 收到 dupACKs 个重复的 ACK
        for i in range(dupACKs):
            self.on_dupACK(err_prob)

        if sent > (newACKs + dupACKs):
            # 发生丢包，超时
            self.on_timeout()


    def send(self):
        # 返回发送的包数量
        return int(self.cwnd // tcp_settings.MSS)


    def pkt_size(self):
        # 简化，每一个包大小都为最大
        return tcp_settings.MSS


class SimpleTCPReceiver:
    def __init__(self):
        pass


    def receive(self, pkts, err_prob):
        """
        模拟简化的接收事件，遍历收到的包
        :param pkts: 收到的包的个数
        :param err_prob: 包出错的概率
        :return: 返回确认收到的包的序号，一个都没正确收到则返回-1
        """
        for i in range(pkts):
            r = random.random()
            if r < err_prob:
                # 以一定概率收到错误的包
                print(f'接收方收到错误的包 {pkts} -> {i}')
                return i-1

        return pkts - 1


# 简单网络，只有一个发送端和一个接收端
class SimpleNetWorking:
    def __init__(self):
        self.sender = None
        self.receiver = None


    def round_trip(self):
        if not all([self.sender, self.receiver]):
            return
        
        pkts = self.sender.send()
        inflight = pkts * self.sender.pkt_size()

        print(f'发送了 {pkts} 个 pkts')

        RTT = tcp_settings.RTprop       # 未超出“管道”容量时的往返时间
        delivered = pkts

        # 可用“管道”容量在 0-1 BDP 间变动
        BDP_avail = random.gauss(tcp_settings.BDP / 2, tcp_settings.BDP / 6)
        BDP_avail = max([BDP_avail, 0])
        print(f'假设可用 BDP {BDP_avail}')

        if inflight > 2 * BDP_avail:
            # 超出“管道”容量
            print('inflight 超出 2BDP')
            exceed = inflight - 2 * BDP_avail    # 超出部分
            queued_pkts = ( exceed // self.sender.pkt_size() ) + 1   # 缓存的包个数
            
            btl_buf_avail = tcp_settings.btl_bufsize
            if BDP_avail < 0.01 * tcp_settings.BDP:
                # 可用 BDP 低于 1% 时假设队列中有其他包，在 0-1 btl_bufsize 间变动
                btl_buf_avail = random.gauss(btl_buf_avail / 2, btl_buf_avail / 6)
                btl_buf_avail = max([btl_buf_avail, 0])
            print(f'当前队列可用大小 {btl_buf_avail}')
            if queued_pkts * self.sender.pkt_size() > btl_buf_avail:
                # 超出瓶颈路由器的缓存大小
                print('超出缓存，发生丢包')
                exceed = queued_pkts * self.sender.pkt_size() - tcp_settings.btl_bufsize
                delivered = int(pkts - ( (exceed // self.sender.pkt_size()) + 1 ))    # 发生丢包，假设丢弃的是序号靠后的

            RTT = delivered * self.sender.pkt_size() / tcp_settings.btl_bw       # 缓存相当于增长管道

        RTT_var_rate = random.gauss(tcp_settings.RTT_var_e, tcp_settings.RTT_var_std)       # 实际略有变动
        RTT_var_rate = max([RTT_var_rate, tcp_settings.RTT_var_e - 3 * tcp_settings.RTT_var_std])

        received = self.receiver.receive(delivered, tcp_settings.corrupt_prob) + 1       # 正确收到的包个数
        self.sender.on_newRTT(RTT, received, delivered - received, tcp_settings.corrupt_prob)

        print(f'成功交付 {delivered} 个 pkts')
        print(f'收到 {received} 个 pkts')


if __name__ == "__main__":
    net = SimpleNetWorking()
    sender = SimpleTCPSender()
    receiver = SimpleTCPReceiver()
    net.sender = sender
    net.receiver = receiver

    print('初始:')
    print(f'cwnd: {sender.cwnd}')
    print(f'ssthresh: {sender.ssthresh}')

    for i in range(500):
        print('-'*30)
        print(f'轮次{i+1}:')
        net.round_trip()
        print(f'cwnd: {sender.cwnd}')
        print(f'ssthresh: {sender.ssthresh}')