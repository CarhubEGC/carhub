import hashlib
import os
from contextlib import nullcontext
from threading import Lock

from sqlalchemy import JSON, Boolean, Column, Integer, MetaData, Table, create_engine
from sqlalchemy.engine import URL, Engine, Row
from sqlalchemy.pool import StaticPool
from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import Conflict

deposits = Table(
    "deposits",
    MetaData(),
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("metadata", JSON, nullable=False),
    Column("previous_id", Integer, unique=True),
    Column("concept_id", Integer),
    Column("published", Boolean, nullable=False),
    Column("files", JSON, nullable=False),
    sqlite_autoincrement=True,
    mysql_engine="InnoDB",
    mariadb_engine="InnoDB",
)


def _representation(row: Row) -> dict:
    concept_id = row.concept_id or row.id
    deposition = {
        "id": row.id,
        "conceptrecid": str(concept_id),
        "metadata": row.metadata,
    }
    if row.published:
        deposition.update(doi=f"10.5072/fakenodo.{row.id}", conceptdoi=f"10.5072/fakenodo.concept.{concept_id}")
    return deposition


class DepositionService:
    def __init__(self, engine: Engine | None = None):
        # In-memory SQLite shares a single connection across the Flask threads.
        self._lock = Lock() if engine is None else nullcontext()
        if engine is None:
            engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
            deposits.create(engine)
        self.engine = engine

    @classmethod
    def from_environment(cls):
        if not os.getenv("FAKENODO_DB_HOST"):
            return cls()

        url = URL.create(
            "mariadb+pymysql",
            host=os.environ["FAKENODO_DB_HOST"],
            port=int(os.environ["FAKENODO_DB_PORT"]),
            database=os.environ["FAKENODO_DB_NAME"],
            username=os.environ["FAKENODO_DB_USER"],
            password=os.environ["FAKENODO_DB_PASSWORD"],
            query={"charset": "utf8mb4"},
        )
        return cls(create_engine(url, pool_pre_ping=True, hide_parameters=True))

    def create(self, metadata: dict) -> dict:
        with self._lock, self.engine.begin() as connection:
            result = connection.execute(deposits.insert().values(metadata=metadata, published=False, files={}))
        deposition_id = result.inserted_primary_key[0]
        return {"id": deposition_id, "conceptrecid": str(deposition_id), "metadata": metadata}

    def get(self, deposition_id: int) -> dict | None:
        with self._lock, self.engine.connect() as connection:
            row = connection.execute(deposits.select().where(deposits.c.id == deposition_id)).one_or_none()
        return None if row is None else _representation(row)

    def list_all(self) -> list[dict]:
        with self._lock, self.engine.connect() as connection:
            return [_representation(row) for row in connection.execute(deposits.select().order_by(deposits.c.id))]

    def update_metadata(self, deposition_id: int, metadata: dict) -> dict | None:
        with self._lock, self.engine.begin() as connection:
            record = deposits.c.id == deposition_id
            row = connection.execute(deposits.select().where(record).with_for_update()).one_or_none()
            if row is None:
                return None
            connection.execute(deposits.update().where(record).values(metadata=metadata))
            return {**_representation(row), "metadata": metadata}

    def upload_file(self, deposition_id: int, name: str, file: FileStorage) -> dict | None:
        # FakeNodo compares uploads by content and does not serve downloads.
        checksum = hashlib.sha256()
        size = 0
        for chunk in iter(lambda: file.stream.read(64 * 1024), b""):
            checksum.update(chunk)
            size += len(chunk)
        entry = {"filename": name, "checksum": f"sha256:{checksum.hexdigest()}", "filesize": size}

        with self._lock, self.engine.begin() as connection:
            record = deposits.c.id == deposition_id
            row = connection.execute(deposits.select().where(record).with_for_update()).one_or_none()
            if row is None:
                return None
            if row.published:
                raise Conflict("Create a new version to change files on a published deposition")
            connection.execute(deposits.update().where(record).values(files={**row.files, name: entry}))
            return entry

    def publish(self, deposition_id: int) -> dict | None:
        with self._lock, self.engine.begin() as connection:
            record = deposits.c.id == deposition_id
            row = connection.execute(deposits.select().where(record).with_for_update()).one_or_none()
            if row is None:
                return None
            if not row.published:
                if row.previous_id is not None:
                    previous = connection.execute(deposits.select().where(deposits.c.id == row.previous_id)).one()
                    if row.files == previous.files:
                        raise Conflict("Change or add files before publishing a new version")
                connection.execute(deposits.update().where(record).values(published=True))
                row = connection.execute(deposits.select().where(record)).one()
            return _representation(row)

    def new_version(self, deposition_id: int) -> tuple[dict, int] | None:
        with self._lock, self.engine.begin() as connection:
            row = connection.execute(
                deposits.select().where(deposits.c.id == deposition_id).with_for_update()
            ).one_or_none()
            if row is None:
                return None
            if not row.published:
                raise Conflict("Publish the deposition before creating a new version")

            successor = connection.execute(
                deposits.select().where(deposits.c.previous_id == deposition_id).with_for_update()
            ).one_or_none()
            if successor is not None:
                if successor.published:
                    raise Conflict("Create the new version from the latest published deposition")
                return _representation(row), successor.id

            result = connection.execute(
                deposits.insert().values(
                    metadata=row.metadata,
                    concept_id=row.concept_id or row.id,
                    previous_id=row.id,
                    published=False,
                    files=row.files,
                )
            )
            return _representation(row), result.inserted_primary_key[0]

    def delete(self, deposition_id: int) -> bool:
        with self._lock, self.engine.begin() as connection:
            record = deposits.c.id == deposition_id
            row = connection.execute(deposits.select().where(record).with_for_update()).one_or_none()
            if row is None:
                return False
            if row.published:
                raise Conflict("Published depositions cannot be deleted")
            connection.execute(deposits.delete().where(record))
            return True
