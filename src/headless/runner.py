"""Timer-driven sequential execution; modal Qt event loops cannot reenter steps."""

import os
import time

from PySide6 import QtCore, QtWidgets

from utils import configUtils
from utils.video_codec import video_codec_id

from .controls import Controls
from .dialogs import DialogPolicy
from .protocol import HeadlessError, emit, expected_value
from .tasks import TaskLedger


class Runner(QtCore.QObject):
    error_received = QtCore.Signal(str)
    interrupt_received = QtCore.Signal()

    def __init__(self, app, window, args, operations):
        super().__init__(app)
        self.app = app
        self.window = window
        self.args = args
        self.operations = operations
        self.download = window.ui.widget_download
        self.position = 0
        self.exit_code = 0
        self._busy = False
        self._failed = False
        self._closing = False
        self._cancelled = False
        self._load_started = {}
        self._wait_started = None
        self._download_started = None
        self._cleanup_started = False
        self.ledger = TaskLedger(self.download, self._task_added)
        self.controls = Controls(window, self.ledger)
        self.dialogs = DialogPolicy(app, self.fail)
        self.readiness = {}
        for alias in ("confirm", "config"):
            self.register_readiness(alias, lambda alias=alias: self._input_ready(alias))
        self.handlers = {}
        self.register_operation("set", self.controls.set)
        self.register_operation("click", self.controls.click)
        self.register_operation("tab", self.controls.tab)
        self.register_operation("double-click", self.controls.double_click)
        self.register_operation("respond", self.dialogs.respond)
        self.register_operation("dialog-path", self.dialogs.path)
        self.register_operation("get", self._get)
        self.register_operation("inspect", self._inspect)
        self.register_operation("list-controls", self._list)
        self.register_operation("export", self._export)
        self.register_operation("quality", self._quality)
        self.register_operation("language", self._language)
        self.register_operation("formats", self._formats)
        self.error_received.connect(lambda message: self.fail(HeadlessError(message)))
        self.interrupt_received.connect(self.interrupt)
        window.ui.tabWidget.currentChanged.connect(self._apply_settings)
        self._apply_settings()
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(25)
        self.timer.timeout.connect(self._tick)

    def register_operation(self, name, handler):
        """Extend execution with an explicit, typed operation handler."""
        self.handlers[name] = handler

    def register_readiness(self, name, probe):
        """A probe returns False while loading, True when ready, or raises."""
        self.readiness[name] = probe

    def start(self):
        self.timer.start()

    def _task_added(self, task):
        if self._download_started is None:
            self._download_started = time.monotonic()

    @QtCore.Slot(int)
    def _apply_settings(self, unused=None):
        count = configUtils.getUserData(configUtils.Configs.MAX_THREAD_COUNT, 4)
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            raise HeadlessError("下载并发数必须为正整数")
        self.download.max_thread_count = count

    def _get(self, target):
        info = self.controls.inspect(target)
        emit("query", target=target, value=info.get("value", info))

    def _inspect(self, target):
        emit("inspect", target=target, value=self.controls.inspect(target))

    def _list(self, alias):
        emit("controls", page=alias, value=self.controls.list_controls(alias))

    def _export(self, target, path):
        self.controls.require_active(target)
        control = self.controls.resolve(target)
        confirm = self.controls.page("confirm")
        if control is not confirm.ui.cover_label:
            raise HeadlessError("--export 当前仅支持 confirm.cover_label")
        if confirm.img is None or confirm.img.isNull():
            raise HeadlessError("没有可导出的封面")
        if not os.path.isdir(os.path.dirname(path)):
            raise HeadlessError("封面保存目录不存在")
        self.dialogs.paths.appendleft(path)
        confirm.save_cover()
        actual_path = path if path.endswith(".png") else path + ".png"
        if not self._failed and not os.path.isfile(actual_path):
            raise HeadlessError("封面导出失败：{}".format(actual_path))

    def _quality(self, value):
        page = self.controls.page("config")
        if value.lower() == "best":
            if not page.quality_match:
                raise HeadlessError("没有可用画质")
            value = max(page.quality_match, key=page.quality_match.get)
        elif value.isdigit():
            value = next(
                (name for name, quality in page.quality_match.items() if quality == int(value)),
                value,
            )
        self.controls.set("config.combo_quality", value)

    def _language(self, value):
        page = self.controls.page("config")
        value = next(
            (name for name, language in page.ai_language_title_map.items() if language == value),
            value,
        )
        self.controls.set("config.combo_ai_language", value)

    def _formats(self):
        page = self.controls.page("config")
        emit("query", target="config.formats", value={
            "quality": [{"id": value, "text": name}
                        for name, value in page.quality_match.items()],
            "codec": [{"id": value, "text": name} for value, name in video_codec_id.items()],
            "audio": [page.ui.combo_audio.itemText(i) for i in range(page.ui.combo_audio.count())],
            "ai_language": [{"id": value, "text": name}
                            for name, value in page.ai_language_title_map.items()],
        })

    def fail(self, error):
        if not isinstance(error, HeadlessError):
            error = HeadlessError(str(error))
        if not self._failed:
            operation = self.operations[self.position] if self.position < len(self.operations) else None
            emit("error", message=str(error), code=error.code,
                 step=self.position + 1 if operation is not None else None,
                 operation=operation.name if operation is not None else None)
        self._failed = True
        if self.exit_code == 0:
            self.exit_code = error.code

    @QtCore.Slot()
    def interrupt(self):
        self.fail(HeadlessError("操作已中断", 130))
        self.exit_code = 130
        self._begin_cancel()
        self.dialogs.reject_open_dialogs()

    def _begin_cancel(self):
        if self._cancelled:
            return
        self._cancelled = True
        self.download.timer.stop()
        queued = list(self.download.tasks) + list(self.download.paused_tasks)
        self.download.tasks[:] = []
        self.download.paused_tasks[:] = []
        for task in queued:
            task["widget"].set_task_state("failed")
            task["state"] = "cancelled"
            task["result"] = "cancelled"
            task["error"] = "任务已取消"
        for task in list(self.download.running_tasks):
            thread = task.get("thread")
            if thread is not None:
                # Protected merge/finalization stages deliberately finish safely.
                thread.request_cancel()

    def _expired(self, since, seconds):
        return seconds > 0 and time.monotonic() - since >= seconds

    def _input_ready(self, alias):
        parent = self.window.ui.widget_input
        index = {"confirm": 1, "config": 3}[alias]
        if parent.current_input_page != index:
            return True
        page = self.controls.page(alias)
        if getattr(page, "load_thread", None) is not None:
            # Wait for load_end/load_finish to consume all queued UI updates and
            # remove load_thread, not merely for QThread.isRunning() to be false.
            return False
        if alias == "confirm" and (page.err or page.meta is None):
            raise HeadlessError("视频信息加载失败：{}".format(page.ui.text_info.toPlainText()))
        if alias == "config" and not page.quality_match:
            raise HeadlessError("未获取到可用画质")
        return True

    def _ready(self):
        ready = True
        for name, probe in self.readiness.items():
            if probe():
                self._load_started.pop(name, None)
            else:
                since = self._load_started.setdefault(name, time.monotonic())
                if self._expired(since, self.args.timeout):
                    raise HeadlessError("{} 页面加载超时".format(name), 3)
                ready = False
        return ready

    def _wait(self, operation):
        if operation.name == "wait-downloads":
            return not self.ledger.pending()
        target, prop, value = operation.args
        info = self.controls.inspect(target)
        if prop not in info:
            raise HeadlessError("目标没有该可查询属性：{}".format(prop))
        if info[prop] == expected_value(value):
            return True
        if self._wait_started is None:
            self._wait_started = time.monotonic()
        if self._expired(self._wait_started, self.args.timeout):
            raise HeadlessError("等待超时：{} {} = {}".format(target, prop, value), 3)
        return False

    @QtCore.Slot()
    def _tick(self):
        if self._busy:
            return
        self._busy = True
        try:
            self._advance()
        except Exception as error:
            self.fail(error)
        finally:
            self._busy = False

    def _advance(self):
        if not self._closing and self._download_started is not None and self.ledger.pending():
            if self._expired(self._download_started, self.args.download_timeout):
                self.fail(HeadlessError("下载总超时", 3))
                self._begin_cancel()
        if any(task["state"] in ("paused", "pausing") for task in self.ledger.tasks):
            self.fail(HeadlessError("headless 不允许存在暂停任务"))
            self._begin_cancel()
        if self._closing:
            self._finish()
            return
        if self._failed:
            if not self.ledger.pending():
                self._closing = True
            return
        if not self._ready():
            return
        if self.position < len(self.operations):
            operation = self.operations[self.position]
            if operation.name in ("wait", "wait-downloads"):
                if not self._wait(operation):
                    return
            else:
                handler = self.handlers.get(operation.name)
                if handler is None:
                    raise HeadlessError("未知操作：{}".format(operation.name))
                handler(*operation.args)
            self.position += 1
            self._wait_started = None
            return
        if not self.ledger.pending():
            if self.dialogs.paths or self.dialogs.answers:
                raise HeadlessError("存在未使用的文件路径或确认回答")
            self._closing = True

    def _finish(self):
        # Loading threads may still be exiting after an error/timeout. Never
        # destroy their parent or use terminate(); finish the network call first.
        threads = self.window.findChildren(QtCore.QThread)
        if any(thread.isRunning() for thread in threads):
            for thread in threads:
                thread.requestInterruption()
            return
        if not self._cleanup_started:
            self._cleanup_started = True
            self.window.ui.widget_settings.save_settings()
        if not self.download.shutdown():
            return
        if not self.download._temporary_files_cleaned:
            self.fail(HeadlessError("退出时无法删除部分下载临时文件"))
        if self.ledger.tasks:
            success = self.ledger.successful()
            if not success and self.exit_code == 0:
                self.exit_code = 1
            try:
                emit("downloads", success=success, tasks=self.ledger.results(False))
            except (OSError, UnicodeError):
                # For example a downstream consumer closed stdout. Downloads
                # have already been safely finalized; do not retry forever.
                if self.exit_code == 0:
                    self.exit_code = 2
        self.timer.stop()
        self.app.exit(self.exit_code)
