"""Oscilloscope-style waveform visualizer."""
import numpy as np
from typing import List
from .base import BaseVisualizer


class OscilloscopeVisualizer(BaseVisualizer):
    """Retro oscilloscope-style waveform display."""
    
    # Characters for drawing lines at different slopes
    LINE_CHARS = {
        'flat': '─',
        'up': '╱',
        'down': '╲',
        'v': '│',
        'h': '─',
        'cross': '╳',
        'dot': '·',
    }
    
    def __init__(self, smoothing: float = 0.1):
        super().__init__(bar_count=0, smoothing=smoothing)
        self._previous_samples = np.zeros(256)
    
    @property
    def name(self) -> str:
        return "oscilloscope"
    
    def process(self, audio_data: np.ndarray, sample_rate: int = 44100) -> np.ndarray:
        """Process audio data for oscilloscope display."""
        # Convert to mono
        if len(audio_data.shape) > 1 and audio_data.shape[1] == 2:
            audio_data = audio_data.mean(axis=1)
        
        # Resample to fixed size for consistent display
        target_size = 128
        if len(audio_data) > target_size:
            # Downsample by taking every Nth sample
            step = len(audio_data) // target_size
            audio_data = audio_data[::step][:target_size]
        elif len(audio_data) < target_size:
            # Pad with zeros
            audio_data = np.pad(audio_data, (0, target_size - len(audio_data)))
        
        # Apply light smoothing for stability
        audio_data = self.smoothing * self._previous_samples[:target_size] + \
                     (1 - self.smoothing) * audio_data
        self._previous_samples = np.pad(audio_data, (0, len(self._previous_samples) - target_size))
        
        return audio_data
    
    def render(self, data: np.ndarray, width: int, height: int) -> List[str]:
        """Render oscilloscope-style waveform."""
        if len(data) == 0:
            return [" " * width] * height
        
        # Create canvas
        canvas = [[" " for _ in range(width)] for _ in range(height)]
        
        # Center line
        center_y = height // 2
        for x in range(width):
            canvas[center_y][x] = "·"
        
        # Resample data to fit width
        if len(data) != width:
            indices = np.linspace(0, len(data) - 1, width, dtype=int)
            data = data[indices]
        
        # Draw waveform
        prev_y = None
        for x, value in enumerate(data):
            if x >= width:
                break
            
            # Map value (-1 to 1) to y coordinate
            # Invert because screen coordinates go down
            y = int((1 - value) * (height - 1) / 2)
            y = max(0, min(height - 1, y))
            
            # Draw point or line
            if prev_y is not None:
                # Draw line from prev_y to y
                if y == prev_y:
                    canvas[y][x] = self.LINE_CHARS['flat']
                elif y < prev_y:
                    # Going up
                    for py in range(y, prev_y + 1):
                        if py == y:
                            canvas[py][x] = self.LINE_CHARS['up']
                        elif py == prev_y:
                            canvas[py][x - 1] = self.LINE_CHARS['down']
                        else:
                            canvas[py][x] = self.LINE_CHARS['v']
                else:
                    # Going down
                    for py in range(prev_y, y + 1):
                        if py == prev_y:
                            canvas[py][x - 1] = self.LINE_CHARS['up']
                        elif py == y:
                            canvas[py][x] = self.LINE_CHARS['down']
                        else:
                            canvas[py][x] = self.LINE_CHARS['v']
            else:
                # First point
                canvas[y][x] = self.LINE_CHARS['dot']
            
            prev_y = y
        
        # Convert canvas to strings
        lines = []
        for row in canvas:
            lines.append("".join(row))
        
        return lines


class DualOscilloscopeVisualizer(BaseVisualizer):
    """Dual-channel oscilloscope for stereo audio."""
    
    def __init__(self, smoothing: float = 0.1):
        super().__init__(bar_count=0, smoothing=smoothing)
        self._prev_left = np.zeros(128)
        self._prev_right = np.zeros(128)
    
    @property
    def name(self) -> str:
        return "oscilloscope_dual"
    
    def process(self, audio_data: np.ndarray, sample_rate: int = 44100) -> np.ndarray:
        """Process stereo audio data."""
        target_size = 64
        
        if len(audio_data.shape) > 1 and audio_data.shape[1] == 2:
            left = audio_data[:, 0]
            right = audio_data[:, 1]
        else:
            left = audio_data
            right = audio_data
        
        # Resample both channels
        if len(left) > target_size:
            step = len(left) // target_size
            left = left[::step][:target_size]
        elif len(left) < target_size:
            left = np.pad(left, (0, target_size - len(left)))
        
        if len(right) > target_size:
            step = len(right) // target_size
            right = right[::step][:target_size]
        elif len(right) < target_size:
            right = np.pad(right, (0, target_size - len(right)))
        
        # Smooth
        left = self.smoothing * self._prev_left + (1 - self.smoothing) * left
        right = self.smoothing * self._prev_right + (1 - self.smoothing) * right
        
        self._prev_left = left.copy()
        self._prev_right = right.copy()
        
        # Interleave: L0, R0, L1, R1, ...
        result = np.zeros(target_size * 2)
        result[0::2] = left
        result[1::2] = right
        
        return result
    
    def render(self, data: np.ndarray, width: int, height: int) -> List[str]:
        """Render dual oscilloscope."""
        if len(data) == 0:
            return [" " * width] * height
        
        # Split data
        left = data[0::2]
        right = data[1::2]
        
        canvas = [[" " for _ in range(width)] for _ in range(height)]
        
        # Split height for two channels
        left_height = height // 2
        right_height = height - left_height
        
        left_center = left_height // 2
        right_center = left_height + right_height // 2
        
        # Draw center lines
        for x in range(width):
            canvas[left_center][x] = "·"
            canvas[right_center][x] = "·"
        
        # Draw left channel (top half)
        self._draw_channel(canvas, left, width, left_center, 0, left_height, "╱", "╲")
        
        # Draw right channel (bottom half)
        self._draw_channel(canvas, right, width, right_center, left_height, height, "╱", "╲")
        
        lines = ["".join(row) for row in canvas]
        return lines
    
    def _draw_channel(self, canvas, data, width, center_y, y_min, y_max, up_char, down_char):
        """Draw a single channel on the canvas."""
        if len(data) != width:
            indices = np.linspace(0, len(data) - 1, width, dtype=int)
            data = data[indices]
        
        prev_y = None
        for x, value in enumerate(data):
            if x >= width:
                break
            
            # Map value to y coordinate within channel bounds
            available_height = min(center_y - y_min, y_max - center_y - 1)
            y = int(center_y - value * available_height)
            y = max(y_min, min(y_max - 1, y))
            
            if prev_y is not None:
                if y == prev_y:
                    canvas[y][x] = "─"
                elif y < prev_y:
                    canvas[y][x] = up_char
                else:
                    canvas[y][x] = down_char
            else:
                canvas[y][x] = "●"
            
            prev_y = y


class VectorScopeVisualizer(BaseVisualizer):
    """Vector scope - Lissajous-style stereo phase display."""
    
    def __init__(self, smoothing: float = 0.2):
        super().__init__(bar_count=0, smoothing=smoothing)
        self._prev_x = 0
        self._prev_y = 0
    
    @property
    def name(self) -> str:
        return "vectorscope"
    
    def process(self, audio_data: np.ndarray, sample_rate: int = 44100) -> np.ndarray:
        """Process stereo data into X,Y pairs."""
        if len(audio_data.shape) > 1 and audio_data.shape[1] == 2:
            left = audio_data[:, 0]
            right = audio_data[:, 1]
        else:
            # Mono - create a fake stereo image
            left = audio_data
            right = np.zeros_like(audio_data)
        
        # Take a subset of samples for display
        target_size = 64
        if len(left) > target_size:
            step = len(left) // target_size
            left = left[::step][:target_size]
            right = right[::step][:target_size]
        
        # Interleave as X(left), Y(right) pairs
        result = np.zeros(target_size * 2)
        result[0::2] = left
        result[1::2] = right
        
        return result
    
    def render(self, data: np.ndarray, width: int, height: int) -> List[str]:
        """Render vector scope as Lissajous figure."""
        if len(data) == 0:
            return [" " * width] * height
        
        # Split into X (left) and Y (right)
        x_data = data[0::2]
        y_data = data[1::2]
        
        canvas = [[" " for _ in range(width)] for _ in range(height)]
        
        cx = width // 2
        cy = height // 2
        
        # Scale factors
        scale_x = min(cx, 10) - 1
        scale_y = min(cy, 5) - 1
        
        # Draw axes
        for x in range(width):
            canvas[cy][x] = "·"
        for y in range(height):
            canvas[y][cx] = "·"
        
        # Draw points
        chars = ["·", "∘", "○", "●"]
        
        for i in range(len(x_data)):
            x = int(cx + x_data[i] * scale_x)
            y = int(cy - y_data[i] * scale_y)  # Invert Y for screen coords
            
            if 0 <= x < width and 0 <= y < height:
                # Use different chars based on recency
                char_idx = min(i // (len(x_data) // len(chars) + 1), len(chars) - 1)
                # Only draw if space or lower intensity
                if canvas[y][x] == " " or canvas[y][x] == "·":
                    canvas[y][x] = chars[char_idx]
        
        lines = ["".join(row) for row in canvas]
        return lines
