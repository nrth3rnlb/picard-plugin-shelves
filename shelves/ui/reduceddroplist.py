from typing import Optional

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QAbstractItemView
from picard import log


class ReducedDropList(QtWidgets.QListWidget):

    itemCountChanged = QtCore.pyqtSignal(int)

    MAX_ITEM_COUNT = 1

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)

        self.setDragEnabled(True)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        log.debug("dropEvent called, event: %s", event)

        source = event.source()
        if not isinstance(source, QtWidgets.QListWidget):
            event.ignore()
            return

        event.setDropAction(QtCore.Qt.MoveAction)

        if self.count() >= self.MAX_ITEM_COUNT:
            event.ignore()
            return

        selected_items = source.selectedItems()
        if not selected_items:
            event.ignore()
            return

        for i, it in enumerate(selected_items):
            if i >= self.MAX_ITEM_COUNT: event.ignore(); return
            log.debug("mit %s", it.text())
            clone = it.clone()
            self.addItem(clone)
            source.takeItem(source.row(it))
        event.accept()

    def _on_rows_changed(self, parent: QtCore.QModelIndex, first: int, last: int) -> None:
        self.setAcceptDrops(self.count() <= self.MAX_ITEM_COUNT)