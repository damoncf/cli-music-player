# CLI Music Player - 主题系统设计文档

## 1. 设计目标

主题系统的核心设计目标是：
- **插件化**：主题作为独立插件，可动态加载
- **可配置**：支持颜色、字符、布局的深度定制
- **热切换**：运行时切换主题，无需重启
- **易开发**：简单的主题创建流程

## 2. 主题结构

### 2.1 目录结构

```
themes/
├── default/                    # 内置默认主题
│   ├── __init__.py            # 主题入口（可选，高级用法）
│   ├── theme.yaml             # 主题主配置
│   ├── colors.yaml            # 颜色定义（可选，可合并到theme.yaml）
│   ├── layout.yaml            # 布局配置（可选）
│   └── assets/                # 资源目录（可选）
│       └── logo.txt
├── neon/
│   ├── theme.yaml
│   └── ...
└── custom/                    # 用户自定义主题目录
    └── my_theme/
        └── theme.yaml
```

### 2.2 主题配置文件 (theme.yaml)

```yaml
# 主题元信息
meta:
  name: "Neon Night"
  version: "1.0.0"
  author: "Your Name"
  description: "A cyberpunk-inspired neon theme"
  tags: ["dark", "colorful", "modern"]
  requires_version: ">=0.1.0"

# 颜色方案
colors:
  # 基础颜色
  background: "#0a0a0f"
  foreground: "#00ff9d"
  secondary: "#ff00ff"
  accent: "#00ffff"
  
  # 状态颜色
  playing: "#00ff9d"
  paused: "#ffff00"
  stopped: "#ff5555"
  
  # 组件特定颜色
  progress_bar:
    filled: "#00ff9d"
    empty: "#333333"
    thumb: "#ffffff"
  
  volume_bar:
    filled: "#00ffff"
    empty: "#333333"
  
  playlist:
    selected: "#1a1a2e"
    current: "#00ff9d"
    text: "#cccccc"
    header: "#ff00ff"
  
  visualizer:
    primary: "#00ff9d"
    secondary: "#ff00ff"
    background: "#0a0a0f"

# 字符映射（ASCII艺术风格）
characters:
  # 边框样式
  border:
    horizontal: "═"
    vertical: "║"
    top_left: "╔"
    top_right: "╗"
    bottom_left: "╚"
    bottom_right: "╝"
    cross: "╬"
    t_down: "╦"
    t_up: "╩"
    t_right: "╠"
    t_left: "╣"
  
  # 进度条样式
  progress_bar:
    filled: "█"
    empty: "░"
    thumb: "▶"
  
  # 音量条样式
  volume_bar:
    filled: "▓"
    empty: "▒"
    mute_indicator: "🔇"
  
  # 播放控制图标
  controls:
    play: "▶"
    pause: "⏸"
    stop: "⏹"
    next: "⏭"
    prev: "⏮"
    shuffle: "🔀"
    repeat: "🔁"
    repeat_one: "🔂"
  
  # 波形显示字符
  waveform:
    levels: ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
    space: " "

# 布局配置
layout:
  # 主布局类型: horizontal, vertical, custom
  type: "vertical"
  
  # 面板配置
  panels:
    header:
      height: 3
      visible: true
      style: "compact"  # compact, detailed
    
    visualizer:
      height: 12
      visible: true
      position: "center"
      margin: [1, 2, 1, 2]  # top, right, bottom, left
    
    controls:
      height: 3
      visible: true
      alignment: "center"  # left, center, right
    
    playlist:
      height: "auto"  # 或固定值
      visible: true
      max_items: 10
      show_header: true
      show_numbers: true
    
    status_bar:
      height: 1
      visible: true
  
  # 面板顺序
  order: ["header", "visualizer", "controls", "playlist", "status_bar"]

# 可视化样式
visualizer:
  # 频谱分析器配置
  spectrum:
    bar_count: 32           # 频谱条数量
    bar_width: 2            # 每个条的宽度（字符）
    bar_spacing: 1          # 条间距
    orientation: "vertical" # vertical, horizontal
    smoothing: 0.3          # 平滑系数 (0-1)
    
  # 波形显示配置
  waveform:
    channels: "stereo"      # mono, stereo, merged
    resolution: "medium"    # low, medium, high
    style: "lines"          # lines, dots, filled
  
  # 圆形可视化配置
  circular:
    radius: 10
    symmetry: 2             # 对称性（花瓣数）
    rotation_speed: 0       # 自动旋转速度

# 动画配置
animation:
  enabled: true
  transition_duration: 200  # 过渡动画时长(ms)
  
  # 特定动画
  progress_update: "smooth"  # instant, smooth
  visualizer_fade: true
  panel_slide: false

# Textual CSS 扩展（可选，高级用法）
tcss: |
  /* 可以覆盖或扩展默认样式 */
  .player-header {
      text-style: bold;
      color: $accent;
  }
  
  .visualizer-canvas {
      border: solid $secondary;
  }
```

## 3. 主题引擎架构

### 3.1 组件图

```
┌─────────────────────────────────────────────────────────┐
│                    ThemeManager                         │
│  - discover_themes()    - load_theme(name)              │
│  - get_current_theme()  - apply_theme(theme)            │
│  - list_themes()        - reload_theme()                │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼ uses
┌─────────────────────────────────────────────────────────┐
│                    ThemeLoader                          │
│  - parse_yaml()        - validate_schema()              │
│  - resolve_inheritance() - load_assets()                │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼ creates
┌─────────────────────────────────────────────────────────┐
│                    ThemeInstance                        │
│  - colors: ColorPalette                                 │
│  - characters: CharMap                                  │
│  - layout: LayoutConfig                                 │
│  - visualizer: VisualizerStyle                          │
│  - get_color(key)      - get_char(key)                  │
│  - get_tcss()          - to_textual_styles()            │
└─────────────────────────────────────────────────────────┘
```

### 3.2 主题解析流程

```
用户选择主题
      │
      ▼
定位主题目录 ──不存在──▶ 报错
      │
      │ 存在
      ▼
解析 theme.yaml ──无效──▶ 回退到默认主题 + 警告
      │
      │ 有效
      ▼
验证颜色格式
      │
      ▼
加载字符映射
      │
      ▼
解析布局配置
      │
      ▼
加载可视化样式
      │
      ▼
生成 Textual CSS
      │
      ▼
应用主题到 UI
      │
      ▼
触发界面重绘
```

## 4. 内置主题预览

### 4.1 Default（默认）
经典终端风格，黑白灰配色，简洁实用。

```yaml
colors:
  background: "#000000"
  foreground: "#ffffff"
  accent: "#00aa00"
  progress_bar:
    filled: "#"
    empty: "-"
```

### 4.2 Neon（霓虹）
赛博朋克风格，荧光绿配紫色，适合暗色终端。

```yaml
colors:
  background: "#0a0a0f"
  foreground: "#00ff9d"
  secondary: "#ff00ff"
  accent: "#00ffff"
```

### 4.3 Minimal（极简）
最简设计，去除装饰，专注内容。

```yaml
layout:
  panels:
    header:
      visible: false
    visualizer:
      height: 5
    playlist:
      show_header: false
      show_numbers: false
```

### 4.4 Retro（复古）
复古计算机风格，琥珀色或绿色荧光屏效果。

```yaml
colors:
  background: "#1a1a00"
  foreground: "#ffb000"  # 琥珀色
  # 或 foreground: "#33ff33"  # 绿色
  accent: "#ff6600"
```

### 4.5 Ocean（海洋）
深蓝配色，平静优雅。

```yaml
colors:
  background: "#001a33"
  foreground: "#66ccff"
  secondary: "#0099cc"
  accent: "#00ffff"
```

## 5. 主题开发指南

### 5.1 创建新主题的步骤

1. **复制模板**
   ```bash
   cp -r themes/default themes/my_theme
   ```

2. **编辑 theme.yaml**
   - 修改 meta 信息
   - 自定义颜色
   - 调整字符映射
   - 配置布局

3. **测试主题**
   ```bash
   music --theme my_theme
   ```

4. **分享主题**
   - 打包为主题文件（zip）
   - 发布到主题市场/社区

### 5.2 颜色值格式

支持的颜色格式：
- HEX: `#RRGGBB` 或 `#RGB`
- 颜色名称: `red`, `blue`, `green`, `white`, `black` 等
- ANSI 256色: `ansi_123`
- RGB元组: `[255, 128, 0]`

### 5.3 布局变量

在主题配置中可使用以下变量：
- `{terminal_width}` - 终端宽度
- `{terminal_height}` - 终端高度
- `{panel_count}` - 可见面板数量

## 6. 动态主题功能

### 6.1 时间/天气响应主题（未来扩展）

```yaml
meta:
  type: "dynamic"
  
dynamic:
  trigger: "time"  # time, weather, audio_analysis
  
  rules:
    - condition: "hour >= 6 and hour < 18"
      theme: "day_theme"
    - condition: "hour >= 18 or hour < 6"
      theme: "night_theme"
```

### 6.2 音频响应主题（未来扩展）

根据音频特征自动调整颜色：

```yaml
dynamic:
  trigger: "audio"
  
  rules:
    - condition: "bpm > 120"
      override:
        colors:
          visualizer:
            primary: "#ff0000"  # 快节奏用红色
    - condition: "bpm < 80"
      override:
        colors:
          visualizer:
            primary: "#0000ff"  # 慢节奏用蓝色
```

## 7. 主题API（供开发者）

### 7.1 程序化创建主题

```python
from cli_music_player.themes import Theme, ColorPalette

theme = Theme(
    name="Custom",
    colors=ColorPalette(
        background="#000000",
        foreground="#ffffff",
        accent="#ff0000"
    ),
    # ... 其他配置
)

theme_manager.register(theme)
theme_manager.apply("Custom")
```

### 7.2 主题事件监听

```python
@app.on(ThemeChange)
def on_theme_change(event: ThemeChange):
    old_theme = event.old_theme
    new_theme = event.new_theme
    # 执行主题切换后的自定义操作
```

## 8. 配置继承机制

主题可以通过 `extends` 字段继承其他主题：

```yaml
meta:
  name: "Neon Blue"
  extends: "neon"  # 继承 neon 主题

colors:
  # 只覆盖想要修改的颜色
  accent: "#0088ff"  # 将霓虹改为蓝色调
  
# 其他未覆盖的配置继承自父主题
```

继承优先级：子主题 > 父主题 > 默认配置
