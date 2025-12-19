import ollama

PROMPT = '''Based on these disaster events, answer the question.

EVENTS:
{context}

QUESTION: {question}

Answer factually based on the data above:'''

class Generator:
    def __init__(self, model="llama3.2"):
        self.model = model
    
    def generate(self, question: str, events: list) -> str:
        context = "\n".join([
            f"- [{e['metadata'].get('source')}] {e['document']}"
            for e in events
        ])
        
        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": PROMPT.format(context=context, question=question)}]
        )
        return response["message"]["content"]
