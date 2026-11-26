from itertools import count


class DepositionStore:
    def __init__(self):
        self._ids = count(1)
        self._depositions = {}

    def create(self, metadata: dict) -> dict:
        deposition_id = next(self._ids)
        deposition = {
            "id": deposition_id,
            "conceptrecid": str(deposition_id),
            "metadata": metadata,
        }
        self._depositions[deposition_id] = deposition
        return deposition

    def get(self, deposition_id: int) -> dict | None:
        return self._depositions.get(deposition_id)
