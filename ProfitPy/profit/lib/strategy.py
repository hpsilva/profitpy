#!/usr/bin/env python
##~
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
##~
""" strategy

"""
import profit.lib.base as base
import profit.lib.series as series

Reverse = base.Directions.Reverse
NoReverse = base.Directions.NoReverse
NoSignal = base.Directions.NoSignal

Short = base.Directions.Short
Long = base.Directions.Long
NoDirection = base.Directions.NoDirection

OpenCloseLookup = {
    NoReverse : 'O', 
    Reverse : 'C',
}


class StrategyIndex(series.SeriesIndex):
    def __init__(self, ser, trade_shares):
        series.SeriesIndex.__init__(self, ser)
        self.trade_shares = trade_shares
        self.indication = (NoDirection, NoReverse)
        self.history = [] ## required for nice plots
        self.position = 0

    def reindex(self):
        signal = self.query()
        ser = self.series
        shares = self.trade_shares
        lastposition = self.position
        reverse = 0
        x = len(ser) - 1
        y = ser[-1]

        if lastposition and signal:
            if (abs(lastposition) / lastposition) != signal:
                reverse = 1

        if signal:
            self.indication = (signal, reverse)
        else:
            self.indication = (NoDirection, NoReverse)

        if lastposition and not reverse:
            quan = shares * signal
            self.position += quan
        elif lastposition and reverse:
            quan = -lastposition
            self.position = 0
        else:
            quan = shares * signal
            self.position += quan

        open_close = OpenCloseLookup[reverse]
        order = base.Order(quantity=quan, limit_price=y, 
                           transmit=0, open_close=open_close)
        record = (x, y, signal, reverse, shares, self.position, order)

        self.history.append(record)
        self.append(signal)


    def summary(self):
        """ summary() -> summarize the orders tracked with this object

        """
        ## simulate a final close order if there's an open position
        ## note that this screws up a call to summary on a live strategy
        if self.position:
            dr = -(self.position / abs(self.position))
            x = len(self.strategy.series)
            y = self.strategy.series[-1]
            self.save(x, y, direction=dr, reverse=1, shares=self.position)

        reports = []
        running_total = 0

        ## maybe need to track error rate here
        for order in [record[6] for record in self]:
            order_cost = base.Order.cost_long(order)
            running_total -= order_cost
            reports.append((order.limit_price, order_cost, running_total))

        return reports

    def query(self):
        exmsg = "Class %s does not reimplement 'query' method'"
        exmsg = exmsg % (self.__class__.__name__, )
        raise NotImplementedError(exmsg)
