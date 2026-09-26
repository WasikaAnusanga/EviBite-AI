"""EviBite AI - Information Retrieval (IR) Evaluation Suite.

Evaluates the multi-factor product retrieval ranking system on standard
Information Retrieval and Web Analytics (IRWA) metrics:
- Precision@1, Precision@3, Precision@5
- Mean Reciprocal Rank (MRR)
- Normalized Discounted Cumulative Gain (NDCG@5)
- Mean Completeness Score
- Average Query Latency (ms)
"""

import math
import time
from typing import Any, Dict, List
from backend.app.agents.agent_stubs import RetrievalRequest
from backend.app.agents.retrieval.service import retrieval_service

# Benchmark Test Collection: 10 representative supermarket queries
BENCHMARK_QUERIES = [
    {
        "id": "Q1",
        "query": "Nutella hazelnut spread",
        "intent": "product_search",
        "category": "snacks",
        "relevant_keywords": ["nutella"],
    },
    {
        "id": "Q2",
        "query": "Oatly Barista oat milk",
        "intent": "product_search",
        "category": "beverages",
        "relevant_keywords": ["oatly", "barista"],
    },
    {
        "id": "Q3",
        "query": "Coca-Cola Zero Sugar",
        "intent": "nutrition_query",
        "category": "beverages",
        "relevant_keywords": ["coca-cola", "zero sugar", "coca cola zero"],
    },
    {
        "id": "Q4",
        "query": "Toblerone milk chocolate with honey and almond",
        "intent": "product_search",
        "category": "chocolate",
        "relevant_keywords": ["toblerone"],
    },
    {
        "id": "Q5",
        "query": "Weetabix whole grain cereal",
        "intent": "product_search",
        "category": "cereal",
        "relevant_keywords": ["weetabix"],
    },
    {
        "id": "Q6",
        "query": "Almond Breeze unsweetened almond milk",
        "intent": "product_search",
        "category": "beverages",
        "relevant_keywords": ["almond breeze", "almond milk"],
    },
    {
        "id": "Q7",
        "query": "KitKat 4 finger chocolate wafers",
        "intent": "product_search",
        "category": "chocolate",
        "relevant_keywords": ["kitkat", "kit kat"],
    },
    {
        "id": "Q8",
        "query": "low sugar drinks",
        "intent": "nutrition_query",
        "category": "beverages",
        "relevant_keywords": ["zero sugar", "diet", "water", "unsweetened", "sugar free"],
    },
    {
        "id": "Q9",
        "query": "dairy milk chocolate",
        "intent": "product_search",
        "category": "chocolate",
        "relevant_keywords": ["dairy milk", "cadbury", "milk chocolate"],
    },
    {
        "id": "Q10",
        "query": "Cheerios honey grain cereal",
        "intent": "product_search",
        "category": "cereal",
        "relevant_keywords": ["cheerios"],
    },
]


def is_relevant(product_name: str, brand: str | None, relevant_keywords: List[str]) -> bool:
    target = f"{product_name} {brand or ''}".lower()
    return any(kw.lower() in target for kw in relevant_keywords)


def calculate_dcg(relevance_scores: List[int], k: int) -> float:
    dcg = 0.0
    for i in range(min(k, len(relevance_scores))):
        rel = relevance_scores[i]
        dcg += (2**rel - 1) / math.log2(i + 2)
    return dcg


def calculate_ndcg(relevance_scores: List[int], k: int) -> float:
    actual_dcg = calculate_dcg(relevance_scores, k)
    ideal_scores = sorted(relevance_scores, reverse=True)
    ideal_dcg = calculate_dcg(ideal_scores, k)
    return (actual_dcg / ideal_dcg) if ideal_dcg > 0 else 0.0


def run_ir_evaluation() -> Dict[str, Any]:
    results = []
    latencies = []
    reciprocal_ranks = []
    p1_list, p3_list, p5_list = [], [], []
    ndcg5_list = []
    completeness_list = []

    print("=" * 80)
    print(" EviBite AI - Information Retrieval & Ranking Evaluation (IT 3041)")
    print("=" * 80)
    print(f"{'ID':<4} {'Query':<35} {'P@1':<6} {'P@3':<6} {'P@5':<6} {'RR':<6} {'NDCG@5':<8} {'Time (ms)':<10}")
    print("-" * 80)

    for item in BENCHMARK_QUERIES:
        start_time = time.perf_counter()
        req = RetrievalRequest(
            trace_id=f"eval-{item['id']}",
            query=item["query"],
            intent=item["intent"],
            category=item["category"],
            requested_fields=["name", "brand", "ingredients", "allergens", "nutrition"],
        )
        res = retrieval_service(req)
        latency = (time.perf_counter() - start_time) * 1000
        latencies.append(latency)

        candidates = res.candidates
        k5_candidates = candidates[:5]

        # Calculate relevance vector (1 for relevant, 0 for not)
        relevance_vector = [
            1 if is_relevant(c.name, c.brand, item["relevant_keywords"]) else 0
            for c in k5_candidates
        ]
        # Pad with 0 if fewer than 5 candidates
        while len(relevance_vector) < 5:
            relevance_vector.append(0)

        # Precision@K
        p1 = relevance_vector[0]
        p3 = sum(relevance_vector[:3]) / 3.0
        p5 = sum(relevance_vector[:5]) / 5.0
        p1_list.append(p1)
        p3_list.append(p3)
        p5_list.append(p5)

        # Reciprocal Rank (RR)
        rr = 0.0
        for rank, rel in enumerate(relevance_vector, start=1):
            if rel == 1:
                rr = 1.0 / rank
                break
        reciprocal_ranks.append(rr)

        # NDCG@5
        ndcg5 = calculate_ndcg(relevance_vector, 5)
        ndcg5_list.append(ndcg5)

        # Data Completeness
        avg_comp = (
            sum(c.completeness for c in k5_candidates) / len(k5_candidates)
            if k5_candidates
            else 0.0
        )
        completeness_list.append(avg_comp)

        query_display = item["query"][:33] + ".." if len(item["query"]) > 33 else item["query"]
        print(f"{item['id']:<4} {query_display:<35} {p1:<6.2f} {p3:<6.2f} {p5:<6.2f} {rr:<6.2f} {ndcg5:<8.2f} {latency:<10.1f}")

    print("-" * 80)
    avg_p1 = sum(p1_list) / len(p1_list)
    avg_p3 = sum(p3_list) / len(p3_list)
    avg_p5 = sum(p5_list) / len(p5_list)
    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks)
    avg_ndcg5 = sum(ndcg5_list) / len(ndcg5_list)
    avg_latency = sum(latencies) / len(latencies)
    avg_completeness = sum(completeness_list) / len(completeness_list)

    print("\n" + "=" * 50)
    print(" OVERALL IR SYSTEM PERFORMANCE SUMMARY")
    print("=" * 50)
    print(f"Mean Precision@1 (P@1):       {avg_p1 * 100:.1f}%")
    print(f"Mean Precision@3 (P@3):       {avg_p3 * 100:.1f}%")
    print(f"Mean Precision@5 (P@5):       {avg_p5 * 100:.1f}%")
    print(f"Mean Reciprocal Rank (MRR):   {mrr:.4f}")
    print(f"Mean NDCG@5:                  {avg_ndcg5:.4f}")
    print(f"Mean Data Completeness:       {avg_completeness * 100:.1f}%")
    print(f"Average Retrieval Latency:    {avg_latency:.1f} ms")
    print("=" * 50)

    return {
        "P@1": avg_p1,
        "P@3": avg_p3,
        "P@5": avg_p5,
        "MRR": mrr,
        "NDCG@5": avg_ndcg5,
        "Latency_ms": avg_latency,
        "Completeness": avg_completeness,
    }


if __name__ == "__main__":
    run_ir_evaluation()
