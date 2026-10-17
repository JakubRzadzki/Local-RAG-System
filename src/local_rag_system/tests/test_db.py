from local_rag_system.db import pool, init_db

init_db()
pool.close()
