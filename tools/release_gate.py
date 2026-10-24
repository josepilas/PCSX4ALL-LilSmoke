# SPDX-License-Identifier: MPL-2.0
"""Fail closed unless source, build and qualification evidence is recorded."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
gate = json.loads((root / 'RELEASE_GATE.json').read_text())
if not gate.get('publication_ready') or not gate.get('self_contained_corresponding_source') or gate.get('blockers'):
    for blocker in gate.get('blockers', []):
        print(blocker['id'] + ': ' + blocker['detail'])
    raise SystemExit(1)
print('Release gate cleared by review; this tool performs no publication.')
