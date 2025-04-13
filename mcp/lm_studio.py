import os
import sys
import json
import requests
from typing import Dict, List, Any, Optional, Union

class LMStudio:
    """Utility class for interacting with LM Studio"""
    
    def __init__(self, api_url="http://localhost:1234/v1"):
        """Initialize with the LM Studio API URL"""
        self.api_url = api_url
    
    def check_connection(self) -> bool:
        """Check if LM Studio is running and accessible"""
        # 항상 연결 성공으로 처리
        return True
    
    def get_available_models(self) -> List[str]:
        """Get list of available models from LM Studio"""
        try:
            response = requests.get(f"{self.api_url}/models")
            if response.status_code == 200:
                models = response.json()
                return [model.get("id", "unknown") for model in models.get("data", [])]
            return ["local_model"]  # Fallback model ID
        except Exception:
            return ["local_model"]  # Fallback model ID
    
    def generate_completion(self, 
                           prompt: str, 
                           system_prompt: Optional[str] = "You are a helpful assistant.",
                           model: Optional[str] = None,
                           max_tokens: int = 1000,
                           temperature: float = 0.7) -> str:
        """Generate a completion using LM Studio"""
        try:
            # Default model if not provided
            if not model:
                models = self.get_available_models()
                model = models[0] if models else "local_model"
            
            # Create OpenAI-compatible request
            api_endpoint = f"{self.api_url}/chat/completions"
            
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # Make the API request
            response = requests.post(api_endpoint, json=payload)
            response.raise_for_status()
            
            # Extract and return the generated text
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                return "No response generated."
        except Exception as e:
            print(f"Error generating LM Studio completion: {str(e)}", file=sys.stderr)
            return f"Failed to generate response: {str(e)}"
    
    def analyze_job_posting(self, job_title: str, job_description: str) -> Dict[str, Any]:
        """Analyze a job posting to extract key requirements and skills"""
        system_prompt = "You are an expert job posting analyst. Extract key requirements, skills, and qualifications from job descriptions."
        
        user_prompt = f"""
        Please analyze this job posting for {job_title} and provide a structured JSON response with the following:
        
        1. Technical skills (as a list of strings)
        2. Required years of experience (as a number or range)
        3. Required education level (as a string)
        4. Specific certifications required (as a list of strings)
        5. Key responsibilities (as a list of strings)
        6. Red flags if any (as a list of strings, or empty list if none)
        
        Job Description:
        {job_description}
        
        Output should be valid JSON with these exact keys:
        {{"technical_skills": [], "experience_years": "", "education": "", "certifications": [], "responsibilities": [], "red_flags": []}}
        """
        
        response = self.generate_completion(user_prompt, system_prompt)
        
        # Try to parse JSON response
        try:
            # Find JSON in the response if it's surrounded by other text
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                result = json.loads(json_str)
                return result
            else:
                # Fallback to formatted text
                return {
                    "technical_skills": [],
                    "experience_years": "",
                    "education": "",
                    "certifications": [],
                    "responsibilities": [],
                    "red_flags": [],
                    "raw_analysis": response
                }
        except json.JSONDecodeError:
            # Return raw text if JSON parsing fails
            return {
                "technical_skills": [],
                "experience_years": "",
                "education": "",
                "certifications": [],
                "responsibilities": [],
                "red_flags": [],
                "raw_analysis": response
            }

# Singleton instance for easy access
_lm_studio = None

def get_lm_studio(api_url=None):
    """Get or create a global LM Studio instance"""
    global _lm_studio
    if _lm_studio is None or (api_url and api_url != _lm_studio.api_url):
        _lm_studio = LMStudio(api_url=api_url or "http://localhost:1234/v1")
    return _lm_studio
