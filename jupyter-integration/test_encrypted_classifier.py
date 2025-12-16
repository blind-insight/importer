#!/usr/bin/env python3
"""
Encrypted aggregation classifier smoke test (integer-scaled features).
Requires: backend running on http://localhost:3001 and integer-scaled iris data in Blind Insight.
"""
import sys
import json
import numpy as np
from blind_insight_client import BlindInsightClient

API_URL = "http://localhost:3001"
ORGANIZATION = "blizzy-insizzy"
DATASET_SLUG = "iris"
SCHEMA_SLUG = "iris-3"

feature = "petal-length"  # integer-scaled
class_a = "I. setosa"
class_b = "I. versicolor"


def agg_value(resp):
    recs = resp.get("records", [])
    if not recs:
        raise ValueError(f"Unexpected aggregation response: {resp}")
    rec0 = recs[0]
    if "data" in rec0 and isinstance(rec0["data"], dict) and "value" in rec0["data"]:
        v = rec0["data"].get("value")
        return float(v) if v is not None else 0.0
    if "value" in rec0:
        v = rec0.get("value")
        return float(v) if v is not None else 0.0
    raise ValueError(f"Unexpected aggregation response shape: {resp}")


def main():
    client = BlindInsightClient(api_url=API_URL)

    # Totals per class
    count_a_total = agg_value(
        client.aggregate(
            organization=ORGANIZATION,
            dataset_slug=DATASET_SLUG,
            schema_slug=SCHEMA_SLUG,
            agg_filter=f"{feature}:count(0~1000)",
            extra_filters=[f"species:{class_a}"],
            decrypt=False,
        )
    )
    count_b_total = agg_value(
        client.aggregate(
            organization=ORGANIZATION,
            dataset_slug=DATASET_SLUG,
            schema_slug=SCHEMA_SLUG,
            agg_filter=f"{feature}:count(0~1000)",
            extra_filters=[f"species:{class_b}"],
            decrypt=False,
        )
    )

    thresholds = range(0, 701, 10)  # adjust to your scaling; here 0..70 *10
    best = {"acc": -1, "t": None, "counts": None}

    for t in thresholds:
        count_a_left = agg_value(
            client.aggregate(
                organization=ORGANIZATION,
                dataset_slug=DATASET_SLUG,
                schema_slug=SCHEMA_SLUG,
                agg_filter=f"{feature}:count(<{t})",
                extra_filters=[f"species:{class_a}"],
                decrypt=False,
            )
        )
        count_b_left = agg_value(
            client.aggregate(
                organization=ORGANIZATION,
                dataset_slug=DATASET_SLUG,
                schema_slug=SCHEMA_SLUG,
                agg_filter=f"{feature}:count(<{t})",
                extra_filters=[f"species:{class_b}"],
                decrypt=False,
            )
        )
        correct = count_a_left + (count_b_total - count_b_left)
        total = count_a_total + count_b_total
        acc = correct / total if total else 0.0
        if acc > best["acc"]:
            best = {"acc": acc, "t": t, "counts": (count_a_left, count_b_left, correct, total)}

    print("=== Encrypted Aggregation Classifier (integer-scaled) ===")
    print(f"Feature: {feature}")
    print(f"Class A: {class_a}, total: {count_a_total}")
    print(f"Class B: {class_b}, total: {count_b_total}")
    print(f"Best threshold: {best['t']}")
    print(
        f"Counts at best threshold -> class_a_left: {best['counts'][0]}, "
        f"class_b_left: {best['counts'][1]}, correct: {best['counts'][2]}/{best['counts'][3]}"
    )
    print(f"Encrypted-rule accuracy: {best['acc']:.4f} ({best['acc']*100:.2f}%)")
    print("Rule: predict class_a if feature < threshold, else class_b (encrypted counts only)")


if __name__ == "__main__":
    sys.exit(main())



