# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/troy/Projects/Profit/test/index_builder_dialog_template.ui'
#
# Created: Wed Nov 5 01:50:44 2003
#      by: The PyQt User Interface Compiler (pyuic) 3.8
#
# WARNING! All changes made in this file will be lost!


import sys
from qt import *


class indexInitBuilder(QDialog):
    def __init__(self,parent = None,name = None,modal = 0,fl = 0):
        QDialog.__init__(self,parent,name,modal,fl)

        if not name:
            self.setName("indexInitBuilder")


        indexInitBuilderLayout = QHBoxLayout(self,6,6,"indexInitBuilderLayout")

        layout3 = QGridLayout(None,1,1,0,6,"layout3")

        self.intrinsicEditView = QListView(self,"intrinsicEditView")
        self.intrinsicEditView.addColumn(self.__tr("Type"))
        self.intrinsicEditView.addColumn(self.__tr("Value"))
        self.intrinsicEditView.setSizePolicy(QSizePolicy(1,7,0,0,self.intrinsicEditView.sizePolicy().hasHeightForWidth()))
        self.intrinsicEditView.setSelectionMode(QListView.Single)
        self.intrinsicEditView.setAllColumnsShowFocus(1)
        self.intrinsicEditView.setResizeMode(QListView.LastColumn)

        layout3.addWidget(self.intrinsicEditView,1,0)

        layout2 = QHBoxLayout(None,0,6,"layout2")
        spacer = QSpacerItem(191,31,QSizePolicy.Expanding,QSizePolicy.Minimum)
        layout2.addItem(spacer)

        self.okayButton = QPushButton(self,"okayButton")
        layout2.addWidget(self.okayButton)

        self.cancelButton = QPushButton(self,"cancelButton")
        layout2.addWidget(self.cancelButton)

        layout3.addMultiCellLayout(layout2,2,2,0,1)

        self.paramNameLabel = QLabel(self,"paramNameLabel")
        self.paramNameLabel.setSizePolicy(QSizePolicy(7,1,0,0,self.paramNameLabel.sizePolicy().hasHeightForWidth()))

        layout3.addMultiCellWidget(self.paramNameLabel,0,0,0,1)

        self.localSelectView = QListView(self,"localSelectView")
        self.localSelectView.addColumn(self.__tr("Name"))
        self.localSelectView.addColumn(self.__tr("Value"))
        self.localSelectView.setLineWidth(1)
        self.localSelectView.setMargin(0)
        self.localSelectView.setAllColumnsShowFocus(1)
        self.localSelectView.setResizeMode(QListView.LastColumn)

        layout3.addWidget(self.localSelectView,1,1)
        indexInitBuilderLayout.addLayout(layout3)

        self.languageChange()

        self.resize(QSize(416,223).expandedTo(self.minimumSizeHint()))
        self.clearWState(Qt.WState_Polished)

        self.connect(self.intrinsicEditView,SIGNAL("clicked(QListViewItem*)"),self.toggleSelection)
        self.connect(self.localSelectView,SIGNAL("clicked(QListViewItem*)"),self.toggleSelection)
        self.connect(self.okayButton,SIGNAL("clicked()"),self,SLOT("accept()"))
        self.connect(self.cancelButton,SIGNAL("clicked()"),self,SLOT("reject()"))


    def languageChange(self):
        self.setCaption(self.__tr("%s Builder"))
        self.intrinsicEditView.header().setLabel(0,self.__tr("Type"))
        self.intrinsicEditView.header().setLabel(1,self.__tr("Value"))
        self.intrinsicEditView.clear()
        item = QListViewItem(self.intrinsicEditView,None)
        item.setText(0,self.__tr("Integer"))
        item.setText(1,self.__tr("0"))

        item = QListViewItem(self.intrinsicEditView,item)
        item.setText(0,self.__tr("Float"))
        item.setText(1,self.__tr("0.0"))

        item = QListViewItem(self.intrinsicEditView,item)
        item.setText(0,self.__tr("List"))
        item.setText(1,self.__tr("[]"))

        item = QListViewItem(self.intrinsicEditView,item)
        item.setText(0,self.__tr("String"))
        item.setText(1,self.__tr("\"\""))

        item = QListViewItem(self.intrinsicEditView,item)
        item.setText(0,self.__tr("Tuple"))
        item.setText(1,self.__tr("()"))

        self.okayButton.setText(self.__tr("&OK"))
        self.cancelButton.setText(self.__tr("&Cancel"))
        self.paramNameLabel.setText(self.__tr("param name: <b>some name</b>"))
        self.localSelectView.header().setLabel(0,self.__tr("Name"))
        self.localSelectView.header().setLabel(1,self.__tr("Value"))
        self.localSelectView.clear()
        item = QListViewItem(self.localSelectView,None)
        item.setText(0,self.__tr("cls"))
        item.setText(1,self.__tr("IndexSeriesClass"))

        item = QListViewItem(self.localSelectView,item)
        item.setText(0,self.__tr("series"))
        item.setText(1,self.__tr("[None, 1.2, 3.4, ]"))



    def toggleSelection(self,a0):
        print "indexInitBuilder.toggleSelection(QListViewItem*): Not implemented yet"

    def __tr(self,s,c = None):
        return qApp.translate("indexInitBuilder",s,c)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
    w = indexInitBuilder()
    a.setMainWidget(w)
    w.show()
    a.exec_loop()
