from dataclasses import dataclass

@dataclass
class Settings:
    resolution: tuple = (800, 600)
    target_fps: int = 60

def get_settings():
    return Settings()