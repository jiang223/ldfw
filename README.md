# LDFW - 手游模拟器通用自动化脚本框架

## 项目简介
LDFW 是一个面向雷电模拟器的**配置驱动自动化框架**，核心目标是：
- 后台运行（基于 ADB，不依赖前台焦点）
- 可视化编排（模块/流程/节点）
- 抗检测（随机偏移 + 随机延时）
- 高容错（失败重试/跳过/终止）
- 无需修改核心代码即可复用到不同游戏

## 特性列表
- ✅ 多模拟器实例（序列号区分）
- ✅ 模板匹配、找色、多点比色
- ✅ 点击/长按/滑动/输入/物理按键
- ✅ IF/WHILE/DELAY/LOG/FIND_IMAGE 等节点
- ✅ 模块配置 JSON 化，支持 CRUD 与排序
- ✅ GUI 可视化界面（PyQt5）
- ✅ OCR 双后端（paddleocr 优先，pytesseract 兜底）
- ✅ 日志控制台 + 按天落盘

## 目录结构

```text
ldfw/
├── README.md
├── requirements.txt
├── main.py
├── config/
│   ├── settings.json
│   └── modules/
│       └── example_module.json
├── core/
│   ├── __init__.py
│   ├── emulator.py
│   ├── image_finder.py
│   ├── input_controller.py
│   ├── flow_engine.py
│   ├── module_manager.py
│   ├── task_scheduler.py
│   ├── ocr_engine.py
│   └── logger.py
├── gui/
│   ├── __init__.py
│   ├── main_window.py
│   ├── module_editor.py
│   ├── flow_editor.py
│   ├── node_config_panel.py
│   └── status_panel.py
├── assets/
│   └── images/
│       └── common/
│           └── .gitkeep
└── utils/
    ├── __init__.py
    ├── random_utils.py
    └── window_utils.py
```

## 安装步骤
```bash
pip install -r requirements.txt
```

> Windows 环境建议已安装 ADB 并加入 PATH。

## 快速开始
1. 编辑 `config/settings.json`（ADB 路径、设备序列号、阈值、快捷键）
2. 参考 `config/modules/example_module.json` 配置你的模块/流程/节点
3. 启动 GUI：
   ```bash
   python main.py
   ```
4. 在 GUI 中管理模块，使用顶部工具栏启动/暂停/停止

## 配置文件说明（settings.json）
- `emulator.type`: 模拟器类型，默认 `leidian`
- `emulator.adb_path`: ADB 可执行路径
- `emulator.devices`: 设备列表（`serial` + `name`）
- `resolution`: 目标分辨率
- `hotkeys`: 启停快捷键提示
- `default_threshold`: 默认找图阈值
- `retry_count` / `retry_interval_ms`: 默认重试策略
- `random_delay`: 人类节奏默认随机区间
- `click_offset`: 点击随机偏移范围
- `log_level`: 日志级别
- `ocr_engine`: OCR 引擎偏好

## 模块/流程/节点说明
- 模块：由多个流程组成，按顺序执行
- 流程：由多个节点组成，支持 `on_error=retry|skip|abort`
- 节点：执行最小操作单元，支持逻辑嵌套

## 支持的节点类型
| 节点类型 | 功能 | 关键字段 |
|---|---|---|
| IF_CHECK | 图片条件分支 | template_path, threshold, true_nodes, false_nodes |
| WHILE_LOOP | 条件循环 | condition_template, max_loops, body_nodes |
| CLICK | 点击/长按 | position/template_path, offset, times, long_press_ms |
| SWIPE | 滑动 | x1,y1,x2,y2,duration_ms,curve |
| INPUT | 输入文本 | text |
| KEY_EVENT | 系统按键 | key(back/home/menu) |
| DELAY | 延时 | delay_ms 或 random_ms[min,max] |
| FIND_IMAGE | 找图并写入上下文 | template_path, save_as |
| LOG | 输出日志 | message |

## 图片资源管理规范
建议按功能分层存放：

```text
assets/images/{游戏名}/{功能}/xxx.png
```

例如：
- `assets/images/game_a/home/main_entry.png`
- `assets/images/game_a/popup/reward_close.png`

## FAQ
### 1）找图失败怎么办？
- 检查模板截图分辨率是否一致
- 降低/提高阈值（0.75~0.92 间测试）
- 使用 `region` 缩小检测范围

### 2）脚本会抢鼠标吗？
不会。全部走 ADB 后台命令，不依赖前台焦点。

### 3）OCR 依赖没装怎么办？
框架会自动降级并返回空字符串，同时记录 warning 日志。

### 4）如何防检测？
内置随机偏移、50~150ms 操作后抖动延时、可配置随机区间 DELAY 节点。

## 扩展开发指南
- 新增节点：在 `core/flow_engine.py` 的 `NodeType` 与 `_execute_single_node` 扩展
- 新增 GUI 表单：在 `gui/node_config_panel.py` 增加类型映射
- 新增模块能力：在 `core/module_manager.py` 增加字段并序列化
- 新增调度策略：在 `core/task_scheduler.py` 增加 cron/窗口期策略

## 日志说明
日志输出到：
- 控制台
- `logs/YYYYMMDD.log`

日志格式：
```text
[时间][级别][模块/流程][消息]
```
