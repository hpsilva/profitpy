#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>


import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s')

def importName(name):
    """ import and return a module by name in dotted form

    Copied from the Python lib docs.

    @param name module name as string
    @return module object
    """
    mod = __import__(name)
    for comp in name.split('.')[1:]:
        mod = getattr(mod, comp)
    return mod


def importItem(name):
    """ import an item from a module by dotted name

    @param name module and attribute string, i.e., foo.bar.baz
    @return value of name from module
    """
    names = name.split('.')
    modname, itemname = names[0:-1], names[-1]
    mod = importName(str.join('.', modname))
    return getattr(mod, itemname)
