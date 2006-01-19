# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/troy/Projects/Profit/designer/designer_form.ui'
#
# Created: Mon Nov 17 22:20:14 2003
#      by: The PyQt User Interface Compiler (pyuic) 3.8
#
# WARNING! All changes made in this file will be lost!


import sys
from qt import *


class DesignerForm(QMainWindow):
    def __init__(self,parent = None,name = None,fl = 0):
        QMainWindow.__init__(self,parent,name,fl)
        self.statusBar()

        if not name:
            self.setName("DesignerForm")


        self.setCentralWidget(QWidget(self,"qt_central_widget"))
        DesignerFormLayout = QVBoxLayout(self.centralWidget(),11,6,"DesignerFormLayout")

        mainControlsLayout = QHBoxLayout(None,0,6,"mainControlsLayout")

        self.tickerCombo = QComboBox(0,self.centralWidget(),"tickerCombo")
        mainControlsLayout.addWidget(self.tickerCombo)

        self.showButton = QPushButton(self.centralWidget(),"showButton")
        mainControlsLayout.addWidget(self.showButton)

        self.resetButton = QPushButton(self.centralWidget(),"resetButton")
        mainControlsLayout.addWidget(self.resetButton)

        self.openButton = QPushButton(self.centralWidget(),"openButton")
        mainControlsLayout.addWidget(self.openButton)
        spacer = QSpacerItem(130,21,QSizePolicy.Expanding,QSizePolicy.Minimum)
        mainControlsLayout.addItem(spacer)
        DesignerFormLayout.addLayout(mainControlsLayout)

        self.widgetStack = QWidgetStack(self.centralWidget(),"widgetStack")

        self.qt_dead_widget_page = QWidget(self.widgetStack,"qt_dead_widget_page")
        self.widgetStack.addWidget(self.qt_dead_widget_page,0)
        DesignerFormLayout.addWidget(self.widgetStack)



        self.languageChange()

        self.resize(QSize(522,434).expandedTo(self.minimumSizeHint()))
        self.clearWState(Qt.WState_Polished)

        self.connect(self.openButton,SIGNAL("clicked()"),self.openFile)
        self.connect(self.showButton,SIGNAL("clicked()"),self.showTickerPage)


    def languageChange(self):
        self.setCaption(self.__tr("Ticker Designer"))
        self.showButton.setText(self.__tr("&Show"))
        self.resetButton.setText(self.__tr("&Reset"))
        self.openButton.setText(self.__tr("&Open"))


    def showTickerPage(self):
        print "DesignerForm.showTickerPage(): Not implemented yet"

    def openFile(self):
        print "DesignerForm.openFile(): Not implemented yet"

    def __tr(self,s,c = None):
        return qApp.translate("DesignerForm",s,c)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
    w = DesignerForm()
    a.setMainWidget(w)
    w.show()
    a.exec_loop()
