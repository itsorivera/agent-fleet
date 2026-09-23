from abc import ABC, abstractmethod
from typing import Any

class LLMProviderPort(ABC):
  @abstractmethod
  def get_llm(
    self,
    model_id: str
  ) -> Any:
    pass

  @abstractmethod
  def validate_credentials(self):
    pass

  @abstractmethod
  def cleanup(self):
    pass

  @abstractmethod
  def get_provider_name(self) -> str:
    pass