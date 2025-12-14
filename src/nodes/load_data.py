import json
from pathlib import Path
from ..state import CoverageState

def load_data(state: CoverageState) -> CoverageState:
    return {
        **state,
        "requirements": json.loads(Path("data/requirements.json").read_text(encoding="utf-8")),
        "testcases": json.loads(Path("data/testcases.json").read_text(encoding="utf-8")),
        "req_tc_mapping": json.loads(Path("data/req_tc_mapping.json").read_text(encoding="utf-8")),
    }
