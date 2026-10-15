from rag import index_pdf, answer, reset_collection, NO_ANSWER

PDF = "sample.pdf"

IN_SCOPE = [
    ("What is Bagging?", ["bootstrap", "parallel", "variance"]),
    ("What is Boosting?", ["sequential", "weak", "errors"]),
    ("What is stacking?", ["meta", "combine", "level"]),
    ("What is AdaBoost?", ["weight", "weak", "misclassified"]),
    ("What is Gradient Boosting?", ["gradient", "residual", "loss"]),
]

# Questions the PDF cannot answer. The app should refuse.
OUT_OF_SCOPE = [
    "Who won the 2018 FIFA World Cup?",
    "What is the capital of Australia?",
    "Who is my best friend?",
]

reset_collection()
n = index_pdf(PDF, name=PDF)
print(f"Indexed {n} chunks from {PDF}\n")

correct = 0
for question, words in IN_SCOPE:
    reply, sources = answer(question)
    ok = any(w.lower() in reply.lower() for w in words) and len(sources) > 0
    correct += ok
    pages = sorted({s["page"] for s in sources})
    print(f"{'PASS' if ok else 'FAIL'} | {question}  (pages used: {pages})")
    print(f"   -> {reply[:120]}\n")

refused = 0
for question in OUT_OF_SCOPE:
    reply, sources = answer(question)
    ok = NO_ANSWER.lower() in reply.lower()
    refused += ok
    print(f"{'PASS' if ok else 'FAIL'} | {question}")
    print(f"   -> {reply[:120]}\n")

print(f"In-scope accuracy: {correct}/{len(IN_SCOPE)}")
print(f"Correct refusals:  {refused}/{len(OUT_OF_SCOPE)}")
