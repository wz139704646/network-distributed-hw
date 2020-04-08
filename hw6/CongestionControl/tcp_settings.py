MSS = 1460                              # 最大报文段长度 1460 Bytes
ini_ssthresh = 64 * 1024                # 初始慢启动阈值 64KB

# 链路相关
RTprop = 40 * 0.001                     # 最小时延 40ms
btl_bw = 100 * (10 ** 6) / 8            # 瓶颈链路物理带宽 100Mbps
btl_bufsize = 32 * 1024                 # 瓶颈链路缓冲区大小
BDP = btl_bw * RTprop                   # 带宽时延积
corrupt_prob = 0.001                    # 包损坏的概率

# RTT采样相关
alpha = 0.125                           # 指数加权移动平均系数
beta = 0.25                             # 安全余量加权系数
RTT_var_e = 1.05                        # RTT 变动的期望
RTT_var_std = 0.05                      # RTT 变动的标准差，3 sigma 范围在 0.9 - 1.2