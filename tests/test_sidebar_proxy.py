import pytest

from PyQt6.QtCore import QSortFilterProxyModel, Qt
from PyQt6.QtGui import QStandardItem, QStandardItemModel

from editor.sidebar import RecursiveFilterProxyModel


@pytest.fixture
def proxy_model():
    model = QStandardItemModel()
    root = model.invisibleRootItem()
    empty_item = QStandardItem()
    root.appendRow(empty_item)

    proxy = RecursiveFilterProxyModel()
    proxy.setSourceModel(model)
    proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
    proxy.setFilterFixedString("needle")
    return proxy


def test_filter_accepts_row_empty_data(proxy_model):
    index = proxy_model.sourceModel().index(0, 0)
    assert proxy_model.filterAcceptsRow(0, index.parent()) is False
