from abc import ABC, abstractmethod


class ConsequenceTextProvider(ABC):
    @abstractmethod
    def render(self, template: str, context: dict) -> str:
        pass


class TemplateTextProvider(ConsequenceTextProvider):
    def render(self, template: str, context: dict) -> str:
        return template.format(**context)


# TODO: Russian-hosted/on-prem model implementation behind this interface.
