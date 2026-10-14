"""The site builder renders every run's story on a runner that has only the documentation tools installed,
so the story and the accounting it reads must import without the adapters' dependencies (`packaging`).
The Pages publish broke on main when the accounting pulled the adapters in at import time."""
import subprocess
import sys


def test_story_and_accounting_import_without_the_adapters_dependencies():
    code = ("import sys; sys.modules['packaging'] = None; sys.modules['packaging.markers'] = None\n"
            "import harness.story, harness.stages.account\n"
            "assert 'harness.adapters' not in sys.modules, 'the story must not load the adapters'\n"
            "print('ok')")
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0 and proc.stdout.strip() == "ok", proc.stderr[-800:]
