import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.retrieval.hybrid import HybridRetriever

r = HybridRetriever()

questions = [
    "How many casual leave days can I carry forward?",
    "Can sick leave be carried to the next year?",
    "How many privilege leave days can I carry forward?",
    "When does carried-forward casual leave expire?",
    "What does section 4.1 say about CL?",
    "Does the Standard health tier cover dental implants?",
    "Can I send confidential company files to my personal Gmail?",
    "Can I expense a personal home gym?",
    "Does the company provide free gym membership?",
    "What is the company's maternity leave policy?"
]

for q in questions:
    res = r.retrieve(q, top_k=1)
    if res:
        x = res[0]
        dist = x.get("distance", 99)
        kw = x.get("keyword_score", 0)
        rrf = x.get("rrf_score", 0)
        sec = x.get("metadata", {}).get("section")
        print(f"{q:<55} | dist={dist:.3f} | kw={kw:.2f} | rrf={rrf:.4f} | sec={sec}")
