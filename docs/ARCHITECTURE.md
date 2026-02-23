# CLI Music Player - 架构设计文档

## 1. 系统架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                        Presentation Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Main Screen │  │ Playlist   │  │  Visualizer Widgets     │  │
│  │             │  │  Screen    │  │  - SpectrumAnalyzer     │  │
│  │  - Header   │  │             │  │  - WaveformDisplay      │  │
│  │  - Progress │  │  - ListView│  │  - CircularVisualizer   │  │
│  │  - Controls │  │  - Search  │  │  - ParticleEffect       │  │
│  │  - Waveform │  │  - Sort    │  │                          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                      Theme Engine Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Theme Loader │  │ Style      │  │  Layout Manager         │  │
│  │             │  │  Resolver  │  │                          │  │
│  │ - Built-in  │  │             │  │  - Panel positioning    │  │
│  │ - Custom    │  │ - Colors   │  │  - Responsive layout    │  │
│  │ - Hot-swap  │  │ - Chars    │  │  - Theme overrides      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                       Business Logic Layer                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Player    │  │  Playlist   │  │   Visualizer Engine     │  │
│  │   Engine    │  │   Manager   │  │                          │  │
│  │             │  │             │  │  - FFT Processor        │  │
│  │ - Play/Pause│  │ - Add/Remove│  │  - Data smoothing       │  │
│  │ - Seek      │  │ - Sort      │  │  - FPS control          │  │
│  │ - Volume    │  │ - Persistence│  │  - Buffer management    │  │
│  │ - Callbacks │  │             │  │                          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                       Data Access Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Audio I/O  │  │  Metadata   │  │   Configuration         │  │
│  │             │  │   Reader    │  │                          │  │
│  │ - PyAudio   │  │             │  │  - YAML parser          │  │
│  │ - SoundFile │  │ - Mutagen   │  │  - Schema validation    │  │
│  │ - Buffer    │  │ - Cover art │  │  - Auto-save            │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 2. 核心组件详解

### 2.1 音频播放引擎 (Player Engine)

```python
class AudioEngine:
    """
    负责音频的解码、播放控制和状态管理
    """
    - 状态: IDLE, PLAYING, PAUSED, STOPPED
    - 音频流管理
    - 播放位置追踪
    - 音量控制
    - 回调注册（用于可视化）
```

**关键设计决策：**
- 使用 PyAudio 的回调模式获取实时音频数据
- 双缓冲机制保证播放流畅
- 独立线程处理音频解码，避免阻塞UI

### 2.2 可视化引擎 (Visualizer Engine)

```python
class VisualizerEngine:
    """
    处理音频数据的FFT分析，驱动各种可视化效果
    """
    - FFT处理器
    - 数据平滑滤波器
    - 多渲染器管理
    - 帧率控制
```

**设计要点：**
- 策略模式支持多种可视化类型
- 可配置的FFT参数（窗口大小、重叠率）
- 与音频引擎解耦，通过数据队列通信

### 2.3 主题系统 (Theme System)

```python
class ThemeManager:
    """
    主题加载、切换和应用
    """
    - 主题发现（内置 + 用户目录）
    - 动态加载
    - 热切换支持
    - CSS生成

class Theme:
    """
    单个主题的定义
    """
    - 颜色配置
    - 字符映射
    - 布局定义
    - 波形样式
```

**插件化设计：**
```
themes/
├── <theme_name>/
│   ├── __init__.py      # 主题入口，定义Theme类
│   ├── theme.yaml       # 配置数据
│   ├── styles.tcss      # Textual CSS（可选）
│   └── assets/          # 资源文件（可选）
```

### 2.4 UI架构

使用 Textual 框架的事件驱动架构：

```
┌─────────────────┐
│   MusicPlayerApp │  ← Textual App
│  (event loop)   │
└────────┬────────┘
         │ messages
         ▼
┌─────────────────┐
│    Screens      │  ← 不同界面（主界面、帮助、设置）
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Widgets      │  ← 可复用组件
│  - PlayerControl│
│  - ProgressBar  │
│  - Visualizer   │
│  - PlaylistView │
└─────────────────┘
```

## 3. 数据流设计

### 3.1 音频播放数据流

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Audio File  │───▶│   Decoder    │───▶│  PCM Buffer  │
└──────────────┘    └──────────────┘    └──────┬───────┘
                                               │
                         ┌─────────────────────┘
                         │
                         ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Speaker    │◄───│   PyAudio    │◄───│   Callback   │
└──────────────┘    └──────────────┘    └──────────────┘
                                               │
                         ┌─────────────────────┘
                         │ copy
                         ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Widgets    │◄───│  RingBuffer  │◄───│  Audio Data  │
└──────────────┘    └──────────────┘    └──────────────┘
                                               │
                         ┌─────────────────────┘
                         │ samples
                         ▼
                  ┌──────────────┐
                  │  FFT Analysis│
                  └──────────────┘
```

### 3.2 配置加载流程

```
启动
  │
  ▼
查找配置文件 ──找不到──▶ 创建默认配置
  │                        │
  │ 找到                   ▼
  ▼                     保存默认
验证配置 ──无效──▶ 使用默认值 + 警告
  │
  │ 有效
  ▼
应用配置
  │
  ├──▶ 主题设置
  ├──▶ 播放器设置
  ├──▶ 快捷键绑定
  └──▶ 可视化设置
```

## 4. 线程模型

```
Main Thread (Textual):
├── Event loop
├── UI rendering
└── User input handling

Audio Thread (PyAudio callback):
├── Audio output
├── Position tracking
└── Data broadcasting

Decoder Thread:
├── File reading
├── Audio decoding
└── Buffer filling

Visualizer Thread (optional):
├── FFT computation
├── Data processing
└── Frame generation
```

**线程安全考虑：**
- 使用 Queue 进行线程间数据传递
- 共享状态使用锁保护
- 音频回调函数保持最简，避免阻塞

## 5. 扩展性设计

### 5.1 可视化插件接口

```python
from abc import ABC, abstractmethod

class VisualizerPlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...
    
    @abstractmethod
    def render(self, fft_data: np.ndarray, canvas: Canvas) -> None: ...
    
    @abstractmethod
    def get_config_schema(self) -> dict: ...
```

### 5.2 主题插件接口

```python
class ThemePlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...
    
    @abstractmethod
    def get_styles(self) -> str: ...
    
    @abstractmethod
    def get_colors(self) -> dict: ...
    
    @abstractmethod
    def get_layout(self) -> dict: ...
```

## 6. 错误处理策略

| 错误类型 | 处理方式 |
|---------|---------|
| 音频文件损坏 | 跳过并记录，继续播放列表 |
| 音频设备不可用 | 提示用户，进入仅UI模式 |
| 主题加载失败 | 回退到默认主题 |
| 配置文件损坏 | 备份旧配置，创建默认配置 |
| 内存不足 | 清理缓存，降低可视化质量 |

## 7. 性能优化策略

1. **音频处理**
   - 预解码缓冲区
   - 合适的缓冲区大小（平衡延迟和流畅度）

2. **可视化**
   - FFT 使用 numpy 优化
   - 降采样减少计算量
   - 自适应帧率

3. **UI渲染**
   - 仅更新变化区域
   - 批量渲染操作
   - 避免不必要的重绘

4. **内存管理**
   - 封面图片缓存限制
   - 播放列表懒加载
   - 定期垃圾回收

## 8. 安全考虑

- 文件路径验证，防止目录遍历
- 音频文件格式验证，防止恶意文件
- 配置文件的沙箱加载
