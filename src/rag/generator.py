import ollama

PROMPT = """You are a helpful Disaster Monitoring Assistant. Use the provided official monitoring data and news context to answer the user's question.

OFFICIAL DATA:
{context}

NEWS:
{news_context}

QUESTION: {question}

INSTRUCTIONS:
- If OFFICIAL DATA lists disaster events, summarize them concisely (Type, Location, Magnitude, Time).
- If OFFICIAL DATA is empty, inform the user that no specific monitoring data was found for this query.
- Always use YYYY-MM-DD HH:MM UTC for dates.
- Be factual and do not invent details not present in the DATA section.

Answer:"""


class Generator:
    def __init__(self, model="qwen3:0.6b"):
        self.model = model

    def generate(self, question: str, events: list, news_context: dict = dict()) -> str:
        # Avoid passing empty string which might be ignored
        if not events:
            context_text = "None available. No events found in database."
        else:
            context_text = "\n".join(
                [f"- [{e['metadata']}] {e['document']}" for e in events]
            )

        news_text = "None available"
        if news_context and news_context.get("articles"):
            news_items = []
            for article in news_context["articles"][:3]:
                news_items.append(f"- {article['title']} ({article['domain']})")
            news_text = "\n".join(news_items)

        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": PROMPT.format(
                        context=context_text, news_context=news_text, question=question
                    ),
                }
            ],
        )
        return response["message"]["content"]
