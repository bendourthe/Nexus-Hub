class User:
    def __init__(self, name: str):
        self.name = name

    def greet(self) -> str:
        return f"hello {self.name}"


class AdminUser(User):
    def is_admin(self) -> bool:
        return True
