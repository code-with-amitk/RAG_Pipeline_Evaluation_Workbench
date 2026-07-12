## What this project is about
> What is [RAG pipeline](https://code-with-amitk.github.io/Machine%20Learning/RAG/Introduction.html)
  
1. This RAG pipeline fetches security logs data from sql DB and log files, answer user Queries(using LLM)
2. Response of LLM is measured using RAGAS on 4 parameters:
- **Faithfulness** — does the generated answer contain only information from the retrieved context?
- **Answer Relevancy** — is the answer actually relevant to the question asked?
- **Context Precision** — are the retrieved chunks ranked with the most relevant ones first?
- **Context Recall** — did the retrieval step find all the chunks needed to answer the question?
3. diagnosed, and improved improving pipeline's performance.

## Documentation

1. [Enviornment Setup](./Documentation/Enviornment_setup.md)
2. [Data Preparation](./Documentation/Preparing_data.md)
3. [RAG(Retrieval-Augmented Generation) Pipeline Stages](./Documentation/RAG_Pipeline.md)
4. [Validating RAG using RAGAS(Retrieval Augmented Generation Assessment)](./Documentation/RAGAS_tests.md)

## Commands
### 1. Running RAG Pipeline & RAGAS evaluation
evaluate.py 

1. creates RAG pipeline, gets user_query response from RAG pipeline=rag_answer
2. Pass RAG pipeline answer(rag_answer) to RAGAS evaluate to get RAGAS metrics
```
cd ~/RAG_Pipeline_Evaluation_Workbench
source venv/bin/activate

# Option A (recommended) — wrapper script
./run_evaluate.sh --use-cache --ragas-only --max-workers 1

# Option B — explicit venv python
./venv/bin/python evaluate.py --use-cache --ragas-only --max-workers 1
```

### 2. test_evaluate