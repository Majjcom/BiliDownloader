"""Translate convenient download arguments into the same UI operations."""

from utils.video_codec import video_codec_id

from .protocol import Operation


def build_operations(args):
    operations = []

    def add(name, *values):
        operations.append(Operation(name, tuple(values)))

    settings = (
        ("threads", "spin_threads"),
        ("danmaku", "check_danmaku"),
        ("audio_only", "check_audio"),
        ("reserve_audio", "check_reserve_audio"),
        ("ultra", "check_hiper"),
        ("dolby", "check_dolby_audio"),
        ("unlimited_title", "check_close_text_len_limit"),
    )
    overrides = []
    for argument, control in settings:
        value = getattr(args, argument)
        if value is not None:
            overrides.append((control, str(value).lower()))
    if args.codec:
        overrides.append(("combo_codec", video_codec_id[{
            "avc": 7, "hevc": 12, "av1": 13,
        }[args.codec]]))
    if overrides:
        add("tab", "settings")
        for control, value in overrides:
            add("set", "settings." + control, value)
        add("tab", "input")

    add("set", "input.line_input", args.url)
    add("click", "input.button_next")
    if args.info:
        add("get", "confirm.text_info")
    if not any((args.list_episodes, args.list_formats, args.download)):
        return operations

    add("click", "confirm.button_next")
    if args.list_episodes:
        add("get", "selection.table_selection")
    if args.episodes is not None:
        add("set", "selection.line_selection", args.episodes)
        add("click", "selection.button_setSelection")
    if not any((args.list_formats, args.download)):
        return operations

    add("click", "selection.button_next")
    if args.path is not None:
        add("set", "config.line_path", args.path)
    if args.quality is not None:
        add("quality", args.quality)
    if args.audio is not None:
        add("set", "config.combo_audio", args.audio)
    if args.ai_language is not None:
        add("language", args.ai_language)
    if args.list_formats:
        add("formats")
    if args.download:
        add("click", "config.button_submit")
    return operations
