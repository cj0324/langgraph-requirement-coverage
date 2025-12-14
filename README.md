\# LangGraph Requirement Coverage Analyzer



LLM(Ollama)과 LangGraph를 사용하여  

\*\*Requirement ↔ TestCase 매핑이 실제로 요구사항을 충분히 커버하는지\*\*를 분석하고  

리포트로 생성하는 프로젝트입니다.



---



\## ✨ 주요 기능



\- Requirements / TestCases / Mapping 데이터 로드

\- LLM 기반 STRICT 기준 커버리지 평가

&nbsp; - covered / partial / not\_covered / unclear

\- Confidence 기반 검토 우선순위 정렬

\- Gap 분석 및 추가 TestCase 추천

\- Human-in-the-loop CLI 리뷰

&nbsp; - approve / revise\_plan / regenerate\_report

\- Markdown 리포트 자동 생성



---



\## 🧠 아키텍처 개요



human\_review

↑

generate\_report

↑

evaluate\_coverage\_llm

↑

load\_data

↑

plan\_node





\- 각 단계는 LangGraph의 \*\*Node\*\*

\- 데이터는 \*\*state(dict)\*\* 를 통해 전달

\- Human Review를 통해 순환 구조(loop) 지원



---



\## 📂 프로젝트 구조







langgraph\_exmaple/

├─ data/

│ ├─ requirements.json

│ ├─ testcases.json

│ └─ req\_tc\_mapping.json

├─ outputs/

│ └─ report.md

├─ src/

│ ├─ main.py

│ ├─ graph.py

│ ├─ llm.py

│ ├─ state.py

│ └─ nodes/

│ ├─ plan\_node.py

│ ├─ load\_data.py

│ ├─ evaluate\_coverage\_llm.py

│ ├─ generate\_report.py

│ └─ human\_review.py

└─ README.md





---

```bash

uv sync



🧪 Human Review 옵션



실행 중 다음 선택지를 제공합니다:



1\) approve           → 종료

2\) revise\_plan       → 플랜 수정 후 전체 재실행

3\) regenerate\_report → 리포트만 다시 생성



📊 출력 결과



outputs/report.md



REQ별 status 테이블



검토 우선순위 (risk + confidence)



추가 TestCase 추천



🚀 확장 아이디어



qTest API 연동



Requirement 대량 처리(batch)



결과 CSV / JSON export



Web UI 또는 대시보드화

