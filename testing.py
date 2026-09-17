from app.llm.llm import run_query


queries = [
    "Find tickets where customers are experiencing problems with payments.",
    "Show tickets related to customers being charged unexpectedly.",
    "Find tickets where users are having technical difficulties with the application.",
    "Find tickets where customers are reporting problems accessing their services.",
]


for i, query in enumerate(queries, start=1):

    print("\n" + "=" * 70)
    print(f"SEMANTIC SEARCH TEST {i}")
    print("=" * 70)

    print(f"\nQuery:\n{query}")

    try:
        answer = run_query(query)

        print("\nAnswer:")
        print(answer)

    except Exception as e:

        print("\nERROR:")
        print(e)