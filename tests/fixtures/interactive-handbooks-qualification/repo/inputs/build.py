from pathlib import Path
import json
root=Path(__file__).parent
config=json.loads((root/'config.json').read_text())
text=f"Retry limit: {config['retry_limit']}. Queue capacity: {config['queue_capacity']}. Timeout: {config['timeout_seconds']} seconds."
out=root/'docs/handbooks/html/operations.html'
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text('<!doctype html><html><body><h1 id="overview">Queue operations</h1><p>'+text+'</p><h2 id="workflow">Observation to queue to analyst to archive</h2><p>Reliability unavailable.</p></body></html>')
