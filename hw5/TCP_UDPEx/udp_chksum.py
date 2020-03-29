
import numpy as np
import warnings

warnings.filterwarnings("ignore")


"""
计算16位udp校验和：方式一，先求和，再取反
:param int16_arr 16位数据数组
:return np.uint32 类型数据，数值等于参数数组的校验和
"""
def cal_chksum16(int16_arr):
    # 先转为32位数据
    uint32_arr = np.array(int16_arr, dtype=np.uint32)
    # 直接计算和
    check_sum = uint32_arr.sum()
    # 将高16位数字加到低十六位上
    check_sum = np.bitwise_and(check_sum, np.uint32(0xffff)) + np.right_shift(check_sum, 16)
    check_sum += np.right_shift(check_sum, 16)

    # 取反后，只保留低十六位数字返回
    return np.bitwise_and(np.bitwise_not(check_sum), np.uint32(0xffff))


"""
计算16位udp校验和：方式二，先取反，再求和
:param int16_arr 16位数据数组
:return np.uint32 类型数据，数值等于参数数组的校验和
"""
def cal_chksum16_2(int16_arr):
    # 先转为32位数据，并进行取反，过程中只保留低16位数据
    uint32_arr = np.bitwise_and(np.bitwise_not(np.array(int16_arr, dtype=np.uint16)), np.uint32(0xffff))
    # 先直接用32位数据进行求和
    check_sum = uint32_arr.sum()
    # 将高16位数字加到低16位上
    check_sum = np.bitwise_and(check_sum, np.uint32(0xffff)) + np.right_shift(check_sum, 16)
    check_sum += np.right_shift(check_sum, 16)

    # 直接返回低16位数字
    return np.bitwise_and(check_sum, np.uint32(0xffff))


"""
接收方进行udp数据段的校验
:param int16_arr 16位数据数组，包含校验和字段
:return bool 类型，是否通过校验
"""
def check(int16_arr):
    # 反码和为0则通过校验
    return cal_chksum16(int16_arr) == 0


if __name__ == "__main__":
    test_arr = []

    test_arr.append(int('0110011001100000', base=2))
    test_arr.append(int('0101010101010101', base=2))
    test_arr.append(int('1000111100001100', base=2))

    check_sum = cal_chksum16(test_arr)
    print(np.binary_repr(check_sum, 32))

    another_way = cal_chksum16_2(test_arr)
    print(f'another way: {np.binary_repr(another_way, 32)}')

    test_arr.append(check_sum)
    print(f'check result: {check(test_arr)}')

    print('-'*30)
    first_two = cal_chksum16([test_arr[0], test_arr[1]])
    last_two = cal_chksum16([np.bitwise_and(np.bitwise_not(first_two), np.uint32(0xffff)), test_arr[2]])
    print(f'first two add: {np.binary_repr(np.bitwise_and(np.bitwise_not(first_two), np.uint32(0xffff)), 32)}')
    print(f'last two add: {np.binary_repr(last_two, 32)}')