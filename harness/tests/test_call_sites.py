from pathlib import Path

from harness.adapters.python import call_sites, imports_root


def write(tmp: Path, rel: str, text: str):
    p = tmp / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def test_call_sites_resolve_aliases_and_flag_tests(tmp_path: Path):
    write(tmp_path, "app/auth.py", "from jose import jwt, JWTError\n\ndef check(t):\n    return jwt.decode(t, 'k', algorithms=['HS256'])\n")
    write(tmp_path, "tests/test_auth.py", "import jose\njose.jwt.encode({}, 'k')\n")
    write(tmp_path, "venv/lib/site-packages/x.py", "import jose\n")
    sites = call_sites(tmp_path, ["jose"])
    prod = [s for s in sites if not s.in_test]
    assert any(s.symbol == "jose.jwt.decode" and s.file == "app/auth.py" and s.line == 4 for s in prod)
    assert all(not s.file.startswith("venv") for s in sites)
    assert any(s.in_test and s.symbol == "jose.jwt.encode" for s in sites)


def test_imports_root_probe(tmp_path: Path):
    write(tmp_path, "app/main.py", "import fastapi\nfrom multipart import parse\n")
    assert imports_root(tmp_path, ["fastapi", "multipart", "PIL"]) == ["fastapi", "multipart"]
