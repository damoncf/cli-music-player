"""Audio playback engine."""
import threading
import queue
import numpy as np
import soundfile as sf
import pyaudio
from pathlib import Path
from typing import Callable, Optional, List
from dataclasses import dataclass
from enum import Enum, auto
import time


class PlaybackState(Enum):
    """Playback states."""
    IDLE = auto()
    PLAYING = auto()
    PAUSED = auto()
    STOPPED = auto()


@dataclass
class Track:
    """Represents an audio track."""
    path: Path
    title: str = ""
    artist: str = ""
    album: str = ""
    duration: float = 0.0
    sample_rate: int = 44100
    channels: int = 2
    
    def __post_init__(self):
        if not self.title:
            self.title = self.path.stem


class AudioEngine:
    """Audio playback engine using PyAudio."""
    
    CHUNK_SIZE = 1024
    BUFFER_SIZE = 4
    
    def __init__(self):
        self._state = PlaybackState.IDLE
        self._current_track: Optional[Track] = None
        self._position = 0.0
        self._volume = 0.7
        self._muted = False
        
        self._audio: Optional[pyaudio.PyAudio] = None
        self._stream: Optional[pyaudio.Stream] = None
        self._sound_file: Optional[sf.SoundFile] = None
        
        self._buffer = queue.Queue(maxsize=self.BUFFER_SIZE)
        self._decoder_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        self._callbacks: List[Callable] = []
        self._position_callbacks: List[Callable] = []
        
        self._lock = threading.Lock()
    
    def initialize(self):
        """Initialize audio system."""
        if self._audio is None:
            self._audio = pyaudio.PyAudio()
    
    def shutdown(self):
        """Shutdown audio system."""
        self.stop()
        if self._audio:
            self._audio.terminate()
            self._audio = None
    
    def register_callback(self, callback: Callable[[np.ndarray], None]):
        """Register audio data callback for visualizer."""
        self._callbacks.append(callback)
    
    def unregister_callback(self, callback: Callable[[np.ndarray], None]):
        """Unregister audio data callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def register_position_callback(self, callback: Callable[[float, float], None]):
        """Register position update callback."""
        self._position_callbacks.append(callback)
    
    @property
    def state(self) -> PlaybackState:
        """Get current playback state."""
        return self._state
    
    @property
    def current_track(self) -> Optional[Track]:
        """Get current track."""
        return self._current_track
    
    @property
    def position(self) -> float:
        """Get current position in seconds."""
        return self._position
    
    @property
    def duration(self) -> float:
        """Get current track duration."""
        if self._sound_file:
            return len(self._sound_file) / self._sound_file.samplerate
        return 0.0
    
    @property
    def volume(self) -> float:
        """Get volume (0.0 - 1.0)."""
        return self._volume
    
    @volume.setter
    def volume(self, value: float):
        """Set volume (0.0 - 1.0)."""
        self._volume = max(0.0, min(1.0, value))
    
    @property
    def muted(self) -> bool:
        """Get mute state."""
        return self._muted
    
    def toggle_mute(self):
        """Toggle mute state."""
        self._muted = not self._muted
    
    def load(self, track: Track) -> bool:
        """Load a track."""
        self.stop()
        
        try:
            self._sound_file = sf.SoundFile(str(track.path))
            track.sample_rate = self._sound_file.samplerate
            track.channels = self._sound_file.channels
            track.duration = len(self._sound_file) / track.sample_rate
            self._current_track = track
            self._position = 0.0
            return True
        except Exception as e:
            print(f"Error loading track: {e}")
            return False
    
    def play(self):
        """Start or resume playback."""
        if self._state == PlaybackState.PLAYING:
            return
        
        if self._state == PlaybackState.PAUSED:
            self._state = PlaybackState.PLAYING
            return
        
        if not self._sound_file:
            return
        
        self.initialize()
        self._state = PlaybackState.PLAYING
        self._stop_event.clear()
        
        # Start decoder thread
        self._decoder_thread = threading.Thread(target=self._decoder_loop)
        self._decoder_thread.daemon = True
        self._decoder_thread.start()
        
        # Open audio stream
        self._stream = self._audio.open(
            format=pyaudio.paFloat32,
            channels=self._sound_file.channels,
            rate=self._sound_file.samplerate,
            output=True,
            frames_per_buffer=self.CHUNK_SIZE,
            stream_callback=self._audio_callback
        )
        
        self._stream.start_stream()
    
    def pause(self):
        """Pause playback."""
        if self._state == PlaybackState.PLAYING:
            self._state = PlaybackState.PAUSED
    
    def stop(self):
        """Stop playback."""
        self._state = PlaybackState.STOPPED
        self._stop_event.set()
        
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None
        
        if self._decoder_thread:
            self._decoder_thread.join(timeout=1.0)
            self._decoder_thread = None
        
        # Clear buffer
        while not self._buffer.empty():
            try:
                self._buffer.get_nowait()
            except queue.Empty:
                break
        
        self._position = 0.0
        if self._sound_file:
            self._sound_file.seek(0)
    
    def seek(self, position: float):
        """Seek to position in seconds."""
        if not self._sound_file:
            return
        
        sample_position = int(position * self._sound_file.samplerate)
        sample_position = max(0, min(sample_position, len(self._sound_file)))
        self._sound_file.seek(sample_position)
        self._position = position
    
    def _decoder_loop(self):
        """Decoder thread loop."""
        while not self._stop_event.is_set():
            if self._state != PlaybackState.PLAYING:
                time.sleep(0.01)
                continue
            
            try:
                # Read chunk
                data = self._sound_file.read(self.CHUNK_SIZE, dtype='float32')
                
                if len(data) == 0:
                    # End of file
                    self._stop_event.wait(0.1)
                    continue
                
                # Handle mono/stereo
                if data.ndim == 1:
                    data = data.reshape(-1, 1)
                
                # Put in buffer (block if full)
                try:
                    self._buffer.put(data, timeout=0.1)
                except queue.Full:
                    pass
                
                # Update position
                self._position = self._sound_file.tell() / self._sound_file.samplerate
                
                # Notify position callbacks
                for callback in self._position_callbacks:
                    try:
                        callback(self._position, self.duration)
                    except Exception:
                        pass
                        
            except Exception as e:
                print(f"Decoder error: {e}")
                break
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """PyAudio callback."""
        try:
            # Get data from buffer
            if self._state == PlaybackState.PLAYING and not self._buffer.empty():
                data = self._buffer.get_nowait()
                
                # Pad if needed
                if len(data) < frame_count:
                    padding = np.zeros((frame_count - len(data), data.shape[1]), dtype='float32')
                    data = np.vstack([data, padding])
                elif len(data) > frame_count:
                    data = data[:frame_count]
                
                # Apply volume
                effective_volume = 0.0 if self._muted else self._volume
                data = data * effective_volume
                
                # Convert to interleaved for PyAudio
                if data.shape[1] == 2:
                    data = data.reshape(-1)
                else:
                    data = data.flatten()
                
                # Notify callbacks for visualization
                if self._callbacks:
                    # Send a copy for visualization
                    vis_data = data.copy()
                    for callback in self._callbacks:
                        try:
                            callback(vis_data)
                        except Exception:
                            pass
                
                return (data.astype('float32').tobytes(), pyaudio.paContinue)
            else:
                # Return silence
                channels = self._sound_file.channels if self._sound_file else 2
                silence = np.zeros(frame_count * channels, dtype='float32')
                return (silence.tobytes(), pyaudio.paContinue)
                
        except queue.Empty:
            channels = self._sound_file.channels if self._sound_file else 2
            silence = np.zeros(frame_count * channels, dtype='float32')
            return (silence.tobytes(), pyaudio.paContinue)
        except Exception as e:
            print(f"Audio callback error: {e}")
            channels = self._sound_file.channels if self._sound_file else 2
            silence = np.zeros(frame_count * channels, dtype='float32')
            return (silence.tobytes(), pyaudio.paContinue)


# Global audio engine instance
audio_engine = AudioEngine()
