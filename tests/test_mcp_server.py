"""Tests for MCP Server."""
import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from cmp.mcp_server import MusicPlayerMCPServer, create_mcp_server
from cmp.player.engine import AudioEngine, PlaybackState
from cmp.player.playlist import Playlist, RepeatMode
from cmp.state import PlayerState


@pytest.fixture
def audio_engine():
    """Create a mock audio engine."""
    engine = Mock(spec=AudioEngine)
    engine.state = PlaybackState.IDLE
    engine.volume = 0.7
    engine.position = 0.0
    engine.duration = 180.0
    engine.muted = False
    engine.current_track = None
    
    engine.play = Mock()
    engine.pause = Mock()
    engine.stop = Mock()
    engine.load = Mock(return_value=True)
    engine.seek = Mock()
    
    return engine


@pytest.fixture
def playlist():
    """Create a playlist instance."""
    return Playlist(name="Test Playlist")


@pytest.fixture
def mcp_server(audio_engine, playlist):
    """Create an MCP server instance."""
    return MusicPlayerMCPServer(
        audio_engine=audio_engine,
        playlist=playlist,
    )


class TestMusicPlayerMCPServer:
    """Tests for MusicPlayerMCPServer."""
    
    def test_create_server(self, mcp_server):
        """Test server creation."""
        assert mcp_server is not None
        assert mcp_server.audio_engine is not None
        assert mcp_server.playlist is not None
    
    def test_create_mcp_server_factory(self):
        """Test create_mcp_server factory function."""
        server = create_mcp_server()
        assert server is not None
        assert isinstance(server, MusicPlayerMCPServer)
    
    @pytest.mark.asyncio
    async def test_tool_play(self, mcp_server, audio_engine):
        """Test play tool."""
        result = await mcp_server._tool_play(None)
        assert "No track to play" in result
    
    @pytest.mark.asyncio
    async def test_tool_play_with_track(self, mcp_server, audio_engine, tmp_path):
        """Test play tool with specific track."""
        # Create a mock audio file
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio data")
        
        with patch('cmp.mcp_server.server.extract_metadata') as mock_metadata:
            from cmp.player.engine import Track
            mock_metadata.return_value = Track(
                path=audio_file,
                title="Test Song",
                artist="Test Artist",
            )
            
            result = await mcp_server._tool_play(str(audio_file))
            assert "Playing" in result
    
    @pytest.mark.asyncio
    async def test_tool_pause(self, mcp_server, audio_engine):
        """Test pause tool."""
        audio_engine.state = PlaybackState.PLAYING
        
        result = await mcp_server._tool_pause()
        assert "paused" in result.lower()
        audio_engine.pause.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tool_stop(self, mcp_server, audio_engine):
        """Test stop tool."""
        result = await mcp_server._tool_stop()
        assert "stopped" in result.lower()
        audio_engine.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tool_set_volume(self, mcp_server, audio_engine):
        """Test set_volume tool."""
        result = await mcp_server._tool_set_volume(80)
        assert "80" in result
        assert audio_engine.volume == 0.8
    
    @pytest.mark.asyncio
    async def test_tool_seek(self, mcp_server, audio_engine):
        """Test seek tool."""
        result = await mcp_server._tool_seek(60.0)
        assert "60" in result
        audio_engine.seek.assert_called_once_with(60.0)
    
    @pytest.mark.asyncio
    async def test_tool_add_to_playlist(self, mcp_server, playlist, tmp_path):
        """Test add_to_playlist tool."""
        # Create mock audio files
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio data")
        
        with patch.object(playlist, 'add_file', return_value=1):
            result = await mcp_server._tool_add_to_playlist([str(audio_file)], False)
            assert "Added" in result
    
    @pytest.mark.asyncio
    async def test_tool_clear_playlist(self, mcp_server, playlist):
        """Test clear_playlist tool."""
        result = await mcp_server._tool_clear_playlist()
        assert "cleared" in result.lower()
    
    @pytest.mark.asyncio
    async def test_tool_set_shuffle(self, mcp_server):
        """Test set_shuffle tool."""
        result = await mcp_server._tool_set_shuffle(True)
        assert "enabled" in result.lower()
        assert mcp_server.playlist.shuffle is True
    
    @pytest.mark.asyncio
    async def test_tool_set_repeat(self, mcp_server):
        """Test set_repeat tool."""
        result = await mcp_server._tool_set_repeat("all")
        assert "all" in result.lower()
        assert mcp_server.playlist.repeat == RepeatMode.ALL
    
    def test_get_status_dict(self, mcp_server, audio_engine):
        """Test status dictionary generation."""
        status = mcp_server._get_status_dict()
        
        assert "playback" in status
        assert "playlist" in status
        assert "current_track" in status
        assert status["playback"]["volume"] == 70
    
    def test_get_playlist_dict(self, mcp_server, playlist):
        """Test playlist dictionary generation."""
        playlist_dict = mcp_server._get_playlist_dict()
        
        assert "name" in playlist_dict
        assert "total_tracks" in playlist_dict
        assert "tracks" in playlist_dict
        assert playlist_dict["name"] == "Playlist"
    
    def test_get_current_track_dict(self, mcp_server, audio_engine):
        """Test current track dictionary generation."""
        from cmp.player.engine import Track
        
        track = Track(
            path=Path("/test/song.mp3"),
            title="Test Song",
            artist="Test Artist",
            album="Test Album",
            duration=180.0,
        )
        audio_engine.current_track = track
        
        track_dict = mcp_server._get_current_track_dict()
        
        assert track_dict is not None
        assert track_dict["title"] == "Test Song"
        assert track_dict["artist"] == "Test Artist"
    
    def test_get_current_track_dict_none(self, mcp_server, audio_engine):
        """Test current track dictionary when no track."""
        audio_engine.current_track = None
        
        track_dict = mcp_server._get_current_track_dict()
        
        assert track_dict is None


class TestMCPTools:
    """Tests for MCP tool definitions."""
    
    @pytest.mark.asyncio
    async def test_list_tools(self, mcp_server):
        """Test tool listing."""
        # This would be called by the MCP framework
        # We're just verifying the server has the tools registered
        assert hasattr(mcp_server.server, 'list_tools')
        assert hasattr(mcp_server.server, 'call_tool')
    
    @pytest.mark.asyncio
    async def test_list_resources(self, mcp_server):
        """Test resource listing."""
        assert hasattr(mcp_server.server, 'list_resources')
        assert hasattr(mcp_server.server, 'read_resource')
