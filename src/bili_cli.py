"""复用现有 API 和下载线程的命令行入口。"""

import argparse
import http.client
import json
import os
import re
import shutil
import signal
import sys
import uuid
from http.cookies import SimpleCookie
from pathlib import Path
from contextlib import contextmanager
from urllib.error import URLError

from utils.removeSpecialChars import removeSpecialChars
from utils.version import __version__


class CLIError(ValueError):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise CLIError(message)


def emit(event, **data):
    print(json.dumps({"schema_version": 1, "event": event, **data},
                     ensure_ascii=False, separators=(",", ":")), flush=True)


def config_file(config_dir=None):
    source_root = Path(__file__).resolve().parents[1]
    roots = [Path(config_dir).expanduser().resolve()] if config_dir else [Path.cwd(), source_root]
    for root in roots:
        path = root / "data" / "userdata.json"
        if path.is_file():
            return path
    return None


def config_root(config_dir=None):
    path = config_file(config_dir)
    return path.parent.parent if path else Path(config_dir).expanduser().resolve() if config_dir else Path.cwd()


@contextmanager
def config_context(config_dir=None):
    old = Path.cwd()
    os.chdir(config_root(config_dir))
    try:
        yield
    finally:
        os.chdir(old)


def gui_setting(key, default=None, config_dir=None):
    from utils import configUtils

    if config_file(config_dir) is None:
        return default
    with config_context(config_dir):
        return configUtils.getUserData(key, default)


def normalize_source(value):
    match = re.search(r"\b(BV[0-9a-z]{10}|(?:AV|MD|EP)\d+)(?![0-9a-z])", value, re.I)
    if not match:
        raise CLIError("请提供 BV、AV、MD 或 EP 编号/链接")
    source = match.group()
    return source[:2].upper(), source[:2].upper() + source[2:]


def page_numbers(spec, total):
    if total < 1:
        raise CLIError("来源没有可下载的分 P")
    if spec.lower() == "all":
        return list(range(1, total + 1))
    selected = []
    for block in spec.replace(" ", "").split(","):
        if not re.fullmatch(r"\d+(?:-\d+)?", block):
            raise CLIError("分 P 使用数字、区间或 all，例如 1-3,5")
        ends = [int(number) for number in block.split("-")]
        start, end = ends[0], ends[-1]
        if not 1 <= start <= end <= total:
            raise CLIError(f"分 P 范围应在 1 到 {total} 之间")
        values = range(start, end + 1)
        for page in values:
            if selected and page <= selected[-1]:
                raise CLIError("分 P 必须按递增顺序且不能重复")
            selected.append(page)
    return selected


def load_passport(args):
    if not args.cookie_file and not os.environ.get(args.cookie_env):
        return load_gui_passport(args.config_dir)
    try:
        value = (Path(args.cookie_file).read_text(encoding="utf-8-sig")
                 if args.cookie_file else os.environ.get(args.cookie_env, ""))
    except OSError as error:
        raise CLIError(f"无法读取 Cookie 文件：{error}") from error
    if not value and not args.cookie_file:
        return None
    from Lib.bili_api.utils.passport import BiliPassport

    cookie = SimpleCookie()
    cookie.load(re.sub(r"^Cookie:\s*", "", value.strip(), flags=re.I))
    if not cookie:
        raise CLIError("Cookie 必须使用 KEY=VALUE 格式")
    return BiliPassport({key: item.value for key, item in cookie.items()})


def load_gui_passport(config_dir=None):
    from Lib.bili_api.utils.passport import BiliPassport, decode_cookie
    from utils.configUtils import Configs

    try:
        stored = gui_setting(Configs.PASSPORT, config_dir=config_dir)
        if not stored:
            return None
        data = stored.get("data")
        if data is None:
            key = gui_setting(Configs.PASSPORT_CRYPT_KEY, config_dir=config_dir)
            data = decode_cookie(stored.get("secure_data", ""), key) if key else None
        return BiliPassport({key: value for key, value in data.items() if key != "Expires"}) if data else None
    except (OSError, ValueError, TypeError):
        return None


def apply_gui_defaults(args):
    from utils.configUtils import Configs

    if hasattr(args, "ultra_resolution"):
        args.ultra_resolution = args.ultra_resolution if args.ultra_resolution is not None else gui_setting(Configs.ULTRA_RESOLUTION, False, args.config_dir)
        args.dolby_audio = args.dolby_audio if args.dolby_audio is not None else gui_setting(Configs.PULL_DOLBY_AUDIO, False, args.config_dir)
    if args.command != "download":
        return
    args.output = args.output or gui_setting(Configs.DOWNLOAD_PATH, str((Path.cwd() / "Download").resolve()), args.config_dir)
    args.codec = args.codec if args.codec is not None else gui_setting(Configs.VIDEO_CODEC, 7, args.config_dir)
    args.keep_audio = args.keep_audio if args.keep_audio is not None else gui_setting(Configs.RESERVE_AUDIO, False, args.config_dir)
    args.audio_only = args.audio_only if args.audio_only is not None else gui_setting(Configs.DOWNLOAD_AUDIO_ONLY, False, args.config_dir)
    args.danmaku = args.danmaku if args.danmaku is not None else gui_setting(Configs.SAVE_DANMAKU, False, args.config_dir)
    args.disable_title_limit = gui_setting(Configs.DISABLE_TITLE_LENGTH_LIMIT, False, args.config_dir)


def inspect_source(kind, value):
    from Lib.bili_api import bangumi, video

    if kind in ("BV", "AV"):
        data = video.get_video_info(**({"bvid": value} if kind == "BV" else {"aid": value[2:]}))
        pages = [{"page": item["page"], "cid": item["cid"], "id": data["bvid"] if kind == "BV" else str(data["aid"]),
                  "name": item["part"], "title": data["title"], "isbvid": kind == "BV",
                  "type": "video"} for item in data.get("pages", [])]
        return {"title": data["title"], "description": data.get("desc", ""),
                "cover": data.get("pic"), "author": data.get("owner", {}).get("name"), "pages": pages}
    details = bangumi.get_bangumi_detailed_info(
        **({"media_id": value[2:]} if kind == "MD" else {"ep_id": value[2:]}))
    media, data = details["info"]["media"], details["data"]
    pages = [{"page": index, "cid": item["cid"], "id": item["bvid"],
              "name": f"{item['title']}-{item.get('long_title', '')}".strip("-"),
              "title": media["title"], "isbvid": True, "type": "video"}
             for index, item in enumerate(data.get("episodes", []), 1)]
    return {"title": media["title"], "description": data.get("evaluate", ""),
            "cover": media.get("cover"), "rating": media.get("rating", {}).get("score"), "pages": pages}


def fnval(args):
    return (16 | 2048 | 128) | ((1024 | 64) if args.ultra_resolution else 0) | (256 if args.dolby_audio else 0)


def formats_for_page(page, args, passport):
    from Lib.bili_api import bangumi, video
    from Lib.bili_api.exceptions import NetWorkException

    kwargs = {"cid": page["cid"], "fnval": fnval(args), "passport": passport}
    kwargs["bvid" if page["isbvid"] else "avid"] = page["id"]
    try:
        media = video.get_video_url(**kwargs, cur_language=args.language)
    except NetWorkException:
        media = bangumi.get_bangumi_url(**kwargs)["video_info"]
    dash = media.get("dash") or {}
    return {"qualities": [{"quality": row["quality"], "description": row.get("new_description")}
                          for row in media.get("support_formats", [])],
            "streams": [{"quality": row["id"], "codec": row["codecid"]} for row in dash.get("video", [])],
            "audio": [name for name in ("flac", "dolby") if (dash.get(name) or {}).get("audio")],
            "languages": [{"lang": row["lang"], "title": row["title"]}
                          for row in media.get("language", {}).get("items", [])],
            "media_type": media.get("type", "DASH")}


def default_quality(formats):
    values = [row["quality"] for row in formats["qualities"] if row.get("quality") is not None]
    if values:
        return values[0]
    values = [row["quality"] for row in formats["streams"] if row.get("quality") is not None]
    if not values:
        raise CLIError("接口没有返回可用画质")
    return values[0]


def find_ffmpeg(explicit):
    if explicit or os.environ.get("BILI_FFMPEG"):
        return str(Path(explicit or os.environ["BILI_FFMPEG"]).expanduser().resolve())
    found = shutil.which("ffmpeg")
    if found:
        return found
    root = Path(__file__).resolve().parents[1] / "ffmpeg"
    return next((str(root / name) for name in ("ffmpeg", "ffmpeg.exe", "ffmpeg.upx.exe")
                 if (root / name).is_file()), None)


def build_task(page, args, passport, quality):
    limit = None if args.disable_title_limit else 20
    name = f"{page['page']:03d}-" + removeSpecialChars(page["name"], limit)
    return {**page, "path": str(Path(args.output).expanduser().resolve()),
            "name": name, "title": removeSpecialChars(page["title"], limit),
            "quality": quality, "codec": args.codec, "reserveAudio": args.keep_audio,
            "onlyAudio": args.audio_only, "saveDanmaku": args.danmaku, "fnval": fnval(args),
            "specialAudio": args.special_audio, "aiLanguage": args.language,
            "tempName": f"{name}_{uuid.uuid4().hex}", "_passport": passport,
            "_passport_provided": True, "_ffmpeg_path": find_ffmpeg(args.ffmpeg)}


def classify_error(error):
    cause = error
    while cause.__cause__ is not None:
        cause = cause.__cause__
    if isinstance(error, CLIError):
        return 2, "input"
    if (isinstance(cause, (URLError, TimeoutError, ConnectionError, http.client.HTTPException))
            or type(cause).__name__ in ("NetWorkException", "GetWbiException")):
        return 3, "network"
    return 4, "filesystem" if isinstance(cause, OSError) else "media"


def run_download(tasks, report):
    from PySide6.QtCore import QCoreApplication, QTimer
    from downloadthread import DownloadTask, RESULT_COMPLETED

    app = QCoreApplication.instance() or QCoreApplication([])
    state = {"index": 0, "thread": None, "code": 0, "interrupted": False}
    # 定时进入 Python，让等待网络时的 Ctrl+C 也能被处理。
    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(100)

    def start_next():
        if state["interrupted"] or state["index"] == len(tasks):
            app.quit()
            return
        task = tasks[state["index"]]
        thread = DownloadTask(None)
        state["thread"] = thread
        thread.setup(task)
        report("start", page=task["page"])
        def status(message):
            state["last_status"] = message
            report("warning" if message == "弹幕下载失败，已跳过" else "status", page=task["page"], message=message)
        thread.update_status.connect(status)
        thread.update_progress.connect(lambda done, total: report(
            "progress", page=task["page"], downloaded=int(done), total=int(total),
            percent=round(done * 100 / total, 2) if total else None))

        def finished():
            root = Path(task["path"]) / task["title"]
            if thread.result == RESULT_COMPLETED:
                extensions = ([".flac", ".m4a"] if task["onlyAudio"] else [".mp4"])
                if task["reserveAudio"]:
                    extensions += [".flac", ".m4a"]
                if task["saveDanmaku"]:
                    extensions.append(".ass")
                report("completed", page=task["page"], files=[str(root / (task["name"] + ext))
                       for ext in dict.fromkeys(extensions) if (root / (task["name"] + ext)).is_file()])
            elif not state["interrupted"]:
                code, label = classify_error(thread.error or RuntimeError("下载失败"))
                state["code"] = max(state["code"], code)
                report("error", page=task["page"], code=label, message=state.get("last_status", "下载失败"))
            for suffix in ("_temp.mp4", "_temp.m4a", "_temp.flac", "_temp.ass", "_merge.mp4"):
                try:
                    (root / (task["tempName"] + suffix)).unlink(missing_ok=True)
                except OSError as error:
                    report("warning", page=task["page"], message=f"清理临时文件失败：{error}")
            state["index"] += 1
            QTimer.singleShot(0, start_next)

        thread.finished.connect(finished)
        thread.start()

    def interrupt(_signum, _frame):
        state["interrupted"] = True
        if state["thread"] is not None:
            state["thread"].request_cancel()

    previous = signal.signal(signal.SIGINT, interrupt)
    QTimer.singleShot(0, start_next)
    try:
        app.exec()
    finally:
        timer.stop()
        signal.signal(signal.SIGINT, previous)
        if state["thread"] is not None:
            state["thread"].wait()
    if state["interrupted"]:
        report("error", code="cancelled", message="任务已取消")
        return 130
    return state["code"]


def build_parser():
    parser = Parser(prog="bili", description="BiliDownloader 命令行工具（JSONL 输出）")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (("info", "读取视频或番剧信息"), ("formats", "读取画质和音轨"), ("download", "下载视频")):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("source")
        command.add_argument("--cookie-file")
        command.add_argument("--cookie-env", default="BILI_COOKIE")
        command.add_argument("--config-dir", help="GUI 配置工作目录，目录下应包含 data/userdata.json")
        if name == "info":
            continue
        command.add_argument("--page", default="all", help="分 P：1、1-3,5 或 all")
        resolution = command.add_mutually_exclusive_group()
        resolution.add_argument("--ultra-resolution", dest="ultra_resolution", action="store_true")
        resolution.add_argument("--no-ultra-resolution", dest="ultra_resolution", action="store_false")
        command.set_defaults(ultra_resolution=None)
        dolby = command.add_mutually_exclusive_group()
        dolby.add_argument("--dolby-audio", dest="dolby_audio", action="store_true")
        dolby.add_argument("--no-dolby-audio", dest="dolby_audio", action="store_false")
        command.set_defaults(dolby_audio=None)
        command.add_argument("--language")
        if name == "formats":
            continue
        command.add_argument("--output")
        command.add_argument("--quality", type=int, help="画质代码，省略时沿用 GUI 首个可用画质")
        command.add_argument("--codec", type=int, choices=(7, 12, 13))
        audio_only = command.add_mutually_exclusive_group()
        audio_only.add_argument("--audio-only", dest="audio_only", action="store_true")
        audio_only.add_argument("--no-audio-only", dest="audio_only", action="store_false")
        command.set_defaults(audio_only=None)
        keep_audio = command.add_mutually_exclusive_group()
        keep_audio.add_argument("--keep-audio", dest="keep_audio", action="store_true")
        keep_audio.add_argument("--no-keep-audio", dest="keep_audio", action="store_false")
        command.set_defaults(keep_audio=None)
        danmaku = command.add_mutually_exclusive_group()
        danmaku.add_argument("--danmaku", dest="danmaku", action="store_true")
        danmaku.add_argument("--no-danmaku", dest="danmaku", action="store_false")
        command.set_defaults(danmaku=None)
        command.add_argument("--special-audio", choices=("flac", "dolby"))
        command.add_argument("--ffmpeg")
    return parser


def main(argv=None):
    args = None
    source = None

    def report(event, **data):
        emit(event, command=args.command if args else None, source=source, **data)

    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        args = build_parser().parse_args(argv)
        apply_gui_defaults(args)
        kind, source = normalize_source(args.source)
        passport = load_passport(args)
        data = inspect_source(kind, source)
        if args.command == "info":
            report("result", data=data)
            return 0
        pages = [data["pages"][index - 1] for index in page_numbers(args.page, len(data["pages"]))]
        if args.command == "formats":
            report("result", data=[{"page": page["page"], **formats_for_page(page, args, passport)} for page in pages])
            return 0
        if args.quality is not None and args.quality <= 0:
            raise CLIError("画质代码必须大于 0")
        Path(args.output).expanduser().mkdir(parents=True, exist_ok=True)
        report("metadata", title=data["title"], pages=pages)
        quality = args.quality
        if quality is None:
            quality = default_quality(formats_for_page(pages[0], args, passport))
        tasks = []
        for page in pages:
            tasks.append(build_task(page, args, passport, quality))
        return run_download(tasks, report)
    except KeyboardInterrupt:
        report("error", code="cancelled", message="任务已取消")
        return 130
    except Exception as error:
        code, label = classify_error(error)
        report("error", code=label, message=str(error))
        return code


if __name__ == "__main__":
    raise SystemExit(main())
