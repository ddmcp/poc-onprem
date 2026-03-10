from abc import ABC, abstractmethod
import os
from typing import Tuple, List
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from logger_config import setup_logger

logger = setup_logger("llm-chat-client")

class LLMChatClient(ABC):
    """Abstract base class for LLM chat clients"""
    
    @abstractmethod
    def generate_response(self, system_prompt: str, context: str, user_prompt: str) -> Tuple[str, List]:
        """Generate a response from the LLM"""
        pass

class OllamaLLMClient(LLMChatClient):
    """Ollama LLM client implementation"""
    
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_CHAT_URL", "http://ollama-llm-chat:11434")
        self.model = os.getenv("OLLAMA_CHAT_MODEL", "gemma:2b")
        
        self.llm = ChatOllama(
            base_url=self.base_url,
            model=self.model,
            temperature=0
        )
        logger.info(f"Initialized OllamaLLMClient with model: {self.model} at {self.base_url}")
    
    def generate_response(self, system_prompt: str, context: str, user_prompt: str) -> Tuple[str, List[BaseMessage]]:
        """Generate a response from Ollama LLM"""
        try:
            logger.info(f"Sending chat request to Ollama: {self.model}")
            
            final_user_content = f"\n\n#Context:\n{context}\n\n#User Question:\n{user_prompt}"
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=final_user_content),
            ]
            
            logger.info(f"=========> messages to Ollama: {messages}")
            response = self.llm.invoke(messages)
            logger.info(f"=========> response from Ollama: {response}")
            
            return response.content.strip(), messages
        except Exception as e:
            logger.error(f"Error calling Ollama chat: {str(e)}")
            raise

class OpenAICompatibleClient(LLMChatClient):
    """OpenAI-compatible endpoint client implementation using LangChain"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required for OpenAI-compatible provider")
        
        base_url = os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
        model = os.getenv("OPENAI_MODEL", "gpt-4")
        temperature = float(os.getenv("OPENAI_TEMPERATURE", "0"))
        
        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=temperature
        )
        logger.info(f"Initialized OpenAICompatibleClient with model: {model} at {base_url}")
    
    def generate_response(self, system_prompt: str, context: str, user_prompt: str) -> Tuple[str, List[BaseMessage]]:
        """Generate a response from OpenAI-compatible endpoint"""
        try:
            logger.info(f"Sending chat request to OpenAI-compatible endpoint: {self.llm.model_name}")
            
            final_user_content = f"\n\n#Context:\n{context}\n\n#User Question:\n{user_prompt}"
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=final_user_content)
            ]
            
            logger.info(f"=========> messages to OpenAI-compatible endpoint: {messages}")
            response = self.llm.invoke(messages)
            logger.info(f"=========> response from OpenAI-compatible endpoint: {response}")
            
            return response.content.strip(), messages
        except Exception as e:
            logger.error(f"Error calling OpenAI-compatible endpoint: {str(e)}")
            raise

def create_llm_client() -> LLMChatClient:
    """Factory function to create the appropriate LLM client based on configuration"""
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    
    logger.info(f"Creating LLM client for provider: {provider}")
    
    if provider == "ollama":
        return OllamaLLMClient()
    elif provider == "openai-compatible":
        return OpenAICompatibleClient()
    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Supported providers: 'ollama', 'openai-compatible'")
