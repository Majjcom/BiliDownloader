"""Page and dynamic-control addressing. Providers survive input page rebuilds."""

import re
from dataclasses import dataclass

from PySide2 import QtCore, QtWidgets

from .adapters import create_adapters
from .protocol import HeadlessError


@dataclass
class Header:
    table: object
    column: int


@dataclass
class TaskReference:
    task: dict


class Controls:
    def __init__(self, window, ledger):
        self.window = window
        self.ledger = ledger
        self.adapters = create_adapters()
        self.pages = {}
        self.register_page("main", lambda: window, lambda: True)
        for index, name in enumerate(("input", "confirm", "selection", "config")):
            self.register_page(
                name,
                lambda index=index: window.ui.widget_input.input_pages[index],
                lambda index=index: window.ui.tabWidget.currentIndex() == 0
                                    and window.ui.widget_input.current_input_page == index,
            )
        for index, name in enumerate(("download", "settings", "about"), 1):
            self.register_page(
                name,
                lambda index=index: window.tabs[index],
                lambda index=index: window.ui.tabWidget.currentIndex() == index,
            )

    def register_page(self, alias, provider, active):
        """Register a lazily resolved page and its logical availability."""
        self.pages[alias] = (provider, active)

    def page(self, alias):
        if alias not in self.pages:
            raise HeadlessError("未知页面：{}".format(alias))
        return self.pages[alias][0]()

    def active(self, target):
        alias = target.split(".", 1)[0]
        self.page(alias)
        return bool(self.pages[alias][1]())

    def require_active(self, target):
        if not self.active(target):
            raise HeadlessError("目标不在当前页面，请先切换页面：{}".format(target))

    def resolve(self, target):
        alias, separator, name = target.partition(".")
        root = self.page(alias)
        if not separator:
            return root
        match = re.fullmatch(r"(tasks|items)\[([^\]]+)\](?:\.([A-Za-z_]\w*))?", name)
        if alias == "download" and match:
            kind, identifier, control_name = match.groups()
            task = self.ledger.find(identifier)
            if kind == "tasks" and control_name is None:
                return TaskReference(task)
            if kind == "items" and control_name is not None:
                widget = task.get("widget")
                if widget is None:
                    raise HeadlessError("下载条目已清理；任务结果仍可通过 download.tasks 查询")
                control = getattr(widget.ui, control_name, None)
                if isinstance(control, QtWidgets.QWidget):
                    return control
            raise HeadlessError("无效的下载控件路径：{}".format(target))
        match = re.fullmatch(r"([A-Za-z_]\w*)\.header\[(\d+)\]", name)
        if match:
            table = getattr(root.ui, match.group(1), None)
            column = int(match.group(2)) - 1
            if isinstance(table, QtWidgets.QTableWidget) and 0 <= column < table.columnCount():
                return Header(table, column)
            raise HeadlessError("表头不存在：{}".format(target))
        match = re.fullmatch(r"([A-Za-z_]\w*)\[(\d+),(\d+)\]", name)
        if match:
            table = getattr(root.ui, match.group(1), None)
            row, column = int(match.group(2)) - 1, int(match.group(3)) - 1
            if not isinstance(table, QtWidgets.QTableWidget) or not (
                    0 <= row < table.rowCount() and 0 <= column < table.columnCount()):
                raise HeadlessError("表格单元格不存在：{}".format(target))
            cell = table.cellWidget(row, column)
            if cell is not None:
                return cell.get_box() if hasattr(cell, "get_box") else cell
            cell = table.item(row, column)
            if cell is None:
                raise HeadlessError("表格单元格为空：{}".format(target))
            return cell
        control = getattr(root.ui, name, None)
        if isinstance(control, QtWidgets.QWidget):
            return control
        raise HeadlessError("找不到控件：{}".format(target))

    def inspect(self, target):
        if target == "download.tasks":
            return {"target": target, "value": self.ledger.results(), "count": len(self.ledger.tasks)}
        if target in self.pages:
            root = self.page(target)
            result = {
                "target": target, "active": self.active(target),
                "controls": {
                    name: self.adapters.inspect(control)
                    for name, control in vars(root.ui).items()
                    if isinstance(control, QtWidgets.QWidget)
                },
            }
            if target == "main":
                result["current_tab"] = ("input", "download", "settings", "about")[
                    self.window.ui.tabWidget.currentIndex()]
                result["input_page"] = ("input", "confirm", "selection", "config")[
                    self.window.ui.widget_input.current_input_page]
            if target == "download":
                result["tasks"] = self.ledger.results()
            return result
        control = self.resolve(target)
        if isinstance(control, TaskReference):
            result = self.ledger.result(control.task)
        elif isinstance(control, Header):
            item = control.table.horizontalHeaderItem(control.column)
            result = {
                "value": item.text() if item is not None else "",
                "column": control.column + 1,
                "enabled": control.table.isEnabled(),
            }
        elif isinstance(control, QtWidgets.QTableWidgetItem):
            table = control.tableWidget()
            result = {
                "value": control.text(), "text": control.text(),
                "enabled": table.isEnabled() and bool(
                    control.flags() & QtCore.Qt.ItemFlag.ItemIsEnabled),
                "read_only": self._cell_read_only(control),
            }
        else:
            result = self.adapters.inspect(control)
        result.update(target=target, active=self.active(target))
        return result

    def list_controls(self, alias):
        aliases = list(self.pages) if alias == "all" else [alias]
        result = []
        for name in aliases:
            page = self.page(name)
            for control_name, control in vars(page.ui).items():
                if not isinstance(control, QtWidgets.QWidget):
                    continue
                target = name + "." + control_name
                result.append({
                    "target": target, "class": type(control).__name__,
                    "active": self.active(target), "enabled": control.isEnabled(),
                })
                if isinstance(control, QtWidgets.QTableWidget):
                    for row in range(control.rowCount()):
                        for column in range(control.columnCount()):
                            result.append({
                                "target": "{}[{},{}]".format(target, row + 1, column + 1),
                                "kind": "cell",
                            })
                    for column in range(control.columnCount()):
                        result.append({
                            "target": "{}.header[{}]".format(target, column + 1),
                            "kind": "header",
                        })
        if alias in ("all", "download"):
            for index, task in enumerate(self.ledger.tasks, 1):
                result.append({
                    "target": "download.tasks[{}]".format(index), "id": self.ledger.identifier(task),
                })
                widget = task.get("widget")
                if widget is not None:
                    for name, control in vars(widget.ui).items():
                        if isinstance(control, QtWidgets.QWidget):
                            result.append({
                                "target": "download.items[{}].{}".format(index, name),
                                "id": self.ledger.identifier(task),
                                "class": type(control).__name__, "enabled": control.isEnabled(),
                            })
        return result

    def mutable(self, target):
        self.require_active(target)
        control = self.resolve(target)
        if isinstance(control, (Header, TaskReference)):
            raise HeadlessError("目标不是可直接修改的控件")
        if isinstance(control, QtWidgets.QTableWidgetItem):
            if not control.tableWidget().isEnabled():
                raise HeadlessError("表格不可用")
            return control
        if not control.isEnabled():
            raise HeadlessError("控件不可用：{}".format(target))
        return control

    def set(self, target, value):
        control = self.mutable(target)
        if isinstance(control, QtWidgets.QTableWidgetItem):
            flags = control.flags()
            if not flags & QtCore.Qt.ItemFlag.ItemIsEnabled or self._cell_read_only(control):
                raise HeadlessError("不能修改只读或禁用的表格单元格")
            control.setText(value)
        else:
            self.adapters.set(control, value)

    @staticmethod
    def _cell_read_only(control):
        return (
                not bool(control.flags() & QtCore.Qt.ItemFlag.ItemIsEditable)
                or control.tableWidget().editTriggers()
                == QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )

    def click(self, target):
        # Check restrictions by object identity, not just the supplied alias.
        control = self.resolve(target)
        settings = self.window.ui.widget_settings.ui
        blocked = (settings.button_login, settings.button_logout,
                   settings.button_config_dir, settings.button_open_download_dir)
        if any(control is item for item in blocked):
            raise HeadlessError("headless 不支持登录变更或打开外部窗口：{}".format(target))
        for task in self.ledger.tasks:
            widget = task.get("widget")
            if widget is None:
                continue
            if control is widget.ui.button_pause or control is widget.ui.button_open:
                raise HeadlessError("headless 不支持暂停/继续或打开目录")
            if control is widget.ui.button_restart and task["state"] != "failed":
                raise HeadlessError("headless 仅允许对失败任务重新开始")
        control = self.mutable(target)
        if not isinstance(control, QtWidgets.QAbstractButton):
            raise HeadlessError("--click 需要按钮或复选框")
        control.click()

    def double_click(self, target):
        self.require_active(target)
        control = self.resolve(target)
        if not isinstance(control, Header):
            raise HeadlessError("当前只支持对表头执行 --double-click")
        if not control.table.isEnabled():
            raise HeadlessError("表格不可用")
        control.table.horizontalHeader().sectionDoubleClicked.emit(control.column)

    def tab(self, alias):
        names = ("input", "download", "settings", "about")
        if alias not in names:
            raise HeadlessError("--tab 需要 input/download/settings/about")
        self.window.change_tab(names.index(alias))
