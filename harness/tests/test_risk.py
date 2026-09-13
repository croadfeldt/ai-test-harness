from harness import risk


def base(**kw):
    d = dict(depth=1, change="bumped", reachable="true", vuln_count=0, high_severity=False, breaking_changes=0,
             changed_symbols=0, lines_changed=0, sensitive=[], preflight_hit=False, new_package=False)
    d.update(kw)
    return risk.score(**d)


def test_depth1_bump_is_full_by_policy():
    assert base().budget["level"] == "full"


def test_transitive_unreachable_low_score_is_snapshot():
    r = base(depth=3, change="bumped", reachable="false")
    assert r.budget["level"] == "snapshot" and r.score < 60


def test_transitive_reachable_is_full():
    assert base(depth=3, reachable="true").budget["level"] == "full"


def test_vulnerability_forces_cve_tests_at_any_depth():
    r = base(depth=4, reachable="false", vuln_count=2, high_severity=True)
    assert r.budget["cve_targeted"] is True


def test_preflight_hit_is_max_and_snapshot_only():
    r = base(preflight_hit=True)
    assert r.score == 100 and r.budget["level"] == "snapshot"


def test_sensitivity_terms():
    assert "authentication" in risk.sensitivity("python-jose", "JOSE implementation", "jwt", [])
    assert risk.sensitivity("six", "Python 2 and 3 compatibility", "", []) == []
