"""
dh2loop LLM Module
==================
This module provides LLM-based alternatives to fuzzy string matching for lithology classification.
Supports AWS Bedrock, OpenRouter, Ollama, and llama-server.

Author: dh2loop contributors
"""

import os
import json
from typing import List, Dict, Tuple, Optional, Any
import re
from enum import Enum


class LLMProvider(Enum):
    """Supported LLM providers"""
    BEDROCK = "bedrock"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    LLAMA_SERVER = "llama-server"


class LithologyMatcher:
    """
    LLM-based lithology matching as an alternative to fuzzywuzzy.
    Uses LangChain to interface with various LLM providers.
    """
    
    def __init__(self, 
                 provider: str = "ollama",
                 model: Optional[str] = None,
                 api_key: Optional[str] = None,
                 endpoint: Optional[str] = None,
                 temperature: float = 0.0,
                 max_tokens: int = 500):
        """
        Initialize the LLM-based lithology matcher.
        
        Args:
            provider: One of 'bedrock', 'openrouter', 'ollama', 'llama-server'
            model: Model name (provider-specific)
            api_key: API key for the provider (if required)
            endpoint: Custom endpoint URL (for Ollama/llama-server)
            temperature: Sampling temperature (0.0 for deterministic)
            max_tokens: Maximum tokens in response
        """
        self.provider = provider.lower()
        self.model = model or self._get_default_model()
        self.api_key = api_key or self._get_api_key_from_env()
        self.endpoint = endpoint or self._get_default_endpoint()
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.llm = None
        
        # Initialize LangChain LLM
        self._init_llm()
    
    def _get_default_model(self) -> str:
        """Get default model for the provider"""
        defaults = {
            "bedrock": "anthropic.claude-3-sonnet-20240229-v1:0",
            "openrouter": "openai/gpt-3.5-turbo",
            "ollama": "llama2",
            "llama-server": "llama2"
        }
        return defaults.get(self.provider, "llama2")
    
    def _get_api_key_from_env(self) -> Optional[str]:
        """Get API key from environment variables"""
        env_vars = {
            "bedrock": None,  # Uses AWS credentials
            "openrouter": "OPENROUTER_API_KEY",
            "ollama": None,  # Local, no key needed
            "llama-server": None  # Local, no key needed
        }
        env_var = env_vars.get(self.provider)
        return os.getenv(env_var) if env_var else None
    
    def _get_default_endpoint(self) -> str:
        """Get default endpoint for the provider"""
        defaults = {
            "ollama": "http://localhost:11434",
            "llama-server": "http://localhost:8080"
        }
        return defaults.get(self.provider, "")
    
    def _init_llm(self):
        """Initialize the LangChain LLM based on provider"""
        try:
            from langchain_community.llms import Ollama
            from langchain_community.chat_models import ChatOpenAI
            
            if self.provider == "bedrock":
                from langchain_aws import ChatBedrock
                self.llm = ChatBedrock(
                    model_id=self.model,
                    model_kwargs={
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens
                    }
                )
            
            elif self.provider == "openrouter":
                self.llm = ChatOpenAI(
                    model=self.model,
                    openai_api_key=self.api_key,
                    openai_api_base="https://openrouter.ai/api/v1",
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
            
            elif self.provider == "ollama":
                self.llm = Ollama(
                    model=self.model,
                    base_url=self.endpoint,
                    temperature=self.temperature
                )
            
            elif self.provider == "llama-server":
                # llama-server uses OpenAI-compatible API
                self.llm = ChatOpenAI(
                    model=self.model,
                    openai_api_base=self.endpoint + "/v1",
                    openai_api_key="not-needed",
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
            
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except ImportError as e:
            raise ImportError(
                f"Required LangChain packages not installed. "
                f"Please install: pip install langchain langchain-community langchain-aws"
            ) from e
    
    def match_lithology(self, 
                       company_litho: str, 
                       litho_dictionary: List[str],
                       threshold: float = 0.8) -> Tuple[str, float]:
        """
        Match a company lithology description to the standard lithology dictionary.
        
        Args:
            company_litho: The company's lithology description
            litho_dictionary: List of standard lithology terms
            threshold: Confidence threshold (0.0-1.0)
        
        Returns:
            Tuple of (best_match, confidence_score)
        """
        # Clean the input
        cleaned_litho = self._clean_text(company_litho)
        
        # Create prompt for LLM
        prompt = self._create_matching_prompt(cleaned_litho, litho_dictionary)
        
        # Get LLM response
        try:
            response = self.llm.invoke(prompt)
            
            # Extract text from response
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            # Parse the response
            best_match, score = self._parse_response(response_text)
            
            # Apply threshold
            if score < threshold * 100:  # Convert to percentage
                return "unclassified_rock", score
            
            return best_match, score
            
        except Exception as e:
            print(f"Error during LLM matching: {e}")
            return "unclassified_rock", 0.0
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove special characters and extra whitespace
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _create_matching_prompt(self, company_litho: str, litho_dict: List[str]) -> str:
        """Create a prompt for lithology matching"""
        # Limit dictionary size for context window
        dict_sample = litho_dict[:100] if len(litho_dict) > 100 else litho_dict
        
        prompt = f"""You are a geological expert specializing in lithology classification. Your task is to match a company's lithology description to the most appropriate standardized lithology term from a dictionary.

Company's lithology description: "{company_litho}"

Standardized lithology dictionary (sample):
{', '.join(dict_sample)}

Instructions:
1. Identify the best matching standardized lithology term from the dictionary
2. Consider geological synonyms and related terms
3. Provide a confidence score from 0-100

Respond in this exact format:
MATCH: <best_matching_term>
SCORE: <confidence_score>

Example:
MATCH: granite
SCORE: 95

Your response:"""
        
        return prompt
    
    def _parse_response(self, response: str) -> Tuple[str, float]:
        """Parse LLM response to extract match and score"""
        match = "unclassified_rock"
        score = 0.0
        
        lines = response.strip().split('\n')
        for line in lines:
            if line.startswith('MATCH:'):
                match = line.replace('MATCH:', '').strip().lower()
            elif line.startswith('SCORE:'):
                score_str = line.replace('SCORE:', '').strip()
                try:
                    score = float(re.search(r'\d+', score_str).group())
                except (AttributeError, ValueError):
                    score = 0.0
        
        return match, score
    
    def batch_match(self, 
                    litho_list: List[Dict[str, Any]], 
                    litho_dictionary: List[str],
                    threshold: float = 0.8) -> List[Dict[str, Any]]:
        """
        Batch process multiple lithology descriptions.
        
        Args:
            litho_list: List of dicts with lithology data
            litho_dictionary: Standard lithology dictionary
            threshold: Confidence threshold
        
        Returns:
            List of dicts with matched lithology and scores
        """
        results = []
        
        for item in litho_list:
            company_litho = item.get('Company_Litho', '')
            best_match, score = self.match_lithology(
                company_litho, 
                litho_dictionary, 
                threshold
            )
            
            result = item.copy()
            result['CET_Litho'] = best_match
            result['Score'] = score
            results.append(result)
        
        return results


def create_matcher(config: Optional[Dict[str, Any]] = None) -> LithologyMatcher:
    """
    Factory function to create a LithologyMatcher from config.
    
    Args:
        config: Configuration dictionary with keys:
            - provider: 'bedrock', 'openrouter', 'ollama', or 'llama-server'
            - model: Model name (optional)
            - api_key: API key (optional)
            - endpoint: Endpoint URL (optional)
            - temperature: Sampling temperature (optional)
            - max_tokens: Max tokens (optional)
    
    Returns:
        LithologyMatcher instance
    """
    if config is None:
        config = {}
    
    return LithologyMatcher(
        provider=config.get('provider', 'ollama'),
        model=config.get('model'),
        api_key=config.get('api_key'),
        endpoint=config.get('endpoint'),
        temperature=config.get('temperature', 0.0),
        max_tokens=config.get('max_tokens', 500)
    )


def load_litho_dictionary(file_path: str) -> List[str]:
    """
    Load lithology dictionary from a thesaurus CSV file.
    
    Args:
        file_path: Path to the thesaurus CSV file
    
    Returns:
        List of lithology terms
    """
    import csv
    litho_terms = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header
            for row in reader:
                if row:
                    litho_terms.append(row[0].lower())
    except Exception as e:
        print(f"Error loading dictionary: {e}")
    
    return litho_terms


# Example usage function
def example_usage():
    """Example of how to use the LLM-based matcher"""
    
    # Example configuration for different providers
    configs = {
        "ollama": {
            "provider": "ollama",
            "model": "llama2",
            "endpoint": "http://localhost:11434"
        },
        "bedrock": {
            "provider": "bedrock",
            "model": "anthropic.claude-3-sonnet-20240229-v1:0"
        },
        "openrouter": {
            "provider": "openrouter",
            "model": "openai/gpt-3.5-turbo",
            "api_key": "your-api-key-here"
        },
        "llama-server": {
            "provider": "llama-server",
            "endpoint": "http://localhost:8080"
        }
    }
    
    # Create matcher (using Ollama by default)
    matcher = create_matcher(configs["ollama"])
    
    # Example lithology dictionary
    litho_dict = [
        "granite", "basalt", "sandstone", "limestone", 
        "shale", "mudstone", "quartzite", "schist"
    ]
    
    # Example company lithology descriptions
    company_descriptions = [
        "coarse grained granite",
        "volcanic rock basaltic",
        "sedimentary sand stone"
    ]
    
    # Match each description
    for desc in company_descriptions:
        match, score = matcher.match_lithology(desc, litho_dict)
        print(f"Description: {desc}")
        print(f"  -> Match: {match}, Score: {score}\n")


if __name__ == "__main__":
    example_usage()
