from ui_selectionwidget import Ui_SelectionWidget
from centralcheckbox import CentralCheckBox
from PySide2 import QtWidgets, QtCore
import pickle


class SelectionWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = ...) -> None:
        super().__init__(parent)
        self.ui = Ui_SelectionWidget()
        self.ui.setupUi(self)

    def data_update(self, back):
        if back:
            return
        self.ui.table_selection.setRowCount(0)
        self.meta: QtCore.QByteArray = self.parent().input_pages[1].meta
        self.data = pickle.loads(self.meta.data())
        for i in self.data["page_data"]:
            box = CentralCheckBox()
            box.get_box().setChecked(True)
            i["box"] = box
            item_text = QtWidgets.QTableWidgetItem(i["name"])
            self.ui.table_selection.setRowCount(self.ui.table_selection.rowCount() + 1)
            self.ui.table_selection.setCellWidget(
                self.ui.table_selection.rowCount() - 1, 0, box
            )
            self.ui.table_selection.setItem(
                self.ui.table_selection.rowCount() - 1, 1, item_text
            )
