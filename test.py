

results = retriever.retrieve("Balochistan minimum wage rate per month", province="balochistan", top_k=5)
for r in results:
    print(r['score'], r['text'][:200])