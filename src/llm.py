from langchain_ollama import ChatOllama

def get_llm(model: str = "qwen3:8b", temperature: float = 0.0):
    # OLLAMA_HOST 환경변수로 원격/로컬 조정 가능
    return ChatOllama(model=model, temperature=temperature)
