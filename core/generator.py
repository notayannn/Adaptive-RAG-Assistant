from groq import Groq
import re
import config

class Generator:
    def __init__(self):
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.model_name = config.LLM_MODEL_NAME

    def generate(self, query: str, context_chunks: list[dict], temperature: float = None) -> str:
        """
        Constructs context-grounded prompt and invokes Groq LPU inference directly.
        """
        temperature = temperature if temperature is not None else config.DEFAULT_TEMPERATURE

        if not context_chunks:
            return "I couldn't find any sufficiently relevant information in your uploaded documents to answer this question accurately."

        formatted_context = ""
        for idx, chunk in enumerate(context_chunks, 1):
            formatted_context += f"\n[Source {idx}: {chunk['source_file']} (Page {chunk['page']})]\n{chunk['text']}\n"

        any_low_confidence = any(c.get("low_confidence") for c in context_chunks)
        confidence_note = (
            "\n\nNOTE: The retrieval similarity scores for this context were below the "
            "configured confidence threshold. Double-check that the context actually "
            "answers the question before asserting it does, and say so if it only "
            "partially covers the question."
            if any_low_confidence else ""
        )

        system_prompt = (
            "You are an executive RAG Knowledge Assistant. Answer the user's question accurately "
            "using ONLY the provided document context below. If the answer cannot be directly "
            "derived from the context, state clearly that the information is not present in the documents. "
            "Do NOT make up facts or use outside unverified knowledge."
            f"{confidence_note}\n\n"
            f"--- CONTEXT START ---\n{formatted_context}\n--- CONTEXT END ---"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=1024
        )

        return response.choices[0].message.content

    def generate_followups(self, query: str, answer: str, num_suggestions: int = 3) -> list[str]:
        """
        Generates short, natural follow-up question suggestions based on the
        last question and answer. Returns a plain list of question strings
        (no numbering/bullets). Returns [] on any failure — this is a nice-to-have,
        never worth breaking the main chat response over.
        """
        try:
            prompt = (
                f"Based on this Q&A exchange, suggest {num_suggestions} short, natural "
                f"follow-up questions the user might ask next. Reply with ONLY the "
                f"questions, one per line, no numbering, no bullets, no preamble.\n\n"
                f"Question: {query}\n"
                f"Answer: {answer}"
            )
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=150
            )
            raw_text = response.choices[0].message.content
            lines = [line.strip() for line in raw_text.split("\n") if line.strip()]

            followups = []
            for line in lines:
                cleaned = re.sub(r"^[\d\.\)\-\*\s]+", "", line).strip()
                if cleaned:
                    followups.append(cleaned)

            return followups[:num_suggestions]
        except Exception:
            return []