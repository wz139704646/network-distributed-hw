import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from anim_plot import anim_line
from tcp_congestion_control import SimpleNetWorking, SimpleTCPSender, SimpleTCPReceiver

if __name__ == "__main__":
    net = SimpleNetWorking()
    sender = SimpleTCPSender()
    receiver = SimpleTCPReceiver()
    net.sender = sender
    net.receiver = receiver

    print('初始:')
    print(f'cwnd: {sender.cwnd}')
    print(f'ssthresh: {sender.ssthresh}')

    cwnds = [sender.cwnd]
    ssthreshs = [sender.ssthresh]
    for i in range(100):
        print('-'*30)
        print(f'轮次{i+1}:')
        net.round_trip()
        cwnds.append(sender.cwnd)
        ssthreshs.append(sender.ssthresh)
        print(f'cwnd: {sender.cwnd}')
        print(f'ssthresh: {sender.ssthresh}')
    print('\n\n')

    rounds = range(len(cwnds))
    xdata = np.array([rounds, rounds])
    ydata = np.array([cwnds, ssthreshs])

    xmax = xdata.max()
    xmin = xdata.min()
    ymax = ydata.max()
    ymin = ydata.min()
    fig = plt.figure(figsize=(8,8))
    plt.xlim(0.9*xmin, 1.1*xmax)
    plt.ylim(0.9*ymin, 1.1*ymax)
    plt.xlabel('round')
    plt.ylabel('cwnd/ssthresh (bytes)')
    
    anim = anim_line(xdata, ydata, fig, fps=25, legend=['cwnd', 'ssthresh'])

    anim.write_gif("congestion_control.gif", fps=25, fuzz=20)
    # anim.write_videofile("congestion_control.mp4", fps=25)