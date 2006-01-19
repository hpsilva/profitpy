# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/troy/Projects/Profit/designer/index_widget.ui'
#
# Created: Mon Nov 17 23:03:32 2003
#      by: The PyQt User Interface Compiler (pyuic) 3.8
#
# WARNING! All changes made in this file will be lost!


import sys
from qt import *


class IndexDesignWidget(QWidget):
    def __init__(self,parent = None,name = None,fl = 0):
        QWidget.__init__(self,parent,name,fl)

        if not name:
            self.setName("IndexDesignWidget")


        IndexDesignWidgetLayout = QVBoxLayout(self,6,6,"IndexDesignWidgetLayout")

        self.indexesView = QListView(self,"indexesView")
        self.indexesView.addColumn(self.__tr("Key"))
        self.indexesView.addColumn(self.__tr("Type"))
        self.indexesView.addColumn(QString.null)
        self.indexesView.addColumn(QString.null)
        IndexDesignWidgetLayout.addWidget(self.indexesView)

        addControlsLayout = QHBoxLayout(None,0,6,"addControlsLayout")

        self.addIndexCombo = QComboBox(0,self,"addIndexCombo")
        self.addIndexCombo.setSizePolicy(QSizePolicy(7,0,0,0,self.addIndexCombo.sizePolicy().hasHeightForWidth()))
        addControlsLayout.addWidget(self.addIndexCombo)

        self.addIndexButton = QPushButton(self,"addIndexButton")
        addControlsLayout.addWidget(self.addIndexButton)
        IndexDesignWidgetLayout.addLayout(addControlsLayout)

        self.languageChange()

        self.resize(QSize(200,246).expandedTo(self.minimumSizeHint()))
        self.clearWState(Qt.WState_Polished)

        self.connect(self.addIndexButton,SIGNAL("clicked()"),self.addNewIndex)


    def languageChange(self):
        self.setCaption(self.__tr("Index Design"))
        self.indexesView.header().setLabel(0,self.__tr("Key"))
        self.indexesView.header().setLabel(1,self.__tr("Type"))
        self.indexesView.header().setLabel(2,QString.null)
        self.indexesView.header().setLabel(3,QString.null)
        self.indexesView.clear()
        item = QListViewItem(self.indexesView,None)
        item.setText(0,self.__tr("New Item"))

        self.addIndexButton.setText(self.__tr("Add"))


    def addNewIndex(self):
        print "IndexDesignWidget.addNewIndex(): Not implemented yet"

    def __tr(self,s,c = None):
        return qApp.translate("IndexDesignWidget",s,c)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
    w = IndexDesignWidget()
    a.setMainWidget(w)
    w.show()
    a.exec_loop()
