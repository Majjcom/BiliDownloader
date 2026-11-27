# CLI 参数与结果协议

本手册针对 Nuitka / PyInstaller 分发的可执行程序。`<BILIDOWNLOADER_EXE>` 必须指向分发包 **`bin` 目录下的实际可执行文件**；外层启动程序不支持 headless 模式，不可用作 CLI 入口。工作目录遵循该分发版要求，不使用 Skill 目录，也不依赖开发者的源码或环境。

## 公共参数

```text
<BILIDOWNLOADER_EXE> --headless --mode download|widgets [参数或有序操作]
```

| 参数 | 语义 |
| --- | --- |
| `--headless` | 必须指定，启用 Qt offscreen 模式 |
| `--mode download` | 单来源业务快捷模式 |
| `--mode widgets` | 有序控件操作模式 |
| `--timeout SECONDS` | 页面加载和普通 `--wait` 的超时，默认 60；0 不限时 |
| `--download-timeout SECONDS` | 自第一个任务提交起计算的下载总超时，默认 0，不限时 |

超时参数为有限非负秒数，是本次调用的全局配置，不是位于某个步骤之前就只对那个步骤生效。超时后仍须安全收尾，因此进程退出可能晚于超时点。

程序会自行调整运行工作目录。CLI 显式提供的 `--path`、`--dialog-path`、`--export` 路径，以及 `--set settings.line_path` / `config.line_path` 的非空值，会先相对于调用目录解析为绝对路径。推荐直接使用用户授权的绝对路径。

配置和随包资源的位置由分发版的运行规则决定；不要把可执行文件目录、启动器目录或单文件包解压目录直接当成配置目录。

- 复用同一分发版 GUI 的配置和登录态，不扫描、输出或手工修改凭据文件。
- headless 配置改动不写回磁盘；没有已有配置时使用内存默认值。
- 下载和封面导出会真实写入文件，且成品可能覆盖已有同名文件；配置只读不代表下载无副作用。

## 业务快捷模式

| 参数 | 语义 |
| --- | --- |
| `--url SOURCE` | 必填；BV、AV、EP、MD 编号，或包含可识别编号的链接；不保证展开 b23.tv 短链 |
| `--info` | 输出视频/番剧信息 |
| `--list-episodes` | 输出选集表格 |
| `--list-formats` | 输出画质、编码、特殊音频及 AI 语言选项 |
| `--download` | 实际提交下载 |
| `--episodes "1-3,5"` | 按 UI 选集语法选择，默认全选 |
| `--path PATH` | 已存在的下载目录；省略则沿用本次读取的配置或默认目录 |
| `--quality VALUE` | 可用画质 ID、UI 完整名称，或 `best`；省略则沿用页面默认选项 |
| `--codec avc\|hevc\|av1` | 优选编码，对应 H.264 / H.265 / AV1 |
| `--audio VALUE` | 可用的特殊音频名称，例如查询结果中的 `flac` 或 `dolby` |
| `--ai-language VALUE` | 查询结果中的语言代码或 UI 名称 |
| `--threads N` | 正整数并发数，同时受设置页数值控件范围约束 |
| `--danmaku BOOL` | 下载弹幕 |
| `--audio-only BOOL` | 仅下载音频 |
| `--reserve-audio BOOL` | 视频下载时保留独立音频 |
| `--ultra BOOL` | 启用现有超高分辨率选项 |
| `--dolby BOOL` | 请求杜比音频相关信息；不等于自动选择 `--audio dolby` |
| `--unlimited-title BOOL` | 关闭现有文件名长度限制；除非用户要求，不主动启用 |

所有 `BOOL` 都必须显式传值，推荐 `true` / `false`。省略布尔参数意味着读取现有设置，**不意味着 false**。

执行流程固定为：临时设置覆盖 → 输入 → 信息确认 → 选集 → 下载配置 → 可选提交。此模式不是按照业务参数的书写顺序重排页面流程：

- 仅 `--info` 会在信息确认页结束，不应用下载配置页的参数。
- `--list-episodes` 输出默认选集表格，发生在应用本次 `--episodes` 之前。
- `--list-formats` 进入下载配置页，输出选项；不带 `--download` 时不下载。
- 每次仅一个来源。复杂的多来源序列用 widgets 模式，不重复传 `--url` 来表示列表。
- 不提供自动提权、账号权限绕过或不存在选项的静默替换。

不要在 widgets 模式直接使用本表业务参数。其 `--set` 下拉框只识别 UI 完整文本或 `@序号`，不识别业务模式的 `best`、画质数字 ID、`hevc` 等快捷值。

## 查询输出

所有 headless 输出统一写入 stdout，格式为 UTF-8 JSON Lines，**每行独立解析**，不能将整个 stdout 当作一个 JSON 对象。直接调用可执行文件即可，无需重定向、合并输出流或额外管道。`--help` 为可读帮助文本，不按 JSON 解析。

| `event` | 字段 |
| --- | --- |
| `query` | `target`、`value`，来自 `--get` 或业务查询 |
| `inspect` | `target`、`value`，包含控件/页面元信息 |
| `controls` | `page`、`value` 控件列表 |
| `downloads` | `success`、`tasks` 最终下载结果；提交过任务时在退出前输出一次 |
| `error` | `message`、`code`，以及可选的 `step`、`operation` |
| `diagnostic` | `source`、`message`，Qt 诊断还包含 `level`；不是下载成功标志 |

业务查询目标：

- `--info`：`confirm.text_info`，`value` 为纯文本。
- `--list-episodes`：`selection.table_selection`，`value` 为二维行数组；选择列为复选框元信息对象，名称列为文本。
- `--list-formats`：`config.formats`，`value` 包含：

```json
{
  "quality": [{"id": 80, "text": "示例画质名称"}],
  "codec": [{"id": 12, "text": "示例编码名称"}],
  "audio": ["", "flac"],
  "ai_language": [{"id": "示例语言代码", "text": "示例语言名称"}]
}
```

以上仅说明数据结构，不能将示例选项当成当前来源一定支持的选项。`config.formats` 是业务查询的输出标识，**不是**可通过 widgets `--get config.formats` 访问的控件。

无显式查询、无下载的成功操作可以没有任何 stdout 输出；不会额外输出通用“成功”事件。

## 下载结果

示意，非实际下载记录：

```json
{"event":"downloads","success":true,"tasks":[{"id":"task-1","title":"示例标题","name":"001-示例分集","state":"completed","files":["<ACTUAL_OUTPUT_FILE_PATH>"],"error":null,"warnings":[]}]}
```

- `files` 来自实际成功保存的产物记录，可能有视频、音频、ASS，也可能在部分失败时仅有部分成品；不自行补全扩展名。
- 最终 `state` 一般为 `completed`、`failed`、`cancelled`。运行中的显式任务查询还可能得到 `queued`、`running` 等状态。
- 成功任务仍可能有 `warnings`，例如弹幕失败后沿用 GUI 逻辑跳过；应向用户说明，不把跳过的文件描述为已下载。
- `success` 只反映任务是否全部完成；即使全部下载成功，脚本操作错误或清理错误也可能使进程非零退出。
- 下载过程中不自动输出进度。显式 `--get` / `--inspect` 查询任务时，可包含临时 `status`、`progress`；最终结果不包含这两个进度字段。
- UI 列表清理不删除本进程的任务账本，最终结果仍包含已提交任务。

## 错误、退出码及等待

CLI 错误也写入 stdout，例如：

```json
{"event":"error","message":"示例错误","code":2,"step":3,"operation":"click"}
```

初始化/参数错误可能没有 `step`、`operation`。Qt 日志及运行时警告、异常诊断转为 stdout 的 `diagnostic` JSON 事件；按 `event` 区分，不把诊断当成查询结果或最终下载结果。

| 退出码 | 含义 |
| --- | --- |
| `0` | 本次操作成功，且提交的下载均成功结束 |
| `1` | 有下载任务失败或取消，且没有更早的其他错误码 |
| `2` | 参数、控件操作、初始化或其他执行错误 |
| `3` | 页面、普通等待或下载总超时 |
| `130` | Ctrl+C 中断 |

操作错误停止后续操作，但已经提交的下载继续收尾；单个下载失败不取消其他下载。超时或 Ctrl+C 请求取消队列/可取消任务，受保护的合并阶段安全完成；不要立即强杀进程。

最终下载等待默认不限时。`--wait-downloads` 也不使用普通 `--timeout`；若需限制整个下载阶段，指定 `--download-timeout`。对单个任务状态使用 `--wait` 则受普通等待超时约束。

## 故障处理

- 程序无法启动或报告缺少随包组件：记录实际错误，请用户检查完整安装包或联系发行者；不要求准备开发环境、编译资源或重新打包。
- 不识别 `--headless` / `--mode`：当前发行版或外层启动器可能不支持或未转发 CLI 参数，要求提供支持该接口的分发版，不尝试未知内部入口。
- 进程退出但 stdout 没有结果：检查是否使用了正确的 CLI 入口及 stdout 捕获方式；不要改用其他输出位置、重定向或管道作为正常调用方案，不能据此宣称下载成功，也不猜测隐藏控制台的打包设置。
- ffmpeg 或媒体处理组件不可用：提示检查随包工具和发行版说明，不擅自替换二进制文件或依赖开发机上的工具路径。
- 登录失效/无账号权限：让用户在 GUI 中重新登录；不导出或修改凭据，不宣称 `best` 可绕过权限。
- 写入失败/目录无效：报告用户提供的目录及错误，未经授权不更改目标位置。
- 不确定是否可重试：先解释失败范围和已有产物，获得用户授权后再重试，避免重复覆盖成功成品。
