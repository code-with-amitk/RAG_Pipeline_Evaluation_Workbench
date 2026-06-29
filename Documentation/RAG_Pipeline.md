# RAG Pipeline
pipeline is defined in app.py

## Retriever Phase
```py
configure_environment()
create_query_engine()
    Settings.embed_model = embed_model  // Embedding model created
    SimpleDirectoryReader(logs_dir)     // Load chunks from dir
    index = VectorStoreIndex.from_documents(documents, insert_batch_size=150)   //index from db
```

## Augumentation Phase
```py
    query_engine = index.as_query_engine(llm=llm, similarity_top_k=top_k)
```

## Generation Phase
```py
    question = "Show firewall policies blocking outbound traffic"
    response = query_engine.query(question)
```