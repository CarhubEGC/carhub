from flask import Blueprint, jsonify, request, url_for
from werkzeug.exceptions import Conflict

from fakenodo.database import DepositionService


def _read_metadata() -> dict | None:
    payload = request.get_json(silent=True)
    if isinstance(payload, dict) and isinstance(payload.get("metadata"), dict):
        return payload["metadata"]
    return None


def _deposition_response(deposition: dict | None, status: int):
    if deposition is None:
        return {"message": "Deposition not found"}, 404
    return deposition, status


def create_depositions_blueprint(store: DepositionService) -> Blueprint:
    depositions = Blueprint("depositions", __name__, url_prefix="/api/deposit/depositions")

    @depositions.errorhandler(Conflict)
    def deposition_conflict(error: Conflict):
        return {"message": error.description}, 409

    @depositions.post("", strict_slashes=False)
    def create_deposition():
        metadata = _read_metadata()
        if metadata is None:
            return {"message": "metadata must be a JSON object"}, 400

        return store.create(metadata), 201

    @depositions.get("", strict_slashes=False)
    def list_depositions():
        return jsonify(store.list_all())

    @depositions.get("/<int:deposition_id>")
    def get_deposition(deposition_id: int):
        return _deposition_response(store.get(deposition_id), 200)

    @depositions.put("/<int:deposition_id>")
    def update_metadata(deposition_id: int):
        metadata = _read_metadata()
        if metadata is None:
            return {"message": "metadata must be a JSON object"}, 400

        return _deposition_response(store.update_metadata(deposition_id, metadata), 200)

    @depositions.post("/<int:deposition_id>/files")
    def upload_file(deposition_id: int):
        file = request.files.get("file")
        if file is None or not file.filename:
            return {"message": "file must be a multipart upload"}, 400

        name = request.form.get("name") or file.filename
        return _deposition_response(store.upload_file(deposition_id, name, file), 201)

    @depositions.post("/<int:deposition_id>/actions/publish")
    def publish_deposition(deposition_id: int):
        return _deposition_response(store.publish(deposition_id), 202)

    @depositions.post("/<int:deposition_id>/actions/newversion")
    def new_version(deposition_id: int):
        version = store.new_version(deposition_id)
        if version is None:
            return {"message": "Deposition not found"}, 404

        deposition, draft_id = version
        draft_url = url_for(".get_deposition", deposition_id=draft_id, _external=True)
        return {**deposition, "links": {**deposition.get("links", {}), "latest_draft": draft_url}}, 201

    @depositions.delete("/<int:deposition_id>")
    def delete_deposition(deposition_id: int):
        if not store.delete(deposition_id):
            return {"message": "Deposition not found"}, 404

        return "", 204

    return depositions
