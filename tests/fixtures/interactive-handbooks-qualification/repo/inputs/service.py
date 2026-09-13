import json
from pathlib import Path
CONFIG = json.loads(Path(__file__).with_name("config.json").read_text())
def attempts():
    return CONFIG["retry_limit"]
def admitted(queue_size):
    return queue_size < CONFIG["queue_capacity"]
