from .evaluation import (
    EVALUATION_CASES,
    EvaluationCase,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)
from .retriever import retrieve

LIMIT = 3

REGRESSION_THRESHOLDS = {
    "hit_rate": 0.90,
    "recall": 0.80,
    "precision": 0.60,
    "mrr": 0.80,
    "duplicate_rate": 0.05,
}


OOS_QUERIES = [
    "What is the weather today?",
    "Who is the president of the United States?",
]


def retrieve_for_evaluation(query: str) -> list[dict]:
    """Retrieve deterministic RAG results for a regression query."""

    return retrieve(
        query,
        limit=LIMIT,
    )


def hit_rate(
    results_by_case: list[tuple[EvaluationCase, list[dict]]],
) -> float:
    """Calculate hit rate across evaluation cases."""

    if not results_by_case:
        return 0.0

    hits = 0

    for case, results in results_by_case:
        expected_sources = case["expected_sources"]

        if not expected_sources:
            continue

        retrieved_sources = {result["source"] for result in results}

        if retrieved_sources & expected_sources:
            hits += 1

    scored_cases = sum(1 for case, _ in results_by_case if case["expected_sources"])

    if scored_cases == 0:
        return 0.0

    return hits / scored_cases


def duplicate_rate(
    results_by_case: list[tuple[EvaluationCase, list[dict]]],
) -> float:
    """Calculate duplicate chunk rate across result lists."""

    if not results_by_case:
        return 0.0

    total_results = 0
    duplicate_results = 0

    for _, results in results_by_case:
        seen_chunks = set()

        for result in results:
            key = (
                result["source"],
                result["chunk"],
            )

            total_results += 1

            if key in seen_chunks:
                duplicate_results += 1
            else:
                seen_chunks.add(key)

    if total_results == 0:
        return 0.0

    return duplicate_results / total_results


def evaluate_retrieval() -> dict:
    """Run the complete deterministic retrieval regression."""

    results_by_case: list[tuple[EvaluationCase, list[dict]]] = []

    for case in EVALUATION_CASES:
        results = retrieve_for_evaluation(case["query"])

        results_by_case.append((case, results))

    scored_cases = [
        (case, results) for case, results in results_by_case if case["expected_sources"]
    ]

    recall_scores: list[float] = []
    precision_scores: list[float] = []
    reciprocal_ranks: list[float] = []

    for case, results in scored_cases:
        expected_sources = case["expected_sources"]

        recall_scores.append(
            recall_at_k(
                results,
                expected_sources,
            )
        )

        precision_scores.append(
            precision_at_k(
                results,
                expected_sources,
            )
        )

        reciprocal_ranks.append(
            reciprocal_rank(
                results,
                expected_sources,
            )
        )

    return {
        "hit_rate": hit_rate(results_by_case),
        "recall": (sum(recall_scores) / len(recall_scores) if recall_scores else 0.0),
        "precision": (
            sum(precision_scores) / len(precision_scores) if precision_scores else 0.0
        ),
        "mrr": (
            sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0
        ),
        "duplicate_rate": duplicate_rate(results_by_case),
    }


def evaluate_oos() -> bool:
    """
    Verify that known out-of-scope queries return no results.

    OOS rejection is intentionally deterministic for CI.
    """

    passed = True

    for query in OOS_QUERIES:
        results = retrieve_for_evaluation(query)

        if results:
            print(f"FAIL: OOS query returned results: {query}")

            for result in results:
                print(
                    f"  {result['source']}:{result['chunk']} "
                    f"score={result.get('score', 0):.4f}"
                )

            passed = False

        else:
            print(f"PASS: Rejected OOS query: {query}")

    return passed


def check_thresholds(metrics: dict) -> bool:
    """Check regression metrics against minimum quality thresholds."""

    passed = True

    print()
    print("REGRESSION THRESHOLDS")

    checks = [
        (
            "Hit Rate",
            metrics["hit_rate"],
            REGRESSION_THRESHOLDS["hit_rate"],
            ">=",
        ),
        (
            "Recall",
            metrics["recall"],
            REGRESSION_THRESHOLDS["recall"],
            ">=",
        ),
        (
            "Precision",
            metrics["precision"],
            REGRESSION_THRESHOLDS["precision"],
            ">=",
        ),
        (
            "MRR",
            metrics["mrr"],
            REGRESSION_THRESHOLDS["mrr"],
            ">=",
        ),
        (
            "Duplicate Rate",
            metrics["duplicate_rate"],
            REGRESSION_THRESHOLDS["duplicate_rate"],
            "<=",
        ),
    ]

    for name, actual, threshold, operator in checks:
        check_passed = actual >= threshold if operator == ">=" else actual <= threshold

        if check_passed:
            print(f"PASS: {name} {actual:.3f} {operator} {threshold:.3f}")
        else:
            print(f"FAIL: {name} {actual:.3f} {operator} {threshold:.3f}")
            passed = False

    return passed


def main() -> int:
    """Run the deterministic regression suite."""

    print("RAG REGRESSION EVALUATION")
    print("=" * 70)
    print()
    print("Retrieval mode: deterministic lexical")
    print(f"Evaluation cases: {len(EVALUATION_CASES)}")
    print(f"Top-K: {LIMIT}")
    print()

    print("Running retrieval evaluation...")

    try:
        metrics = evaluate_retrieval()

    except Exception as exc:
        print(f"ERROR: Retrieval evaluation failed: {exc}")
        return 1

    print()
    print("METRICS")
    print("-" * 70)

    print(f"Hit Rate@{LIMIT}:       {metrics['hit_rate']:.3f}")

    print(f"Recall@{LIMIT}:         {metrics['recall']:.3f}")

    print(f"Precision@{LIMIT}:      {metrics['precision']:.3f}")

    print(f"MRR@{LIMIT}:            {metrics['mrr']:.3f}")

    print(f"Duplicate Rate@{LIMIT}: {metrics['duplicate_rate']:.3f}")

    thresholds_passed = check_thresholds(metrics)

    print()
    print("OUT-OF-SCOPE EVALUATION")
    print("-" * 70)

    oos_passed = evaluate_oos()

    print()
    print("=" * 70)

    if thresholds_passed and oos_passed:
        print("RAG REGRESSION PASSED")
        return 0

    print("RAG REGRESSION FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
