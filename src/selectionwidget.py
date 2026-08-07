import pickle

from PySide2 import QtWidgets, QtCore
from ui_selectionwidget import Ui_SelectionWidget

from centralcheckbox import CentralCheckBox

SELECTTON_HELP = """输入你要下载的区段：
区段使用单集数字或 A-B 的格式指定头尾，使用英文逗号(,)分割多个区段。
如果不输入内容点击设置选集则对全部选项进行反选操作。

举例：
假设你要下载第一P和第二P，你可以输入：1-2 或者输入 1, 2

如果要下载第一P到第五P，但是不要第三P，你可以分成两个区段以规避3：1-2, 4-5

最后，按下设置选集按钮完成设置。"""


class SelectionWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget = ...) -> None:
        super().__init__(parent)
        self.ui = Ui_SelectionWidget()
        self.ui.setupUi(self)
        self.meta = None
        self.data = None
        self.ui.button_setSelection.clicked.connect(self.on_set_button_clicked)
        self.ui.button_help.clicked.connect(self.on_help_button_clicked)

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
            box.get_box().toggled.connect(self.on_check_button_changed)
            item_text = QtWidgets.QTableWidgetItem(i["name"])
            self.ui.table_selection.setRowCount(self.ui.table_selection.rowCount() + 1)
            self.ui.table_selection.setCellWidget(
                self.ui.table_selection.rowCount() - 1, 0, box
            )
            self.ui.table_selection.setItem(
                self.ui.table_selection.rowCount() - 1, 1, item_text
            )

    @QtCore.Slot(bool)
    def on_check_button_changed(self, _checked: bool):
        count = 0
        for i in self.data["page_data"]:
            box = i["box"]
            box = box.get_box()
            if box.isChecked():
                count += 1
        self.ui.button_next.setEnabled(count > 0)

    @QtCore.Slot()
    def on_help_button_clicked(self):
        QtWidgets.QMessageBox.information(self, "选集帮助", SELECTTON_HELP)

    @QtCore.Slot()
    def on_set_button_clicked(self):
        selection_str = self.ui.line_selection.text()

        # Defult to select all
        if len(selection_str) == 0:
            for i in self.data["page_data"]:
                tmp = i["box"].get_box()
                tmp.setChecked(not tmp.isChecked())
            return

        selection_str = selection_str.replace(" ", "")
        selections = selection_str.split(",")
        selected = []
        select_max = -1
        if len(selections) == 0:
            QtWidgets.QMessageBox.critical(self, "错误", "语法错误")
            return
        for block in selections:
            if '-' in block:
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
            else:
                if not block.isdigit():
                    QtWidgets.QMessageBox.critical(self, "错误", "选集不是数字")
                    return
                if int(block) < 1:
                    QtWidgets.QMessageBox.critical(self, "错误", "语法错误")
                    return
                if int(block) > len(self.data["page_data"]):
                    QtWidgets.QMessageBox.critical(self, "错误", "选集过大")
                    return
                if int(block) <= select_max:
                    QtWidgets.QMessageBox.critical(self, "错误", "顺序错误")
                    return
                rng = [int(block)] * 2

            for i in range(int(rng[0]) - 1, int(rng[1])):
                selected.append(i)
                select_max = i

        for i in self.data["page_data"]:
            i["box"].get_box().setChecked(False)

        for i in selected:
            self.data["page_data"][i]["box"].get_box().setChecked(True)
