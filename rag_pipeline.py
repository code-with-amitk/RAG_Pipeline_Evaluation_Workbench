import os
import dotenv
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.llms.openai import OpenAI		#Import LLM
from llama_index.core import Settings

# Load GitHub Token and set env
dotenv.load_dotenv()
if not os.getenv("GITHUB_TOKEN"):
    raise ValueError("GITHUB_TOKEN is not set")
os.environ["OPENAI_API_KEY"] = os.getenv("GITHUB_TOKEN")
os.environ["OPENAI_BASE_URL"] = "https://models.inference.ai.azure.com/"

############## 1. Retrieval Phase Start #################
## A. Setup Embedding Model. This is Neural Network	
embed_model = OpenAIEmbedding(
    model="text-embedding-3-small",
    api_key=os.getenv("OPENAI_API_KEY"),
    api_base=os.getenv("OPENAI_BASE_URL"),
)
Settings.embed_model = embed_model

## B. Break documents into Chunks
documents = SimpleDirectoryReader("./logs").load_data()

## C. Pass Chunked documents to Embedding model
# And store Chunks into local vectorDB
# def from_documents(documents, insert_batch_size=150): 
#   embed_model = Settings.embed_model #embed_model from Global
#   nodes = self._chunk_documents(documents) #chunks the documents into Nodes
#   for batch in batches(nodes, batch_size=insert_batch_size):
#       texts = [node.text for node in batch]
#       embeddings = embed_model.get_text_embedding_batch(texts)          
#       self._vector_store.add(embeddings, metadata=batch.metadata) #Store Tensors into the vector DB
index = VectorStoreIndex.from_documents(documents, insert_batch_size=150)
############## Retrieval Phase End #####################

# Create LLM
llm = OpenAI(
    model="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY"),
    api_base=os.getenv("OPENAI_BASE_URL"),
)

############## 2,3. Augumentation & Generation Phase Start #################
# def query_engine(query_string: str):
#////// Augumentation Phase. Create augmented_prompt //////
#    query_tensor = Settings.embed_model.get_text_embedding(user_query_string)
#	 top_k_nodes = self._vector_store.similarity_search(
#       query_tensor, 
#       similarity_top_k=3
#    )
# top_k_nodes now contains the 3 most relevant text chunks (Nodes)
# e.g., Node 1: "Big Star Collectibles was founded in 1988..."
#       Node 2: "The company started as a small garage operation..."
#       Node 3: "By 1990, they had moved to a larger warehouse..."
#    vectordb_text = [Node1][Node2][Node3] 
# augmented_prompt=
#	"Context: 
#	[Node1][Node2][Node3] 
#	Question: Big Star Collectibles Started in
#	Answer:"
#
#

query_engine = index.as_query_engine(
  llm=llm
)
response = query_engine.query("Show firewall policies blocking outbound traffic")
print(response)
#Response=
#The firewall policies blocking outbound traffic are as follows:
#1. Policy: OUTBOUND_BLOCK
#   - Source: 10.1.1.5
#   - Destination: 8.8.8.8
#2. Policy: OUTBOUND_BLOCK
#   - Source: 10.1.1.6
#   - Destination: 1.1.1.1

response = query_engine.query("Why is john.doe unable to connect to VPN?")
print(response)
#john.doe is unable to connect to the VPN due to repeated login failures, as 
#indicated by the log entries showing two instances of VPN_LOGIN_FAILED for the user.