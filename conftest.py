import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


collect_ignore_glob = [
    "tests/app_setup/*",
    "tests/my_connections/*",
    "tests/my_modules/*",
]
