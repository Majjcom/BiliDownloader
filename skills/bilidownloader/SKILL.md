---
name: bilidownloader
description: BiliDownloader 使用手册。用户需要下载 Bilibili/B站视频或音频、查询 BV/AV/EP/MD 信息与选集、选择画质/编码/弹幕/AI音轨，或通过 headless CLI 精确操作 Qt 页面和控件、解析下载结果时使用。
---

# BiliDownloader 使用手册

通过 Nuitka 或 PyInstaller 打包分发的 BiliDownloader 可执行程序使用 headless CLI，不自行重写 API 调用或下载逻辑。本手册面向分发版，不依赖开发者的源码目录或本机开发环境。

> **重要：只有分发包 `bin` 目录下的实际可执行文件支持 headless 模式。分发包外层的启动程序不支持此操作，不能用于传入 `--headless` 或其他 CLI 参数。**

## 先读哪些内容

- 普通查询、下载和结果解析：阅读 [CLI 参数及协议](references/cli.md)。
- 逐控件操作、逐集设置、封面导出、失败重试：另读 [控件手册](references/widgets.md)。
- 本 Skill 是使用手册，不是安装软件、修改程序或执行测试的授权；始终遵守用户授权及所在工作区的执行限制。禁止验证命令时，不为了验证手册执行示例、`--help` 或测试下载。

## 推荐工作流

1. 确定用户实际安装的分发包中 `bin` 目录下的 BiliDownloader 可执行文件及其分发版要求的工作目录。不要使用外层启动程序。使用用户提供或已确认的程序路径，不猜测文件名或安装位置；不以 Skill 的安装目录作为程序工作目录。
2. 从用户输入确定来源、是否实际下载、目标目录、选集和必要的媒体参数。只要求补充会影响执行的缺失信息，不反复询问已明确的要求。
3. 简单的单来源任务优先用 `--mode download`；需要特定按钮、逐行复选框、多个来源或执行过程中查询时，用 `--mode widgets`。两种模式不能混用参数。
4. 不确定可用画质、音轨或选集时，先进行用户请求范围内的只读查询，不猜测 UI 选项文本。每次调用是独立进程，后续调用必须重新提供来源或重放完整页面流程。
5. 仅在用户要求实际下载时使用 `--download` 或点击 `config.button_submit`。下载目录须已存在；未获授权不创建目录、不覆盖已有产物。用户未提供目录时，可以使用已有配置，但不得猜测它的具体路径。
6. 等待进程正常结束，逐行解析 stdout 的 JSON，并检查退出码。查询、下载结果、错误和诊断均在 stdout；直接调用即可，不使用重定向、合并输出流或额外管道。不因“已加入队列”或进度到 100% 就报告完成。
7. 最后只汇报下载成功/失败、实际产物路径和重要警告；用户要求查询时再提供对应查询结果。不要直接展示冗长控件树或内部诊断。

## 分发版启动约定

- 直接调用分发包 `bin` 目录下的实际可执行文件，不要求用户安装解释器、激活虚拟环境或准备源码。
- 外层启动程序仅用于正常启动 GUI，不支持 headless 操作，不能作为本 Skill 的 CLI 入口。
- `bin` 目录是分发包提供的程序目录，不是打包运行时的临时解压目录；不要猜测或调用临时目录中的内部程序，并保持分发文件完整。
- 实际文件名、扩展名和工作目录由用户安装的分发版决定。本手册不预设任何开发机路径、账号或环境名称。
- 使用能接收 CLI 参数并返回 stdout 和退出码的入口。所有 headless 输出统一通过 stdout 返回。若外层启动器不转发参数、发行版不支持 headless 或无法捕获结果，应报告限制并请用户提供合适的分发版，不回退到本机源码运行。
- 默认不安装、修复、重新打包或修改分发文件；启动失败时按实际错误报告。

在允许查询参数时，可使用实际程序入口查看帮助。以下为 PowerShell 调用格式，`&` 用于执行引号包围的程序路径：

```powershell
& "<BILIDOWNLOADER_EXE>" --headless --help
```

`<BILIDOWNLOADER_EXE>` 必须替换为分发包 `bin` 目录下的实际可执行文件路径，不能指向外层启动程序；它不是固定文件名。其他 shell 使用对应的可执行文件调用语法。使用进程工具时，优先分别传入程序路径、有序参数数组和工作目录，不拼接未经转义的用户输入。

## 最小命令模板

以下命令中的 `<BILIDOWNLOADER_EXE>`、`<BV_ID>`、`<DOWNLOAD_DIR>` 必须替换为实际程序路径、用户提供的编号和已存在的目标目录，不能直接执行占位符。

只查询信息、选集和格式：

```powershell
& "<BILIDOWNLOADER_EXE>" --headless --mode download --url "<BV_ID>" --info --list-episodes --list-formats
```

下载指定选集：

```powershell
& "<BILIDOWNLOADER_EXE>" --headless --mode download --url "<BV_ID>" --path "<DOWNLOAD_DIR>" --episodes "1-3,5" --codec hevc --danmaku true --download
```

仅下载音频：

```powershell
& "<BILIDOWNLOADER_EXE>" --headless --mode download --url "<BV_ID>" --path "<DOWNLOAD_DIR>" --audio-only true --download
```

发现控件或读取当前逻辑页面：

```powershell
& "<BILIDOWNLOADER_EXE>" --headless --mode widgets --list-controls
& "<BILIDOWNLOADER_EXE>" --headless --mode widgets --inspect main
```

## 必须遵守的语义

- **每次调用独立**：不提供持久会话、交互式 stdin、脚本文件或任意代码执行接口；任务 ID 只在本进程内稳定。
- **只读持久配置**：读取 GUI 的配置和登录凭据，本次改动仅在内存中。不得要求或输出 Cookie、密钥，也不通过修改 `userdata.json` 实现登录。
- **不支持登录变更**：headless 无扫码登录、Cookie 导入、注销；相关按钮明确报不支持。需要登录时，请用户在 GUI 中处理。
- **不支持暂停**：暂停/继续和打开目录等外部 GUI 操作被禁用；仅失败任务可重新开始。
- **真实页面约束**：只读或禁用控件不可强行改写；写入、点击前必须进入对应逻辑页面。隐藏页面可以读取，但其动态数据未必已加载。
- **自动等待**：已知页面加载自动等待；普通等待默认 60 秒，最终下载默认不限时。可调整超时，禁止用固定 sleep 或高频外部轮询代替已有等待机制。
- **安全退出**：提交下载后自动等待全部任务收尾，包括合并、弹幕和清理；无须另加退出参数。操作错误停止后续步骤，但已经提交的任务继续收尾。超时或 Ctrl+C 请求取消，不强杀受保护的合并阶段。
- **结果可信来源**：以最终 `downloads.tasks[].files` 为实际路径，不根据标题自行拼接。`success: true` 仍可能附有弹幕跳过等 `warnings`；进程非零退出也必须向用户说明。

## 避免常见误用

- `--tab confirm` 无效：`confirm` 是输入流程子页，要点击输入页的下一步进入。
- widgets 模式不能使用 `--url`、`--quality`、`--download` 等业务参数；应使用 `--set`、`--click`。
- download 模式必须提供 `--url`，且至少有 `--info`、`--list-episodes`、`--list-formats`、`--download` 之一；仅给出媒体参数不会下载。
- 业务布尔参数需要值：`--danmaku true`，不是裸 `--danmaku`。
- 不把 `visible: false` 当成无法操作：offscreen 根窗口始终不显示，应看 `active`、`enabled` 和 `read_only`。
- 不猜测数字画质映射、音轨名称或行号，先读可用选项；画质是现有下载逻辑中的优选/上限，不承诺账号无权访问的画质。
- 不盲目重跑已经成功的下载，成品文件可能被替换。只重试用户授权的失败任务。

## 接口变化时

以用户实际安装版本的帮助信息、控件枚举及随包文档为准。仅在允许执行时使用实际可执行文件的 `--headless --help`、`--list-controls` 核对接口。旧版没有对应能力时明确说明，不编造参数、不假设可访问源码或开发环境。
