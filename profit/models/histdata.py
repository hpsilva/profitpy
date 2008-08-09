#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from PyQt4.QtCore import Qt, QModelIndex, QVariant, QString
from ib.opt.message import HistoricalData as HistDataMessage
from profit.lib import Signals, logging, valueAlign
from profit.models import BasicItem, BasicItemModel

## TODO: add the incoming requests to the parent session's extra
## object list.


##
## First is the parent model and it's items.
##

class HistDataRequestModel(BasicItemModel):
    """ HistDataRequestModel -> logical parent of individual hist data models

    This class receives, queues, and submits historical data requests.
    As new requests are received (or when un-requested historical data
    messages are received), instances create child models of type HistDataModel.

    """
    def __init__(self, session=None, parent=None):
        """ Initializer.

        @param session=None session reference or None
        @param parent=None ancestor of this object or None
        """
        BasicItemModel.__init__(self, RootHistDataRequestItem(), parent)
        self.session = session
        if session is not None:
            session.registerMeta(self)
        self.startTimer(1000)

    def data(self, index, role):
        """ Framework hook to retreive data stored at index for given role.

        @param index QModelIndex instance
        @param role Qt.DisplayRole flags
        @return QVariant instance
        """
        if not index.isValid():
            return QVariant()
        item = index.internalPointer()
        data = QVariant()
        column = index.column()
        if role == Qt.DecorationRole and column==2:
            data = QVariant(self.symbolIcon(item.symbol()))
        elif role in (Qt.DisplayRole, Qt.ToolTipRole):
            data = QVariant(item[column])
        elif role in (Qt.TextAlignmentRole, ):
            try:
                float(item[column])
                data = QVariant(valueAlign)
            except (TypeError, ValueError, ):
                pass
        return data

    def findHistDataRequest(self, reqId):
        """ Returns the item for the given hist data message, or None.

        """
        items = self.invisibleRootItem.children
        try:
            return [i for i in items if i.reqId==reqId][0]
        except (IndexError, ):
            pass

    def on_session_HistoricalData(self, message):
        """ Called when the session receives a HistoricalData message.

        @param message ib.opt.message instance
        """
        reqId = message.reqId
        item = self.findHistDataRequest(reqId)
        if item:
            if message.date.startswith('finished-'):
                item[1] = 'Finished'
                self.reset()
        else:
            root = self.invisibleRootItem
            root.append(HistDataRequestItem.fromMessage(reqId, message, root, {}))
            ## cheater
            self.reset()

    def on_session_historicalDataRequest(self, params):
        """ Called when a request for historical data is made.

        """
        reqId = params['tickerId']
        requests = self.requests
        if reqId in requests:
            logging.warn('Ignoring duplicate hist data request %s', reqId)
            return
        requests[reqId] = params.copy()
        root = self.invisibleRootItem
        root.append(HistDataRequestItem.fromRequest(reqId, params, root))
        self.reset()


class HistDataRequestItem(BasicItem):
    columnLookups = [
        ('Request Id', None),
        ('Status', None),
        ('Symbol', None),
        ('Security Type', None),
        ('Expiry', None),
        ('Right', None),
    ]

    def __init__(self, values, parent=None):
        BasicItem.__init__(self, values, parent)

    @classmethod
    def fromRequest(cls, reqId, req, parent):
        values = [None for i in cls.columnLookups]
        values[0] = reqId
        values[1] = 'Queued'
        item = cls(values, parent)
        item.reqId = reqId
        item.req = req
        return item

    @classmethod
    def fromMessage(cls, reqId, message, parent, req):
        values = [None for i in cls.columnLookups]
        values[0] = reqId
        values[1] = 'Queued'
        item = cls(values, parent)
        item.reqId = reqId
        item.req = req
        return item

    def symbol(self):
        """ Returns the symbol for this item or ''

        """
        try:
            return self.message.contract.m_symbol
        except (AttributeError, ):
            return ''

class RootHistDataRequestItem(HistDataRequestItem):
    def __init__(self):
        HistDataRequestItem.__init__(self, self.horizontalLabels())

    def horizontalLabels(self):
        """ Generates list of horizontal header values.

        """
        return map(QVariant, [label for label, lookup in self.columnLookups])


##
## Next is the model and items for an individual request and it's messages.
##

class HistDataModel(BasicItemModel):
    """ HistDataModel -> model of hist data requests and responses

    This model supports online and offline processing of messages.  In
    the case of missing requests (as in when messages are read from
    disk), the model simply fills in what it can.  In the case where
    the model is given a request, it enqueues the request with the
    session and then associates the responses accordingly.
    """
    def __init__(self, session=None, parent=None):
        """ Initializer.

        @param session=None session reference or None
        @param parent=None ancestor of this object or None
        """
        BasicItemModel.__init__(self, RootHistDataItem(), parent)
        self.requests = {}
        self.session = session
        if session is not None:
            session.registerMeta(self)
        self.startTimer(1000)

    def data(self, index, role):
        """ Framework hook to retreive data stored at index for given role.

        @param index QModelIndex instance
        @param role Qt.DisplayRole flags
        @return QVariant instance
        """
        if not index.isValid():
            return QVariant()
        item = index.internalPointer()
        data = QVariant()
        column = index.column()
        amChild = index.parent().isValid()
        if role == Qt.DecorationRole and column==2:
            if not amChild:
                data = QVariant(self.symbolIcon(item.symbol()))
        elif role in (Qt.DisplayRole, Qt.ToolTipRole):
            if amChild and (column==0):
                data = QVariant(item.row())
            else:
                data = QVariant(item[column])
        elif role in (Qt.TextAlignmentRole, ):
            try:
                float(item[column])
                data = QVariant(valueAlign)
            except (TypeError, ValueError, ):
                pass
        return data

    def findHistDataItem(self, reqId):
        """ Returns the item for the given hist data message, or None.

        """
        items = self.invisibleRootItem.children
        try:
            return [i for i in items if i.reqId==reqId][0]
        except (IndexError, ):
            pass

    def on_session_HistoricalData(self, message):
        """ Called when the session receives a HistoricalData message.

        @param message ib.opt.message instance
        """
        reqId = message.reqId
        req = self.requests.get(reqId, {})
        item = self.findHistDataItem(reqId)
        if item:
            item.append(HistDataItem.fromMessage(reqId, message, item, req))
            if message.date.startswith('finished'):
                item.setStatus('Finished')
                self.emit(Signals.histdata.finish, reqId)
        else:
            root = self.invisibleRootItem
            root.append(HistDataItem.fromMessage(reqId, message, root, req))
            self.emit(Signals.histdata.start, reqId)
        ## cheater
        self.reset()

    def on_session_historicalDataRequest(self, params):
        """ Called when a request for historical data is made.

        """
        reqId = params['tickerId']
        requests = self.requests
        if reqId in requests:
            logging.warn('Ignoring duplicate hist data request %s', reqId)
            return
        requests[reqId] = params.copy()
        root = self.invisibleRootItem
        root.append(HistDataItem.fromRequest(reqId, params, root))
        self.reset()

    def busy(self):
        for item in iter(self.invisibleRootItem.children):
            if item[1] == States.active:
                return True

    def next(self):
        for item in iter(self.invisibleRootItem.children):
            if item[1] == States.unsubmitted and item.req:
                return item

    def timerEvent(self, event):
        if not self.session.isConnected() or self.busy():
            return
        next = self.next()
        if next:
            self.session.connection.reqHistoricalData(**next.req)


class States(object):
    unsubmitted, active, finished, errored = range(4)
    labelMap = {
        unsubmitted:'Unsubmitted',
        active:'Active',
        finished:'Finished',
        errored:'Errored',
    }


class HistDataItem(BasicItem):
    """ Base class for items in the portfolio model.

    """
    columnLookups = [
        ('Request Id', lambda x:x.reqId),
        ('Status', lambda x:x.request.status),
        ('Symbol', lambda x:x.request.contract.symbol),
        ('Date', lambda x:x.date),
        ('Open', lambda x:x.open),
        ('High', lambda x:x.high),
        ('Low', lambda x:x.low),
        ('Close', lambda x:x.close),
        ('Volume', lambda x:x.volume),
        ('Count', lambda x:x.count),
        ('Weighted Average Price', lambda x:x.WAP),
        ('Has Gaps', lambda x:x.hasGaps),
    ]

    def __init__(self, data, parent=None, message=None,
                 reqId=None,
                 req={},
                 state=States.unsubmitted):
        BasicItem.__init__(self, data, parent)
        self.message = message
        self.reqId = reqId
        self.req = req
        self.state = state

    def setStatus(self, text):
        self.data[1] = text

    @classmethod
    def fromRequest(cls, requestId, params, parent):
        """ New instance from a request

        @param cls class object
        @param requestId client identifier for request as int
        @param params request parameter as dictionary
        @param parent parent of this item
        @return new instance of cls
        """
        values = [None for item in cls.columnLookups]
        values[0] = requestId
        return cls(values, parent, None, requestId, params.copy())

    @classmethod
    def fromMessage(cls, requestId, message, parent, request):
        """ New instance from message values

        @param cls class object
        @param requestId client identifier for request as int
        @param message ib.opt.message object
        @param parent parent of this item
        @return new instance of cls
        """
        values = []
        for label, lookup in cls.columnLookups:
            try:
                value = lookup(message)
            except (AttributeError, ):
                value = None
            values.append(value)
        item = cls(values, parent, message, requestId, request)
        if message.date.startswith('finished-'):
            parent.data[1] = item.data[1] = States.labelMap[States.finished]
            item[2:] = [None for i in item[2:]]
        return item

    def symbol(self):
        """ Returns the symbol for this item or ''

        """
        try:
            return self.message.contract.m_symbol
        except (AttributeError, ):
            return ''

    def update(self, message):
        """ Update the item with values from a message.

        @param message ib.opt.message object
        @return None
        """
        for column, (label, lookup) in enumerate(self.columnLookups):
            try:
                self[column] = lookup(message)
            except (AttributeError, ):
                pass


class RootHistDataItem(HistDataItem):
    """ HistData model item with automatic values (for horizontal headers).

    """
    def __init__(self):
        HistDataItem.__init__(self, self.horizontalLabels())

    def horizontalLabels(self):
        """ Generates list of horizontal header values.

        """
        return map(QVariant, [label for label, lookup in self.columnLookups])


## params = {'endDateTime': '20080707 08:00:00',
##  'durationStr': '2 D',
##  'whatToShow': 'TRADES',
##  'contract': <ib.ext.Contract.Contract object at 0x8dd8f0c>,
##  'barSizeSetting': '1 min',
##  'formatDate': 1,
##  'tickerId': 1146,
##  'useRTH': 1}
