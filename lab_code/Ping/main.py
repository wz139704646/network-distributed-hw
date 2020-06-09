import sys
import os
import PyQt5
from PyQt5.QtWidgets import QApplication
from traceroute_gui import TracerouteGUI
import qdarkstyle


if __name__ == '__main__':
    # 解决运行无法出现 GUI 的问题
    dirname = os.path.dirname(PyQt5.__file__)
    plugin_path = os.path.join(dirname, 'Qt', 'plugins', 'platforms')
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
    
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    main_window = TracerouteGUI()
    main_window.show()

    sys.exit(app.exec_())