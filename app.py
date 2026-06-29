"""
app.py
RAG pipeline over security logs. Returns both the generated answer and
retrieved context chunks for each question (required for RAGAS evaluation).
"""

import os

import dotenv
from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

LOGS_DIR = "./logs"
DEFAULT_TOP_K = 3


def configure_environment() -> None:
    """Load credentials and configure OpenAI-compatible API access."""
    dotenv.load_dotenv()
    if not os.getenv("GITHUB_TOKEN"):
        raise ValueError("GITHUB_TOKEN is not set")
    os.environ["OPENAI_API_KEY"] = os.getenv("GITHUB_TOKEN")
    os.environ["OPENAI_BASE_URL"] = "https://models.inference.ai.azure.com/"


def create_query_engine(top_k: int = DEFAULT_TOP_K, logs_dir: str = LOGS_DIR):
    """
    Build the vector index and return a query engine.

    Parameters
    ----------
    top_k : int
        Number of retrieved context chunks per query.
    logs_dir : str
        Directory containing firewall.log and vpn.log.
    """
    configure_environment()

    embed_model = OpenAIEmbedding(
        model="text-embedding-3-small",
        api_key=os.getenv("OPENAI_API_KEY"),
        api_base=os.getenv("OPENAI_BASE_URL"),
    )
    Settings.embed_model = embed_model

    documents = SimpleDirectoryReader(logs_dir).load_data()
    index = VectorStoreIndex.from_documents(documents, insert_batch_size=150)

    # List all indexed nodes
    for i, node in enumerate(index.docstore.docs.values()):
        print(f"--- Node {i} ---")
        print("Chunk Text: ", node.get_content()[:200])   # chunk text
        print("Metadata: ",node.metadata)              # e.g. file path
        print("--------------------------------")

    llm = OpenAI(
        model="gpt-4o-mini",
        api_key=os.getenv("OPENAI_API_KEY"),
        api_base=os.getenv("OPENAI_BASE_URL"),
    )

    return index.as_query_engine(llm=llm, similarity_top_k=top_k)


def query_with_context(query_engine, question: str) -> dict:
    """
    Run a question through the RAG pipeline.

    Returns
    -------
    dict with keys:
        question   – the input question
        answer     – LLM-generated answer
        contexts   – list of retrieved log chunk strings
    """
    response = query_engine.query(question)
    contexts = [node.node.get_content() for node in response.source_nodes]
    return {
        "question": question,
        "answer": str(response),
        "contexts": contexts,
    }


def main() -> None:
    """Demo: run two sample queries and print answers with retrieved contexts."""
    query_engine = create_query_engine()

    demo_questions = [
        "Show firewall policies blocking outbound traffic",
        "Why is john.doe unable to connect to VPN?",
    ]

    for question in demo_questions:
        result = query_with_context(query_engine, question)
        print(f"\nQuestion: {result['question']}")
        print(f"Answer: {result['answer']}")
        print(f"Retrieved {len(result['contexts'])} context chunk(s)")


if __name__ == "__main__":
    main()
