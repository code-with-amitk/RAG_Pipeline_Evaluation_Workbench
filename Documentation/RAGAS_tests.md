# [RAGAS](https://code-with-amitk.github.io/Machine%20Learning/)

file : evaluate.py

## Steps
1. Enter virtual env

2. Create command line parser, which can take following arguments
```
evaluate.py     
    --top-k (default 3) //Retrieval depth
    --limit (default None)      //Evaluate only first N questions
    --use-cache (default )  //Reuse cached RAG responses from rag_responses.json
    --ragas-only   ()   //Skip RAG queries; score cached responses with RAGAS only
    --max-workers   (default 2)  //RAGAS parallel workers 
    --output (default evaluation_results.csv)   //Output CSV path
```

3. Load questions from [benchmark_qa.json](../benchmark_qa.json)

4. Create RAGAS pipeline(This is similar to RAG pipeline) and get {answers, contexts}
```
evaluate.py
def collect_rag_responses():    # Call create_query_engine()
    query_engine = create_query_engine(top_k=top_k)
    for i, item in enumerate(questions, start=1):
        rag_out = query_with_context(query_engine, item["question"])
        # → { "answer": ..., "contexts": [...] }
``` 