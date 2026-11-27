"""Session-owned task ledger, independent of the visible download list."""

from .protocol import HeadlessError


class TaskLedger:
    def __init__(self, download, on_added):
        self.tasks = []
        self._ids = {}
        self._on_added = on_added
        download.task_added.connect(self.add)

    def add(self, task):
        self.tasks.append(task)
        self._ids[id(task)] = "task-{}".format(len(self.tasks))
        self._on_added(task)

    def identifier(self, task):
        return self._ids[id(task)]

    def find(self, identifier):
        for index, task in enumerate(self.tasks, 1):
            if identifier in (str(index), self.identifier(task)):
                return task
        raise HeadlessError("找不到下载任务：{}".format(identifier))

    def result(self, task, include_progress=True):
        state = task["state"]
        if task.get("result") == "cancelled" and state == "failed":
            state = "cancelled"
        result = {
            "id": self.identifier(task),
            "title": task["title"],
            "name": task["name"],
            "state": state,
            "files": list(task.get("outputFiles", [])),
            "error": task.get("error"),
            "warnings": list(task.get("warnings", [])),
        }
        widget = task.get("widget")
        if widget is not None and include_progress:
            result["status"] = widget.ui.label_status.text()
            result["progress"] = widget.ui.progressBar.value()
        return result

    def results(self, include_progress=True):
        return [self.result(task, include_progress) for task in self.tasks]

    def pending(self):
        return any(task["state"] not in ("completed", "failed", "cancelled")
                   for task in self.tasks)

    def successful(self):
        return all(task["state"] == "completed" for task in self.tasks)
