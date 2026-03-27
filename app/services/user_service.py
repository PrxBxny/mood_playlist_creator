from app.models.user_schemas import User

def get_users() -> list[User]:
    # ... логика обращения к бд и т.д.
    users = [
        User(id=1, email="mail@mail.com", password="password"),
        User(id=2, email="mail@mail.com", password="password")
    ]

    return users