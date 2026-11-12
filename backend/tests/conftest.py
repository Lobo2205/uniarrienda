import os
import tempfile

# Las pruebas usan una base SQLite temporal: no tocan tu PostgreSQL.
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/pruebas.db"
os.environ["CARPETA_MEDIA"] = f"{_tmp}/media"
