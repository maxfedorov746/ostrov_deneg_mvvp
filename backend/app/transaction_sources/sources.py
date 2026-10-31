from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ImportedTransaction:
    amount_kopecks: int
    category: str
    date: date
    comment: str | None = None


class TransactionSource(ABC):
    @abstractmethod
    def normalize(self, payload: dict) -> ImportedTransaction:
        """Return a validated, source-independent transaction."""


class ManualInput(TransactionSource):
    def normalize(self, payload: dict) -> ImportedTransaction:
        return ImportedTransaction(**payload)


class BankAdapter(TransactionSource):
    def normalize(self, payload: dict) -> ImportedTransaction:
        # TODO: consent, bank API mapping, idempotency, reconciliation.
        raise NotImplementedError("Bank integration is not part of the MVP")


class OCRAdapter(TransactionSource):
    def normalize(self, payload: dict) -> ImportedTransaction:
        # TODO: local OCR, confirmation screen, receipt image retention policy.
        raise NotImplementedError("OCR integration is not part of the MVP")
