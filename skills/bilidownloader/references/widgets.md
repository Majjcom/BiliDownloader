# 页面、控件及有序操作

## 调用模型

```text
<BILIDOWNLOADER_EXE> --headless --mode widgets [有序操作...]
```

`<BILIDOWNLOADER_EXE>` 必须为分发包 **`bin` 目录下的实际可执行文件路径**，外层启动程序不支持 headless 操作。操作参数严格按出现顺序执行，允许多次出现相同参数。不要用会丢失重复键的字典表示整条命令；使用有序参数列表。优先使用进程工具的工作目录选项，工作目录以分发版要求为准，不猜测开发者的项目位置。

每个进程从输入流程第一页开始。两次独立启动可执行文件不共享页面、临时设置、选集或任务 ID。

## 操作速查

| 操作 | 语义 |
| --- | --- |
| `--set TARGET VALUE` | 设置可写控件；布尔值推荐 `true/false`；下拉框用完整文本或 `"@1"` 等一基序号 |
| `--click TARGET` | 点击按钮或复选框；普通按钮不能用 `--set` |
| `--get TARGET` | 输出当前值；没有 `value` 字段的目标返回整体信息 |
| `--inspect TARGET` | 输出完整控件信息或页面控件映射 |
| `--list-controls [PAGE]` | 枚举控件路径；省略页面时为 `all` |
| `--tab PAGE` | 仅允许 `input/download/settings/about` 主页面 |
| `--wait TARGET PROPERTY VALUE` | 等待属性等于指定 JSON 值或普通文本 |
| `--wait-downloads` | 静默等待当前下载全部结束 |
| `--double-click TARGET` | 模拟表头双击，例如 `"config.table_downloads.header[1]"` |
| `--dialog-path PATH` | 为下一次文件/目录对话框排队一个路径，须在触发对话框之前执行 |
| `--respond ANSWER` | 为下一次确认框排队回答 `yes/no/ok/cancel` |
| `--export confirm.cover_label PATH` | 导出已加载封面；不必另加 `--dialog-path`；无小写 `.png` 后缀时按现有 UI 规则补充 |

`--wait` 的属性写成独立参数，不拼在控件路径后。例如 `--wait input.button_next enabled true`，而非 `--get input.button_next.enabled`。可用属性以 `--inspect` 返回的字段为准：

- 通用控件：`enabled`、`active`、`value` 等。
- 复选框：`checked`。
- 下拉框：`current_index`、`count`、`text`、`options`；序号从 1 开始，无选中项时序号为 0。
- 表格：`row_count`、`column_count`、`headers`、`rows`。
- 任务：`state`、`error`、`files` 等。
- `--inspect main`：`current_tab`、`input_page`。

正常的页面切换会自动等待网络加载，不需要每个 `--click ...button_next` 后加一次 `--wait`。动态表格必须在对应流程加载后才有单元格。

## 页面与导航

| 别名 | 含义 | 进入方式 |
| --- | --- | --- |
| `main` | 主窗口 | 总是可查询 |
| `input` | 输入编号/链接 | 初始页；`--tab input` 只切换主标签，不重置其子页 |
| `confirm` | 信息确认/封面 | `--click input.button_next` |
| `selection` | 选集 | `--click confirm.button_next` |
| `config` | 本次下载配置 | `--click selection.button_next` |
| `download` | 下载列表 | `--tab download`；提交下载后自动切到这里 |
| `settings` | 临时全局设置 | `--tab settings` |
| `about` | 关于信息 | `--tab about` |

`confirm`、`selection`、`config` 通过各自的 `button_back` 返回上一子页；`--tab input` 不意味着回到输入第一页。提交后输入子页会重建，之后 `--tab input` 可开始新的来源。

读隐藏页面合法，但写入/点击要求该页面 `active: true`，且控件启用、可写。offscreen 中 `visible` 经常为 false，不能代替逻辑 `active` 判断。

## 常用控件

这里是常用路径，不替代 `--list-controls` 的实际枚举结果。

| 页面 | 控件 |
| --- | --- |
| `input` | `line_input`、`label_hint`、`button_next` |
| `confirm` | `text_info`、`cover_label`、`button_back`、`button_next` |
| `selection` | `line_selection`、`button_setSelection`、`button_help`、`table_selection`、`button_back`、`button_next` |
| `config` | `line_path`、`button_path`、`combo_quality`、`combo_codec`、`combo_audio`、`combo_ai_language`、`table_downloads`、`button_back`、`button_submit` |
| `download` | `listWidget`、`button_clean` |
| `settings` | `line_path`、`button_path`、`spin_threads`、`combo_codec`、`combo_style`、`check_audio`、`check_reserve_audio`、`check_danmaku`、`check_hiper`、`check_dolby_audio`、`check_close_text_len_limit`、`check_read_clipboard`、`check_highdpi`、`line_login`、`button_reset` |
| `about` | `label_version`、`button_changelog`、`button_license`、`button_about_qt` |

设置页的修改在离开设置页后保存到**本次内存配置**，不会跨进程保留。需要影响本次下载的全局参数，先进入设置页修改，再离开该页，之后进入输入流程。

下拉框文本必须完整匹配；不确定名称时读取 `--inspect config.combo_quality` 等。不要在 widgets 模式用 `--set config.combo_quality best` 或业务数字 ID 替代真实文本。`"@1"` 是合法选项序号，但第一项未必就是用户要求的画质。

## 动态表格

所有行列从 **1** 开始，建议对含方括号的路径加引号。

| 路径 | 含义 |
| --- | --- |
| `"selection.table_selection[1,1]"` | 第 1 行选集复选框 |
| `"selection.table_selection[1,2]"` | 第 1 行分集名称，只读 |
| `"config.table_downloads[1,1]"` | 本次选中项目中的第 1 行是否下载弹幕 |
| `"config.table_downloads[1,2]"` | 第 1 行是否仅下载音频 |
| `"config.table_downloads[1,3]"` | 第 1 行名称，只读 |
| `"config.table_downloads.header[1]"` | 弹幕列表头，双击执行现有批量勾选逻辑 |
| `"config.table_downloads.header[2]"` | 仅音频列表头，双击执行现有批量勾选逻辑 |

下载配置表只包含选中的分集，因此其行号不一定等于原视频分集编号。先读名称再定位行。表头双击是按当前状态全选/取消，不是固定设置为 true。

选集默认全选。`line_selection` 支持递增、不重叠的 `"1-3,5"`；设为非空后还须点击 `button_setSelection`。空字符串在该控件中表示**反选**，不是全选。

## 动态任务

- `"download.tasks"`：本进程所有任务的账本。
- `"download.tasks[1]"` / `"download.tasks[task-1]"`：同一个任务的查询路径。
- `"download.items[1].button_restart"` / `"download.items[task-1].button_restart"`：下载条目按钮；仅失败时允许点击。
- 条目还可读取 `label_title`、`label_part`、`label_status`、`label_progress`、`progressBar` 等；以实际枚举为准。
- `button_pause`、`button_open` 不支持执行。
- `--click download.button_clean` 清除完成条目的 UI，不删除成品或账本；清理后对应 `download.items[...]` 不再存在，但 `download.tasks[...]` 仍可查询。
- ID 和序号只在本次进程内稳定，不是跨调用的恢复下载标识。

在同一条完整操作序列中，可以按用户授权加入：

```text
--wait "download.tasks[1]" state failed
--click "download.items[1].button_restart"
--wait-downloads
```

这不是“成功则跳过，否则重试”的条件分支：如果任务成功，等待 `failed` 会超时。CLI 不提供通用条件语句，不应将此模式无条件加入每次下载。

## 完整例子

以下 PowerShell 命令须替换可执行文件、来源和已存在目录等占位符；`&` 用于调用引号包围的程序路径，反引号必须位于行末，不带尾随空格。其他 shell 使用其对应的调用和续行语法。

修改本次全局设置、选集、逐行音频选项并提交：

```powershell
& "<BILIDOWNLOADER_EXE>" --headless --mode widgets `
  --tab settings `
  --set settings.spin_threads 2 `
  --set settings.check_danmaku true `
  --tab input `
  --set input.line_input "<BV_ID>" `
  --click input.button_next `
  --get confirm.text_info `
  --click confirm.button_next `
  --set selection.line_selection "1-3" `
  --click selection.button_setSelection `
  --click selection.button_next `
  --set config.line_path "<DOWNLOAD_DIR>" `
  --set "config.table_downloads[1,2]" true `
  --inspect config.table_downloads `
  --click config.button_submit
```

此例显式查询了信息和表格，因此除最终下载结果外还会输出查询 JSON。只需下载结果时删去 `--get` 和 `--inspect` 操作；不需要额外 `--wait-downloads` 就会在最终下载结束后退出。

只导出封面，不下载视频：

```powershell
& "<BILIDOWNLOADER_EXE>" --headless --mode widgets --set input.line_input "<BV_ID>" --click input.button_next --export confirm.cover_label "<COVER_PNG_PATH>"
```

通过按钮选择目录而非直接设置输入框时，在完整流程到达 config 页后加入：

```text
--dialog-path "<DOWNLOAD_DIR>"
--click config.button_path
```

多个来源需要在**同一个进程**里重复完整输入流程。第一个来源提交后加 `--tab input`，输入第二个来源，再逐页提交；最终自动等待全部任务。若只有一个来源，优先采用更短的业务模式。

## 弹窗与限制

- 普通提示、关于 Qt、许可证和更新说明等信息弹窗自动关闭，不提供弹窗内部逐控件操作。
- 错误弹窗转为 CLI 错误，停止后续操作。
- 确认框默认拒绝；仅在用户授权且确定将触发确认框时，预置 `--respond yes` 等回答。
- 已存在封面的覆盖确认也遵循上述规则；未授权不自动同意。
- `--respond yes --click settings.button_reset` 只重置本次内存设置，保留现有登录凭据；不用于修改 GUI 持久配置。
- 预置路径或回答按队列消费。剩余未消费项会导致退出错误，不能“为了保险”无条件预置。
- 不支持登录/注销、打开目录/浏览器、坐标点击、原始键盘模拟、任意 QObject 方法调用或任意代码执行。不要编造 `--login`、`--cookie`、`--eval`、`--script`、`--quit` 等不存在参数。
