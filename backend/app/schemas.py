from datetime import date as Date
from typing import Literal
from pydantic import BaseModel, Field, field_validator


class RegisterIn(BaseModel):
    nickname: str = Field(min_length=3, max_length=32, pattern=r"^[\w-]+$")
    contact: str = Field(min_length=6, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    birth_year: int
    parental_consent: bool = False

    @field_validator("contact")
    @classmethod
    def contact_valid(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" in value:
            from email_validator import validate_email, EmailNotValidError
            try:
                return validate_email(value, check_deliverability=False).normalized
            except EmailNotValidError as exc:
                raise ValueError("Укажи корректный email") from exc
        digits = value[1:] if value.startswith("+") else value
        if not digits.isdigit() or not 10 <= len(digits) <= 15:
            raise ValueError("Укажи email или телефон с 10–15 цифрами")
        return "+" + digits


class LoginIn(BaseModel):
    contact: str
    password: str


class BudgetIn(BaseModel):
    amount_kopecks: int = Field(gt=0, le=100_000_000_00)
    savings_target_percent: int = Field(default=10, ge=0, le=50)


class TransactionIn(BaseModel):
    amount_kopecks: int = Field(gt=0, le=100_000_000_00)
    type: Literal["expense", "saving"]
    category: Literal["necessary", "wanted", "savings"]
    comment: str | None = Field(default=None, max_length=240)
    date: Date | None = None


class AvoidedIn(BaseModel):
    amount_kopecks: int = Field(gt=0, le=100_000_000_00)
    item_name: str | None = Field(default=None, max_length=100)
    comment: str | None = Field(default=None, max_length=240)
    date: Date | None = None


class BatchEntryIn(BaseModel):
    expense_kopecks: int = Field(default=0, ge=0, le=100_000_000_00)
    expense_category: Literal["necessary", "wanted"] = "necessary"
    saving_kopecks: int = Field(default=0, ge=0, le=100_000_000_00)
    avoided_kopecks: int = Field(default=0, ge=0, le=100_000_000_00)
    avoided_name: str | None = Field(default=None, max_length=100)
    comment: str | None = Field(default=None, max_length=240)
    date: Date | None = None


class TutorialIn(BaseModel):
    choice: Literal["guide", "skip", "complete"]


class FriendIn(BaseModel):
    nickname: str


class ChoiceIn(BaseModel):
    option_id: str
