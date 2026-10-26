"""Run with PYTHONPATH=src python scripts/demo_relational.py."""
import json
from datetime import datetime,timezone
from pathlib import Path
from mirror_ai.relational import DevelopmentalExport,InterpretationBundle,interpret_fixture
root=Path(__file__).resolve().parents[1]/'examples/relational'
request=DevelopmentalExport.model_validate_json((root/'developmental_export.json').read_text())
bundle=InterpretationBundle.model_validate_json((root/'plurality_bundle.json').read_text())
reply=interpret_fixture(request,bundle,expected_profile_id='fictional:participant',expected_revision='7',purpose='compare_candidate_interpretations',now=datetime(2026,9,27,tzinfo=timezone.utc),allow_fixture=True)
print(json.dumps(reply.model_dump(mode='json'),indent=2))
