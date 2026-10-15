from rag import index_pdf, answer, reset_collection, NO_ANSWER

PDF = "sample.pdf"

# Fill these with YOUR pdf's content.
# (question, keyword that must appear in a correct answer)
IN_SCOPE = [
    "What is Bagging?",
    "What is Boosting?",
    "What is stacking?",
    "what is AdaBoost?",
    "what is Gradient Boosting?",
]
# Questions the PDF cannot answer. The app should refuse.
OUT_OF_SCOPE = [
    "Who won the 2018 FIFA World Cup?",
    "What is the capital of Australia?",
    "Who is my best friend?",
]

reset_collection()
index_pdf(PDF)

correct = 0
for q, kw in IN_SCOPE:
    reply, _ = answer(q)
    ok = kw.lower() in reply.lower()
    correct += ok
    print(f"{'PASS' if ok else 'FAIL'} | {q}\n   -> {reply[:120]}\n")

refused = 0
for q in OUT_OF_SCOPE:
    reply, _ = answer(q)
    ok = NO_ANSWER.lower() in reply.lower()
    refused += ok
    print(f"{'PASS' if ok else 'FAIL'} | {q}\n   -> {reply[:120]}\n")

print(f"In-scope accuracy: {correct}/{len(IN_SCOPE)}")
print(f"Correct refusals:  {refused}/{len(OUT_OF_SCOPE)}")