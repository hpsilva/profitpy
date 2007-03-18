#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

def tickerUrls():
    return [
        'Profile:http://www.marketwatch.com/tools/quotes/profile.asp?symb=$symbol',
        'News:http://www.marketwatch.com/tools/quotes/news.asp?symb=$symbol',
        'Financials:http://www.marketwatch.com/tools/quotes/financials.asp?symb=$symbol',
        'Historical Quotes:http://www.marketwatch.com/tools/quotes/historical.asp?symb=$symbol'
        'Message Board:http://www.marketwatch.com/discussions/msgIndex.asp?symb=$symbol',
        'SEC Filings:http://www.marketwatch.com/tools/quotes/secfilings.asp?symb=$symbol',
        'Options:http://www.marketwatch.com/tools/quotes/options1.asp?symb=$symbol',
    ]

class connection:
    host = 'localhost'
    port = 7496
    client = 0
