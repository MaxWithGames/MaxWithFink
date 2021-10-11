from dataclasses import dataclass, fields

@dataclass
class Settings:
    resolution_x: int = 800
    resolution_y: int = 600
    target_fps: int = 60
    server_addres: str = 'localhost'
    server_port: int = 1236
    name: str = 'noname'
    show_debug: bool = False  

def get_settings():
    def str_to_type(s, t):
        if t is bool:
            if s == 'True':
                return True
            else:
                return False
        return t(s)

    settings_file = open('settings.cfg', 'r')
    settings_lines = settings_file.readlines()

    settings_keys = [field.name for field in fields(Settings)]
    settings_types = dict((field.name, field.type) for field in fields(Settings))

    settings_updates = {}

    for line in settings_lines:
        key = line.split('=')[0]
        if not key in settings_keys:
            raise KeyError(f'{key} is not in settings')
        settings_updates[key] = str_to_type(line.split('=')[1].split('\n')[0], settings_types[key])

    return Settings(**settings_updates)