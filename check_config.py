import os
import yaml
import json

REQUIRED_KEYS = {
    "obs": ["host", "port", "password_file", "scene_start", "scene_live", "text_source", "stream_start_offset_minutes", "scene_switch_offset_minutes"],
    "telegram": ["credentials_file", "notify_on_start", "notify_on_end"],
    "email": ["credentials_file", "notify"],
    "paths": ["youtube_output_dir", "xml_output_dir", "log_file"],
    "web": ["church_id", "target_offset_days", "keywords"]
}

SECRETS_REQUIRED = {
    "telegram": ["bot_token", "chat_id"],
    "email": ["email", "app_password"],
    "obs": ["password"]
}

def load_yaml(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"❌ config.yaml nicht gefunden unter: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def check_keys(config):
    for section, keys in REQUIRED_KEYS.items():
        if section not in config:
            raise KeyError(f"❌ Abschnitt '{section}' fehlt in config.yaml")
        for key in keys:
            if key not in config[section]:
                raise KeyError(f"❌ config.yaml: '{section}.{key}' fehlt")

def check_secret(path, required_fields):
    if not os.path.exists(path):
        raise FileNotFoundError(f"❌ Secret-Datei nicht gefunden: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for field in required_fields:
        if field not in data:
            raise KeyError(f"❌ Secret '{path}' fehlt Feld: {field}")

def main():
    print("🔍 Prüfe config.yaml und Secrets...")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "config.yaml")
    config = load_yaml(config_path)
    check_keys(config)

    for section, fields in SECRETS_REQUIRED.items():
        file_rel = config[section]["credentials_file"] if section != "obs" else config[section]["password_file"]
        path = os.path.join(base_dir, file_rel)
        check_secret(path, fields)

    print("✅ Konfiguration vollständig und korrekt.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(str(e))
        exit(1)
