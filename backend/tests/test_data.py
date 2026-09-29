"""Unit tests for the SmartGuide Development Dataset.

Verifies that development assets load properly, validate against Pydantic models,
maintain referential integrity, and strictly use prototype:// URIs without fabricating
official Samsung schemes.
"""

import json
from pathlib import Path
import pytest
from backend.app.config import settings
from backend.app.models.data_models import (
    DeeplinkRecord,
    QueryVariationRecord,
    TestQueryRecord,
    TroubleshootingRecord,
)


@pytest.fixture
def data_dir() -> Path:
    """Fixture to obtain the development data directory path."""
    return settings.DATA_DIR


def test_troubleshooting_data_loads(data_dir: Path):
    """Test 1: Development troubleshooting data loads and validates against model."""
    path = data_dir / "troubleshooting.json"
    assert path.exists(), f"troubleshooting.json missing at {path}"

    with open(path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    assert isinstance(raw_data, list)
    assert len(raw_data) == 32

    records = [TroubleshootingRecord.model_validate(r) for r in raw_data]
    assert len(records) == 32

    domains = {r.domain for r in records}
    assert domains == {"battery", "camera", "display", "performance"}

    for r in records:
        assert len(r.actions) >= 1
        assert len(r.keywords) >= 1
        assert r.source == "development_prototype"


def test_deeplink_data_loads(data_dir: Path):
    """Test 2: Development deeplink data loads and validates against model."""
    path = data_dir / "deeplinks.json"
    assert path.exists(), f"deeplinks.json missing at {path}"

    with open(path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    assert isinstance(raw_data, list)
    assert len(raw_data) == 16

    records = [DeeplinkRecord.model_validate(r) for r in raw_data]
    assert len(records) == 16
    for r in records:
        assert r.source == "development_prototype"


def test_test_queries_load(data_dir: Path):
    """Test 3: Test queries load and separate into supported and unsupported."""
    path = data_dir / "test_queries.json"
    assert path.exists(), f"test_queries.json missing at {path}"

    with open(path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    assert isinstance(raw_data, list)
    assert len(raw_data) == 72

    records = [TestQueryRecord.model_validate(r) for r in raw_data]
    supported = [r for r in records if r.expected_domain is not None]
    unsupported = [r for r in records if r.expected_domain is None]

    assert len(supported) == 64
    assert len(unsupported) == 8


def test_query_variations_load(data_dir: Path):
    """Test 4: Query variations load and contain valid variation lists."""
    path = data_dir / "query_variations.json"
    assert path.exists(), f"query_variations.json missing at {path}"

    with open(path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    assert isinstance(raw_data, list)
    assert len(raw_data) == 32

    records = [QueryVariationRecord.model_validate(r) for r in raw_data]
    assert len(records) == 32
    for r in records:
        assert len(r.query_variations) >= 1
        assert r.canonical_query in r.query_variations


def test_ids_are_valid_and_unique(data_dir: Path):
    """Test 5: IDs in troubleshooting and deeplinks are valid and unique."""
    with open(data_dir / "troubleshooting.json", "r", encoding="utf-8") as f:
        tb_data = json.load(f)
    with open(data_dir / "deeplinks.json", "r", encoding="utf-8") as f:
        dl_data = json.load(f)

    tb_ids = [r["id"] for r in tb_data]
    assert len(tb_ids) == len(set(tb_ids)), "Duplicate troubleshooting IDs detected"

    action_ids = [a["id"] for r in tb_data for a in r["actions"]]
    assert len(action_ids) == len(set(action_ids)), "Duplicate action IDs detected"

    dl_ids = [r["id"] for r in dl_data]
    assert len(dl_ids) == len(set(dl_ids)), "Duplicate deeplink IDs detected"


def test_prototype_deeplinks_use_prototype_scheme(data_dir: Path):
    """Test 6: Prototype deeplinks strictly start with prototype://."""
    with open(data_dir / "deeplinks.json", "r", encoding="utf-8") as f:
        dl_data = json.load(f)

    for record in dl_data:
        uri = record.get("uri", "")
        assert uri.startswith("prototype://"), f"URI {uri} does not start with prototype://"


def test_no_official_samsung_uris_claimed(data_dir: Path):
    """Test 7: Ensure no development URI claims to be an official Samsung URI."""
    with open(data_dir / "deeplinks.json", "r", encoding="utf-8") as f:
        dl_data = json.load(f)

    forbidden_schemes = ["bixby://", "samsungapps://", "samsung://", "sec://"]
    for record in dl_data:
        uri = record.get("uri", "")
        for forbidden in forbidden_schemes:
            assert forbidden not in uri.lower(), (
                f"Found forbidden vendor URI scheme '{forbidden}' in URI: {uri}"
            )
