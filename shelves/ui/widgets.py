from typing import Optional

from PyQt5 import QtCore, QtWidgets, QtGui
from picard import log


class MaxItemsDropListWidget(QtWidgets.QListWidget):
    itemCountChanged = QtCore.pyqtSignal(int)

    UNLIMITED = 0

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)

        self._max_item_count: int = self.UNLIMITED
        self._update_drop_acceptance()

    def maximumItemCount(self) -> int:
        return self._max_item_count

    def setMaximumItemCount(self, count: int = UNLIMITED) -> None:
        normalized = max(0, int(count))
        if normalized == self._max_item_count:
            return

        self._max_item_count = normalized
        self._update_drop_acceptance()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        if self._max_item_count <= self.UNLIMITED:
            super().dropEvent(event)
            return

        source = event.source()
        if not isinstance(source, QtWidgets.QListWidget):
            event.ignore()
            return
        event.setDropAction(QtCore.Qt.MoveAction)

        selected_items = source.selectedItems()
        if not selected_items:
            event.ignore()
            return

        log.debug(
            "already available: %s, to add: %s, maximum: %s",
            self.count(),
            len(selected_items),
            self._max_item_count,
        )
        if self.count() + len(selected_items) > self._max_item_count:
            event.ignore()
            return

        for item in selected_items:
            clone = item.clone()
            self.addItem(clone)
            source.takeItem(source.row(item))

        event.accept()

    def _update_drop_acceptance(self) -> None:
        # 0 means "unlimited"
        self.setAcceptDrops(
            self._max_item_count <= self.UNLIMITED
            or self.count() <= self._max_item_count
        )
