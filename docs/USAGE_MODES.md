# CLI Music Player 使用方式

本文档说明两种使用方式：**本地 CLI 模式** 和 **远程 MCP 模式**。

---

## 概览

| 模式 | 适用场景 | 启动方式 | 交互方式 |
|------|----------|----------|----------|
| **CLI 模式** | 本地安装，直接使用 | `cmp` | 终端 TUI，键盘操作 |
| **MCP 模式** | 远程/局域网控制 | `cmp --mcp` | AI 助手远程调用 |

---

## 1. CLI 模式（本地使用）

### 1.1 适用场景

- ✅ 个人电脑本地使用
- ✅ 直接在终端操作
- ✅ 需要可视化界面
- ✅ 实时交互响应

### 1.2 安装

```bash
# 安装系统依赖
brew install portaudio  # macOS

# 安装播放器
cd ~/works2/cli-music-player
pip install -e .
```

### 1.3 启动方式

```bash
# 基本使用
cmp song.mp3                    # 播放单个文件
cmp ~/Music/                    # 播放文件夹
cmp playlist.m3u                 # 播放播放列表

# 带参数启动
cmp -t neon ~/Music/            # 使用 neon 主题
cmp -s ~/Music/                 # 启用随机播放
cmp --layout visual song.mp3    # 使用可视化布局
```

### 1.4 键盘操作

| 按键 | 功能 |
|------|------|
| `Space` | 播放/暂停 |
| `N` / `P` | 下一曲/上一曲 |
| `←` / `→` | 快退/快进 10 秒 |
| `↑` / `↓` | 音量增/减 |
| `M` | 静音 |
| `S` | 随机播放 |
| `R` | 循环模式 |
| `T` | 切换主题 |
| `V` | 切换可视化 |
| `L` | 切换布局 |
| `Q` | 退出 |

### 1.5 配置文件

配置保存在 `~/.config/cmp/config.yaml`：

```yaml
player:
  default_volume: 70
  remember_position: true

visualizer:
  enabled: true
  type: spectrum
  fps: 30

interface:
  layout: default
  theme: default
```

---

## 2. MCP 模式（远程控制）

### 2.1 适用场景

- ✅ AI 助手远程控制（Claude、ChatGPT 等）
- ✅ 局域网多设备控制
- ✅ 自动化脚本调用
- ✅ 无头服务器运行

### 2.2 启动方式

```bash
# 启动 MCP Server
cmp --mcp

# 指定端口（默认使用 stdio）
cmp --mcp --port 8080

# 后台运行（daemon 模式）
cmp --daemon --port 8080 --mcp
```

### 2.3 MCP 工具列表

MCP Server 暴露以下工具供 AI 助手调用：

#### 播放控制

| 工具 | 说明 | 参数 |
|------|------|------|
| `play` | 播放 | `track_id` (可选) |
| `pause` | 暂停 | - |
| `stop` | 停止 | - |
| `next_track` | 下一曲 | - |
| `previous_track` | 上一曲 | - |
| `seek` | 跳转 | `position_seconds` |
| `set_volume` | 设置音量 | `volume` (0-100) |
| `set_shuffle` | 随机播放 | `enabled` (bool) |
| `set_repeat` | 循环模式 | `mode` (none/all/one) |

#### 播放列表管理

| 工具 | 说明 | 参数 |
|------|------|------|
| `get_playlist` | 获取播放列表 | - |
| `add_to_playlist` | 添加曲目 | `paths` (list) |
| `remove_from_playlist` | 移除曲目 | `indices` (list) |
| `clear_playlist` | 清空播放列表 | - |
| `sort_playlist` | 排序 | `by`, `reverse` |
| `search_playlist` | 搜索 | `query` |
| `jump_to_track` | 跳转到指定曲目 | `index` |

#### 可视化与主题

| 工具 | 说明 | 参数 |
|------|------|------|
| `set_visualizer` | 设置可视化类型 | `type` |
| `list_visualizers` | 列出可用可视化 | - |
| `set_theme` | 设置主题 | `name` |
| `list_themes` | 列出可用主题 | - |
| `set_layout` | 设置布局 | `name` |

#### 状态查询

| 工具 | 说明 |
|------|------|
| `get_current_track` | 获取当前曲目信息 |
| `get_player_status` | 获取播放器状态 |
| `get_config` | 获取当前配置 |

### 2.4 与 AI 助手集成

#### Claude Desktop 配置

编辑 Claude Desktop 配置文件：

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "cmp": {
      "command": "cmp",
      "args": ["--mcp"]
    }
  }
}
```

#### 使用示例

```
用户: 帮我播放一些爵士乐
AI: [调用 add_to_playlist 添加爵士乐文件夹]
    [调用 play 开始播放]

用户: 把音量调到 50
AI: [调用 set_volume(50)]

用户: 切换到圆形可视化
AI: [调用 set_visualizer("circle")]

用户: 现在播放的是什么歌？
AI: [调用 get_current_track]
    现在播放的是 "Take Five" - Dave Brubeck
```

### 2.5 HTTP API（Daemon 模式）

启动 daemon 后，可通过 HTTP API 控制：

```bash
# 启动 daemon
cmp --daemon --port 8080

# HTTP 调用示例
curl http://localhost:8080/api/play
curl http://localhost:8080/api/pause
curl http://localhost:8080/api/volume?value=50
curl http://localhost:8080/api/status
```

#### WebSocket 实时事件

```javascript
// 连接 WebSocket
const ws = new WebSocket('ws://localhost:8080/ws');

// 接收事件
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.type, data.data);
};

// 事件类型
// - playback.started
// - playback.paused
// - playback.position_changed
// - track.changed
// - volume.changed
```

---

## 3. 模式对比

### 3.1 功能对比

| 功能 | CLI 模式 | MCP 模式 |
|------|----------|----------|
| 可视化界面 | ✅ 完整 TUI | ❌ 无界面 |
| 键盘操作 | ✅ | ❌ |
| AI 控制 | ❌ | ✅ |
| 远程控制 | ❌ | ✅ |
| 多客户端 | ❌ | ✅ |
| 自动化脚本 | ❌ | ✅ |
| 实时响应 | ✅ 毫秒级 | ⚠️ 网络延迟 |

### 3.2 资源占用

| 模式 | 内存 | CPU | 网络 |
|------|------|-----|------|
| CLI | ~30-50MB | 可视化时较高 | 无 |
| MCP | ~50-80MB | 较低 | 监听端口 |

### 3.3 选择建议

```
┌─────────────────────────────────────────────────────────────┐
│                    如何选择使用模式？                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  你是否需要 AI 助手控制？                                    │
│       │                                                     │
│       ├── 是 ──▶ MCP 模式                                   │
│       │           │                                         │
│       │           └── 需要可视化界面？                       │
│       │                    │                                │
│       │                    ├── 是 ──▶ 同时运行 CLI + MCP     │
│       │                    │         (两个进程)              │
│       │                    │                                │
│       │                    └── 否 ──▶ 仅 MCP 模式            │
│       │                                                     │
│       └── 否 ──▶ CLI 模式                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. 同时使用两种模式

可以在同一台机器上同时运行 CLI 和 MCP：

```bash
# 终端 1：启动 MCP Server（后台）
cmp --daemon --port 8080 --mcp

# 终端 2：启动 CLI TUI
cmp ~/Music/

# AI 助手可以远程控制
# 同时你可以在终端看到可视化效果
```

**注意**：两个进程共享同一个配置文件，但播放状态可能不同步。建议：
- 使用 CLI 时，AI 助手只做查询操作
- 或使用 daemon 模式，CLI 作为客户端连接

---

## 5. 故障排除

### CLI 模式问题

| 问题 | 解决方案 |
|------|----------|
| 无声音 | 检查 PortAudio 安装：`brew install portaudio` |
| 可视化卡顿 | 降低 FPS 或使用 compact 布局 |
| 配置丢失 | 检查 `~/.config/cmp/config.yaml` 权限 |

### MCP 模式问题

| 问题 | 解决方案 |
|------|----------|
| AI 无法连接 | 确认 MCP Server 正在运行 |
| 工具调用失败 | 检查日志：`~/.local/share/cmp/logs/` |
| 端口被占用 | 使用 `--port` 指定其他端口 |

---

## 6. 快速参考

```bash
# CLI 模式
cmp ~/Music/                    # 播放音乐
cmp -t neon -s ~/Music/         # neon 主题 + 随机

# MCP 模式
cmp --mcp                       # 启动 MCP Server
cmp --daemon --port 8080 --mcp   # 后台运行 + HTTP API

# 查看帮助
cmp --help
cmp --mcp --help
```