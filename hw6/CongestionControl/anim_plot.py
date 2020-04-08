import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from moviepy.video.io.bindings import mplfig_to_npimage
import moviepy.editor as mpy


def linear_interp(xdata, ydata, fillsize=10):
    """
    线性插值
    :param xdata: x轴数据
    :param ydata: y轴数据，与x轴数据长度相同
    :param fillsize: 相邻点之间线性插入点的个数
    :return xnew, ynew: 新的x, y轴数据
    """
    if fillsize <= 0:
        return xdata, ydata

    xnew = []
    ynew = []
    rawsize = len(xdata)

    for i in range(rawsize):
        if i == rawsize-1:
            # 最后一个点直接添加到新数据中
            xnew.append(xdata[i])
            ynew.append(ydata[i])
        else:
            xdelta = (xdata[i+1]-xdata[i]) / (fillsize+1)       # x轴两点数据的间隔距离
            ydelta = (ydata[i+1]-ydata[i]) / (fillsize+1)       # y轴两点数据的间隔距离

            for j in range(fillsize):
                xnew.append(xdata[i] + xdelta*(j+1))
                ynew.append(ydata[i] + ydelta*(j+1))

    return xnew, ynew


def anim_line(xdata, ydata, fig, fps=20, legend=None, c=['r', 'b', 'g']):
    """
    将数据点以直线连接并动画展示
    :param xdata: x轴数据（可包含多行，即多个折线图）
    :param ydata: y轴数据（可包含多行，即多个折线图）
    :param fig: 画布
    :param fps: 每秒帧数
    :param legend: 图例，字符串或字符串数组，数据包含多行时该参数为数组
    :param c: 连线的颜色，字符串或字符串数组数组，数据包含多行时该参数为数组，默认使用红蓝绿交替
    :return: 制作的动画 VideoClip 对象
    """
    if len(xdata.shape) == 1:
        xdata = xdata.reshape(1, xdata.shape[0])
        ydata = ydata.reshape(1, ydata.shape[0])
        if type(c) == str:
            c = [c]
        if type(legend) == str:
            legend = [legend]

    def animate(t):
        # 定义时刻 t 返回的帧（图片）
        i = int(fps*t)  # 计算当前帧的索引

        # 存放已绘制的对象
        lines = []
        for row in range(xdata.shape[0]):
            # 绘制每一行数据
            # 帧数超出索引值时绘制整幅图，即保持静止
            xrow = xdata[row][:int(i+1)]
            yrow = ydata[row][:int(i+1)]
            line = plt.plot(xrow, yrow, c=c[row%len(c)], label=legend[row], marker='.', mfc='w')

            lines.append(line)

        if legend is not None:
            # 显示图例在右下角图外面
            plt.legend(bbox_to_anchor=(1, -0.06), loc=0, borderaxespad=0)

        return mplfig_to_npimage(fig)

    duration = (xdata.shape[1] // fps) + 1  # 计算动画持续时间

    return mpy.VideoClip(animate, duration=duration)


if __name__ == "__main__":
    # 测试
    xdata = np.arange(0, 2*np.pi, 0.1)
    ydata = np.sin(xdata)

    xdata = np.array([xdata, xdata])
    ydata = np.array([ydata, ydata+1])
    fig = plt.figure(figsize=(8, 8))

    # xnew, ynew = linear_interp(xdata, ydata, 3)
    ani = anim_line(xdata, ydata, fig, fps=20, legend=['sin(x)', 'sin(x)+1'])
    # ani.write_videofile("animation.mp4", fps=20)      # 写入mp4文件
    ani.write_gif("animation.gif", fps=20, fuzz=20, loop=-1)        # 写入gif文件