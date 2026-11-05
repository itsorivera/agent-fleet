from src_domain1_subagents1_service.ports.llm_provider_port import LLMProviderPort
from typing import Optional
from langchain_aws import ChatBedrockConverse
import traceback
import boto3
import os

from src_domain1_subagents1_service.utils.logger import get_logger

logger = get_logger(__name__)

class AWSLLMProviderAdapter(LLMProviderPort):
  def __init__(self, 
               aws_access_key_id: Optional[str] = None,
               aws_secret_access_key: Optional[str] = None,
               aws_session_token: Optional[str] = None,
               aws_region: Optional[str] = None):
    self.aws_access_key_id = aws_access_key_id or os.getenv('aws_access_key_id')
    self.aws_secret_access_key = aws_secret_access_key or os.getenv('aws_secret_access_key')
    self.aws_session_token = aws_session_token or os.getenv('aws_session_token')
    self.aws_region = aws_region or os.getenv('aws_region', 'us-east-1')

    self._session = None
    self._client = None
 
  def get_llm(self,
              model_id: str,
              *,
              temperature: float | None = None,
              max_tokens: int | None = None,
              **kwargs) -> ChatBedrockConverse:
    
    if self._client is None:
      logger.debug("Initializing bedrock client")
      self._session = boto3.Session(
        aws_access_key_id=self.aws_access_key_id,
        aws_secret_access_key=self.aws_secret_access_key,
        aws_session_token=self.aws_session_token,
        region_name=self.aws_region
      )
      self._client = self._session.client('bedrock-runtime')
    
    llm = ChatBedrockConverse(
      client=self._client,
      model=model_id,
      **kwargs,
    )

    return llm

  def validate_credentials(self) -> bool:
    try:
      self._session = boto3.Session(
        aws_access_key_id=self.aws_access_key_id,
        aws_secret_access_key=self.aws_secret_access_key,
        aws_session_token=self.aws_session_token,
        region_name=self.aws_region
      )
      self._client = self._session.client('bedrock-runtime')
      logger.info("Credentials validated successfully")
      return True
    except Exception as e:
      logger.error(f"Error validating credentials: {str(e)}", exc_info=True)
      return False
  
  def cleanup(self) -> None:
    self._session = None
    self._client = None
    logger.debug("AWS Bedrock client cleaned up")

  def get_provider_name(self) -> str:
    return "AWS Bedrock (AWS LLM Provider)"

