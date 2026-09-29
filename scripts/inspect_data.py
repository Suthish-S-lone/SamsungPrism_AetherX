#!/usr/bin/env python3
"""Data inspection script for SmartGuide Development Dataset.

Validates and inspects all development JSON assets using Pydantic data models.
Checks for duplicate IDs, invalid URIs, missing fields, and schema integrity.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Add repository root to path for imports
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from backend.app.config import settings
from backend.app.models.data_models import (
    DeeplinkRecord,
    QueryVariationRecord,
    TestQueryRecord,
    TroubleshootingRecord,
)


def load_json(file_path: Path) -> Any:
    """Load JSON file safely."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def inspect_dataset(data_dir: Path = None) -> Dict[str, Any]:
    """Inspect and validate the development dataset."""
    if data_dir is None:
        data_dir = settings.DATA_DIR

    troubleshooting_path = data_dir / "troubleshooting.json"
    deeplinks_path = data_dir / "deeplinks.json"
    test_queries_path = data_dir / "test_queries.json"
    query_variations_path = data_dir / "query_variations.json"

    validation_errors: List[str] = []

    # 1. Inspect Troubleshooting Records
    raw_troubleshooting = load_json(troubleshooting_path)
    troubleshooting_records: List[TroubleshootingRecord] = []
    seen_trouble_ids = set()
    seen_action_ids = set()
    total_actions = 0

    for idx, raw in enumerate(raw_troubleshooting):
        try:
            record = TroubleshootingRecord.model_validate(raw)
            troubleshooting_records.append(record)
            if record.id in seen_trouble_ids:
                validation_errors.append(
                    f"Duplicate troubleshooting ID found: '{record.id}' at record {idx}"
                )
            seen_trouble_ids.add(record.id)

            for act in record.actions:
                total_actions += 1
                if act.id in seen_action_ids:
                    validation_errors.append(
                        f"Duplicate action ID found: '{act.id}' in record '{record.id}'"
                    )
                seen_action_ids.add(act.id)
        except Exception as e:
            validation_errors.append(
                f"Troubleshooting record validation error at index {idx}: {e}"
            )

    domains = sorted(list({r.domain for r in troubleshooting_records}))

    # 2. Inspect Deeplinks
    raw_deeplinks = load_json(deeplinks_path)
    deeplink_records: List[DeeplinkRecord] = []
    seen_dl_ids = set()
    seen_dl_uris = set()

    for idx, raw in enumerate(raw_deeplinks):
        try:
            dl_record = DeeplinkRecord.model_validate(raw)
            deeplink_records.append(dl_record)
            if dl_record.id in seen_dl_ids:
                validation_errors.append(
                    f"Duplicate deeplink ID found: '{dl_record.id}' at index {idx}"
                )
            seen_dl_ids.add(dl_record.id)

            if dl_record.uri in seen_dl_uris:
                validation_errors.append(
                    f"Duplicate deeplink URI found: '{dl_record.uri}' at index {idx}"
                )
            seen_dl_uris.add(dl_record.uri)

            if not dl_record.uri.startswith("prototype://"):
                validation_errors.append(
                    f"Invalid URI scheme (must start with 'prototype://'): '{dl_record.uri}'"
                )
        except Exception as e:
            validation_errors.append(
                f"Deeplink validation error at index {idx}: {e}"
            )

    # 3. Inspect Test Queries
    raw_test_queries = load_json(test_queries_path)
    test_query_records: List[TestQueryRecord] = []
    supported_queries: List[TestQueryRecord] = []
    unsupported_queries: List[TestQueryRecord] = []

    for idx, raw in enumerate(raw_test_queries):
        try:
            tq_record = TestQueryRecord.model_validate(raw)
            test_query_records.append(tq_record)
            if tq_record.expected_domain is not None:
                supported_queries.append(tq_record)
                if (
                    tq_record.expected_problem_id
                    and tq_record.expected_problem_id not in seen_trouble_ids
                ):
                    validation_errors.append(
                        f"Test query '{tq_record.id}' references unknown problem ID: '{tq_record.expected_problem_id}'"
                    )
            else:
                unsupported_queries.append(tq_record)
        except Exception as e:
            validation_errors.append(
                f"Test query validation error at index {idx}: {e}"
            )

    # 4. Inspect Query Variations
    raw_query_variations = load_json(query_variations_path)
    variation_records: List[QueryVariationRecord] = []
    seen_variation_problem_ids = set()

    for idx, raw in enumerate(raw_query_variations):
        try:
            qv_record = QueryVariationRecord.model_validate(raw)
            variation_records.append(qv_record)
            if qv_record.problem_id in seen_variation_problem_ids:
                validation_errors.append(
                    f"Duplicate query variation problem_id: '{qv_record.problem_id}' at index {idx}"
                )
            seen_variation_problem_ids.add(qv_record.problem_id)

            if qv_record.problem_id not in seen_trouble_ids:
                validation_errors.append(
                    f"Query variation references unknown problem ID: '{qv_record.problem_id}'"
                )
        except Exception as e:
            validation_errors.append(
                f"Query variation validation error at index {idx}: {e}"
            )

    return {
        "troubleshooting_count": len(troubleshooting_records),
        "domains": domains,
        "actions_count": total_actions,
        "deeplinks_count": len(deeplink_records),
        "test_queries_count": len(test_query_records),
        "supported_count": len(supported_queries),
        "unsupported_count": len(unsupported_queries),
        "semantic_variation_groups_count": len(variation_records),
        "validation_errors": validation_errors,
    }


def main():
    """Run data inspection and print structured output."""
    report = inspect_dataset()

    print("DEVELOPMENT DATASET")
    print("===================")
    print()
    print("Troubleshooting records:")
    print(f"  {report['troubleshooting_count']} records loaded and validated")
    print()
    print("Domains:")
    for domain in report["domains"]:
        print(f"  - {domain}")
    print()
    print("Actions:")
    print(f"  {report['actions_count']} total resolution actions across records")
    print()
    print("Deeplink records:")
    print(f"  {report['deeplinks_count']} prototype deeplinks (all verified prototype://)")
    print()
    print("Test queries:")
    print(f"  {report['test_queries_count']} total benchmark test queries")
    print()
    print("Supported queries:")
    print(f"  {report['supported_count']} domain-supported queries")
    print()
    print("Unsupported queries:")
    print(f"  {report['unsupported_count']} out-of-scope / unsupported queries")
    print()
    print("Semantic variation groups:")
    print(f"  {report['semantic_variation_groups_count']} problem variation groups")
    print()
    print("Validation errors:")
    if not report["validation_errors"]:
        print("  None (0 errors). All records conform to Pydantic models.")
    else:
        for err in report["validation_errors"]:
            print(f"  [ERROR] {err}")
    print()

    if report["validation_errors"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
