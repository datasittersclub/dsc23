import os
from typing import Optional

class LLMProvider:
    def __init__(self, provider: str, model: str, api_keys: dict, ollama_url: str = 'http://localhost:11434'):
        self.provider = provider
        self.model = model
        self.api_keys = api_keys
        self.ollama_url = ollama_url
        self.client = None
        self._init_client()

    def _init_client(self):
        if self.provider == 'anthropic':
            try:
                import anthropic
                api_key = self.api_keys.get('anthropic') or os.getenv('ANTHROPIC_API_KEY')
                self.client = anthropic.Anthropic(api_key=api_key) if api_key else None
            except ImportError:
                self.client = None
        elif self.provider == 'openai':
            try:
                import openai
                api_key = self.api_keys.get('openai') or os.getenv('OPENAI_API_KEY')
                self.client = openai.OpenAI(api_key=api_key) if api_key else None
            except ImportError:
                self.client = None
        elif self.provider == 'ollama':
            try:
                import ollama
                self.client = ollama.Client(host=self.ollama_url)
            except ImportError:
                self.client = None

    def test_connection(self) -> bool:
        # Implement a simple test for each provider
        return self.client is not None

    def get_status(self):
        return {
            'provider': self.provider,
            'model': self.model,
            'client_ready': self.client is not None
        }

    def call_llm(self, prompt: str) -> str:
        """Call the LLM with the given prompt and return the response"""
        if not self.client:
            raise ValueError(f"No client available for provider {self.provider}")
        
        try:
            if self.provider == 'ollama':
                response = self.client.chat(
                    model=self.model,
                    messages=[{'role': 'user', 'content': prompt}]
                )
                return response['message']['content']
            
            elif self.provider == 'openai':
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{'role': 'user', 'content': prompt}],
                    max_tokens=4000,
                    temperature=0.7
                )
                return response.choices[0].message.content
            
            elif self.provider == 'anthropic':
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4000,
                    messages=[{'role': 'user', 'content': prompt}]
                )
                return response.content[0].text
            
            else:
                raise ValueError(f"Unknown provider: {self.provider}")
                
        except Exception as e:
            print(f"Error calling {self.provider} LLM: {e}")
            return ""
