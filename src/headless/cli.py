"""Argument parsing without importing Qt or initializing user configuration."""

import argparse
import math
import os

from .protocol import HeadlessError, Operation, boolean


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise HeadlessError(message)


class OrderedAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        operations = list(getattr(namespace, self.dest, None) or [])
        if isinstance(values, str):
            values = [values]
        operations.append(Operation(option_string[2:], tuple(values or [])))
        setattr(namespace, self.dest, operations)


def nonnegative_seconds(value):
    try:
        result = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError("超时必须是秒数")
    if not math.isfinite(result) or result < 0:
        raise argparse.ArgumentTypeError("超时必须是有限的非负秒数；0 表示不限时")
    return result


def positive_integer(value):
    try:
        result = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("必须是正整数")
    if result < 1:
        raise argparse.ArgumentTypeError("必须是正整数")
    return result


def parse(argv):
    parser = Parser(
        description="BiliDownloader headless CLI (Python 3.8+)",
        epilog=(
            "示例：--headless --mode widgets --set input.line_input BV... "
            "--click input.button_next --get confirm.text_info\n"
            "示例：--headless --mode download --url BV... --path D:\\Videos "
            "--episodes 1-3 --quality 80 --download\n"
            "控件名：input/confirm/selection/config/download/settings/about/main；"
            "表格 selection.table_selection[1,1]；任务 download.tasks[1]；"
            "按钮 download.items[1].button_restart。\n"
            "表格行列、任务和 @选项序号均从 1 开始；"
            "download.tasks[task-1] 也可使用稳定任务 ID。\n"
            "写入/点击前需进入当前页面；可读取隐藏页面。"
            "--set 下拉框 TARGET @1 按序号选择，否则按完整文本选择。\n"
            "--wait 的 VALUE 按 JSON 值解析，普通文本直接比较。"
            "例：--wait download.tasks[1] state failed\n"
            "控件模式例：--tab settings --set settings.check_danmaku true --tab input\n"
            "特殊操作例：--dialog-path D:\\Videos --click config.button_path\n"
            "退出码：0 成功，1 下载失败，2 操作/参数错误，3 超时，130 中断。\n"
            "下载目录必须已存在。超时/中断后会安全收尾，"
            "因此退出可能晚于超时点；受保护的合并阶段不会被强杀。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        allow_abbrev=False,
    )
    parser.add_argument("--headless", action="store_true", required=True)
    parser.add_argument("--mode", choices=("widgets", "download"), required=True)
    parser.add_argument("--timeout", type=nonnegative_seconds, default=60,
                        help="页面加载和普通等待超时，单位秒；0 不限时")
    parser.add_argument("--download-timeout", type=nonnegative_seconds, default=0,
                        help="从首个任务提交起计算的下载总超时，默认不限时")
    group = parser.add_argument_group("widgets：操作严格按照参数顺序执行")
    specifications = (
        ("set", 2, ("TARGET", "VALUE"), "设置文本、布尔值、数值或下拉框文本"),
        ("click", 1, "TARGET", "点击按钮"),
        ("get", 1, "TARGET", "输出控件当前值"),
        ("inspect", 1, "TARGET", "输出控件完整信息；TARGET 可为页面别名"),
        ("tab", 1, "PAGE", "切换 input/download/settings/about 主页面"),
        ("wait", 3, ("TARGET", "PROPERTY", "VALUE"), "等待属性等于指定值"),
        ("wait-downloads", 0, None, "等待当前下载结束，不输出进度"),
        ("double-click", 1, "TARGET", "双击表头，如 config.table_downloads.header[1]"),
        ("respond", 1, "ANSWER", "预置下一个确认框回答 yes/no/ok/cancel"),
        ("dialog-path", 1, "PATH", "预置下一次文件或目录选择路径"),
        ("export", 2, ("TARGET", "PATH"), "导出封面：confirm.cover_label PATH"),
    )
    for name, nargs, metavar, help_text in specifications:
        kwargs = dict(dest="operations", nargs=nargs, action=OrderedAction, help=help_text)
        if metavar is not None:
            kwargs["metavar"] = metavar
        group.add_argument("--" + name, **kwargs)
    group.add_argument("--list-controls", dest="operations", nargs="?",
                       const="all", action=OrderedAction, metavar="PAGE",
                       help="列出可定位控件，默认全部页面")
    business = parser.add_argument_group("download：一个来源的业务快捷参数")
    business.add_argument("--url", help="BV/AV/EP/MD 或链接")
    business.add_argument("--episodes", help="1-3,5；默认全部")
    business.add_argument("--path", help="已存在的下载目录")
    business.add_argument("--quality", help="画质 ID 或 UI 完整名称；best 表示最高选项")
    business.add_argument("--codec", choices=("avc", "hevc", "av1"))
    business.add_argument("--audio", help="特殊音频，如 flac/dolby")
    business.add_argument("--ai-language", help="AI 翻译语言代码或 UI 名称")
    business.add_argument("--threads", type=positive_integer)
    for flag in ("danmaku", "audio-only", "reserve-audio", "ultra",
                 "dolby", "unlimited-title"):
        business.add_argument("--" + flag, type=boolean, default=None, metavar="BOOL")
    for flag in ("info", "list-episodes", "list-formats", "download"):
        business.add_argument("--" + flag, action="store_true")
    args = parser.parse_args(argv)
    args.operations = args.operations or []
    business_fields = (
        "url", "episodes", "path", "quality", "codec", "audio", "ai_language",
        "threads", "danmaku", "audio_only", "reserve_audio", "ultra", "dolby",
        "unlimited_title",
    )
    if args.mode == "widgets":
        if any(getattr(args, key) is not None for key in business_fields) or any((
                args.info, args.list_episodes, args.list_formats, args.download)):
            parser.error("widgets 模式不能使用 download 模式的参数")
        if not args.operations:
            parser.error("请至少指定一个操作，例如 --list-controls")
    else:
        if args.operations:
            parser.error("download 模式不能混用控件操作参数")
        if not args.url:
            parser.error("download 模式需要 --url")
        if not any((args.info, args.list_episodes, args.list_formats, args.download)):
            parser.error("请指定 --info、--list-episodes、--list-formats 或 --download")
    # main.py changes cwd at startup; user-supplied paths are relative to invocation.
    if args.path is not None:
        if not args.path:
            parser.error("--path 不能为空")
        args.path = os.path.abspath(os.path.expanduser(args.path))
    if any(op.name in ("export", "dialog-path") and not op.args[-1]
           for op in args.operations):
        parser.error("导出或文件选择路径不能为空")
    args.operations = [
        Operation(op.name, op.args[:-1] + (os.path.abspath(os.path.expanduser(op.args[-1])),))
        if op.name in ("export", "dialog-path") or (
            op.name == "set" and op.args[0] in ("settings.line_path", "config.line_path")
            and op.args[-1] != ""
        ) else op
        for op in args.operations
    ]
    return args
