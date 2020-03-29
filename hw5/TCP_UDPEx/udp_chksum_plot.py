import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from udp_chksum import cal_chksum16
from square_wave import gen_square_wave


"""
将数值转为二进制 0, 1 数组
:param val 拆分的数值
:return val的二进制形式表示. (0, 1组成的数组)
"""
def val_to_bitarr(val, len):
    bit_arr = []
    
    for i in range(len):
        bit_arr.append((val >> i) & 1)

    bit_arr.reverse()

    return bit_arr


if __name__ == '__main__':
    val1 = int('0110011001100000', base=2)
    val2 = int('0101010101010101', base=2)
    val3 = int('1000111100001100', base=2)

    bits1_x, bits1_y = gen_square_wave(val_to_bitarr(val1, 16))
    bits2_x, bits2_y = gen_square_wave(val_to_bitarr(val2, 16))
    bits3_x, bits3_y = gen_square_wave(val_to_bitarr(val3, 16))

    # 展示的结果不需要包含最后的取反过程，故将数值取反后保留低16位
    # 前两个比特字求校验和
    val_1_2 = np.bitwise_and(np.bitwise_not(cal_chksum16([val1, val2])), np.uint32(0xffff))
    bits_1_2_x, bits_1_2_y = gen_square_wave(val_to_bitarr(val_1_2, 16))

    # 再与第三个比特字求校验和
    val_1_2_3 = np.bitwise_and(np.bitwise_not(cal_chksum16([val_1_2, val3])), np.uint32(0xffff))
    bits_1_2_3_x, bits_1_2_3_y = gen_square_wave(val_to_bitarr(val_1_2_3, 16))

    fig = plt.figure(figsize=(12, 12))

    # 绘制第一次相加过程
    # 将方波分隔开看的更清楚
    bits1_y = np.array(bits1_y, dtype=np.int) + 4
    bits2_y = np.array(bits2_y, dtype=np.int) + 2
    # 绘图
    ax1 = fig.add_subplot(211)
    ax1.set_xlabel('bit')
    ax1.set_ylabel('0/1')
    ax1.set_title(f'(1) {np.binary_repr(val1, 16)} + {np.binary_repr(val2, 16)} = {np.binary_repr(val_1_2, 16)}')
    ax1.set_xticks(range(16))
    ax1.set_xticklabels(range(15, -1, -1))
    ax1.set_yticks(range(8))
    ax1.set_yticklabels([0, 1, 0, 1, 0, 1])
    ax1.plot(bits1_x, bits1_y, label='val1')
    ax1.plot(bits2_x, bits2_y, label='val2')
    ax1.plot(bits_1_2_x, bits_1_2_y, label='res1=val1+val2')
    ax1.legend(bbox_to_anchor=(1, -0.06), loc=0, borderaxespad=0) # 图例放置于右下角外侧

    # 绘制第二次相加过程
    # 将方波分隔开
    bits_1_2_y = np.array(bits_1_2_y, dtype=np.int) + 4
    bits3_y = np.array(bits3_y, dtype=np.int) + 2
    ax2 = fig.add_subplot(212)
    ax2.set_xlabel('bit')
    ax2.set_ylabel('0/1')
    ax2.set_title(f'(2) {np.binary_repr(val_1_2, 16)} + {np.binary_repr(val_1_2, 16)} = {np.binary_repr(val_1_2_3, 16)}')
    ax2.set_xticks(range(16))
    ax2.set_xticklabels(range(15, -1, -1))
    ax2.set_yticks(range(8))
    ax2.set_yticklabels([0, 1, 0, 1, 0, 1])
    ax2.plot(bits_1_2_x, bits_1_2_y, label='res1')
    ax2.plot(bits3_x, bits3_y, label='val3')
    ax2.plot(bits_1_2_3_x, bits_1_2_3_y, label='res2=res1+val3')
    ax2.legend(bbox_to_anchor=(1, -0.06), loc=0, borderaxespad=0) # 图例放置于右下角外侧

    # 调整子图间距，保存
    fig.subplots_adjust(hspace=0.5)
    plt.savefig('check_sum.png')