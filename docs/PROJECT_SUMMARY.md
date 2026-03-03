# Music v0.2.0 - 功能增强

## 项目统计

- **总代码行数**: ~3,500+ 行 Python 代码
- **文件数**: 30+ 个 Python 模块
- **新增功能**: 可视化效果系统 + 布局系统

## 功能实现

### ✅ 核心功能 (M1)
- [x] 音频播放引擎 (PyAudio + soundfile)
- [x] 支持格式: MP3, FLAC, WAV, AAC, OGG, M4A
- [x] 播放控制: 播放/暂停/停止/跳转
- [x] 音量控制 + 静音
- [x] 元数据读取 (mutagen)

### ✅ UI界面 (M2)
- [x] Textual TUI 框架
- [x] 多布局系统 (6种布局)
- [x] 进度条显示
- [x] 音量条显示
- [x] 播放列表视图
- [x] 完整的键盘快捷键支持

### ✅ 音频可视化 (M3)
- [x] **可视化管理器**: 统一管理和切换所有可视化效果
- [x] **频谱分析器** (spectrum): 经典频率柱状图
- [x] **波形显示** (waveform): 时域波形
- [x] **圆形频谱** (circle): 径向/圆形频谱显示 🆕
- [x] **立体声分离** (stereo): 左右声道分别显示 🆕
- [x] **镜像频谱** (mirror): 上下对称显示 🆕
- [x] **对称频谱** (symmetry): 中心对称显示 🆕
- [x] **示波器** (oscilloscope): 复古示波器风格 🆕
- [x] **紧凑频谱** (compact): 单行频谱
- [x] 实时音频数据回调

### ✅ 布局系统 (M4) 🆕
- [x] **布局管理器**: 统一管理和切换所有布局
- [x] **默认布局** (default): 均衡显示所有组件
- [x] **紧凑布局** (compact): 小终端优化，隐藏可视化
- [x] **视觉布局** (visual): 最大化可视化区域
- [x] **播放列表布局** (playlist): 播放列表占主导
- [x] **极简布局** (minimal): 单行显示
- [x] **分栏布局** (split): 宽屏左右分栏
- [x] 自动根据终端尺寸选择布局

### ✅ 主题系统 (M5)
- [x] 5个内置主题: default, neon, minimal, retro, ocean
- [x] 主题管理器
- [x] 热切换支持
- [x] 颜色/字符/布局配置

### ✅ 播放列表 (M2+M4)
- [x] 播放列表管理
- [x] M3U/JSON 格式支持
- [x] 播放模式: 顺序/随机/单曲循环/列表循环
- [x] 排序功能
- [x] 搜索功能

### ✅ 配置管理
- [x] YAML 配置文件
- [x] 配置验证 (Pydantic)
- [x] 自动保存/加载
- [x] 默认配置生成

## 项目结构

```
cmp/
├── __main__.py          # CLI入口
├── config/              # 配置管理
│   └── settings.py      # 配置模型和管理
├── player/              # 音频播放
│   ├── engine.py        # 播放引擎
│   ├── playlist.py      # 播放列表
│   └── metadata.py      # 元数据读取
├── visualizer/          # 可视化系统
│   ├── base.py          # 基类
│   ├── spectrum.py      # 频谱分析
│   ├── waveform.py      # 波形显示
│   ├── circle.py        # 圆形频谱 🆕
│   ├── stereo.py        # 立体声分离 🆕
│   ├── mirror.py        # 镜像频谱 🆕
│   ├── oscilloscope.py  # 示波器 🆕
│   └── manager.py       # 可视化管理器 🆕
├── themes/              # 主题系统
│   └── manager.py       # 主题管理
└── ui/                  # 用户界面
    ├── app.py           # 主应用
    ├── layouts/         # 布局系统 🆕
    │   ├── base.py      # 布局基类和管理器
    │   ├── default.py   # 默认布局
    │   ├── compact.py   # 紧凑布局
    │   ├── visual.py    # 视觉布局
    │   ├── playlist.py  # 播放列表布局
    │   ├── minimal.py   # 极简布局
    │   └── split.py     # 分栏布局
    ├── screens/         # 屏幕组件 🆕
    │   ├── player_screen.py  # 播放器屏幕
    │   └── menus.py     # 选择菜单
    └── widgets/         # UI组件
        ├── progress_bar.py
        ├── volume_bar.py
        ├── visualizer_widget.py
        └── playlist_widget.py
```

## 快捷键

### 播放控制
| 键 | 功能 |
|-----|------|
| Space | 播放/暂停 |
| N/P | 下一首/上一首 |
| ←/→ | 快进/快退 10s |
| ↑/↓ | 音量增减 |

### 控制
| 键 | 功能 |
|-----|------|
| M | 静音 |
| S | 随机播放 |
| R | 循环模式 |
| T | 切换主题 |
| V | 下一个可视化 |
| Shift+V | 上一个可视化 |
| Ctrl+V | 可视化菜单 |
| L | 播放列表开关 |
| Shift+L | 下一个布局 |
| Ctrl+L | 布局菜单 |

### 通用
| 键 | 功能 |
|-----|------|
| Q | 退出 |
| ? | 帮助 |

## 可视化效果

| 效果 | 快捷键 | 描述 |
|------|--------|------|
| spectrum | V | 经典频谱柱状图 |
| waveform | V | 时域波形 |
| circle | V | 圆形/径向频谱 |
| stereo | V | 左右声道分离 |
| mirror | V | 上下镜像对称 |
| symmetry | V | 中心对称 |
| oscilloscope | V | 复古示波器 |
| compact | V | 单行紧凑 |

## 布局样式

| 布局 | 快捷键 | 描述 |
|------|--------|------|
| default | Shift+L | 均衡显示所有组件 |
| compact | Shift+L | 小终端优化 |
| visual | Shift+L | 最大化可视化 |
| playlist | Shift+L | 播放列表优先 |
| minimal | Shift+L | 单行极简 |
| split | Shift+L | 宽屏分栏 |

## 安装使用

```bash
# 安装依赖
pip install -e .

# 播放音乐
music song.mp3
music ~/Music/
music -t neon playlist.m3u
```

## 待扩展功能 (未来版本)

- 歌词显示
- 在线歌词获取
- 更多可视化效果 (粒子、瀑布图)
- 插件系统
- 远程控制 API
- 音效均衡器
- 交叉淡入淡出
