# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/troy/Projects/Profit/designer/index_controls.ui'
#
# Created: Mon Nov 17 00:39:00 2003
#      by: The PyQt User Interface Compiler (pyuic) 3.8
#
# WARNING! All changes made in this file will be lost!


import sys
from qt import *


class IndexControlsWidget(QWidget):
    def __init__(self,parent = None,name = None,fl = 0):
        QWidget.__init__(self,parent,name,fl)

        if not name:
            self.setName("IndexControlsWidget")


        IndexControlsWidgetLayout = QHBoxLayout(self,6,6,"IndexControlsWidgetLayout")

        self.indexLabel = QLabel(self,"indexLabel")
        self.indexLabel.setSizePolicy(QSizePolicy(0,5,0,0,self.indexLabel.sizePolicy().hasHeightForWidth()))
        self.indexLabel.setMinimumSize(QSize(50,0))
        self.indexLabel.setFrameShape(QLabel.NoFrame)
        self.indexLabel.setFrameShadow(QLabel.Plain)
        IndexControlsWidgetLayout.addWidget(self.indexLabel)

        self.valueSlider = QSlider(self,"valueSlider")
        self.valueSlider.setMinimumSize(QSize(100,0))
        self.valueSlider.setOrientation(QSlider.Horizontal)
        IndexControlsWidgetLayout.addWidget(self.valueSlider)

        self.valueSpinner = QSpinBox(self,"valueSpinner")
        IndexControlsWidgetLayout.addWidget(self.valueSpinner)

        self.previewToggle = QCheckBox(self,"previewToggle")
        IndexControlsWidgetLayout.addWidget(self.previewToggle)

        self.languageChange()

        self.resize(QSize(382,46).expandedTo(self.minimumSizeHint()))
        self.clearWState(Qt.WState_Polished)


    def languageChange(self):
        self.setCaption(self.__tr("Index Controls"))
        self.indexLabel.setText(self.__tr("<b>label</b>"))
        self.previewToggle.setText(self.__tr("&Preview"))


    def __tr(self,s,c = None):
        return qApp.translate("IndexControlsWidget",s,c)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
    w = IndexControlsWidget()
    a.setMainWidget(w)
    w.show()
    a.exec_loop()
