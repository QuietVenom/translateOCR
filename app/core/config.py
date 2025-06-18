from pathlib import Path
import os

class Settings:
    def __init__(self):
        self.FONT_PATH = self._resolve_font_path()
    
    def _resolve_font_path(self) -> Path:
        """Resolve font path with proper validation"""
        raw_path = os.getenv("FONT_PATH", "")
        if not raw_path:
            return None
        
        path = Path(raw_path)
        
        # Handle relative paths
        if not path.is_absolute():
            project_root = Path(__file__).parent.parent.parent
            path = (project_root / path).resolve()
        
        return path if path.exists() else None

settings = Settings()