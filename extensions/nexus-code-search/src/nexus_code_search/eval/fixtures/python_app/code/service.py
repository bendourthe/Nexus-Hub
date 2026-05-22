from models import User, AdminUser


def make_user(name: str) -> User:
    return User(name)


def make_admin(name: str) -> AdminUser:
    return AdminUser(name)


def greet_user(user: User) -> str:
    return user.greet()
