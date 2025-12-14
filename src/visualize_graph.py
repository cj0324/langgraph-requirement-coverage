from pathlib import Path

from .llm import get_llm
from .graph import build_graph


def main():
    llm = get_llm(model="qwen3:8b", temperature=0.0)
    app = build_graph(llm)

    # LangGraph 내부 그래프 객체 얻기
    g = app.get_graph()

    # 1) Mermaid 텍스트로 저장 (가장 확실/가벼움)
    mermaid = g.draw_mermaid()
    Path("outputs").mkdir(exist_ok=True)
    Path("outputs/graph.mmd").write_text(mermaid, encoding="utf-8")

    print("Saved: outputs/graph.mmd")

    # 2) (선택) PNG로 저장 시도
    # mermaid-cli(mmdc) 환경이 있으면 PNG까지 자동 생성 가능
    try:
        png_bytes = g.draw_mermaid_png()
        Path("outputs/graph.png").write_bytes(png_bytes)
        print("Saved: outputs/graph.png")
    except Exception as e:
        print("PNG export skipped (environment missing).")
        print(f"Reason: {e}")


if __name__ == "__main__":
    main()
