# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/troy/Projects/Profit/test/ticker_design_form.ui'
#
# Created: Wed Nov 5 22:23:18 2003
#      by: The PyQt User Interface Compiler (pyuic) 3.8
#
# WARNING! All changes made in this file will be lost!


import sys
from qt import *


class TickerDesignForm(QDialog):
    def __init__(self,parent = None,name = None,modal = 0,fl = 0):
        QDialog.__init__(self,parent,name,modal,fl)

        if not name:
            self.setName("TickerDesignForm")


        TickerDesignFormLayout = QHBoxLayout(self,6,6,"TickerDesignFormLayout")

        self.controlsFrame = QFrame(self,"controlsFrame")
        self.controlsFrame.setSizePolicy(QSizePolicy(0,5,0,0,self.controlsFrame.sizePolicy().hasHeightForWidth()))
        self.controlsFrame.setFrameShape(QFrame.StyledPanel)
        self.controlsFrame.setFrameShadow(QFrame.Raised)
        controlsFrameLayout = QGridLayout(self.controlsFrame,1,1,6,6,"controlsFrameLayout")

        self.openButton = QToolButton(self.controlsFrame,"openButton")
        self.openButton.setSizePolicy(QSizePolicy(7,0,0,0,self.openButton.sizePolicy().hasHeightForWidth()))
        self.openButton.setUsesTextLabel(0)
        self.openButton.setTextPosition(QToolButton.Right)

        controlsFrameLayout.addWidget(self.openButton,1,0)

        self.clearButton = QToolButton(self.controlsFrame,"clearButton")
        self.clearButton.setSizePolicy(QSizePolicy(7,0,0,0,self.clearButton.sizePolicy().hasHeightForWidth()))
        self.clearButton.setUsesTextLabel(0)
        self.clearButton.setTextPosition(QToolButton.Right)

        controlsFrameLayout.addWidget(self.clearButton,1,1)

        self.seriesListView = QListView(self.controlsFrame,"seriesListView")
        self.seriesListView.addColumn(self.__tr("Series"))
        self.seriesListView.addColumn(self.__tr("Value"))
        self.seriesListView.addColumn(self.__tr("Color"))
        self.seriesListView.setSizePolicy(QSizePolicy(7,7,0,0,self.seriesListView.sizePolicy().hasHeightForWidth()))
        self.seriesListView.setAllColumnsShowFocus(1)
        self.seriesListView.setTreeStepSize(20)

        controlsFrameLayout.addMultiCellWidget(self.seriesListView,2,2,0,2)

        self.tickerListView = QListView(self.controlsFrame,"tickerListView")
        self.tickerListView.addColumn(self.__tr("Id"))
        self.tickerListView.addColumn(self.__tr("Size"))
        self.tickerListView.setSizePolicy(QSizePolicy(7,7,0,0,self.tickerListView.sizePolicy().hasHeightForWidth()))
        self.tickerListView.setSelectionMode(QListView.Single)
        self.tickerListView.setAllColumnsShowFocus(1)
        self.tickerListView.setShowSortIndicator(1)

        controlsFrameLayout.addMultiCellWidget(self.tickerListView,0,0,0,2)

        self.editIndexSlider = QSlider(self.controlsFrame,"editIndexSlider")
        self.editIndexSlider.setEnabled(1)
        self.editIndexSlider.setSizePolicy(QSizePolicy(3,0,0,0,self.editIndexSlider.sizePolicy().hasHeightForWidth()))
        self.editIndexSlider.setOrientation(QSlider.Horizontal)
        self.editIndexSlider.setTickmarks(QSlider.NoMarks)

        controlsFrameLayout.addMultiCellWidget(self.editIndexSlider,3,3,1,2)

        self.editIndexSpinner = QSpinBox(self.controlsFrame,"editIndexSpinner")
        self.editIndexSpinner.setEnabled(1)
        self.editIndexSpinner.setSizePolicy(QSizePolicy(1,5,0,0,self.editIndexSpinner.sizePolicy().hasHeightForWidth()))
        self.editIndexSpinner.setMaxValue(1000)
        self.editIndexSpinner.setValue(100)

        controlsFrameLayout.addWidget(self.editIndexSpinner,3,0)

        self.testButton = QToolButton(self.controlsFrame,"testButton")
        self.testButton.setSizePolicy(QSizePolicy(7,0,0,0,self.testButton.sizePolicy().hasHeightForWidth()))
        self.testButton.setUsesTextLabel(0)
        self.testButton.setTextPosition(QToolButton.Right)

        controlsFrameLayout.addWidget(self.testButton,1,2)

        self.addIndexButton = QToolButton(self.controlsFrame,"addIndexButton")
        self.addIndexButton.setSizePolicy(QSizePolicy(7,0,0,0,self.addIndexButton.sizePolicy().hasHeightForWidth()))
        self.addIndexButton.setUsesTextLabel(0)
        self.addIndexButton.setTextPosition(QToolButton.Right)

        controlsFrameLayout.addWidget(self.addIndexButton,4,0)

        self.indexTypeCombo = QComboBox(0,self.controlsFrame,"indexTypeCombo")

        controlsFrameLayout.addMultiCellWidget(self.indexTypeCombo,4,4,1,2)
        TickerDesignFormLayout.addWidget(self.controlsFrame)

        self.languageChange()

        self.resize(QSize(265,548).expandedTo(self.minimumSizeHint()))
        self.clearWState(Qt.WState_Polished)

        self.connect(self.tickerListView,SIGNAL("clicked(QListViewItem*)"),self.selectTicker)
        self.connect(self.openButton,SIGNAL("clicked()"),self.openFile)
        self.connect(self.clearButton,SIGNAL("clicked()"),self.clearAll)
        self.connect(self.clearButton,SIGNAL("clicked()"),self.seriesListView,SLOT("clear()"))
        self.connect(self.clearButton,SIGNAL("clicked()"),self.tickerListView,SLOT("clear()"))
        self.connect(self.addIndexButton,SIGNAL("clicked()"),self.addIndex)


    def languageChange(self):
        self.setCaption(self.__tr("Ticker Designer"))
        self.openButton.setText(self.__tr("Open"))
        self.openButton.setTextLabel(self.__tr("Open"))
        self.clearButton.setText(self.__tr("Clear"))
        self.clearButton.setTextLabel(self.__tr("Clear"))
        self.seriesListView.header().setLabel(0,self.__tr("Series"))
        self.seriesListView.header().setLabel(1,self.__tr("Value"))
        self.seriesListView.header().setLabel(2,self.__tr("Color"))
        self.seriesListView.clear()
        item = QListViewItem(self.seriesListView,None)
        item.setText(0,self.__tr("Ask Price"))

        item_2 = QListViewItem(self.seriesListView,item)
        item_2.setOpen(1)
        item = QListViewItem(item_2,item)
        item.setText(0,self.__tr("BollingerUpper"))
        item.setText(1,self.__tr("0.15"))
        item_2.setOpen(1)
        item = QListViewItem(item_2,item)
        item.setText(0,self.__tr("EMA"))
        item.setText(1,self.__tr("33"))
        item_2.setText(0,self.__tr("Bid Price"))

        item = QListViewItem(self.seriesListView,item_2)
        item.setText(0,self.__tr("Last Price"))

        self.tickerListView.header().setLabel(0,self.__tr("Id"))
        self.tickerListView.header().setLabel(1,self.__tr("Size"))
        self.testButton.setText(self.__tr("Test"))
        self.testButton.setTextLabel(self.__tr("Open"))
        self.addIndexButton.setText(self.__tr("Add"))
        self.addIndexButton.setTextLabel(self.__tr("Open"))


    def selectColor(self):
        print "TickerDesignForm.selectColor(): Not implemented yet"

    def clearAll(self):
        print "TickerDesignForm.clearAll(): Not implemented yet"

    def openFile(self):
        print "TickerDesignForm.openFile(): Not implemented yet"

    def selectTicker(self,a0):
        print "TickerDesignForm.selectTicker(QListViewItem*): Not implemented yet"

    def seriesListContextMenu(self,a0,a1,a2):
        print "TickerDesignForm.seriesListContextMenu(QListViewItem*,const QPoint&,int): Not implemented yet"

    def addIndex(self):
        print "TickerDesignForm.addIndex(): Not implemented yet"

    def __tr(self,s,c = None):
        return qApp.translate("TickerDesignForm",s,c)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
    w = TickerDesignForm()
    a.setMainWidget(w)
    w.show()
    a.exec_loop()
