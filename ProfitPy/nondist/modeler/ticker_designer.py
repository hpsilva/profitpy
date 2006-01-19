#!/usr/bin/env python
"""

"""
import sys

from qt import *

from profit.device import Node

from profit.lib import Base, Series, Tickers
from profit.lib.Tools import load_object
from profit.lib.Tools import timed_ticker_rebuild

from ticker_design_form import TickerDesignForm


class ReferenceTickerData(object):
    """ clients use case is this:

        given some reference structure, recalc only one combination of series 
        indexes at at time.

        the client will supply the reference data.

        the client will request that one or more attributes of a series changed
        and that the corresponding series and *only that index* are rebuit
    """
    def __init__(self):
        self.templates = {}
        self.design_cache = {}

    def setTemplates(self, ticker_supervisor):
        for (tid, tsym), tobj in ticker_supervisor.items():
            nobj = Tickers.TechnicalTicker(tid, tsym)
            for series_key, series in tobj.series.items():
                nser = {series_key : Series.Series(series)}
                nobj.series.update(nser)
            self.templates[tsym] = nobj

    def redesignTicker(self, source_ticker, series_key, index_key, empty_index):
        src = self.templates[source_ticker.symbol].series[series_key]
        tmp = Series.Series()
        tmp.indexes.append(empty_index)
        for k in src:
            tmp.append(k)
        source_ticker.series[series_key].indexes[index_key] = tmp.indexes[0]



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

    def classorder(A,B):
        return cmp(A.__name__, B.__name__)

    index_classes = [c for c in Series.__dict__.values() if classfilter(c)]
    index_classes.sort(classorder)

    return index_classes


class IndexBuilderParameterView(QListView):
    """ IndexBuilderParameterView(...) -> a list control for parameters

    """
    col_defs = ['Name', 'Value', ]

    default_view_defs = [ 
        ('Integer', 0), ('Float', 0.0), ('List', []),  
        ('String', '""'), ('Tuple', ()), ('Dict', {}),
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

        self.key_control = QLineEdit(self, cls.__name__)
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
                value = eval(value)
            else:
                value = item.value
            results[page.parameter_name] = value
        key = str(self.key_control.text())
        return key, results


class TickerDesigner(TickerDesignForm):
    """ TickerDesigner(...) -> implementation of the TickerDesignForm

    """
    title = 'Ticker Designer [%s] [%s]'
    data_directory = ''


    def __init__(self, filename=None, parent=None, name=None, modal=0, fl=0):
        TickerDesignForm.__init__(self, parent, name, modal, fl)
        self.tickers = None
        self.plot = None
        self.ticker = None

        self.fillIndexTypes()
        if filename:
            self.loadFile(filename)


    def fillIndexTypes(self):
        """ fillIndexTypes() -> fills the index type combo with available names

        """
        for cls in allIndexClasses():
            self.indexTypeCombo.insertItem(cls.__name__)
        self.indexTypeCombo.setCurrentItem(0)


    def clearAll(self):
        self.clearPlot()


    def clearPlot(self):
        """ clearPlot() -> clears the plot window

        """
        if self.plot:
            self.layout().remove(self.plot)
            self.plot.reparent(None, 0, QPoint(0,0), False)


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
        tickers = load_object(filename)
        self.filename = filename
        self.setCaption(self.title % (filename, ''))

        self.clearButton.emit(SIGNAL('clicked()'), ())

        for (tid, tsym), tobj in tickers.items():
            item = QListViewItem(self.tickerListView)
            item.setText(0, '%s' % (tsym, ))
            try:
                bp_len = len(tobj.series[1])
            except (AttributeError, IndexError, ):
                bp_len = 0
            item.setText(1, '%s' % (bp_len, ))

        self.tickers = tickers
        self.ref_data = ReferenceTickerData()
        self.ref_data.setTemplates(tickers)


    def selectTicker(self, item):
        """ selectTicker(item) -> responds to ticker select by showing its plot

        """
        symbol = str(item.text(0))
        layout = self.layout()

        new_ticker = src_ticker = self.tickers[symbol]

        for pricesize, series in new_ticker.series.items():
            if not hasattr(series, 'index_map'):
                new_ticker.series[pricesize] = Series.Series(series)

        new_plot= Node.TechnicalTickerNode(self, new_ticker)
        new_plot.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, 
                                           QSizePolicy.Expanding, False))
        self.clearPlot()
        layout.add(new_plot)
        new_plot.show()
        self.setCaption(self.title % (self.filename, symbol))

        self.plot = new_plot
        self.ticker = new_ticker

        self.plotTabChanged(self.plot.currentPage())
        self.connect(self.plot, SIGNAL('currentChanged(QWidget*)'), 
                     self.plotTabChanged)


    def plotTabChanged(self, current):
        price_size_key = current.price_size_key
        listview = self.seriesListView

        listview.clear()
        series = self.ticker.series[price_size_key]
        root = QListViewItem(listview, Base.PriceSizeLookup[price_size_key])
        root.series = root.line = series

    def selectSeriesItem(self, item):
        pass


    def addIndex(self):
        series_view = self.seriesListView
        parent_item = series_view.selectedItem()
        root_item = series_view.firstChild()
        idx_key = series_view.childCount()

        line = getattr(parent_item, 'line', None)
        series = getattr(root_item, 'series', None)

        if not parent_item or \
            not series or \
            not root_item:
            return

        index_class_name = str(self.indexTypeCombo.currentText())
        index_class = getIndexClass(index_class_name)

        series_args = self.runIndexBuilder(index_class, locals())
        if series_args:
            ## instead of all this below, the listview needs to be flattened
            ## and the builder dialog namespace should include each item from
            ## the list.  this will allow new indexes to select from all the
            ## current indexes as parameters, and allows for simplified 
            ## reconstruction of an empty ticker with new indexes.

            ## when a new index is created, the whole ticker needs to be 
            ## reconstructed.  the existing indexes must be re-created (lame)
            ## and the ticker must be refilled.  after that, the plot widget 
            ## needs to be deleted, and then a new plot widget stuck in its 
            ## place.

            # make a new index (on the existing series!!)
            idx_func = series.index_map.set
            idx_lbl = '%s-%s' % (index_class_name, idx_key)
            new_idx = idx_func(idx_lbl, index_class, **series_args)

            # ...

            # finally, add the new item to the listview
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
            return

        dlgok = dlg.exec_loop()
        if dlgok == QDialog.Rejected:
            return

        varargs = dlg.inspectSelections()
        return varargs


def main(args):
    """ main(args) -> run the ticker designer

    """
    app = QApplication(args)
    QObject.connect(app, SIGNAL('lastWindowClosed()'), app, SLOT('quit()'))

    try:
        filename = args[1]
    except (IndexError, ):
        filename = None

    window = TickerDesigner(filename=filename)
    app.setMainWidget(window)

    window.show()
    app.exec_loop()


if __name__ == '__main__':
    main(sys.argv)
