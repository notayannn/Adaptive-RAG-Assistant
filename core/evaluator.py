import time

class Evaluator:
    def __init__(self):
        pass

    def evaluate_response(self, retrieved_chunks: list[dict], answer: str, latency_dict: dict) -> dict:
        """
        Calculates telemetry metrics: Grounding Confidence Index (GCI),
        retrieval score averages, and latency breakdowns.
        """
        if not retrieved_chunks:
            avg_score = 0.0
            gci_score = 0.0
            hallucination_risk = "High / No Context"
        else:
            scores = [c["score"] for c in retrieved_chunks]
            avg_score = round(sum(scores) / len(scores), 4)

            context_text = " ".join([c["text"] for c in retrieved_chunks]).lower()
            answer_words = set(answer.lower().split())
            stopwords = {"the", "a", "an", "is", "in", "it", "of", "and", "to", "for", "on", "with", "this", "that", "are"}
            meaningful_words = answer_words - stopwords

            if meaningful_words:
                matched = sum(1 for w in meaningful_words if w in context_text)
                overlap_ratio = matched / len(meaningful_words)
            else:
                overlap_ratio = 1.0

            gci_score = round((avg_score * 0.6) + (overlap_ratio * 0.4), 4)

            if gci_score >= 0.70:
                hallucination_risk = "Low Risk (Grounded)"
            elif gci_score >= 0.45:
                hallucination_risk = "Medium Risk"
            else:
                hallucination_risk = "High Risk"

        return {
            "avg_retrieval_score": avg_score,
            "gci_score": gci_score,
            "gci_percentage": f"{round(gci_score * 100, 1)}%",
            "hallucination_risk": hallucination_risk,
            "latency": latency_dict
        }