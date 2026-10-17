import ollama

emb = ollama.embed(model="nomic-embed-text", input="test")
print(len(emb["embeddings"][0]))

resp = ollama.chat(model="llama3.2:3b", messages=[{"role": "user", "content": "Powiedz cześć"}])
print(resp["message"]["content"])
