import os
import json
from datetime import datetime

def get_history_file() -> str:
    instance_name = os.getenv("ACTIVE_INSTANCE", "")
    if not instance_name:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "logs", "history.jsonl"))
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "instances", instance_name, "logs", "history.jsonl"))

def get_event_log_file() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "instances", "shared_agora", "agora_event_log.jsonl"))

def append_to_history(entry: dict):
    history_file = get_history_file()
    os.makedirs(os.path.dirname(history_file), exist_ok=True)
    with open(history_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

def log_agora_event(event_type: str, actor: str, details: dict):
    log_file = get_event_log_file()
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "actor": actor,
        "details": details
    }
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')

def load_history() -> list:
    history_file = get_history_file()
    if not os.path.exists(history_file):
        return []
    history = []
    with open(history_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    history.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return history
