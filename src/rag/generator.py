from datetime import datetime
import ollama

PROMPT = """You are a professional Disaster Monitoring Assistant. Use the provided official data and secondary news reports to answer the user's question.

CURRENT TIME: {current_time}

OFFICIAL MONITORING DATA:
{context}

SECONDARY NEWS REPORTS:
{news_context}

QUESTION: {question}

INSTRUCTIONS:
1. Summarize official alerts if available.
2. If official data is empty, search the NEWS reports for mentions of disasters.
3. BE SPECIFIC. Mention article titles and their dates.
4. DO NOT use placeholders like [DATE], [TIME], or [IMPACT]. If a detail is missing, simply don't report it.
5. If both sections are empty, state that no information was found for this specific location.
6. If using news, explicitly note: "Internal sensors are quiet, but secondary news reports indicate..."

Answer:"""


class Generator:
    def __init__(self, model="llama3.2:3b"):
        self.model = model

    def generate(self, question: str, events: list, news_context: dict = dict()) -> str:
        # Format current time
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        # Avoid passing empty string which might be ignored
        if not events:
            context_text = "No official events found in our monitoring database."
        else:
            context_text = "\n".join(
                [
                    f"- [{e['metadata'].get('timestamp', 'Unknown Time')}] {e['document']}"
                    for e in events
                ]
            )

        news_text = ""
        if news_context and news_context.get("articles"):
            news_items = []
            for article in news_context["articles"][:3]:
                date_str = article.get("seendate", "Recent")
                # Format GDELT date (YYYYMMDDHHMMSS) to readable
                if len(date_str) >= 8:
                    try:
                        date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                    except:
                        pass
                news_items.append(
                    f"- \"{article['title']}\" (Ref: {article['domain']}, Date: {date_str})"
                )
            news_text = "\n".join(news_items)
        else:
            news_text = "No relevant secondary news articles found."

        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": PROMPT.format(
                        current_time=now_str,
                        context=context_text,
                        news_context=news_text,
                        question=question,
                    ),
                }
            ],
        )
        return response["message"]["content"]
