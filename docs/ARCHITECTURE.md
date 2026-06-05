# 曲库管理系统架构设计

## 1. 系统概览

```
┌─────────────────────────────────────────────────────────────┐
│                    Music Library System                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  Crawler │───▶│  Parser  │───▶│  Indexer │              │
│  │  爬虫层   │    │  解析层   │    │  索引层   │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│       │               │               │                     │
│       ▼               ▼               ▼                     │
│  ┌──────────────────────────────────────────────┐          │
│  │              Storage Layer (存储层)            │          │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────────┐   │          │
│  │  │  Audio  │  │ Metadata│  │   Search    │   │          │
│  │  │  Files  │  │   DB    │  │   Index     │   │          │
│  │  └─────────┘  └─────────┘  └─────────────┘   │          │
│  └──────────────────────────────────────────────┘          │
│                        │                                    │
│                        ▼                                    │
│  ┌──────────────────────────────────────────────┐          │
│  │              API Layer (API层)                 │          │
│  │  REST API / MCP Tools / CLI Commands          │          │
│  └──────────────────────────────────────────────┘          │
│                        │                                    │
│                        ▼                                    │
│  ┌──────────────────────────────────────────────┐          │
│  │         CLI Music Player Integration          │          │
│  └──────────────────────────────────────────────┘          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 合法音乐来源

### 🟢 推荐来源（免费/开源）

| 来源 | 类型 | API | 特点 |
|------|------|-----|------|
| **Jamendo** | 免费音乐 | ✅ REST API | CC 授权，独立音乐人 |
| **Free Music Archive** | 免费音乐 | ✅ REST API | CC 授权，高质量 |
| **Internet Archive** | 公有领域 | ✅ REST API | 海量历史录音 |
| **ccMixter** | 混音作品 | ✅ REST API | CC 授权混音 |
| **Musopen** | 古典音乐 | ✅ REST API | 公有领域古典乐 |
| **Incompetech** | 背景音乐 | ✅ 直接下载 | Kevin MacLeod 作品 |
| **Bensound** | 免费音乐 | ✅ 直接下载 | 适合背景音乐 |

### 🟡 国内平台（需授权）

| 来源 | 类型 | 备注 |
|------|------|------|
| 网易云音乐 | 商业 | 需要会员/版权 |
| QQ 音乐 | 商业 | 需要会员/版权 |
| 酷狗音乐 | 商业 | 需要会员/版权 |

---

## 3. 目录结构设计

```
~/Music/
├── library/                    # 曲库根目录
│   ├── jamendo/               # 按来源分类
│   │   ├── pop/
│   │   │   ├── track_id.mp3
│   │   │   └── track_id.lrc   # 歌词文件
│   │   ├── electronic/
│   │   └── classical/
│   ├── fma/                   # Free Music Archive
│   ├── archive_org/           # Internet Archive
│   └── local/                 # 本地导入
│
├── metadata/                   # 元数据存储
│   ├── library.db             # SQLite 数据库
│   └── covers/                # 专辑封面缓存
│       ├── hash_abc123.jpg
│       └── hash_def456.png
│
└── playlists/                  # 播放列表
    ├── favorites.m3u
    └── recent.json
```

---

## 4. 数据库设计

```sql
-- 曲库主表
CREATE TABLE tracks (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    title TEXT,
    artist TEXT,
    album TEXT,
    year INTEGER,
    genre TEXT,
    duration REAL,
    bitrate INTEGER,
    sample_rate INTEGER,
    
    -- 来源信息
    source TEXT,           -- 'jamendo', 'fma', 'local', etc.
    source_id TEXT,        -- 来源平台的 ID
    source_url TEXT,       -- 原始 URL
    
    -- 元数据
    cover_path TEXT,       -- 封面图片路径
    lyrics_path TEXT,      -- 歌词文件路径
    
    -- 统计
    play_count INTEGER DEFAULT 0,
    last_played TIMESTAMP,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 索引字段
    title_fts TEXT,        -- 用于全文搜索
    artist_fts TEXT,
    
    -- 哈希（去重）
    file_hash TEXT UNIQUE,
    audio_hash TEXT        -- 音频指纹（可选）
);

-- 专辑表
CREATE TABLE albums (
    id INTEGER PRIMARY KEY,
    name TEXT,
    artist TEXT,
    year INTEGER,
    cover_path TEXT,
    track_count INTEGER,
    total_duration REAL
);

-- 艺术家表
CREATE TABLE artists (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    bio TEXT,
    image_path TEXT,
    track_count INTEGER
);

-- 标签表（多对多）
CREATE TABLE tags (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE
);

CREATE TABLE track_tags (
    track_id INTEGER,
    tag_id INTEGER,
    PRIMARY KEY (track_id, tag_id)
);

-- 下载队列表
CREATE TABLE download_queue (
    id INTEGER PRIMARY KEY,
    source TEXT,
    source_id TEXT,
    url TEXT,
    status TEXT DEFAULT 'pending',  -- pending, downloading, completed, failed
    progress INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 全文搜索索引
CREATE VIRTUAL TABLE tracks_fts USING fts5(
    title, artist, album, genre,
    content='tracks',
    content_rowid='id'
);
```

---

## 5. 模块设计

### 5.1 爬虫模块

```python
# cmp/library/crawlers/base.py
from abc import ABC, abstractmethod
from typing import AsyncIterator
from dataclasses import dataclass

@dataclass
class TrackInfo:
    """爬取到的曲目信息"""
    title: str
    artist: str
    album: str = None
    duration: float = None
    source: str = None
    source_id: str = None
    stream_url: str = None
    download_url: str = None
    cover_url: str = None
    tags: list[str] = None
    license: str = None  # CC 授权类型

class BaseCrawler(ABC):
    """爬虫基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """爬虫名称"""
        pass
    
    @abstractmethod
    async def search(self, query: str, limit: int = 20) -> list[TrackInfo]:
        """搜索曲目"""
        pass
    
    @abstractmethod
    async def get_track(self, track_id: str) -> TrackInfo:
        """获取单曲信息"""
        pass
    
    @abstractmethod
    async def download(self, track: TrackInfo, dest_path: str) -> str:
        """下载曲目"""
        pass
    
    async def crawl_genre(self, genre: str, limit: int = 100) -> AsyncIterator[TrackInfo]:
        """按分类爬取"""
        pass
```

```python
# cmp/library/crawlers/jamendo.py
import aiohttp
from .base import BaseCrawler, TrackInfo

class JamendoCrawler(BaseCrawler):
    """Jamendo 爬虫 - 免费音乐平台"""
    
    name = "jamendo"
    BASE_URL = "https://api.jamendo.com/v3.0"
    
    def __init__(self, client_id: str):
        self.client_id = client_id
    
    async def search(self, query: str, limit: int = 20) -> list[TrackInfo]:
        async with aiohttp.ClientSession() as session:
            url = f"{self.BASE_URL}/tracks"
            params = {
                "client_id": self.client_id,
                "format": "json",
                "limit": limit,
                "namesearch": query,
                "include": "musicinfo"
            }
            async with session.get(url, params=params) as resp:
                data = await resp.json()
                return [self._parse_track(t) for t in data.get("results", [])]
    
    async def download(self, track: TrackInfo, dest_path: str) -> str:
        # Jamendo 提供免费下载
        async with aiohttp.ClientSession() as session:
            async with session.get(track.download_url) as resp:
                with open(dest_path, "wb") as f:
                    f.write(await resp.read())
        return dest_path
```

### 5.2 曲库管理器

```python
# cmp/library/manager.py
import sqlite3
import hashlib
from pathlib import Path
from typing import Optional
from datetime import datetime

class LibraryManager:
    """曲库管理器"""
    
    def __init__(self, library_path: str = "~/Music/library"):
        self.library_path = Path(library_path).expanduser()
        self.db_path = self.library_path / "metadata" / "library.db"
        self._init_db()
    
    def add_track(self, 
                  file_path: str,
                  source: str = "local",
                  source_id: str = None,
                  source_url: str = None) -> int:
        """添加曲目到曲库"""
        # 1. 计算文件哈希（去重）
        file_hash = self._compute_hash(file_path)
        
        # 2. 提取元数据
        metadata = self._extract_metadata(file_path)
        
        # 3. 插入数据库
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT OR IGNORE INTO tracks 
                (path, title, artist, album, duration, source, source_id, 
                 source_url, file_hash, date_added)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                file_path, metadata.title, metadata.artist, metadata.album,
                metadata.duration, source, source_id, source_url, file_hash,
                datetime.now()
            ))
            return cursor.lastrowid
    
    def search(self, query: str, limit: int = 50) -> list[dict]:
        """全文搜索"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM tracks 
                WHERE tracks_fts MATCH ?
                ORDER BY play_count DESC
                LIMIT ?
            """, (query, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_by_artist(self, artist: str) -> list[dict]:
        """按艺术家获取"""
        pass
    
    def get_by_album(self, album: str) -> list[dict]:
        """按专辑获取"""
        pass
    
    def get_random(self, count: int = 10, genre: str = None) -> list[dict]:
        """随机获取"""
        pass
    
    def update_play_stats(self, track_id: int):
        """更新播放统计"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE tracks 
                SET play_count = play_count + 1,
                    last_played = ?
                WHERE id = ?
            """, (datetime.now(), track_id))
    
    def cleanup_missing(self):
        """清理不存在的文件"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                DELETE FROM tracks 
                WHERE path NOT IN (
                    SELECT path FROM tracks 
                    WHERE file_hash IS NOT NULL
                )
            """)
```

### 5.3 下载管理器

```python
# cmp/library/downloader.py
import asyncio
from pathlib import Path
from typing import Optional
from datetime import datetime

class DownloadManager:
    """下载管理器"""
    
    def __init__(self, library: LibraryManager):
        self.library = library
        self.queue = asyncio.Queue()
        self.active_downloads = {}
    
    async def add_to_queue(self, 
                           crawler: BaseCrawler,
                           track: TrackInfo,
                           genre: str = None) -> int:
        """添加到下载队列"""
        # 记录到数据库
        with sqlite3.connect(self.library.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO download_queue 
                (source, source_id, url, status)
                VALUES (?, ?, ?, 'pending')
            """, (crawler.name, track.source_id, track.download_url))
            queue_id = cursor.lastrowid
        
        # 加入异步队列
        await self.queue.put((queue_id, crawler, track, genre))
        return queue_id
    
    async def start_worker(self, workers: int = 3):
        """启动下载工作线程"""
        tasks = [
            asyncio.create_task(self._download_worker(i))
            for i in range(workers)
        ]
        await asyncio.gather(*tasks)
    
    async def _download_worker(self, worker_id: int):
        """下载工作线程"""
        while True:
            queue_id, crawler, track, genre = await self.queue.get()
            
            try:
                # 更新状态
                self._update_status(queue_id, "downloading")
                
                # 确定保存路径
                dest_dir = self.library.library_path / crawler.name / (genre or "unknown")
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_path = dest_dir / f"{track.source_id}.mp3"
                
                # 下载
                await crawler.download(track, str(dest_path))
                
                # 添加到曲库
                self.library.add_track(
                    str(dest_path),
                    source=crawler.name,
                    source_id=track.source_id,
                    source_url=track.download_url
                )
                
                self._update_status(queue_id, "completed")
                
            except Exception as e:
                self._update_status(queue_id, "failed", str(e))
    
    def get_queue_status(self) -> list[dict]:
        """获取队列状态"""
        with sqlite3.connect(self.library.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM download_queue 
                WHERE status IN ('pending', 'downloading')
                ORDER BY created_at
            """)
            return [dict(row) for row in cursor.fetchall()]
```

---

## 6. CLI 命令设计

```bash
# 曲库管理命令
music library scan              # 扫描本地曲库
music library stats             # 显示统计信息
music library cleanup           # 清理无效条目

# 搜索和下载
music library search "jazz"     # 搜索曲库
music library crawl jamendo --genre jazz --limit 50   # 从 Jamendo 爬取
music library download <track_id>  # 下载指定曲目

# 队列管理
music library queue             # 查看下载队列
music library queue clear       # 清空队列

# 播放集成
music play --from-library "jazz"  # 从曲库播放
music play --random --genre pop   # 随机播放
```

---

## 7. 与播放器集成

```python
# cmp/library/integration.py
class PlayerIntegration:
    """与 CLI Music Player 集成"""
    
    def __init__(self, library: LibraryManager, player_api: str = "http://localhost:8080"):
        self.library = library
        self.player_api = player_api
    
    async def play_from_library(self, query: str):
        """从曲库搜索并播放"""
        tracks = self.library.search(query)
        if tracks:
            # 添加到播放器播放列表
            paths = [t["path"] for t in tracks]
            async with aiohttp.ClientSession() as session:
                await session.post(
                    f"{self.player_api}/api/playlist/add",
                    json={"paths": paths}
                )
                await session.post(f"{self.player_api}/api/play")
    
    async def play_random(self, genre: str = None, count: int = 10):
        """随机播放"""
        tracks = self.library.get_random(count, genre)
        # ... 同上
```

---

## 8. 配置文件

```yaml
# ~/.config/cmp/library.yaml
library:
  path: ~/Music/library
  
  # 存储设置
  max_storage_gb: 100
  auto_cleanup: true
  cleanup_days: 365  # 超过一年未播放的自动清理

crawlers:
  jamendo:
    enabled: true
    client_id: "${JAMENDO_CLIENT_ID}"
    
  fma:
    enabled: true
    api_key: "${FMA_API_KEY}"
    
  archive_org:
    enabled: true

download:
  workers: 3
  rate_limit_mb: 5  # 限速
  formats: ["mp3", "flac"]
  min_bitrate: 128
  
scheduler:
  # 定时爬取
  - source: jamendo
    genre: jazz
    limit: 20
    schedule: "0 2 * * 0"  # 每周日凌晨2点
```

---

## 9. 实现优先级

### Phase 1: 基础架构 (v0.2.0)
- [ ] 数据库设计和初始化
- [ ] LibraryManager 核心功能
- [ ] 本地文件扫描和导入
- [ ] 基础搜索功能

### Phase 2: 爬虫集成 (v0.2.1)
- [ ] Jamendo 爬虫
- [ ] Free Music Archive 爬虫
- [ ] 下载队列管理
- [ ] 进度显示

### Phase 3: 高级功能 (v0.2.2)
- [ ] 播放器集成
- [ ] 智能推荐
- [ ] 自动爬取调度
- [ ] Web UI 管理
