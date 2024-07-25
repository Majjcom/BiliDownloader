import pickle

from PySide6 import QtWidgets, QtCore

from centralcheckbox import CentralCheckBox
from ui_selectionwidget import Ui_SelectionWidget

SELECTTON_HELP = """输入你要下载的区段：

假设你要下载第一P和第二P，你可以输入：1-1, 2-2 或者输入1-2

如果要下载第一P到第五P，但是不要第三P，你可以输入：1-2, 4-5

最后，按下设置选集按钮完成设置"""


class SelectionWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = ...) -> None:
        super().__init__(parent)
        self.ui = Ui_SelectionWidget()
        self.ui.setupUi(self)
        self.meta = None
        self.data = None
        self.connect(
            self.ui.button_setSelection,
            QtCore.SIGNAL("clicked()"),
            self.on_set_button_clicked,
        )
        self.connect(
            self.ui.button_help,
            QtCore.SIGNAL("clicked()"),
            self.on_help_button_clicked,
        )

    def data_update(self, back):
        if back:
            return
        self.ui.table_selection.setRowCount(0)
        self.ui.button_next.setEnabled(True)
        self.meta: QtCore.QByteArray = self.parent().input_pages[1].meta
        self.data = pickle.loads(self.meta.data())
        for i in self.data["page_data"]:
            box = CentralCheckBox()
            box.get_box().setChecked(True)
            i["box"] = box
            self.connect(
                box.get_box(),
                QtCore.SIGNAL("toggled(bool)"),
                self.on_check_button_changed
            )
            item_text = QtWidgets.QTableWidgetItem(i["name"])
            self.ui.table_selection.setRowCount(self.ui.table_selection.rowCount() + 1)
            self.ui.table_selection.setCellWidget(
                self.ui.table_selection.rowCount() - 1, 0, box
            )
            self.ui.table_selection.setItem(
                self.ui.table_selection.rowCount() - 1, 1, item_text
            )

    # Slot
    def on_check_button_changed(self, _checked: bool):
        count = 0
        for i in self.data["page_data"]:
            box = i["box"]
            box = box.get_box()
            if box.isChecked():
                count += 1
        self.ui.button_next.setEnabled(count > 0)

    # Slot
    def on_help_button_clicked(self):
        QtWidgets.QMessageBox.information(self, "选集帮助", SELECTTON_HELP)

    # Slot
    def on_set_button_clicked(self):
        selection_str = self.ui.line_selection.text()
        selection_str = selection_str.replace(" ", "")
        selections = selection_str.split(",")
        selected = []
        select_max = -1
        if len(selections) == 0:
            QtWidgets.QMessageBox.critical(self, "错误", "语法错误")
            return
        for block in selections:
            rng = block.split('-')
            if len(rng) != 2:
                QtWidgets.QMessageBox.critical(self, "错误", "语法错误")
                return
            if not rng[0].isdigit() or not rng[1].isdigit():
                QtWidgets.QMessageBox.critical(self, "错误", "语法错误")
                return
            if int(rng[0]) < 1:
                QtWidgets.QMessageBox.critical(self, "错误", "语法错误")
                return
            if int(rng[0]) > int(rng[1]):
                QtWidgets.QMessageBox.critical(self, "错误", "语法错误")
                return
            if int(rng[1]) > len(self.data["page_data"]):
                QtWidgets.QMessageBox.critical(self, "错误", "选集过大")
                return
            if int(rng[0]) <= select_max:
                QtWidgets.QMessageBox.critical(self, "错误", "顺序错误")
                return

            for i in range(int(rng[0]) - 1, int(rng[1])):
                selected.append(i)
                select_max = i

        for i in self.data["page_data"]:
            i["box"].get_box().setChecked(False)

        for i in selected:
            self.data["page_data"][i]["box"].get_box().setChecked(True)
