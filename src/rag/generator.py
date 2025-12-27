import ollama

PROMPT = """You are a helpful Disaster Monitoring Assistant. Use the provided official monitoring data and news context to answer the user's question.

OFFICIAL DATA:
{context}

QUESTION: {question}

QUESTION: {question}

INSTRUCTIONS:
- If OFFICIAL DATA lists disaster events, summarize them concisely (Type, Location, Magnitude, Time).
- If OFFICIAL DATA is empty, inform the user that no specific monitoring data was found for this query.
- Always use YYYY-MM-DD HH:MM UTC for dates.
- Be factual and do not invent details not present in the DATA section.

Answer:"""


class Generator:
    def __init__(self, model="llama3.2"):  # tinyllama
        self.model = model

    def generate(self, question: str, events: list) -> str:
        context = "\n".join(
            [f"- [{e['metadata']}] {e['document']}" for e in events]
        )

        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": PROMPT.format(context=context, question=question),
                }
            ],
        )
        return response["message"]["content"]
