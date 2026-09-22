"""GF-026: the advisory a test proves is found by id regardless of the case the model used in the name."""
from harness.stages.packet import _names_advisory


def test_advisory_ids_match_test_names_in_any_case():
    ids = ["PYSEC-2024-232", "CVE-2024-33663", "GHSA-6c5p-j8vq-pqhj"]
    assert _names_advisory("test_GHSA_6c5p_j8vq_pqhj_exposure", ids)
    assert _names_advisory("test_ghsa_6c5p_j8vq_pqhj_fix_pinning", ids)
    assert _names_advisory("test_CVE_2024_33663_fix_pinning", ids)
    assert not _names_advisory("test_cve_2024_29370_fix_pinning", ids)


def test_the_plain_terms_count_uses_the_same_rule():
    import inspect
    from harness.stages import packet
    src = inspect.getsource(packet.packet_package)
    assert "_names_advisory(n, [v[\"id\"], *v.get(\"aliases\", [])])" in src, "the packet's sentence and its VEX must count proofs the same way"
