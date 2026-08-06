"""
Image generation module for AI Director using Stability AI API
"""
from pathlib import Path
from src.model_utils import generate_image as _generate_image

class StoryboardGenerator:
    def generate_image(self, prompt: str, output_path: str, seed: int = 42) -> str:
        success = _generate_image(prompt, output_path)
        if success:
            return output_path
        return None
                
        except Exception as e:
            print(f"Error generating image: {e}")
            return None