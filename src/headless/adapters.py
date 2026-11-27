"""Extensible, typed widget readers/writers; no arbitrary QObject invocation."""

from PySide6 import QtCore, QtWidgets

from .protocol import HeadlessError, boolean


class AdapterRegistry:
    def __init__(self):
        self._adapters = []

    def register(self, widget_type, reader, writer=None):
        """Last registration wins, so custom widgets can override Qt defaults."""
        self._adapters.insert(0, (widget_type, reader, writer))

    def _find(self, widget):
        for widget_type, reader, writer in self._adapters:
            if isinstance(widget, widget_type):
                return reader, writer
        raise HeadlessError("不支持的控件类型：{}".format(type(widget).__name__))

    def inspect(self, widget):
        reader, unused = self._find(widget)
        result = {
            "class": type(widget).__name__,
            "object_name": widget.objectName(),
            "enabled": widget.isEnabled(),
            # The root window deliberately remains invisible. Logical page
            # availability is reported separately as 'active'.
            "visible": widget.isVisible(),
            "tooltip": widget.toolTip(),
        }
        result.update(reader(widget))
        return result

    def set(self, widget, value):
        unused, writer = self._find(widget)
        if writer is None:
            raise HeadlessError("该控件不支持设置值")
        writer(widget, value)


def _set_line(widget, value):
    if widget.isReadOnly():
        raise HeadlessError("不能修改只读输入框")
    widget.setText(value)


def _set_text(widget, value):
    if widget.isReadOnly():
        raise HeadlessError("不能修改只读文本框")
    widget.setPlainText(value)


def _read_button(widget):
    result = {"text": widget.text(), "checkable": widget.isCheckable()}
    if widget.isCheckable():
        result.update(value=widget.isChecked(), checked=widget.isChecked())
    else:
        result["value"] = widget.text()
    return result


def _set_button(widget, value):
    if not widget.isCheckable():
        raise HeadlessError("按钮不是可勾选控件，请使用 --click")
    if isinstance(widget, QtWidgets.QCheckBox) and widget.isTristate():
        raise HeadlessError("三态复选框需要专用适配器")
    widget.setChecked(boolean(value))


def _combo_index(widget, value):
    if value.startswith("@"):
        try:
            index = int(value[1:]) - 1
        except ValueError:
            raise HeadlessError("选项序号格式为 @1、@2 等")
        if 0 <= index < widget.count():
            return index
    else:
        index = widget.findText(value, QtCore.Qt.MatchFlag.MatchExactly)
        if index >= 0:
            return index
    raise HeadlessError("下拉框没有该选项：{}".format(value))


def _set_combo(widget, value):
    index = _combo_index(widget, value)
    model_item = widget.model().index(index, widget.modelColumn(), widget.rootModelIndex())
    if not widget.model().flags(model_item) & QtCore.Qt.ItemFlag.ItemIsEnabled:
        raise HeadlessError("该选项不可用")
    widget.setCurrentIndex(index)
    # Non-editable QComboBox normally also emits activated on user selection.
    widget.activated.emit(index)


def _set_spin(widget, value):
    try:
        number = float(value) if isinstance(widget, QtWidgets.QDoubleSpinBox) else int(value)
    except ValueError:
        raise HeadlessError("数值格式错误：{}".format(value))
    if not widget.minimum() <= number <= widget.maximum():
        raise HeadlessError("数值超出范围 {}..{}".format(widget.minimum(), widget.maximum()))
    if widget.isReadOnly():
        raise HeadlessError("不能修改只读数值框")
    widget.setValue(number)


def _set_tab(widget, value):
    if value.startswith("@"):
        try:
            index = int(value[1:]) - 1
        except ValueError:
            raise HeadlessError("页面序号格式为 @1、@2 等")
    else:
        index = next((i for i in range(widget.count()) if widget.tabText(i) == value), -1)
    if not 0 <= index < widget.count() or not widget.isTabEnabled(index):
        raise HeadlessError("无效或不可用的页面：{}".format(value))
    widget.setCurrentIndex(index)


def create_adapters():
    adapters = AdapterRegistry()
    adapters.register(QtWidgets.QWidget, lambda w: {"value": None})
    adapters.register(QtWidgets.QLineEdit, lambda w: {
        "value": w.text(), "text": w.text(), "read_only": w.isReadOnly(),
        "placeholder": w.placeholderText(),
    }, _set_line)
    adapters.register((QtWidgets.QTextEdit, QtWidgets.QPlainTextEdit), lambda w: {
        "value": w.toPlainText(), "text": w.toPlainText(), "read_only": w.isReadOnly(),
    }, _set_text)
    adapters.register(QtWidgets.QAbstractButton, _read_button, _set_button)
    adapters.register(QtWidgets.QComboBox, lambda w: {
        "value": w.currentText(), "text": w.currentText(),
        "current_index": w.currentIndex() + 1,
        "count": w.count(), "options": [w.itemText(i) for i in range(w.count())],
    }, _set_combo)
    adapters.register((QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox), lambda w: {
        "value": w.value(), "minimum": w.minimum(), "maximum": w.maximum(),
        "read_only": w.isReadOnly(),
    }, _set_spin)
    adapters.register(QtWidgets.QProgressBar, lambda w: {
        "value": w.value(), "minimum": w.minimum(), "maximum": w.maximum(),
    })

    def read_label(widget):
        result = {"value": widget.text(), "text": widget.text()}
        pixmap = widget.pixmap()
        if pixmap is not None and not pixmap.isNull():
            result["image"] = {"width": pixmap.width(), "height": pixmap.height()}
        return result

    adapters.register(QtWidgets.QLabel, read_label)
    adapters.register(QtWidgets.QTabWidget, lambda w: {
        "value": w.currentIndex() + 1,
        "current_index": w.currentIndex() + 1,
        "count": w.count(), "options": [w.tabText(i) for i in range(w.count())],
    }, _set_tab)

    def cell_value(table, row, column):
        widget = table.cellWidget(row, column)
        if widget is not None:
            if hasattr(widget, "get_box"):
                widget = widget.get_box()
            return adapters.inspect(widget)
        item = table.item(row, column)
        return None if item is None else item.text()

    def read_table(table):
        rows = [
            [cell_value(table, row, column) for column in range(table.columnCount())]
            for row in range(table.rowCount())
        ]
        return {
            "value": rows, "rows": rows, "row_count": table.rowCount(),
            "column_count": table.columnCount(),
            "headers": [
                table.horizontalHeaderItem(i).text()
                if table.horizontalHeaderItem(i) is not None else ""
                for i in range(table.columnCount())
            ],
        }

    adapters.register(QtWidgets.QTableWidget, read_table)

    def read_list(widget):
        items = []
        for index in range(widget.count()):
            item = widget.item(index)
            child = widget.itemWidget(item)
            entry = {"index": index + 1, "text": item.text()}
            if child is not None and hasattr(child, "ui"):
                entry["controls"] = {
                    name: adapters.inspect(control)
                    for name, control in vars(child.ui).items()
                    if isinstance(control, QtWidgets.QWidget)
                }
            items.append(entry)
        return {"value": items, "count": widget.count(), "items": items}

    adapters.register(QtWidgets.QListWidget, read_list)
    return adapters
