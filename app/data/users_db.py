from app.schemas.user_schema import User

usuarios_db: list[User] = [
    User(id=1, name="Ana Torres", email="ana@example.com", role="admin", is_active=True),
    User(id=2, name="Carlos Ruiz", email="carlos@example.com", role="user", is_active=False),
    User(id=3, name="Elena Gómez", email="elena@example.com", role="support", is_active=True),
]