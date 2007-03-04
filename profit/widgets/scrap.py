class __CallableItem():
    icons = {
        pyclbr.Class : 'blockdevice',
        pyclbr.Function : 'exec',
        'method' : 'network',
    }

    def __init__(self, parent, text, descriptor, includeMethods=False):
        QStandardItem.__init__(self, parent)
        self.setText(text)
        iconame = self.icons.get(descriptor,
                                 self.icons.get(descriptor.__class__))
        #if iconame:
        #    self.setPixmap(0, util.loadIcon(iconame))
        ## change this to if includeMethods first
        try:
            methods = descriptor.methods
        except (AttributeError, ):
            pass
        else:
            if includeMethods:
                for name in methods:
                    CallableViewItem(self, name, 'method')


class __ImportableItem(QStandardItem):
    icons = sourceIcons()

    def __init__(self, name, label, full=False, parent=None):
        print '## ImportableItem', name, label, full, parent

        QStandardItem.__init__(self)
        self.setText(label)
        self.setEditable(False)
        self.name = name
        try:
            self.name = name = join(parent.name, name)
        except (AttributeError, ):
            pass
        ico = self.iconForPath(name)
        if ico:
            self.setIcon(ico)
        self.isDir = isdir = isdir(name)
        self.isSrc = issrc = splitext(name)[-1] in pyExts
        if isdir:
            paths = [join(name, p) for p in listdir(name)]
            paths = [p for p in paths if self.pathContentFilter(p)]
            #self.setColumnCount(2)
            #self.setRowCount(len(paths))
            #    self.setExpanded(True)
        elif issrc:
            pathname, filename = split(name)
            filename = splitext(filename)[0]
            try:
                readmodule = pyclbr.readmodule_ex
                self.pyitems = items = readmodule(filename, [pathname, ])
                #if items:
                #    self.setExpanded(True)
                #self.setColumnCount(2)
                #self.setRowCount(len(items))
            except (ImportError, ):
                pass

    def setExpanded(self, which):
        """ setExpanded(which) -> add or remove items

        """
        if which:
            if self.isSrc:
                items = self.pyitems.items()
                items = [(name, desc)
                            for name, desc in items
                                if not name.startswith('_')]
                items.sort()
                items.reverse()
                for name, desc in items:
                    CallableItem(self, name, desc)
            else:
                name = self.name
                paths = [join(name, p) for p in listdir(name)]
                paths = [p for p in paths if self.pathContentFilter(p)]
                paths.sort()
                paths.reverse()
                for path in paths:
                    ImportableItem(self, path, basename(path))
        QStandardItem.setExpanded(self, which)

    def iconForPath(self, item):
        """ Provides an icon appropriate to the item.

        """
        return QIcon()
        #if isdir(item):
        #    return util.loadIcon('folder')
        #name = self.icons.get(splitext(item)[-1], None)
        #if name:
        #    return util.loadIcon(name)

    @staticmethod
    def pathContentFilter(item, exts=pyExts):
        """ True if item is a package, module, or source.

        """
        ispkg = isdir(item) and ('__init__.py' in listdir(item))
        issrc = splitext(item)[-1] in exts
        return ispkg or issrc

    def selectPath(self):
        """ selectPath() -> tracks item selection to path construction

        """
        path = []
        try:
            item = self.view.selectedItems()[0]
        except (IndexError, ):
            return
        while item:
            txt = '%s' % (item.text(0), )
            name, ext = splitext(txt)
            if ext in pyExts:
                txt = name
            path.append(txt)
            item = item.parent()
        path.reverse()
        self.path = path[1:]

    def printPath(self):
        """ printPath() -> simple pprint

        """
        import pprint
        pprint.pprint(self.path, sys.__stdout__)





if 0:
    if 0:
        try:
            name = self.iconNameMap[key]
            icon = QIcon(':images/icons/%s.png' % name)
        except (KeyError, ):
            style = QApplication.style()
            icon = style.standardIcon(style.SP_DirIcon)
        return icon


