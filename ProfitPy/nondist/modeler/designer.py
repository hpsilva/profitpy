#!/usr/bin/env python
##~ Copyright 2004 Troy Melhase <troy@gci.net>
##~ 
##~ This file is part of the ProfitPy package.
##~ 
##~ ProfitPy is free software; you can redistribute it and/or modify
##~ it under the terms of the GNU General Public License as published by
##~ the Free Software Foundation; either version 2 of the License, or
##~ (at your option) any later version.
##~ 
##~ ProfitPy is distributed in the hope that it will be useful,
##~ but WITHOUT ANY WARRANTY; without even the implied warranty of
##~ MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##~ GNU General Public License for more details.
##~ 
##~ You should have received a copy of the GNU General Public License
##~ along with ProfitPy; if not, write to the Free Software
##~ Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
import sys
import traceback

from qt import *

from profit.designer.designer_form import DesignerForm
from profit.designer.index_widget import IndexDesignWidget
from profit.designer.index_controls import IndexControlsWidget

from profit.device import Node
from profit.device import Plot

from profit.lib import Base, Series, Tickers
from profit.lib.Tools import load_object
from profit.lib.Tools import timed_ticker_rebuild


## fix buildControls below to use the inspect module


def getIndexClass(cls_name):
    """ getIndexClass(cls_name) -> returns a Series class from its name

    """
    return Series.__dict__[cls_name]


def allIndexClasses():
    """ allIndexClasses() -> returns sorted list of SeriesIndex sub-classes

    """
    root_cls = Series.SeriesIndex
    cls_type = type(root_cls)

    def classfilter(C):
        return isinstance(C, cls_type) and \
               issubclass(C, root_cls) and \
               (C is not root_cls)

    def classorder(A, B):
        return cmp(A.__name__, B.__name__)

    index_classes = [c for c in Series.__dict__.values() if classfilter(c)]
    index_classes.sort(classorder)

    return index_classes

class IndexBuilderParameterView(QListView):
    """ IndexBuilderParameterView(...) -> a list control for parameters

    """
    col_defs = ['Name', 'Value', ]

    default_view_defs = [ 
        ('Expression', ""),
    ]

    def setUp(self, locals_map):
        self.clear()
        self.setLineWidth(1)
        self.setMargin(0)
        self.setAllColumnsShowFocus(1)
        self.setDefaultRenameAction(QListView.Accept)

        for name in self.col_defs:
            self.addColumn(name)

        item = None
        for typ, val in self.default_view_defs:
            item = QListViewItem(self, item)
            item.setText(0, typ)
            item.setText(1, str(val))
            item.setRenameEnabled(1, True)

        for typ, val in locals_map.items():
            item = QListViewItem(self, item)
            item.setText(0, typ)
            item.setText(1, str(val))
            item.value = val
        self.setCurrentItem(self.firstChild())


class IndexBuilderDialog(QDialog):
    """ IndexBuilderDialog(...) -> dialog box for building an index

    """


    def __init__(self, parent=None, name='IndexBuilderDialog' ,modal=1, fl=0):
        QDialog.__init__(self,parent,name,modal,fl)
        self.main_layout = QVBoxLayout(self, 6, 6)
        self.sizeMin()
        self.clearWState(Qt.WState_Polished)

    def sizeMin(self):
        self.resize(QSize(400, 200).expandedTo(self.minimumSizeHint()))

    def buildControls(self, cls, ns):
        """ buildControls(cls) -> build editing controls for cls init

        """
        try:
            initcode = cls.__init__.im_func.func_code
            argcnt = initcode.co_argcount
            flags = initcode.co_flags
            argnames = initcode.co_varnames
        except (AttributeError, ):
            return False

        if flags & 0x04:
            argcnt += 1
        if flags & 0x08:
            argcnt += 1

        default_key = '%s' % (cls.__name__, )
        self.key_control = QLineEdit(default_key, self)
        self.main_layout.add(self.key_control)

        self.tabs_control = QTabWidget(self)
        self.main_layout.add(self.tabs_control)

        objmap = ns.copy()
        ns.update({'cls':cls, })

        for argname in argnames[1:argcnt]:
            control = IndexBuilderParameterView(self)
            control.setUp(objmap)
            control.parameter_name = argname
            self.tabs_control.addTab(control, "parameter '%s'" % (argname, ))

        self.okayButton = QPushButton('&OK', self)
        self.cancelButton = QPushButton('&Cancel', self)

        buttonBox= QHBoxLayout(None, 0, 6)
        buttonBox.addItem(QSpacerItem(191, 31, QSizePolicy.Expanding, 
                                      QSizePolicy.Minimum))
        buttonBox.addWidget(self.okayButton)
        buttonBox.addWidget(self.cancelButton)
        self.main_layout.addLayout(buttonBox)

        self.connect(self.okayButton, SIGNAL('clicked()'), self, SLOT('accept()'))
        self.connect(self.cancelButton, SIGNAL('clicked()'), self, SLOT('reject()'))
        return True

    def inspectSelections(self):
        """ inspectSelections() -> returns two-tuple of name, value

        """
        results, tabs = {}, self.tabs_control
        pages = [tabs.page(i) for i in range(tabs.count())]

        for page in pages:
            item = page.currentItem()
            if not item:
                value = 0
            elif item.renameEnabled(1):
                value = str(item.text(1))
                try:
                    value = eval(value)
                except (SyntaxError, ):
                    banner = '-- Could not evaluate index param' + '-' * 20
                    print banner
                    traceback.print_exc()
                    print '-' * len(banner)
                    return
            else:
                value = item.value
            results[page.parameter_name] = value

        key = str(self.key_control.text())
        return key, results


class MainForm(DesignerForm):
    """ MainForm(...) -> implementation of the DesignerForm

    """
    title = 'Ticker Designer [%s] [%s]'
    data_directory = ''
    ticker_designs = {}
    ticker_supervisor = None

    def __init__(self, filename=None, parent=None, name=None, fl=0):
        DesignerForm.__init__(self, parent, name, fl)
        self.tickers = None
        self.plot = None
        self.ticker = None

        if filename:
            self.loadFile(filename)

    def openFile(self):
        """ openFile() -> prompts user for file to load

        """
        filename = QFileDialog.getOpenFileName(self.data_directory, '*', self)
        filename = str(filename)
        if not filename:
            return
        self.loadFile(filename)

    def loadFile(self, filename):
        """ loadFile(filename) -> loads a data file and displays its content

        """
        self.tickers = tickers = load_object(filename)
        self.filename = filename
        self.setCaption(self.title % (filename, ''))

        syms = [tsym for (tid, tsym) in tickers.keys()]
        syms.sort()

        ## spruce up the combo with the symbols
        self.tickerCombo.clear()
        for sym in syms:
            self.tickerCombo.insertItem(sym)

        ## mop up the existing design pages
        wstack = self.widgetStack
        for sym, page in self.ticker_designs.items():
            wstack.removeWidget(page)
        wstack.raiseWidget(self.qt_dead_widget_page)
        self.ticker_designs.clear()
        self.resize(QSize(1024,768).expandedTo(self.minimumSizeHint()))

    def showTickerPage(self):
        ## copy the widgets from the template page
        wstack = self.widgetStack
        designs = self.ticker_designs
        sym = str(self.tickerCombo.currentText())
        ticker = self.tickers[sym]

        if designs.has_key(sym):
            wstack.raiseWidget(designs[sym])
        else:
            designs[sym] = new_designer = DesignerControls(wstack, ticker, 1)
            wstack.addWidget(new_designer)
            wstack.raiseWidget(new_designer)
            self.connect(new_designer, PYSIGNAL('RebuiltSeries'), 
                     self.updateDesign)

    def updateDesign(self, series, sym, key):
        wstack = self.widgetStack
        self.tickers[sym].series[key] = series

        page = wstack.visibleWidget()
        page.plot.reparent(None, 0, QPoint(0,0), False)

        page.plot = plot = Plot.SeriesNode(page, series)
        plot.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, 
                                       QSizePolicy.Expanding, False))
        plot.show()

        page.main_layout.addWidget(plot)
        page.main_layout.setStretchFactor(plot, 10)


class DesignerControls(QWidget):
    def __init__(self, parent, ticker, series_key):
        QWidget.__init__(self, parent)
        self.symbol = symbol = ticker.symbol
        self.series = series = ticker.series[series_key]
        self.series_key = series_key

        self.main_layout = main_layout = QHBoxLayout(self)
        self.controls_layout = controls_layout = QVBoxLayout(main_layout)

        self.index_designer = index_designer = IndexDesiger(self, series)
        controls_layout.addWidget(index_designer, 0, 0)

        if not hasattr(series, 'indexes'):
            series = Series.Series(series)
            #series.indexes = indexes = []
            #series.index_map = Series.IndexMapping(indexes)

        self.plot = plot = Plot.SeriesPlot(self, series)
        plot.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, 
                                       QSizePolicy.Expanding, False))
        plot.show()

        main_layout.addWidget(plot)
        main_layout.setStretchFactor(plot, 10)

        self.index_controls = index_controls = {}


        self.connect(index_designer, PYSIGNAL('AddedIndex'), 
                     self.rebuildIndexes)


    ### CONTEXT gets wrong series -- whatthe...?

    def rebuildIndexes(self, view, definitions):
        src_series = self.series
        series = Series.Series()
        idx_setr = series.index_map.set

        all_params = {'series':series, }
        for key, cls, params in definitions:
            kwds = adjust_keywords(cls, params, all_params)
            all_params[key] = idx_setr(key, cls, **kwds)
            

        for k in src_series:
            series.append(k)

        self.emit(PYSIGNAL('RebuiltSeries'), (series, 
                                              self.symbol, 
                                              self.series_key))

        #for index, label in enumerate(('periods', 'k', )):
        #    index_controls[label] = controls = IndexControls(self, label)
        #     controls_layout.addWidget(controls) 


def adjust_keywords(klass, supplied, context):
    initcode = klass.__init__.im_func.func_code
    out = {}
    for aname in initcode.co_varnames[1:]:
        if supplied.has_key(aname) and context.has_key(aname):
            out[aname] = context[aname]
        else:
            out[aname] = supplied[aname]
    return out


class IndexDesiger(IndexDesignWidget):
    def __init__(self, parent, series):
        IndexDesignWidget.__init__(self, parent)
        self.indexesView.clear()
        self.indexes_shadow = []
        self.series = series

        for cls in allIndexClasses():
            self.addIndexCombo.insertItem(cls.__name__)
        self.addIndexCombo.setCurrentItem(0)

    def addNewIndex(self):
        cls = getIndexClass(str(self.addIndexCombo.currentText()))
        idx_view = self.indexesView
        idx_shadow = self.indexes_shadow

        build_vars = {'series':self.series, }
        for ik, icls, iparam in idx_shadow:
            build_vars.update({ik:[]})

        try:
            idx_key, idx_params = self.runIndexBuilder(cls, build_vars)
            if idx_key in [k for k, c, p in idx_shadow]:
                q = QErrorMessage(self)
                q.setCaption("New Index Error")
                q.message("Duplicate key - index not built")
                q.show()
                return

        except (ValueError, ):
            # couldn't unpack the None - build canceled
            return

        idx_shadow.append((idx_key, cls, idx_params))
        item = QListViewItem(idx_view, idx_view.lastItem())
        item.setText(0, idx_key)
        item.setText(1, cls.__name__)
        self.emit(PYSIGNAL('AddedIndex'), (idx_view, idx_shadow, ))


        if 0:
            idx_func = series.index_map.set
            idx_lbl = '%s-%s' % (index_class_name, idx_key)
            new_idx = idx_func(idx_lbl, index_class, **series_args)
            new_item = QListViewItem(parent_item)
            new_item.setText(0, index_class_name)
            new_item.line = line
            parent_item.setExpandable(True)
            parent_item.setOpen(True)

    def runIndexBuilder(self, cls, namespace):
        dlg = IndexBuilderDialog(self, 'index_builder', True)
        dlg.setCaption('Build %s Index' % (cls.__name__, ))

        if not dlg.buildControls(cls, namespace):
            cap = 'Index Builder Dialog Error'
            msg = 'Could not build dialog controls.'
            btns = QMessageBox.Ok
            QMessageBox.warning(self, cap, msg, btns)
            return ()

        dlgok = dlg.exec_loop()
        if dlgok == QDialog.Rejected:
            return ()

        try:
            key, params = dlg.inspectSelections()
            return (key, params, )
        except (TypeError, ):
            return ()


class IndexControls(IndexControlsWidget):
    def __init__(self, parent, label):
        IndexControlsWidget.__init__(self, parent)
        self.indexLabel.setText("<b>%s</b>" % (label, ))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    QObject.connect(app, SIGNAL('lastWindowClosed()'), app, SLOT('quit()'))

    try:
        filename = sys.argv[1]
    except (IndexError, ):
        filename = None

    window = MainForm(filename)
    app.setMainWidget(window)
    window.show()
    app.exec_loop()
