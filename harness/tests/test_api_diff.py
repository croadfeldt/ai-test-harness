from harness.adapters.python import api_diff, _required_params
from harness.model import ApiSymbol


def sym(q, sig, kind="function"):
    return ApiSymbol(module=q.rsplit(".", 1)[0], qualname=q, kind=kind, signature=sig, doc="", file="m.py", line=1)


def test_required_params_ignore_self_and_defaults():
    assert _required_params("(self, token, key, algorithms=None, *, verify=True)") == ["token", "key"]
    assert _required_params("(a, /, b, *, c, d=1) -> int") == ["a", "b", "c"]


def test_removed_symbol_is_breaking():
    ch = api_diff([sym("m.f", "(a)")], [])
    assert ch[0].kind == "removed" and ch[0].breaking


def test_added_optional_param_is_not_breaking():
    ch = api_diff([sym("m.f", "(a)")], [sym("m.f", "(a, b=None)")])
    assert ch[0].kind == "changed" and not ch[0].breaking


def test_new_required_param_is_breaking():
    ch = api_diff([sym("m.f", "(a)")], [sym("m.f", "(a, b)")])
    assert ch[0].breaking and "required parameters changed" in ch[0].reason


def test_unchanged_and_added():
    ch = api_diff([sym("m.f", "(a)")], [sym("m.f", "(a)"), sym("m.g", "()")])
    assert [c.kind for c in ch] == ["added"] and not ch[0].breaking
