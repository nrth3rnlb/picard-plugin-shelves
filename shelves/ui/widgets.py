from typing import Optional

from PyQt5 import QtCore, QtGui, QtWidgets


class QShelvesWidget(QtWidgets.QListWidget):
    """
    Custom QListWidget that supports limiting the number of items it can contain.
    """

    UNLIMITED: int = 0
    _max_item_count: int = UNLIMITED

    def __init__(
        self,
        parent: Optional[QtWidgets.QWidget] = None,
        max_count: int = UNLIMITED,
    ):
        super().__init__(parent)

        # self._max_item_count: int = self.UNLIMITED
        self.max_item_count = max_count
        self._update_drop_acceptance()

    @property
    def max_item_count(self):
        """
        Gets the maximum item count allowed.

        :return: The maximum number of items permitted.
        :rtype: int
        """
        return self._max_item_count

    @max_item_count.setter
    def max_item_count(self, value: int):
        """
        Sets the maximum number of items that are allowed.

        :param value: The maximum count of items to be set. Must be an integer and comply with
            the constraints of the system.
        :type value: int
        :return: None
        :rtype: None
        """
        normalized = max(0, int(value))
        if normalized == self._max_item_count:
            return

        self._max_item_count = normalized
        self._update_drop_acceptance()

    def dropEvent(self, event: Optional[QtGui.QDropEvent]) -> None:
        """

        :param event:
        :type event:
        :return:
        :rtype:
        """
        if not event:
            return

        if self._max_item_count <= self.UNLIMITED:
            super().dropEvent(event)
            return

        source = event.source()
        if not isinstance(source, QShelvesWidget):
            event.ignore()
            return
        event.setDropAction(QtCore.Qt.DropAction.MoveAction)

        selected_items = source.selectedItems()
        if not selected_items:
            event.ignore()
            return

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
            self.max_item_count <= self.UNLIMITED
            or self.count() <= self.max_item_count,
        )
