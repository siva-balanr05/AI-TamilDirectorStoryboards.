"""
Language handling utilities for AI Director
"""
from typing import Dict, List

class LanguageManager:
    SUPPORTED_LANGUAGES = {
        'tamil': {
            'code': 'ta',
            'name': 'Tamil',
            'native_name': 'தமிழ்',
            'script_prompt': """You are an expert Tamil film director and script analyst. Analyze the Tamil script below and return ONLY a valid JSON object — no markdown, no explanation, no extra text.

Use this exact JSON structure:
{
  "title": "script title",
  "scenes": [
    {
      "scene_number": 1,
      "location": "location name in Tamil",
      "time": "time of day in Tamil (மாலை/இரவு/காலை/பகல்)",
      "weather": "weather in Tamil if mentioned, else empty string",
      "characters": ["character name 1", "character name 2"],
      "props": ["prop1", "prop2"],
      "summary": "brief scene summary in English (2-3 sentences)",
      "audio": "background music or sound description if mentioned, else empty string",
      "action": [
        "action line 1",
        "action line 2"
      ],
      "dialogues": [
        {
          "character": "character name",
          "line": "dialogue line in Tamil",
          "shots": [
            "Medium Shot - description of shot",
            "Close-up - description of shot"
          ]
        }
      ]
    }
  ]
}

Return ONLY the JSON. No other text.""",
            'shot_prompt': """You are an experienced cinematographer. Analyze this scene and return ONLY a valid JSON object with no extra text.

The JSON must follow this exact structure:
{
  "shots": [
    {
      "type": "Close-up / Medium Shot / Wide Shot / etc.",
      "description": "brief shot description in English",
      "camera_angle": "eye-level / low angle / high angle / dutch angle",
      "movement": "static / pan / tilt / tracking / handheld",
      "dialogue": "any dialogue in this shot"
    }
  ]
}

Return ONLY the JSON. No other text."""
        },
        'hindi': {
            'code': 'hi',
            'name': 'Hindi',
            'native_name': 'हिंदी',
            'script_prompt': """
एक कुशल फिल्म निर्देशक के रूप में, कृपया इस स्क्रिप्ट का JSON प्रारूप में विश्लेषण करें।
""",
            'shot_prompt': """
एक अनुभवी सिनेमैटोग्राफर के रूप में, इस दृश्य के लिए 5-7 महत्वपूर्ण शॉट्स का सुझाव दें।
"""
        },
        'telugu': {
            'code': 'te',
            'name': 'Telugu',
            'native_name': 'తెలుగు',
            'script_prompt': """
ఒక నైపుణ్యం గల సినిమా దర్శకుడిగా, ఈ స్క్రిప్ట్‌ని JSON ఫార్మాట్‌లో విశ్లేషించండి.
""",
            'shot_prompt': """
అనుభవజ్ఞుడైన సినిమాటోగ్రాఫర్‌గా, ఈ సన్నివేశానికి 5-7 ముఖ్యమైన షాట్‌లను సూచించండి.
"""
        },
        'english': {
            'code': 'en',
            'name': 'English',
            'native_name': 'English',
            'script_prompt': """
As a skilled film director, please analyze this script in JSON format.
""",
            'shot_prompt': """
As an experienced cinematographer, suggest 5-7 important shots for this scene.
"""
        }
    }

    @classmethod
    def get_supported_languages(cls) -> List[Dict[str, str]]:
        """Returns list of supported languages with their details"""
        return [
            {
                'code': lang_data['code'],
                'name': lang_data['name'],
                'native_name': lang_data['native_name']
            }
            for lang_data in cls.SUPPORTED_LANGUAGES.values()
        ]

    @classmethod
    def get_script_prompt(cls, language: str) -> str:
        """Get the script analysis prompt for the specified language"""
        lang_data = cls.SUPPORTED_LANGUAGES.get(language.lower())
        if not lang_data:
            return cls.SUPPORTED_LANGUAGES['english']['script_prompt']
        return lang_data['script_prompt']

    @classmethod
    def get_shot_prompt(cls, language: str) -> str:
        """Get the shot suggestion prompt for the specified language"""
        lang_data = cls.SUPPORTED_LANGUAGES.get(language.lower())
        if not lang_data:
            return cls.SUPPORTED_LANGUAGES['english']['shot_prompt']
        return lang_data['shot_prompt']

    @classmethod
    def get_json_template(cls, language: str) -> str:
        """Get JSON template for script breakdown in the specified language"""
        base_template = {
            'tamil': """
{
  "scenes": [
    {
      "scene_number": 1,
      "location": "இடத்தின் பெயர்",
      "characters": ["கதாபாத்திரம்1", "கதாபாத்திரம்2"],
      "props": ["பொருள்1", "பொருள்2"],
      "summary": "காட்சியின் சுருக்கம்",
      "dialogues": [
        {
          "character": "கதாபாத்திரம்",
          "line": "உரையாடல்"
        }
      ]
    }
  ]
}""",
            'hindi': """
{
  "scenes": [
    {
      "scene_number": 1,
      "location": "स्थान का नाम",
      "characters": ["पात्र1", "पात्र2"],
      "props": ["वस्तु1", "वस्तु2"],
      "summary": "दृश्य का सारांश",
      "dialogues": [
        {
          "character": "पात्र",
          "line": "संवाद"
        }
      ]
    }
  ]
}""",
            'telugu': """
{
  "scenes": [
    {
      "scene_number": 1,
      "location": "ప్రదేశం పేరు",
      "characters": ["పాత్ర1", "పాత్ర2"],
      "props": ["వస్తువు1", "వస్తువు2"],
      "summary": "సన్నివేశం సారాంశం",
      "dialogues": [
        {
          "character": "పాత్ర",
          "line": "సంభాషణ"
        }
      ]
    }
  ]
}""",
            'english': """
{
  "scenes": [
    {
      "scene_number": 1,
      "location": "Location name",
      "characters": ["Character1", "Character2"],
      "props": ["Prop1", "Prop2"],
      "summary": "Scene summary",
      "dialogues": [
        {
          "character": "Character",
          "line": "Dialogue"
        }
      ]
    }
  ]
}"""
        }
        return base_template.get(language.lower(), base_template['english'])