
from functools import partial

from profit.widgets.dock import Dock
from profit.widgets.sessiontree import SessionTree
from profit.widgets.shell import PythonShell
from profit.widgets.strategytree import StrategyTree
from profit.widgets.ui_profitdevice import Ui_ProfitDeviceWindow
from profit.widgets.output import OutputWidget

from profit.widgets.breadfan_network import BreadFanNetworkTree
from profit.widgets.breadfan_train import BreadFanTrainTree
from profit.widgets.breadfan_test import BreadFanTestTree

from PyQt4 import QtGui
from PyQt4.QtCore import QUrl, QVariant, Qt, pyqtSignature
from PyQt4.QtGui import QAction, QApplication, QColor, QMainWindow
from PyQt4.QtGui import QFileDialog, QMessageBox, QProgressDialog, QMenu
from PyQt4.QtGui import QSystemTrayIcon, QToolBar
from PyQt4.QtGui import QIcon, QDesktopServices



from ui_breadfan_main import Ui_BreadFanMain
from ffnet import ffnet, loadnet, savenet


class BreadFanMain(QMainWindow, Ui_BreadFanMain):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setupUi(self)
        self.setupDockWidgets()
        self.net = None

    @pyqtSignature('')
    def on_actionNew_triggered(self):
        print 'new file'

    @pyqtSignature('')
    def on_actionOpen_triggered(self):
        print 'open file'

    @pyqtSignature('')
    def on_actionSave_triggered(self):
        print 'save file'

    @pyqtSignature('')
    def on_actionSaveAs_triggered(self):
        print 'save as file'

    @pyqtSignature('')
    def on_actionClose_triggered(self):
        print 'close file'

    @pyqtSignature('')
    def on_actionImport_triggered(self):
        filename = QFileDialog.getOpenFileName(
            self, 'Import Network', '')
        if filename:
            self.net = loadnet(filename)

    @pyqtSignature('')
    def on_actionExport_triggered(self):
        print 'export'
        if not self.net:
            print 'no network to export'
            return
        filename = QFileDialog.getOpenFileName(
            self, 'Export Network', '')
        if filename:
            savenet(self.net, filename)

    def setupDockWidgets(self):
        bottom = Qt.BottomDockWidgetArea
        tabify = self.tabifyDockWidget
        self.networkDock = net = Dock('Network', self, BreadFanNetworkTree)
        self.trainDock = Dock('Train', self, BreadFanTrainTree)
        self.testDock = Dock('Test', self, BreadFanTestTree)
        tabify(self.networkDock, self.trainDock)
        tabify(self.trainDock, self.testDock)
        tabify(self.testDock, self.networkDock)

        self.stdoutDock = Dock('Standard Output', self, OutputWidget, bottom)
        self.stderrDock = Dock('Standard Error', self, OutputWidget, bottom)
        makeShell = partial(
            PythonShell,
            stdout=self.stdoutDock.widget(),
            stderr=self.stderrDock.widget())
        self.shellDock = Dock('Python Shell', self, makeShell, bottom)
        tabify(self.shellDock, self.stdoutDock)
        tabify(self.stdoutDock, self.stderrDock)


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    win = BreadFanMain()
    win.show()
    sys.exit(app.exec_())

