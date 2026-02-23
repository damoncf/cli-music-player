"""Audio metadata extraction."""
from pathlib import Path
from mutagen import File as MutagenFile
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.wavpack import WavPack
from mutagen.oggvorbis import OggVorbis
from mutagen.mp4 import MP4

from .engine import Track


def extract_metadata(path: Path) -> Track:
    """Extract metadata from audio file."""
    path = Path(path)
    
    # Default values
    title = path.stem
    artist = ""
    album = ""
    duration = 0.0
    
    try:
        audio = MutagenFile(str(path))
        
        if audio is None:
            return Track(path=path, title=title, artist=artist, album=album, duration=duration)
        
        # Get duration
        if hasattr(audio, 'info') and hasattr(audio.info, 'length'):
            duration = audio.info.length
        
        # Extract tags based on file type
        if isinstance(audio, MP3):
            title = audio.get('TIT2', [title])[0]
            artist = audio.get('TPE1', [artist])[0]
            album = audio.get('TALB', [album])[0]
        
        elif isinstance(audio, FLAC):
            title = audio.get('title', [title])[0]
            artist = audio.get('artist', [artist])[0]
            album = audio.get('album', [album])[0]
        
        elif isinstance(audio, OggVorbis):
            title = audio.get('title', [title])[0]
            artist = audio.get('artist', [artist])[0]
            album = audio.get('album', [album])[0]
        
        elif isinstance(audio, MP4):
            title = audio.get('\xa9nam', [title])[0]
            artist = audio.get('\xa9ART', [artist])[0]
            album = audio.get('\xa9alb', [album])[0]
        
        else:
            # Generic fallback
            title = audio.get('title', [title])[0] if 'title' in audio else title
            artist = audio.get('artist', [artist])[0] if 'artist' in audio else artist
            album = audio.get('album', [album])[0] if 'album' in audio else album
    
    except Exception:
        # If extraction fails, return defaults
        pass
    
    return Track(
        path=path,
        title=str(title),
        artist=str(artist),
        album=str(album),
        duration=duration
    )


def format_duration(seconds: float) -> str:
    """Format duration as MM:SS or HH:MM:SS."""
    if seconds < 0:
        return "0:00"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"
