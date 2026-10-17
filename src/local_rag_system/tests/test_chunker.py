from local_rag_system.chunker import chunk_text

text = """First paragraph about dogs. Dogs love walks and playing.

Second paragraph about cats. Cats sleep for most of the day.

Third paragraph about fish. Fish swim in water and do not need walks.

""" + "Very long paragraph without breaks. " * 8

for size in (100, 200):
    chunks = chunk_text(text, size=size, overlap=20)
    print(f"===== size={size}: {len(chunks)} chunks =====")
    for i, c in enumerate(chunks):
        print(f"--- chunk {i} ({len(c)} chars) ---")
        print(c)
