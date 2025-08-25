import tiktoken
import requests
import os
from typing import Dict, Tuple, Optional

class TokenEstimator:
    """Estimates tokens and costs for different LLM providers"""
    
    def __init__(self):
        # Current pricing as of August 2025 (per 1M tokens)
        self.pricing = {
            'openai': {
                'gpt-4': {'input': 30.0, 'output': 60.0},
                'gpt-4-turbo': {'input': 10.0, 'output': 30.0}, 
                'gpt-3.5-turbo': {'input': 0.5, 'output': 1.5},
                'gpt-4o': {'input': 5.0, 'output': 15.0},
                'gpt-4o-mini': {'input': 0.15, 'output': 0.60}
            },
            'anthropic': {
                'claude-3-opus': {'input': 15.0, 'output': 75.0},
                'claude-3-sonnet': {'input': 3.0, 'output': 15.0},
                'claude-3-haiku': {'input': 0.25, 'output': 1.25},
                'claude-3.5-sonnet': {'input': 3.0, 'output': 15.0}
            },
            'ollama': {
                # Ollama is free but we estimate compute costs
                'llama3:8b': {'input': 0.0, 'output': 0.0, 'note': 'Free (local)'},
                'llama3:70b': {'input': 0.0, 'output': 0.0, 'note': 'Free (local)'},
                'mistral': {'input': 0.0, 'output': 0.0, 'note': 'Free (local)'},
                'codellama': {'input': 0.0, 'output': 0.0, 'note': 'Free (local)'}
            }
        }
    
    def count_tokens(self, text: str, model: str = "gpt-4") -> int:
        """Count tokens in text using tiktoken"""
        try:
            # Map models to tiktoken encodings
            encoding_map = {
                'gpt-4': 'cl100k_base',
                'gpt-4-turbo': 'cl100k_base',
                'gpt-3.5-turbo': 'cl100k_base',
                'gpt-4o': 'cl100k_base',
                'gpt-4o-mini': 'cl100k_base',
                'claude-3-opus': 'cl100k_base',
                'claude-3-sonnet': 'cl100k_base', 
                'claude-3-haiku': 'cl100k_base',
                'claude-3.5-sonnet': 'cl100k_base'
            }
            
            encoding_name = encoding_map.get(model, 'cl100k_base')
            encoding = tiktoken.get_encoding(encoding_name)
            return len(encoding.encode(text))
        except Exception:
            # Fallback: approximate 4 chars per token
            return len(text) // 4
    
    def estimate_corpus_tokens(self, corpus_path: str, model: str, sample_size: Optional[int] = None) -> Dict:
        """Estimate tokens for entire corpus or sample"""
        total_input_tokens = 0
        total_files = 0
        processed_files = 0
        
        # Estimate output tokens per analysis (rough estimate)
        output_tokens_per_analysis = 1000  # JSON response with goals, conflicts, scenes
        
        try:
            if os.path.isfile(corpus_path):
                files = [corpus_path]
            else:
                files = [f for f in os.listdir(corpus_path) if f.endswith('.txt')]
            
            total_files = len(files)
            
            if sample_size:
                files = files[:sample_size]
            
            for filename in files:
                file_path = os.path.join(corpus_path, filename) if os.path.isdir(corpus_path) else corpus_path
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Add prompt overhead (roughly 500 tokens for instructions)
                    prompt_overhead = 500
                    file_tokens = self.count_tokens(content, model) + prompt_overhead
                    total_input_tokens += file_tokens
                    processed_files += 1
                    
                except Exception as e:
                    print(f"Error processing {filename}: {e}")
                    continue
            
            # Calculate total output tokens
            total_output_tokens = processed_files * output_tokens_per_analysis
            
            return {
                'total_files': total_files,
                'processed_files': processed_files,
                'input_tokens': total_input_tokens,
                'output_tokens': total_output_tokens,
                'total_tokens': total_input_tokens + total_output_tokens,
                'is_sample': sample_size is not None,
                'sample_size': sample_size if sample_size else processed_files
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'total_files': 0,
                'processed_files': 0,
                'input_tokens': 0,
                'output_tokens': 0,
                'total_tokens': 0
            }
    
    def calculate_cost(self, provider: str, model: str, input_tokens: int, output_tokens: int) -> Dict:
        """Calculate cost based on provider and model"""
        try:
            if provider not in self.pricing:
                return {'error': f'Unknown provider: {provider}'}
            
            model_pricing = None
            # Find matching model (handle variations in naming)
            for pricing_model, pricing_info in self.pricing[provider].items():
                if pricing_model.lower() in model.lower() or model.lower() in pricing_model.lower():
                    model_pricing = pricing_info
                    break
            
            if not model_pricing:
                # Default pricing for unknown models
                if provider == 'openai':
                    model_pricing = {'input': 10.0, 'output': 30.0}  # GPT-4 turbo default
                elif provider == 'anthropic':
                    model_pricing = {'input': 3.0, 'output': 15.0}   # Claude-3 sonnet default
                else:
                    model_pricing = {'input': 0.0, 'output': 0.0}
            
            # Calculate costs (pricing is per 1M tokens)
            input_cost = (input_tokens / 1_000_000) * model_pricing['input']
            output_cost = (output_tokens / 1_000_000) * model_pricing['output']
            total_cost = input_cost + output_cost
            
            result = {
                'input_cost': round(input_cost, 4),
                'output_cost': round(output_cost, 4),
                'total_cost': round(total_cost, 4),
                'currency': 'USD',
                'input_rate': model_pricing['input'],
                'output_rate': model_pricing['output']
            }
            
            if 'note' in model_pricing:
                result['note'] = model_pricing['note']
            
            return result
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_sample_options(self, corpus_path: str) -> Dict:
        """Get available sample sizes for testing"""
        try:
            if os.path.isfile(corpus_path):
                return {
                    'total_files': 1,
                    'sample_options': [1]
                }
            
            files = [f for f in os.listdir(corpus_path) if f.endswith('.txt')]
            total_files = len(files)
            
            # Suggest sample sizes
            sample_options = [1, 3, 5, 10]
            if total_files > 20:
                sample_options.extend([20, total_files // 4, total_files // 2])
            
            # Remove options larger than total files
            sample_options = [s for s in sample_options if s <= total_files]
            sample_options.append(total_files)  # Full corpus
            
            return {
                'total_files': total_files,
                'sample_options': sorted(set(sample_options))
            }
            
        except Exception as e:
            return {'error': str(e)}
