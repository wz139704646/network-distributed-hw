import os
import sys
import time
import socket
import random
from functools import partial
from concurrent.futures import ThreadPoolExecutor

import PyQt5
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView
from PyQt5.QtWidgets import QMessageBox, QTableWidget, QAbstractItemView

import settings
import ping_udp
from Ping_form import Ui_MainWindow


class TracerouteGUI(QMainWindow, Ui_MainWindow):
    """
    Traceroute GUI 类
    """

    def __init__(self):
        """
        初始化
        """
        super(TracerouteGUI, self).__init__()
        self.setupUi(self)
        self.init_table() # 初始化表格
        self.init_input() # 初始化输入值
        self.init_handler() # 初始化句柄

        self.pool = ThreadPoolExecutor(max_workers=4)
        
        return

    def init_table(self):
        """
        初始化表格
        """
        # 添加列
        self.tbWidgetRoute.setColumnCount(6)
        self.tbWidgetRoute.setHorizontalHeaderLabels(
            ['hop', 'packet loss %', 'IP', 'Name', 'Avg(ms)', 'Cur(ms)']
        )

        # 设置表格头为伸缩模式
        self.tbWidgetRoute.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # 设置表格不可编辑
        self.tbWidgetRoute.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        return

    def init_input(self):
        """
        初始化输入数值
        """
        self.lneditPktSize.setText(str(settings.PING_PKT_SIZE))
        self.lneditDefaultPort.setText("{0}-{1}".format(settings.UDP_PING_PORT_LOWER, settings.UDP_PING_PORT_HIGHER))
        self.lneditTimeout.setText(str(settings.TRACE_TIMEOUT))
        self.lneditMaxHops.setText(str(settings.TRACE_MAX_HOPS))

        return

    def init_handler(self):
        """
        初始化空间事件处理句柄
        """
        self.btnPing.clicked.connect(self.start_trace)
        self.radbtnFixed.toggled.connect(partial(self.select_port_mode, self.radbtnFixed))
        self.radbtnDefault.toggled.connect(partial(self.select_port_mode, self.radbtnDefault))

        return

    def start_trace(self):
        """
        Ping 按钮点击事件，开始追踪路由
        """
        if not self.check_input():
            # 输入有误
            QMessageBox.information(self, 'Hint', 'Please check the input!', QMessageBox.Ok, QMessageBox.Ok)
            return
        self.disable_all()
        self.clear_table()
        self.pool.submit(self.trace).add_done_callback(lambda res: self.enable_all())

        return

    def select_port_mode(self, btn):
        """
        port radio button 被点击，选择路由输入方式
        """
        if btn == self.radbtnDefault and btn.isChecked():
            # 禁用 fixed port 输入框
            self.lneditFixedPort.setDisabled(True)
        elif btn == self.radbtnFixed and btn.isChecked():
            # 开启使用 fixed port 输入框
            self.lneditFixedPort.setEnabled(True)

        return

    def check_input(self):
        """
        检查输入值的正确性
        """
        if self.lneditTarget.text() == "":
            return False
        if not str.isnumeric(self.lneditPktSize.text()):
            return False
        if not str.isnumeric(self.lneditMaxHops.text()):
            return False
        if self.radbtnFixed.isChecked():
            if not str.isnumeric(self.lneditFixedPort.text()) or int(self.lneditFixedPort.text()) > 65535:
                return False
        try:
            timeout = float(self.lneditTimeout.text())
            if timeout < 0:
                return False
        except ValueError:
            return False

        return True

    def disable_all(self):
        """
        禁用所有输入控件
        """
        self.lneditTarget.setDisabled(True)
        self.lneditPktSize.setDisabled(True)
        self.lneditMaxHops.setDisabled(True)
        self.lneditTimeout.setDisabled(True)
        if self.radbtnFixed.isChecked():
            self.lneditFixedPort.setDisabled(True)
        self.radbtnFixed.setDisabled(True)
        self.radbtnDefault.setDisabled(True)
        self.btnPing.setDisabled(True)

        return

    def enable_all(self):
        """
        启用所有输入控件
        """
        self.lneditTarget.setEnabled(True)
        self.lneditPktSize.setEnabled(True)
        self.lneditMaxHops.setEnabled(True)
        self.lneditTimeout.setEnabled(True)
        if self.radbtnFixed.isChecked():
            self.lneditFixedPort.setEnabled(True)
        self.radbtnFixed.setEnabled(True)
        self.radbtnDefault.setEnabled(True)
        self.btnPing.setEnabled(True)

        return

    def clear_table(self):
        """
        清空表格内容
        """
        self.tbWidgetRoute.clearContents()

        return

    def trace(self):
        print('trace start')
        
        try:
            # 获取输入信息
            max_hops = int(self.lneditMaxHops.text())
            target = self.lneditTarget.text()
            pkt_size = int(self.lneditPktSize.text())
            timeout = int(self.lneditTimeout.text())
            probes = settings.TRACE_MAX_PORBES
            if self.radbtnFixed.isChecked():
                port_lo = int(self.lneditFixedPort.text())
                port_hi = port_lo + 1
            else:
                port_lo = settings.UDP_PING_PORT_LOWER
                port_hi = settings.UDP_PING_PORT_HIGHER
            # 获取目标 IP 地址
            dst_addr = socket.gethostbyname(target)

            for i in range(max_hops):
                # 插入新行
                self.tbWidgetRoute.insertRow(i)
                # 添加跳数
                new_item = QTableWidgetItem(str(i+1))
                self.tbWidgetRoute.setItem(i, 0, new_item)
                # 设置默认值
                cols = self.tbWidgetRoute.columnCount()
                for c in range(1, cols):
                    new_item = QTableWidgetItem('*')
                    self.tbWidgetRoute.setItem(i, c, new_item)

                if self.trace_hop(i, dst_addr, pkt_size, timeout, probes, port_lo, port_hi):
                    break

        except Exception as err:
            # 出现异常
            QMessageBox.information(self, 'Hint', str(err), QMessageBox.Ok, QMessageBox.Ok)

        self.tbWidgetRoute.resizeColumnsToContents()
        print('trace end')
        return

    def trace_hop(self, i, dst_addr, pkt_size, timeout, probes, port_lo, port_hi):
        """
        最终第 i 跳路由
        :return: 是否到达目的地
        """
        # ping
        end = False # 是否到达目的地
        loss = 0 # 损失包数
        tot_rtt = 0 # 延迟之和
        for j in range(probes):
            rand_port = random.randint(port_lo, port_hi)
            # 发起一次 ping 探测
            try:
                result = ping_udp.udp_ping_once(dst_addr, rand_port, pkt_size, i+1, timeout)
            except Exception as err:
                raise err

            if not result:
                # 超时
                loss += 1
            else:
                delay = int(result[1]*1000)
                tot_rtt += delay
                # 设置当前延迟
                self.tbWidgetRoute.setItem(i, 5, QTableWidgetItem(str(delay)+'ms'))
                # 设置当前平均延迟
                self.tbWidgetRoute.setItem(i, 4, QTableWidgetItem(str(tot_rtt / (j+1-loss))+'ms'))
                        
                if not result[0]:
                    # ttl 到期
                    addr = result[2]
                else:
                    # 到达目的地
                    addr = dst_addr
                    end = True # 追踪终止

                # 设置主机/路由器 IP 及名称
                self.tbWidgetRoute.setItem(i,2, QTableWidgetItem(addr))
                try:
                    name = socket.gethostbyaddr(addr)[0]
                except Exception:
                    name = 'Unknown'
                self.tbWidgetRoute.setItem(i, 3, QTableWidgetItem(name))

            time.sleep(0.25)
               
        # 设置丢包率
        self.tbWidgetRoute.setItem(i, 1, QTableWidgetItem(str(loss * 100 / probes)+'%'))

        return end



if __name__ == '__main__':
    # 测试

    # 解决运行无法出现 GUI 的问题
    dirname = os.path.dirname(PyQt5.__file__)
    plugin_path = os.path.join(dirname, 'Qt', 'plugins', 'platforms')
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

    app = QApplication(sys.argv)
    main = TracerouteGUI()
    main.show()

    sys.exit(app.exec_())