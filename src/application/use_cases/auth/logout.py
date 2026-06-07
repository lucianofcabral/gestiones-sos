from dataclasses import dataclass


@dataclass
class LogoutOutput:
    success: bool
    message: str


@dataclass
class LogoutInput:
    token: str
