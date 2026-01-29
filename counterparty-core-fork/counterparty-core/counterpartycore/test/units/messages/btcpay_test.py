import binascii
import struct

import pytest
from counterpartycore.lib import config, exceptions
from counterpartycore.lib.messages import btcpay


def test_unpack_valid():
    """Test valid btcpay unpack."""
    tx0_hash = "0000000000000000000000000000000000000000000000000000000000000001"
    tx1_hash = "0000000000000000000000000000000000000000000000000000000000000002"

    tx0_hash_bytes = binascii.unhexlify(tx0_hash)
    tx1_hash_bytes = binascii.unhexlify(tx1_hash)
    message = struct.pack(">32s32s", tx0_hash_bytes, tx1_hash_bytes)

    result = btcpay.unpack(message)
    assert result[0] == tx0_hash
    assert result[1] == tx1_hash
    assert result[2] == f"{tx0_hash}_{tx1_hash}"
    assert result[3] == "valid"


def test_unpack_valid_return_dict():
    """Test valid btcpay unpack with return_dict=True."""
    tx0_hash = "0000000000000000000000000000000000000000000000000000000000000001"
    tx1_hash = "0000000000000000000000000000000000000000000000000000000000000002"

    tx0_hash_bytes = binascii.unhexlify(tx0_hash)
    tx1_hash_bytes = binascii.unhexlify(tx1_hash)
    message = struct.pack(">32s32s", tx0_hash_bytes, tx1_hash_bytes)

    result = btcpay.unpack(message, return_dict=True)
    assert result["tx0_hash"] == tx0_hash
    assert result["tx1_hash"] == tx1_hash
    assert result["order_match_id"] == f"{tx0_hash}_{tx1_hash}"
    assert result["status"] == "valid"


def test_unpack_invalid_length():
    """Test btcpay unpack with invalid message length."""
    # Too short message
    message = b"\x00" * 10

    result = btcpay.unpack(message)
    assert result[0] is None
    assert result[1] is None
    assert result[2] is None
    assert result[3] == "invalid: could not unpack"


def test_unpack_invalid_length_return_dict():
    """Test btcpay unpack with invalid length returning dict."""
    message = b"\x00" * 10

    result = btcpay.unpack(message, return_dict=True)
    assert result["tx0_hash"] is None
    assert result["tx1_hash"] is None
    assert result["order_match_id"] is None
    assert result["status"] == "invalid: could not unpack"


def test_validate_no_order_match(ledger_db):
    """Test btcpay validate with non-existent order match."""
    fake_order_match_id = (
        "0000000000000000000000000000000000000000000000000000000000000001_"
        "0000000000000000000000000000000000000000000000000000000000000002"
    )
    source = "test_source"

    dest, btc_qty, escrowed_asset, escrowed_qty, order_match, problems = btcpay.validate(
        ledger_db, source, fake_order_match_id, 100000
    )

    assert dest is None
    assert btc_qty is None
    assert escrowed_asset is None
    assert escrowed_qty is None
    assert order_match is None
    assert len(problems) == 1
    assert "no such order match" in problems[0]


def test_validate_expired_order_match(ledger_db, defaults, monkeypatch):
    """Test btcpay validate with an expired order match."""
    fake_order_match_id = "abc_def"
    source = defaults["addresses"][0]

    # Mock the get_order_match function
    def mock_get_order_match(db, match_id):
        return [
            {
                "status": "expired",
                "tx0_address": source,
                "tx1_address": defaults["addresses"][1],
                "forward_asset": config.BTC,
                "backward_asset": "XCP",
                "forward_quantity": 100000,
                "backward_quantity": 1000000,
                "match_expire_index": 100,
            }
        ]

    monkeypatch.setattr("counterpartycore.lib.ledger.markets.get_order_match", mock_get_order_match)

    dest, btc_qty, escrowed_asset, escrowed_qty, order_match, problems = btcpay.validate(
        ledger_db, source, fake_order_match_id, 100000
    )

    assert "order match expired" in problems


def test_validate_completed_order_match(ledger_db, defaults, monkeypatch):
    """Test btcpay validate with a completed order match."""
    fake_order_match_id = "abc_def"
    source = defaults["addresses"][0]

    def mock_get_order_match(db, match_id):
        return [
            {
                "status": "completed",
                "tx0_address": source,
                "tx1_address": defaults["addresses"][1],
                "forward_asset": config.BTC,
                "backward_asset": "XCP",
                "forward_quantity": 100000,
                "backward_quantity": 1000000,
                "match_expire_index": 100,
            }
        ]

    monkeypatch.setattr("counterpartycore.lib.ledger.markets.get_order_match", mock_get_order_match)

    dest, btc_qty, escrowed_asset, escrowed_qty, order_match, problems = btcpay.validate(
        ledger_db, source, fake_order_match_id, 100000
    )

    assert "order match completed" in problems


def test_validate_invalid_order_match(ledger_db, defaults, monkeypatch):
    """Test btcpay validate with an invalid order match."""
    fake_order_match_id = "abc_def"
    source = defaults["addresses"][0]

    def mock_get_order_match(db, match_id):
        return [
            {
                "status": "invalid: some reason",
                "tx0_address": source,
                "tx1_address": defaults["addresses"][1],
                "forward_asset": config.BTC,
                "backward_asset": "XCP",
                "forward_quantity": 100000,
                "backward_quantity": 1000000,
                "match_expire_index": 100,
            }
        ]

    monkeypatch.setattr("counterpartycore.lib.ledger.markets.get_order_match", mock_get_order_match)

    dest, btc_qty, escrowed_asset, escrowed_qty, order_match, problems = btcpay.validate(
        ledger_db, source, fake_order_match_id, 100000
    )

    assert "order match invalid" in problems


def test_validate_unrecognised_status(ledger_db, defaults, monkeypatch):
    """Test btcpay validate with an unrecognised order match status."""
    fake_order_match_id = "abc_def"
    source = defaults["addresses"][0]

    def mock_get_order_match(db, match_id):
        return [
            {
                "status": "unknown_status",
                "tx0_address": source,
                "tx1_address": defaults["addresses"][1],
                "forward_asset": config.BTC,
                "backward_asset": "XCP",
                "forward_quantity": 100000,
                "backward_quantity": 1000000,
                "match_expire_index": 100,
            }
        ]

    monkeypatch.setattr("counterpartycore.lib.ledger.markets.get_order_match", mock_get_order_match)

    with pytest.raises(exceptions.OrderError, match="unrecognised order match status"):
        btcpay.validate(ledger_db, source, fake_order_match_id, 100000)


def test_validate_pending_forward_btc(ledger_db, defaults, monkeypatch):
    """Test btcpay validate with pending order match where forward asset is BTC."""
    fake_order_match_id = "abc_def"
    source = defaults["addresses"][0]

    def mock_get_order_match(db, match_id):
        return [
            {
                "status": "pending",
                "tx0_address": source,
                "tx1_address": defaults["addresses"][1],
                "forward_asset": config.BTC,
                "backward_asset": "XCP",
                "forward_quantity": 100000,
                "backward_quantity": 1000000,
                "match_expire_index": 100,
            }
        ]

    monkeypatch.setattr("counterpartycore.lib.ledger.markets.get_order_match", mock_get_order_match)

    dest, btc_qty, escrowed_asset, escrowed_qty, order_match, problems = btcpay.validate(
        ledger_db, source, fake_order_match_id, 100000
    )

    assert dest == defaults["addresses"][1]
    assert btc_qty == 100000
    assert escrowed_asset == "XCP"
    assert escrowed_qty == 1000000
    assert len(problems) == 0


def test_validate_pending_backward_btc(ledger_db, defaults, monkeypatch):
    """Test btcpay validate with pending order match where backward asset is BTC."""
    fake_order_match_id = "abc_def"
    source = defaults["addresses"][1]

    def mock_get_order_match(db, match_id):
        return [
            {
                "status": "pending",
                "tx0_address": defaults["addresses"][0],
                "tx1_address": source,
                "forward_asset": "XCP",
                "backward_asset": config.BTC,
                "forward_quantity": 1000000,
                "backward_quantity": 100000,
                "match_expire_index": 100,
            }
        ]

    monkeypatch.setattr("counterpartycore.lib.ledger.markets.get_order_match", mock_get_order_match)

    dest, btc_qty, escrowed_asset, escrowed_qty, order_match, problems = btcpay.validate(
        ledger_db, source, fake_order_match_id, 100000
    )

    assert dest == defaults["addresses"][0]
    assert btc_qty == 100000
    assert escrowed_asset == "XCP"
    assert escrowed_qty == 1000000
    assert len(problems) == 0
