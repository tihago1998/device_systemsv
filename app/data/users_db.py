from typing import List

fake_db: List[dict] = [
    {"id": 1, "name": "Ana Torres", "email": "ana@device.com", "role": "admin", "is_active": True},
    {"id": 2, "name": "Luis Pérez", "email": "luis@device.com", "role": "user", "is_active": False},
]


def get_next_id() -> int:
    return max((u["id"] for u in fake_db), default=0) + 1