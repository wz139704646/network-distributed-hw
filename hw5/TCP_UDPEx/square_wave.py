import matplotlib
import matplotlib.pyplot as plt


"""
生成方波数据
:param bin_arr 0, 1数组，代表二进制序列
:return (x, y) 方波的x轴坐标和y轴坐标
"""
def gen_square_wave(bin_arr):   
    val_len = len(bin_arr) # 二进制串长度
    x_arr = [] # x轴坐标
    y_arr = [] # y轴坐标
    
    for i in range(val_len):
        # x轴两端端点
        x_ahead = i - 0.5
        x_later = i + 0.5

        x_arr.extend([x_ahead, x_later])
        y_arr.extend([bin_arr[i], bin_arr[i]])

    return x_arr, y_arr



if __name__ == '__main__':
    test_bin = [1, 0, 0, 1]
    x, y = gen_square_wave(test_bin)
    plt.plot(x, y)
    plt.savefig('test.png')