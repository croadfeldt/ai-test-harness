"""GF-023: the agent may submit only a file the sandbox ran, and that collected on every version."""
import json

from harness.stages.agent import Tools, run_agent


class FakeModel:
    """Scripted turns: run a bad file, submit it (refused), submit a never-run file (refused), run a good file, submit it."""
    class cfg:
        label = "fake"

    def __init__(self):
        self.turns = [
            [("run_tests", {"code": "BAD"})],
            [("submit", {"code": "BAD", "note": "n"})],
            [("submit", {"code": "NEVER", "note": "n"})],
            [("run_tests", {"code": "GOOD"})],
            [("submit", {"code": "GOOD", "note": "n"})],
        ]
        self.i = 0

    def chat_tools(self, messages, tools, tag, max_tokens=0):
        calls = [{"id": f"c{self.i}{j}", "type": "function", "function": {"name": n, "arguments": json.dumps(a)}} for j, (n, a) in enumerate(self.turns[self.i])]
        self.i += 1
        return {"content": "", "tool_calls": calls}, {"finish_reason": "tool_calls"}


class Adapter:
    SYSTEM = "sys"

    @staticmethod
    def extract_code(text):
        return None


def test_submit_needs_a_run_that_collected_on_every_version():
    results = {"BAD": "[new 2 = FIXED] TestA=error (did not compile: ./candidate_test.go:3:1: undefined: y)", "GOOD": "[new 2 = FIXED] test_a=pass\n[old 1 = VULNERABLE] test_a=fail (boom)"}
    tools = Tools({}, {"symbols": []}, {"symbols": []}, lambda code: results[code], adapter=Adapter())
    res = run_agent(FakeModel(), "prompt", tools, gate_fn=lambda code: [], max_tool_calls=14, max_turns=8, tag="t")
    subs = [t for t in res["trace"] if t.get("tool") == "submit"]
    assert [s["ok"] for s in subs] == [False, False, True]
    assert "did not compile or collect" in subs[0]["problems"][0]
    assert "has not been run" in subs[1]["problems"][0]
    assert res["submitted"]["code"] == "GOOD"
