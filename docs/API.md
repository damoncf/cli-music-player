# CLI Music Player - API 设计文档

## 1. 公共 API

### 1.1 命令行接口 (CLI)

```bash
music [OPTIONS] [PATH]
```

#### 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `PATH` | string | 要播放的文件、文件夹或播放列表 |

#### 选项

| 选项 | 简写 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--theme` | `-t` | string | "default" | 指定主题 |
| `--no-visualizer` | | flag | false | 禁用可视化 |
| `--visualizer-type` | | string | "spectrum" | 可视化类型 |
| `--config` | `-c` | string | ~/.config/... | 配置文件路径 |
| `--volume` | `-v` | int | 70 | 初始音量 (0-100) |
| `--shuffle` | `-s` | flag | false | 启用随机播放 |
| `--loop` | `-l` | string | "none" | 循环模式: none, all, one |
| `--debug` | `-d` | flag | false | 调试模式 |
| `--help` | `-h` | flag | | 显示帮助 |
| `--version` | `-V` | flag | | 显示版本 |

#### 示例

```bash
# 播放单个文件
music song.mp3

# 播放文件夹
music ~/Music/

# 使用霓虹主题播放
music -t neon playlist.m3u

# 禁用可视化，以波形模式播放
music --no-visualizer ~/Music/

# 指定配置文件启动
music -c ./my_config.yaml song.mp3
```

### 1.2 交互命令

在播放器运行时，可通过以下命令控制：

#### 播放控制

| 命令 | 快捷键 | 说明 |
|------|--------|------|
| `play` | Space | 播放/暂停 |
| `stop` | S | 停止播放 |
| `next` | N | 下一首 |
| `prev` | P | 上一首 |
| `seek <seconds>` | → / ← | 跳转（秒，可为负数） |
| `volume <0-100>` | ↑ / ↓ | 设置音量 |
| `mute` | M | 静音切换 |

#### 播放列表

| 命令 | 快捷键 | 说明 |
|------|--------|------|
| `list` | L | 显示/隐藏播放列表 |
| `add <path>` | | 添加文件/文件夹 |
| `remove <index>` | D | 移除指定索引的歌曲 |
| `clear` | | 清空播放列表 |
| `sort <by>` | | 排序: name, artist, album, random |
| `search <query>` | / | 搜索播放列表 |
| `jump <index>` | Enter | 跳转到指定索引 |

#### 播放模式

| 命令 | 快捷键 | 说明 |
|------|--------|------|
| `shuffle` | R | 切换随机播放 |
| `repeat <mode>` | | 设置循环: none, all, one |

#### 界面

| 命令 | 快捷键 | 说明 |
|------|--------|------|
| `theme <name>` | T | 切换主题 |
| `visualizer <type>` | V | 切换可视化类型 |
| `fullscreen` | F | 全屏切换 |
| `help` | ? / H | 显示帮助 |
| `quit` | Q / Esc | 退出 |

---

## 2. 配置文件 API

### 2.1 配置结构

```yaml
# config.yaml 结构定义

version: "1.0"                    # 配置格式版本

player:
  default_volume: 70              # 默认音量 (0-100)
  remember_position: true         # 记住播放位置
  auto_play: false                # 自动开始播放
  fade_in_out: true               # 淡入淡出效果
  
  # 音频输出设置
  output:
    device: null                  # null = 默认设备
    buffer_size: 1024             # 缓冲区大小
    sample_rate: 44100            # 采样率

playlist:
  default_sort: "name"            # 默认排序方式
  recursive_add: true             # 添加文件夹时递归
  save_on_exit: true              # 退出时保存播放列表
  history_size: 100               # 最近播放历史大小
  
  # 文件过滤
  filters:
    include: ["*.mp3", "*.flac", "*.wav", "*.aac", "*.ogg"]
    exclude: ["*temp*", "*cache*"]

visualizer:
  enabled: true                   # 默认启用
  type: "spectrum"                # 默认类型
  fps: 30                         # 刷新率
  sensitivity: 1.0                # 灵敏度 (0.1-3.0)
  
  # 频谱分析器设置
  spectrum:
    bar_count: 32
    bar_width: 2
    smoothing: 0.3
    
  # 波形设置
  waveform:
    style: "lines"
    channels: "stereo"
    
  # 性能设置
  performance:
    skip_frames: false            # 帧率不足时跳过
    quality: "medium"             # low, medium, high

theme:
  name: "default"                 # 默认主题
  custom_path: null               # 自定义主题路径
  
  # 主题特定的覆盖
  overrides:
    colors: {}
    layout: {}

keybindings:
  # 自定义快捷键
  # 格式: action: "key"
  quit: "q"
  play_pause: "space"
  next: "n"
  prev: "p"
  volume_up: "up"
  volume_down: "down"
  # ... 更多

interface:
  language: "zh_CN"               # 界面语言
  show_notifications: true        # 显示通知
  compact_mode: false             # 紧凑模式
  
  # 面板可见性
  panels:
    header: true
    visualizer: true
    controls: true
    playlist: true
    status_bar: true

advanced:
  log_level: "info"               # debug, info, warning, error
  log_file: null                  # 日志文件路径
  cache_dir: "~/.cache/music"
  
  # 插件设置
  plugins:
    enabled: []
    paths: []
```

### 2.2 配置管理命令

```bash
# 查看当前配置
music config show

# 编辑配置
music config edit

# 重置配置为默认
music config reset

# 验证配置
music config validate

# 导入配置
music config import <path>

# 导出配置
music config export <path>
```

---

## 3. 主题 API

### 3.1 主题管理命令

```bash
# 列出所有可用主题
music theme list

# 查看主题详情
music theme info <name>

# 预览主题
music theme preview <name>

# 安装主题
music theme install <path-or-url>

# 卸载主题
music theme uninstall <name>

# 创建主题模板
music theme create <name>

# 验证主题
music theme validate <path>
```

### 3.2 程序化主题接口

```python
from cli_music_player.themes import ThemeManager, Theme

# 获取主题管理器
tm = ThemeManager()

# 列出主题
themes = tm.list_themes()
for theme in themes:
    print(f"{theme.name}: {theme.description}")

# 加载主题
theme = tm.load_theme("neon")

# 应用主题
tm.apply_theme(theme)

# 注册自定义主题
custom_theme = Theme.from_file("/path/to/theme.yaml")
tm.register(custom_theme)

# 获取当前主题
current = tm.get_current_theme()
print(current.colors.accent)
```

---

## 4. 播放列表 API

### 4.1 播放列表格式

#### M3U 格式
```m3u
#EXTM3U
#EXTINF:234,Artist Name - Song Title
/path/to/song1.mp3
#EXTINF:185,Another Artist - Another Song
/path/to/song2.flac
```

#### JSON 格式
```json
{
  "version": "1.0",
  "name": "My Playlist",
  "created": "2024-01-15T10:30:00Z",
  "items": [
    {
      "path": "/path/to/song1.mp3",
      "title": "Song Title",
      "artist": "Artist Name",
      "duration": 234
    }
  ]
}
```

### 4.2 播放列表管理命令

```bash
# 创建播放列表
music playlist create <name>

# 添加歌曲到播放列表
music playlist add <playlist> <path>

# 从播放列表移除
music playlist remove <playlist> <index>

# 查看播放列表内容
music playlist show <playlist>

# 合并播放列表
music playlist merge <playlist1> <playlist2> <output>

# 转换格式
music playlist convert <input> <output> --format <json|m3u>

# 导出播放列表
music playlist export <name> --format <json|m3u>
```

### 4.3 程序化播放列表接口

```python
from cli_music_player.playlist import Playlist, PlaylistManager

# 创建播放列表
pl = Playlist(name="Favorites")
pl.add("/path/to/song.mp3")
pl.add("/path/to/folder/", recursive=True)

# 排序
pl.sort(by="artist", reverse=False)

# 保存
pl.save("favorites.json")

# 加载
pl2 = Playlist.load("favorites.json")

# 播放列表管理器
pm = PlaylistManager()
recent = pm.get_recently_played(limit=10)
```

---

## 5. 可视化 API

### 5.1 可视化类型

| 类型 | 标识符 | 描述 |
|------|--------|------|
| 频谱分析器 | `spectrum` | FFT频谱柱状图 |
| 波形图 | `waveform` | 时域波形显示 |
| 圆形频谱 | `circular` | 径向频谱显示 |
| 粒子效果 | `particles` | 基于音频的粒子动画 |
| 禁用 | `none` | 无可视化 |

### 5.2 可视化配置命令

```bash
# 切换可视化类型
music visualizer set <type>

# 调整灵敏度
music visualizer sensitivity <0.1-3.0>

# 设置刷新率
music visualizer fps <15|30|60>

# 测试可视化
music visualizer test
```

### 5.3 程序化可视化接口

```python
from cli_music_player.visualizer import VisualizerEngine, SpectrumVisualizer

# 创建可视化引擎
engine = VisualizerEngine()

# 注册可视化器
engine.register(SpectrumVisualizer(
    bar_count=32,
    smoothing=0.3
))

# 设置音频数据源
def audio_callback(data):
    engine.process(data)

engine.set_callback(audio_callback)

# 渲染到画布
engine.render(canvas)

# 自定义可视化器
class MyVisualizer(VisualizerPlugin):
    @property
    def name(self) -> str:
        return "my_visualizer"
    
    def render(self, fft_data: np.ndarray, canvas: Canvas) -> None:
        # 自定义渲染逻辑
        pass

engine.register(MyVisualizer())
```

---

## 6. 事件系统

### 6.1 可用事件

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class PlaybackStarted:
    track: Track
    position: int = 0

@dataclass
class PlaybackPaused:
    track: Track
    position: int

@dataclass
class PlaybackResumed:
    track: Track
    position: int

@dataclass
class PlaybackStopped:
    track: Optional[Track]

@dataclass
class TrackChanged:
    previous: Optional[Track]
    current: Track
    index: int

@dataclass
class PositionChanged:
    position: int
    duration: int
    percentage: float

@dataclass
class VolumeChanged:
    volume: int  # 0-100
    muted: bool

@dataclass
class PlaylistUpdated:
    action: str  # "added", "removed", "reordered", "cleared"
    items: list

@dataclass
class ThemeChanged:
    old_theme: str
    new_theme: str

@dataclass
class VisualizerData:
    fft_data: np.ndarray
    waveform_data: np.ndarray
    peak: float
    rms: float
```

### 6.2 事件监听示例

```python
from cli_music_player.events import event_bus

# 订阅事件
@event_bus.on(PlaybackStarted)
def on_playback_started(event: PlaybackStarted):
    print(f"Started playing: {event.track.title}")

@event_bus.on(VolumeChanged)
def on_volume_changed(event: VolumeChanged):
    if event.muted:
        print("Muted")
    else:
        print(f"Volume: {event.volume}%")

# 发送事件
event_bus.emit(PlaybackStarted(track=current_track))
```

---

## 7. 插件 API（未来扩展）

### 7.1 插件接口

```python
from abc import ABC, abstractmethod

class Plugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...
    
    @property
    @abstractmethod
    def version(self) -> str: ...
    
    @abstractmethod
    def initialize(self, app) -> None: ...
    
    @abstractmethod
    def shutdown(self) -> None: ...

class VisualizerPlugin(Plugin):
    @abstractmethod
    def render(self, data: AudioData, canvas: Canvas) -> None: ...
    
    @abstractmethod
    def get_config_schema(self) -> dict: ...

class ThemePlugin(Plugin):
    @abstractmethod
    def get_styles(self) -> str: ...
    
    @abstractmethod
    def get_layout(self) -> dict: ...
```

### 7.2 插件生命周期

```
┌─────────┐    ┌──────────┐    ┌─────────┐    ┌──────────┐
│  Load   │───▶│ Initialize│───▶│  Run   │───▶│ Shutdown │
│         │    │          │    │         │    │          │
│ 发现插件 │    │ 注册组件  │    │ 事件监听 │    │ 资源清理  │
│ 验证接口 │    │ 加载配置  │    │ 提供服务 │    │ 保存状态  │
└─────────┘    └──────────┘    └─────────┘    └──────────┘
```

---

## 8. 错误代码

| 代码 | 含义 | 说明 |
|------|------|------|
| E001 | 文件不存在 | 指定的音频文件或配置文件不存在 |
| E002 | 格式不支持 | 音频格式无法解码 |
| E003 | 音频设备错误 | 无法初始化音频输出设备 |
| E004 | 主题加载失败 | 主题文件损坏或不存在 |
| E005 | 配置无效 | 配置文件格式错误或验证失败 |
| E006 | 权限错误 | 文件读写权限不足 |
| E007 | 内存不足 | 无法分配所需内存 |
| E008 | 网络错误 | 下载主题或歌词时网络错误 |
| E009 | 插件错误 | 插件加载或执行错误 |
| E010 | 解码错误 | 音频解码过程中出错 |
