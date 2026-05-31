from __future__ import annotations

from werkzeug.security import check_password_hash, generate_password_hash


def _looks_hashed(value: str) -> bool:
    return value.startswith(("pbkdf2:", "scrypt:"))


class UserDto:
    def __init__(self, username: str = "", password: str = "", role: str = "professor"):
        self.username = username
        self.password = password if _looks_hashed(password) else generate_password_hash(password)
        self.role = role

    def check_password(self, plain: str) -> bool:
        if check_password_hash(self.password, plain):
            return True
        if self.password == plain:
            self.password = generate_password_hash(plain)
            return True
        return False

    def set_password(self, plain: str) -> None:
        self.password = generate_password_hash(plain)

    def __str__(self) -> str:
        return f"UserDto({self.username!r}, role={self.role!r})"
