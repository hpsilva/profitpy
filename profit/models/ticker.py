#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from PyQt4.QtCore import Qt, QModelIndex, QVariant, QString
from profit.lib import valueAlign
from profit.models import BasicItem, BasicItemModel


class TickerModel(BasicItemModel):
    """ Model for a single ticker.

    """
    def __init__(self, session=None, parent=None):
        BasicItemModel.__init__(self, TickerRootItem(), parent)
        self.symbolIcon = lambda x:None
        self.session = session
        if session is not None:
            session.registerMeta(self)
