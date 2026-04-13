from app.utils.ttl_response_cache import (
    get_cached_report_detail,
    set_cached_report_detail,
)


def test_report_detail_cache_roundtrip() -> None:
    class _Dummy:
        value = 1

    d = _Dummy()
    set_cached_report_detail("u1", "r1", d)
    assert get_cached_report_detail("u1", "r1") is d
    assert get_cached_report_detail("u1", "r2") is None
