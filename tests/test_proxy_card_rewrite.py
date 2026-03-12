from typing import cast

from buddy.control_plane.routes.proxy import rewrite_card_payload


def test_rewrite_card_updates_url() -> None:
    card = {"name": "demo", "url": "http://upstream"}
    rewritten = cast(dict[str, object], rewrite_card_payload(card, "http://proxy/a2a/external/demo"))
    assert rewritten["url"] == "http://proxy/a2a/external/demo"


def test_rewrite_card_sets_preferred_transport_when_missing() -> None:
    card = {"name": "demo", "url": "http://upstream"}
    rewritten = cast(dict[str, object], rewrite_card_payload(card, "http://proxy", preferred_transport="JSONRPC"))
    assert rewritten["preferredTransport"] == "JSONRPC"
