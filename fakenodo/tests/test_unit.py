from io import BytesIO
from unittest.mock import create_autospec

import pytest
from flask import Flask

from fakenodo.routes import DepositionService, create_depositions_blueprint

DEPOSITIONS = "/api/deposit/depositions"


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
