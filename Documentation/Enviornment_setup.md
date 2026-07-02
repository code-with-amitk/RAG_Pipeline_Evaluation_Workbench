## Env Setup 
RAG pipeline is run inside Python venv
```bash
python3 -m venv venv
source venv/bin/activate
pip install ragas llama-index llama-index-embeddings-openai llama-index-llms-openai python-dotenv pandas seaborn scipy matplotlib
```
Create a `.env` file in the project root and add your GitHub token:
```
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```