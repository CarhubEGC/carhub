from io import BytesIO
from unittest.mock import create_autospec

import pytest
from flask import Flask
from sqlalchemy import JSON, Column, Integer, MetaData, Table, create_engine, inspect

from fakenodo import database
from fakenodo.app import create_app
from fakenodo.database import DepositionService
from fakenodo.routes import create_depositions_blueprint

DEPOSITIONS = "/api/deposit/depositions"


def test_deposition_lifecycle_uses_real_storage(monkeypatch):
    monkeypatch.delenv("FAKENODO_DB_HOST", raising=False)
    client = create_app().test_client()
    original = f"{DEPOSITIONS}/1"
    assert client.get(DEPOSITIONS).json == []
    assert client.post(DEPOSITIONS, json={"metadata": {"title": "Dataset"}}).status_code == 201
    assert client.post(f"{original}/actions/newversion").status_code == 409
    assert client.post(f"{original}/files", data={"file": (BytesIO(b"original"), "model.uvl")}).status_code == 201

    published = client.post(f"{original}/actions/publish")
    assert published.status_code == 202
    updated = client.put(original, json={"metadata": {"title": "Edited"}})
    assert updated.status_code == 200
    assert updated.json["doi"] == published.json["doi"]
    assert client.delete(original).status_code == 409
    assert client.post(f"{original}/files", data={"file": (BytesIO(b"changed"), "model.uvl")}).status_code == 409

    action = f"{original}/actions/newversion"
    version = client.post(action)
    assert version.status_code == 201
    draft = version.json["links"]["latest_draft"]
    assert client.post(action).json["links"]["latest_draft"] == draft
    assert client.get(draft).json["metadata"] == {"title": "Edited"}
    assert client.post(f"{draft}/files", data={"file": (BytesIO(b"original"), "model.uvl")}).status_code == 201
    assert client.post(f"{draft}/actions/publish").status_code == 409

    assert client.post(f"{draft}/files", data={"file": (BytesIO(b"changed"), "model.uvl")}).status_code == 201
    new_publication = client.post(f"{draft}/actions/publish")
    assert new_publication.status_code == 202
    assert new_publication.json["doi"] != published.json["doi"]
    assert new_publication.json["conceptdoi"] == published.json["conceptdoi"]
    assert client.post(f"{draft}/actions/publish").json == new_publication.json
    assert client.post(action).status_code == 409
    assert client.get(original).json == updated.json
    assert client.get(DEPOSITIONS).json == [updated.json, new_publication.json]

    disposable = client.post(f"{draft}/actions/newversion").json["links"]["latest_draft"]
    assert client.delete(disposable).status_code == 204
    assert client.get(disposable).status_code == 404


def test_app_uses_configured_database_to_create_and_read_deposition(monkeypatch):
    monkeypatch.setenv("FAKENODO_DB_HOST", "mariadb.example.test")
    monkeypatch.setenv("FAKENODO_DB_PORT", "61000")
    monkeypatch.setenv("FAKENODO_DB_NAME", "fakenodo")
    monkeypatch.setenv("FAKENODO_DB_USER", "fakenodo")
    monkeypatch.setenv("FAKENODO_DB_PASSWORD", "test-password")
    engine = create_engine("sqlite://")
    database.deposits.create(engine)

    def use_test_engine(url, **kwargs):
        assert url.drivername == "mariadb+pymysql"
        assert (url.host, url.port, url.database) == ("mariadb.example.test", 61000, "fakenodo")
        assert (url.username, url.password) == ("fakenodo", "test-password")
        return engine

    monkeypatch.setattr(database, "create_engine", use_test_engine)
    try:
        created = create_app().test_client().post(DEPOSITIONS, json={"metadata": {"title": "Dataset"}})
        assert created.status_code == 201
        assert created.json == {"id": 1, "conceptrecid": "1", "metadata": {"title": "Dataset"}}

        client = create_app().test_client()
        read = client.get(f"{DEPOSITIONS}/1")
        assert read.status_code == 200
        assert read.json == created.json
        assert client.get(f"{DEPOSITIONS}/2").status_code == 404
    finally:
        engine.dispose()


@pytest.mark.parametrize("legacy_schema", [False, True])
def test_init_db_handles_empty_and_legacy_databases(monkeypatch, tmp_path, legacy_schema):
    engine = create_engine(f"sqlite:///{(tmp_path / 'fakenodo.db').as_posix()}")
    if legacy_schema:
        Table(
            "deposits",
            MetaData(),
            Column("id", Integer, primary_key=True),
            Column("metadata", JSON, nullable=False),
        ).create(engine)
    monkeypatch.setattr(DepositionService, "from_environment", lambda: DepositionService(engine))
    runner = create_app().test_cli_runner()

    try:
        result = runner.invoke(args=["init-db"])
        columns = {column["name"] for column in inspect(engine).get_columns("deposits")}
        if legacy_schema:
            assert result.exit_code == 1
            assert "needs a migration" in result.output
            assert columns == {"id", "metadata"}
        else:
            assert result.exit_code == 0, result.output
            assert columns == set(database.deposits.c.keys())
            assert runner.invoke(args=["init-db"]).exit_code == 0
    finally:
        engine.dispose()


def test_recreating_a_deleted_version_draft_preserves_the_original(monkeypatch):
    monkeypatch.delenv("FAKENODO_DB_HOST", raising=False)
    client = create_app().test_client()
    created = client.post(DEPOSITIONS, json={"metadata": {}})
    assert created.status_code == 201
    original = f"{DEPOSITIONS}/{created.json['id']}"
    published = client.post(f"{original}/actions/publish")
    assert published.status_code == 202
    action = f"{original}/actions/newversion"

    first_version = client.post(action)
    assert first_version.status_code == 201
    first_draft = first_version.json["links"]["latest_draft"]
    assert client.delete(first_draft).status_code == 204
    assert client.delete(first_draft).status_code == 404

    second_version = client.post(action)
    assert second_version.status_code == 201
    second_draft = second_version.json["links"]["latest_draft"]
    assert second_draft != first_draft
    assert client.get(first_draft).status_code == 404
    assert client.get(second_draft).json["conceptrecid"] == published.json["conceptrecid"]
    assert client.get(original).json == published.json


@pytest.fixture
def fakenodo():
    store = create_autospec(DepositionService, instance=True, spec_set=True)
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(create_depositions_blueprint(store))
    return app.test_client(), store


@pytest.mark.parametrize("suffix", ["", "/"])
def test_create_and_list_depositions(fakenodo, suffix):
    client, store = fakenodo
    metadata = {"title": "Dataset"}
    deposition = {"id": 1, "conceptrecid": "1", "metadata": metadata}
    store.create.return_value = deposition
    store.list_all.return_value = [deposition]

    response = client.post(DEPOSITIONS + suffix, json={"metadata": metadata})
    assert response.status_code == 201
    assert response.json == deposition
    store.create.assert_called_once_with(metadata)

    response = client.get(DEPOSITIONS + suffix)
    assert response.status_code == 200
    assert response.json == [deposition]
    store.list_all.assert_called_once_with()


@pytest.mark.parametrize(("method", "suffix"), [("POST", ""), ("PUT", "/1")])
@pytest.mark.parametrize("payload", [{}, {"metadata": []}, ["metadata"]])
def test_reject_invalid_metadata(fakenodo, method, suffix, payload):
    client, store = fakenodo
    response = client.open(DEPOSITIONS + suffix, method=method, json=payload)
    assert response.status_code == 400
    assert store.mock_calls == []


def test_delete_deposition(fakenodo):
    client, store = fakenodo
    store.delete.return_value = True
    response = client.delete(f"{DEPOSITIONS}/1")
    assert response.status_code == 204
    assert response.data == b""
    store.delete.assert_called_once_with(1)


def test_upload_requires_multipart_file(fakenodo):
    client, store = fakenodo
    response = client.post(f"{DEPOSITIONS}/1/files", data={"name": "model.uvl"})
    assert response.status_code == 400
    store.upload_file.assert_not_called()


def test_upload_to_unknown_deposition_uses_file_name_from_multipart(fakenodo):
    client, store = fakenodo
    store.upload_file.return_value = None
    response = client.post(
        f"{DEPOSITIONS}/42/files",
        data={"file": (BytesIO(b"features"), "model.uvl")},
    )

    assert response.status_code == 404
    assert store.upload_file.call_args.args[:2] == (42, "model.uvl")


@pytest.mark.parametrize(
    ("method", "suffix", "operation", "kwargs"),
    [
        ("GET", "", "get", {}),
        ("PUT", "", "update_metadata", {"json": {"metadata": {}}}),
        ("POST", "/actions/publish", "publish", {}),
        ("POST", "/actions/newversion", "new_version", {}),
        ("DELETE", "", "delete", {}),
    ],
)
def test_unknown_deposition(fakenodo, method, suffix, operation, kwargs):
    client, store = fakenodo
    getattr(store, operation).return_value = False if operation == "delete" else None
    response = client.open(f"{DEPOSITIONS}/42{suffix}", method=method, **kwargs)
    assert response.status_code == 404
    assert response.json == {"message": "Deposition not found"}


def test_metadata_edit_returns_same_doi(fakenodo):
    client, store = fakenodo
    original = {"id": 1, "doi": "10.5072/zenodo.1", "conceptdoi": "10.5072/zenodo.100"}
    metadata = {"title": "Updated dataset"}
    store.get.return_value = original
    store.update_metadata.return_value = {**original, "metadata": metadata}

    before = client.get(f"{DEPOSITIONS}/1")
    updated = client.put(f"{DEPOSITIONS}/1", json={"metadata": metadata})

    assert before.status_code == updated.status_code == 200
    assert updated.json == {**before.json, "metadata": metadata}
    store.get.assert_called_once_with(1)
    store.update_metadata.assert_called_once_with(1, metadata)
    store.new_version.assert_not_called()


def test_publish_new_version_returns_new_doi_and_shared_concept_doi(fakenodo):
    client, store = fakenodo
    original = {"id": 1, "doi": "10.5072/zenodo.1", "conceptdoi": "10.5072/zenodo.100"}
    draft = {"id": 2, "conceptdoi": original["conceptdoi"]}
    published = {**draft, "doi": "10.5072/zenodo.2"}
    store.new_version.return_value = original, 2
    store.get.side_effect = [draft, published]
    store.publish.return_value = published

    def upload_file(deposition_id, name, file):
        assert deposition_id == 2
        assert name == "model.uvl"
        assert file.read() == b"features"
        return {"filename": name}

    store.upload_file.side_effect = upload_file

    new_version = client.post(f"{DEPOSITIONS}/1/actions/newversion")
    assert new_version.status_code == 201
    draft_url = new_version.json["links"]["latest_draft"]
    assert new_version.json == {**original, "links": {"latest_draft": f"http://localhost{DEPOSITIONS}/2"}}
    draft_response = client.get(draft_url)
    assert draft_response.status_code == 200
    assert draft_response.json == draft

    upload = client.post(
        f"{draft_url}/files",
        data={"name": "model.uvl", "file": (BytesIO(b"features"), "local.uvl")},
        content_type="multipart/form-data",
    )
    assert upload.status_code == 201
    assert upload.json == {"filename": "model.uvl"}

    publish = client.post(f"{draft_url}/actions/publish")
    assert publish.status_code == 202
    assert publish.json["doi"] != new_version.json["doi"]
    assert publish.json["conceptdoi"] == new_version.json["conceptdoi"]
    stored = client.get(draft_url)
    assert stored.status_code == 200
    assert stored.json == publish.json
    store.new_version.assert_called_once_with(1)
    store.publish.assert_called_once_with(2)
