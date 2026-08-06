"""Script to Dataset Converter for AI Director"""
import os
import json
import re
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ScriptConverter:
    """Class to handle script conversion operations"""
    
    def __init__(self):
        """Initialize converter"""
        # Scene tracking
        self.scene_counter = 1
        self.shot_counter = 1
        self.image_counter = 1
        self.current_scene = None
        self.scenes = []
        
        # Setup logging
        logging.info("Initialized ScriptConverter")

    def clean_scene_text(self, text: str) -> str:
        """Clean up scene text for better parsing"""
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove multiple empty lines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove page numbers and header/footer content
        text = re.sub(r'\n\s*\d+\.?\s*\n', '\n', text)
        text = re.sub(r'\n\s*\([Cc]ontinued\)\s*\n', '\n', text)
        
        # Fix common formatting issues while preserving indentation
        lines = []
        for line in text.split('\n'):
            if line.strip():
                # Keep original indentation
                indent = re.match(r'^(\s*)', line).group(1)
                # Clean the line content but preserve indentation
                clean_line = line.strip()
                clean_line = re.sub(r'\s*\(\s*', ' (', clean_line)
                clean_line = re.sub(r'\s*\)\s*', ') ', clean_line)
                clean_line = re.sub(r'\s*--\s*', ' -- ', clean_line)
                clean_line = re.sub(r'\s+', ' ', clean_line)
                lines.append(indent + clean_line)
            else:
                lines.append('')
        
        text = '\n'.join(lines)
        
        # Remove common script markup but preserve FADE IN/OUT when at start of script
        text = re.sub(r'\(MORE\)|\(CONTINUED\)|\(cont\'d\)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'(?<!^)(?:FADE IN:?|FADE OUT\.?|CUT TO:?|DISSOLVE TO:?)', '', text)
        
        # Clean up character cues
        text = re.sub(r'\((V\.O\.)\)', '(V.O.)', text)  # Standardize voice-over
        text = re.sub(r'\((O\.S\.)\)', '(O.S.)', text)  # Standardize off-screen
        
        return text.strip()

    def detect_scene_boundaries(self, text: str) -> List[str]:
        """Split text into scenes based on scene headers"""
        # First, clean up the text
        text = self.clean_scene_text(text)
        
        # Split into lines and look for scene headers
        scenes = []
        current_scene = []
        
        # Scene header patterns
        scene_patterns = [
            r'^(?:INT\.|EXT\.|INT/EXT\.|INTERIOR|EXTERIOR)\s*[A-Z0-9\s\-\_\/\'\,\.\(\)]+(?:\s*[-—]\s*|\s+)(?:DAY|NIGHT|MORNING|EVENING|DAWN|DUSK|CONTINUOUS|LATER|SAME)?',
            r'^SCENE\s+\d+[\.:]\s*[A-Z0-9\s\-\_\/\'\,]+',
            r'^\d+\s*[\.:]?\s*(?:INT\.|EXT\.|INT/EXT\.)\s+[A-Z0-9\s\-\_\/\'\,]+',
            r'^[A-Z][A-Z\s\-\_\/\'\,]+(?:\s*[-—]\s*|\s+)(?:DAY|NIGHT|MORNING|EVENING|CONTINUOUS)?',
            r'^EXT\s+[A-Z][A-Z0-9\s\-\_\/\'\,\.\(\)]+\s*(?:[-—]\s*)?'  # Special pattern for "EXT A SENTRY TOWER" format
        ]
        
        # Compile patterns
        scene_start = re.compile('|'.join(f'(?:{p})' for p in scene_patterns))
        
        # Process each line
        lines = text.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                i += 1
                continue
                
            # Check for scene header (allow for indented headers)
            original_line = lines[i]  # Get the original line with indentation
            if original_line.lstrip().startswith(('INT.', 'EXT.', 'INT/EXT.', 'INTERIOR', 'EXTERIOR')):
                # Save previous scene if exists
                if current_scene:
                    scene_text = '\n'.join(current_scene).strip()
                    if len(scene_text) > 10:  # Minimum meaningful scene length
                        scenes.append(scene_text)
                    current_scene = []
                
                # Start new scene
                current_scene = [original_line]
            else:
                if current_scene:  # Only add lines if we've started a scene
                    current_scene.append(original_line)  # Keep the original line with indentation
            
            i += 1
        
        # Add final scene
        if current_scene:
            scene_text = '\n'.join(current_scene).strip()
            if len(scene_text) > 10:
                scenes.append(scene_text)
        
        # If no scenes were found but we have significant text content,
        # treat the whole script as one scene (fallback)
        if not scenes and text.strip():
            logging.warning("No scene headers found. Treating entire script as one scene.")
            scenes = [text.strip()]
        
        logging.info(f"Detected {len(scenes)} scenes")
        return scenes

    def extract_scene_elements(self, scene_text: str) -> Dict:
        """Extract key elements from a scene"""
        try:
            if not isinstance(scene_text, str):
                raise ValueError("Scene text must be a string")
            
            if not scene_text.strip():
                raise ValueError("Scene text is empty")
            
            # Clean up the text first
            scene_text = self.clean_scene_text(scene_text)
            lines = scene_text.split('\n')
            
            # Extract location and time from first line
            first_line = lines[0].strip() if lines else ""
            location = "Unknown Location"
            time_of_day = "day"
            
            # Scene heading patterns
            heading_pattern = re.compile(
                r'^(?:INT\.|EXT\.|INT/EXT\.|INTERIOR|EXTERIOR)\s*[.|-]?\s*'
                r'([^-—]*?)'  # Location
                r'(?:\s*[-—]\s*'  # Separator
                r'(DAY|NIGHT|MORNING|EVENING|DAWN|DUSK|CONTINUOUS|LATER|SAME TIME))?$',  # Time
                re.IGNORECASE
            )
            
            # Parse the scene heading
            if first_line:
                # Remove common scene prefixes
                first_line = re.sub(r'^(?:FADE IN:|CUT TO:|DISSOLVE TO:)\s*', '', first_line)
                # Handle scene headers with EXT/INT
                heading_match = re.match(
                    r'(?:INT\.|EXT\.|INT/EXT\.|INTERIOR|EXTERIOR)\s*[-.]?\s*'
                    r'([^-]*?)(?:\s*[-—]\s*'  # Location
                    r'(DAY|NIGHT|MORNING|EVENING|DAWN|DUSK|CONTINUOUS|LATER|SAME))?$',  # Time
                    first_line,
                    re.IGNORECASE
                )
                if heading_match:
                    location = heading_match.group(1).strip().upper()
                    if heading_match.group(2):
                        time_of_day = heading_match.group(2).lower()
                else:
                    # Try simpler format (e.g., "EXT A SENTRY TOWER")
                    simple_match = re.match(r'(?:INT\.|EXT\.|INT/EXT\.)\s+(.+?)$', first_line)
                    if simple_match:
                        location = simple_match.group(1).strip().upper()
            
            # Regular expressions for character and dialogue detection
            character_line = re.compile(r'^[\s]{0,20}([A-Z][A-Z0-9\'\s\-]+?)(?:\s*\([^)]*\))?$')
            dialogue_line = re.compile(r'^[\s]{15,}(?!\s*(?:INT\.|EXT\.|CUT TO:|FADE IN:|DISSOLVE TO:|\())(.+)$')
            character_name = re.compile(r'(?:^|\s|\()([A-Z][A-Z\'\s\-]+)(?:\b|\'S|\s|\))')  # For finding names in action lines
            action_prop = re.compile(r'(?:the|a|an)\s+([a-zA-Z0-9\'\s\-]+)', re.IGNORECASE)
            
            # Lists to store scene elements
            characters = set()
            dialogues = []
            current_character = None
            current_dialogue = []
            parenthetical = None
            
            # Words that shouldn't be considered character names or props
            unwanted_words = {
                'INT', 'EXT', 'INT/EXT', 'INTERIOR', 'EXTERIOR', 'CONTINUED', 'SCENE',
                'CUT TO', 'FADE IN', 'FADE OUT', 'DISSOLVE TO', 'BACK TO', 'FLASHBACK',
                'DAY', 'NIGHT', 'MORNING', 'EVENING', 'CONTINUOUS', 'LATER', 'SAME',
                'THE', 'AND', 'BUT', 'FOR', 'WITH', 'ABOUT', 'AROUND', 'ABOVE', 'BELOW',
                'UNDER', 'OVER', 'INTO', 'ONTO', 'THIS', 'THAT', 'THERE', 'HERE', 'WHERE',
                'WHEN', 'WHAT', 'WHO', 'HEAR', 'SEE', 'WATCH', 'LOOK', 'VIEW',
                'ANGLE ON', 'WIDE SHOT', 'CLOSE ON', 'POV', 'THE END', 'CREDIT',
                'CAMERA', 'ANGLE', 'PAN', 'WIDE', 'CLOSE', 'MOVING', 'TRACKING',
                'SUBTITLE', 'CUT', 'TITLE', 'TITLES', 'ROLL', 'CREDITS', 'HIGH', 'LOW',
                'THE', 'AND', 'BAND', 'TOURISTS', 'DAY-CAMPERS',
                'ROOM', 'OFFICE', 'STREET', 'ROAD', 'CORRIDOR', 'ALLEY',
                'DOOR', 'WINDOW', 'FLOOR', 'WALL', 'STAIRS', 'HALLWAY',
                'STATION', 'BASE', 'FENCE', 'LINE', 'CLUB', 'BAR',
                'A', 'AN', 'HIS', 'HER', 'THEIR', 'ITS', 'OUR', 'YOUR', 'MY',
            }
            
            # Lists to store scene elements
            characters = set()
            dialogues = []
            current_character = None
            current_dialogue = []
            parenthetical = None
            action_lines = []  # Initialize action_lines list
            
            # Process each line for characters and dialogue
            for i, line in enumerate(lines[1:], 1):  # Skip first line (scene heading)
                original_line = line
                line = line.strip()
                if not line:
                    continue
                
                # Check if line starts with significant indentation (action description)
                if original_line.startswith('               '):
                    if not current_character:  # Only add to action if not in dialogue
                        action_lines.append(line)
                    continue
                
                # Check for character name
                line_stripped = line.strip()
                char_match = character_line.match(original_line) if original_line else None
                
                # Add debug logging
                if line_stripped and len(line_stripped) > 2 and not any(word in line_stripped for word in unwanted_words):
                    logging.info(f"Checking line as character: '{original_line}' - Match: {bool(char_match)}")
                    
                # Check if this could be a character name
                if char_match and not any(word in line_stripped for word in unwanted_words):
                    # Extract character name and any parenthetical
                    full_name = line_stripped
                    paren_start = full_name.find('(')
                    if paren_start != -1:
                        name = full_name[:paren_start].strip()
                        paren = full_name[paren_start:].strip('()')
                    else:
                        name = full_name
                        paren = None
                    
                    # Clean up character name
                    # Remove possessive 's if present
                    name = re.sub(r'\'s$', '', name)
                    
                    # Split into words and filter out articles/determiners at start
                    name_words = name.split()
                    while name_words and name_words[0] in ['A', 'AN', 'THE']:
                        name_words = name_words[1:]
                    
                    # Skip if no words left after filtering
                    if not name_words:
                        continue
                        
                    # Rejoin filtered words
                    name = ' '.join(name_words)
                    
                    # Check for common location patterns that might be mistaken for characters
                    if (any(loc in name for loc in ['ROOM', 'OFFICE', 'STREET', 'CORRIDOR', 'BUILDING', 
                                                  'DOOR', 'WINDOW', 'FLOOR', 'WALL', 'COURTROOM']) or
                        name.endswith(('BUILDING', 'ROOM', 'OFFICE', 'STREET', 'CORRIDOR'))):
                        continue
                    
                    if (len(name) > 1 and 
                        all(w.isupper() for w in name_words) and  # Names should be all uppercase
                        not name.isdigit() and 
                        not any(word in name for word in unwanted_words) and
                        len(name_words) <= 3 and  # Character names are typically 1-3 words
                        len(name_words[0]) > 1 and  # First word should be at least 2 letters
                        not any(name.endswith(suffix) for suffix in ['ROOM', 'OFFICE', 'STREET', 'HALL'])):  # Additional location check
                        
                        # Save previous dialogue if any
                        if current_character and current_dialogue:
                            dialogues.append({
                                "character": current_character,
                                "dialogue": ' '.join(current_dialogue).strip(),
                                "parenthetical": parenthetical
                            })
                        
                        # Start new dialogue
                        current_character = name
                        characters.add(current_character)
                        current_dialogue = []
                        parenthetical = paren
                        continue
                
                # Check for dialogue or parenthetical
                if current_character:
                    # Check for parenthetical
                    if line_stripped.startswith('(') and line_stripped.endswith(')'):
                        parenthetical = line_stripped[1:-1].strip()
                    # Check for dialogue (must not look like a scene heading or character name)
                    elif dialogue_line.match(line_stripped):
                        if not any(line_stripped.startswith(w) for w in unwanted_words):
                            current_dialogue.append(line_stripped)
            
            # Add the last dialogue if any
            if current_character and current_dialogue:
                dialogues.append({
                    "character": current_character,
                    "dialogue": ' '.join(current_dialogue).strip(),
                    "parenthetical": parenthetical
                })
            
            # Extract characters from action lines
            seen_chars = {c.replace("'s", "") for c in characters}  # Track characters without 's
            for line in action_lines:
                # Skip if line is too short
                if len(line) < 5:
                    continue
                
                # Look for character names in action lines (ignoring possessive forms)
                for match in character_name.finditer(line):
                    name = match.group(1)
                    name = re.sub(r"'s$", "", name)  # Remove possessive
                    
                    # Skip names that are lone articles or prepositions
                    if name in ['A', 'AN', 'THE'] or name in unwanted_words:
                        continue
                    
                    # Skip if we've seen this character before (without 's)
                    if name in seen_chars:
                        continue
                        
                    # Validate potential character names from action
                    name_words = name.split()
                    
                    # Remove leading articles
                    if len(name_words) > 1 and name_words[0] in ['A', 'THE', 'AN']:
                        name_words = name_words[1:]
                        name = ' '.join(name_words)
                    
                    if (len(name) > 1 and 
                        all(w.isupper() for w in name_words) and  # Names should be all uppercase
                        not name.isdigit() and 
                        not any(word in name for word in unwanted_words) and
                        len(name_words) <= 3 and  # Character names are typically 1-3 words
                        len(name_words[0]) > 1):  # First word should be at least 2 letters
                        
                        characters.add(name)
                        seen_chars.add(name)
                for match in character_name.finditer(line):
                    name = match.group(1).strip()
                    if (len(name) > 1 and
                        not any(word in name for word in unwanted_words) and
                        len(name.split()) <= 3):  # Character names are typically 1-3 words
                        characters.add(name)
            
            # Extract props from action lines
            props = set()
            
            # Process action lines for props
            for line in action_lines:
                # Skip if line is too short
                if len(line) < 5:
                    continue
                    
                # Look for props with verbs
                prop_patterns = [
                    r'(?:holds?|carries?|picks? up|grabs?|puts? down|using|with|sees?|looking at|points? (?:at|to)|opens?|closes?|wearing|puts? on|takes? off|carrying|holding)\s+(?:a|an|the|his|her|their)\s+([a-zA-Z][^.,!?()]+)',
                    r'(?:a|an|the)\s+([a-zA-Z][^.,!?()]+?)(?:\s+(?:is|sits?|rests?|lies?|stands?|appears?|drops?|falls?|moves?|slides?|slips?))',
                    r'(?:on|at|by|near|beside)\s+(?:a|an|the)\s+([a-zA-Z][^.,!?()]+)',
                    r'(?:the|a|an)\s+([a-zA-Z][^.,!?()]+?)(?:\s+(?:on|in|at|by|near|beside))'
                ]
                
                for pattern in prop_patterns:
                    prop_matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in prop_matches:
                        prop = match.group(1).strip().lower()
                        if len(prop) > 2 and not any(word.lower() in prop for word in unwanted_words):
                            props.add(prop)
                
                # Add found props
                for match in prop_matches:
                    prop = match.group(1).strip().lower()
                    if len(prop) > 2 and not any(word.lower() in prop for word in unwanted_words):
                        props.add(prop)
            
            # Process dialogues to add emotions
            processed_dialogues = []
            for dialogue in dialogues:
                emotion = self.analyze_emotion(dialogue.get('parenthetical', ''), dialogue['dialogue'])
                processed_dialogues.append({
                    "character": dialogue["character"],
                    "dialogue": dialogue["dialogue"],
                    "emotion": emotion["type"],
                    "intensity": emotion["intensity"],
                    "tone": emotion["tone"]
                })
            
            # Log extraction results
            logging.info(f"Scene breakdown - Location: {location}, Characters: {len(characters)}, "
                      f"Props: {len(props)}, Dialogues: {len(processed_dialogues)}")
            
            return {
                "location": location,
                "time_of_day": time_of_day,
                "characters": sorted(list(characters)),
                "props": sorted(list(props)),
                "dialogues": processed_dialogues
            }
            
        except Exception as e:
            logging.error(f"Error extracting scene elements: {str(e)}")
            raise

    def analyze_emotion(self, parenthetical: str, text: str) -> Dict:
        """Analyze emotion from parenthetical and dialogue text"""
        emotion_keywords = {
            "angry": {"type": "anger", "intensity": 8, "tone": "intense"},
            "happy": {"type": "happiness", "intensity": 7, "tone": "upbeat"},
            "sad": {"type": "sadness", "intensity": 6, "tone": "somber"},
            "afraid": {"type": "fear", "intensity": 7, "tone": "tense"},
            "surprised": {"type": "surprise", "intensity": 6, "tone": "dramatic"},
            "laughing": {"type": "happiness", "intensity": 8, "tone": "joyful"},
            "crying": {"type": "sadness", "intensity": 7, "tone": "emotional"},
            "shouting": {"type": "anger", "intensity": 9, "tone": "aggressive"},
            "whispering": {"type": "mystery", "intensity": 4, "tone": "secretive"},
            "nervous": {"type": "anxiety", "intensity": 5, "tone": "uneasy"}
        }
        
        # Default emotion
        default_emotion = {"type": "neutral", "intensity": 5, "tone": "normal"}
        
        # Check parenthetical first
        if parenthetical:
            parenthetical_lower = parenthetical.lower()
            for keyword, emotion in emotion_keywords.items():
                if keyword in parenthetical_lower:
                    return emotion
        
        # Check dialogue text for emotional indicators
        text_lower = text.lower()
        exclamation_count = text.count('!')
        question_count = text.count('?')
        
        # Check for emotional keywords in the text
        for keyword, emotion in emotion_keywords.items():
            if keyword in text_lower:
                emotion = emotion.copy()
                if exclamation_count > 0:
                    emotion["intensity"] = min(10, emotion["intensity"] + exclamation_count)
                return emotion
        
        # Adjust default emotion based on punctuation
        if exclamation_count > 1:
            default_emotion["intensity"] = min(8, default_emotion["intensity"] + exclamation_count)
            default_emotion["tone"] = "intense"
        elif question_count > 1:
            default_emotion["type"] = "confusion"
            default_emotion["intensity"] = min(7, default_emotion["intensity"] + question_count - 1)
            default_emotion["tone"] = "uncertain"
        
        return default_emotion

    def generate_shots(self, scene_elements: Dict) -> List[Dict]:
        """Generate appropriate shots based on scene elements"""
        shots = []
        
        # Establishing shot for every scene
        shots.append({
            "type": "Establishing Shot",
            "description": f"Wide view of {scene_elements['location']}",
            "camera_movement": "Static/Slow Pan",
            "angle": "Wide",
            "lighting": f"Natural {scene_elements['time_of_day']} lighting"
        })
        
        # Character introductions
        for character in scene_elements['characters']:
            shots.append({
                "type": "Medium Shot",
                "description": f"Character: {character}",
                "camera_movement": "Static",
                "angle": "Eye Level",
                "lighting": "Key light with soft fill"
            })
        
        # Dialog coverage
        if len(scene_elements['dialogues']) > 0:
            # Two-shot for conversations
            if len(scene_elements['characters']) >= 2:
                shots.append({
                    "type": "Two Shot",
                    "description": "Conversation coverage",
                    "camera_movement": "Static",
                    "angle": "Eye Level",
                    "lighting": "Even lighting"
                })
            
            # Close-ups for emotional moments
            for dialogue in scene_elements['dialogues']:
                if dialogue['intensity'] > 6:
                    shots.append({
                        "type": "Close Up",
                        "description": f"Emotional moment: {dialogue['character']}",
                        "camera_movement": "Slow Push In",
                        "angle": "Slight Low",
                        "lighting": "Dramatic side lighting"
                    })
        
        # Prop shots
        if scene_elements['props']:
            shots.append({
                "type": "Insert Shot",
                "description": f"Detail of {', '.join(scene_elements['props'][:2])}",
                "camera_movement": "Static",
                "angle": "High Angle",
                "lighting": "Focused spot lighting"
            })
        
        return shots

    def convert_to_script_analysis(self, scenes_text: List[str]) -> Dict:
        """Convert scenes to script analysis format"""
        dataset = {"scenes": []}
        
        # Reset counters for new conversion
        self.scene_counter = 1
        
        for scene_text in scenes_text:
            try:
                elements = self.extract_scene_elements(scene_text)
                shots = self.generate_shots(elements)
                
                scene = {
                    "scene_number": self.scene_counter,
                    "location": elements["location"],
                    "time_of_day": elements["time_of_day"],
                    "characters": elements["characters"],
                    "props": elements["props"],
                    "dialogues": elements["dialogues"],
                    "shots": shots,
                    "summary": f"Scene {self.scene_counter}: {elements['location']} - {elements['time_of_day']}"
                }
                
                dataset["scenes"].append(scene)
                self.scene_counter += 1
                logging.info(f"Processed scene {self.scene_counter}")
                
            except Exception as e:
                logging.error(f"Error processing scene {self.scene_counter}: {str(e)}")
                continue
        
        return dataset

    def convert_to_shot_analysis(self, scenes_text: List[str]) -> Dict:
        """Convert scenes to shot analysis format"""
        dataset = {"scene_samples": []}
        
        for scene_text in scenes_text:
            try:
                elements = self.extract_scene_elements(scene_text)
                shots = self.generate_shots(elements)
                
                sample = {
                    "input": {
                        "location": elements["location"],
                        "time_of_day": elements["time_of_day"],
                        "characters": elements["characters"],
                        "props": elements["props"],
                        "emotions": [d["emotion"] for d in elements["dialogues"]]
                    },
                    "output": {
                        "shots": shots
                    }
                }
                
                dataset["scene_samples"].append(sample)
                
            except Exception as e:
                logging.error(f"Error in shot analysis: {str(e)}")
                continue
        
        return dataset

    def convert_to_image_generation(self, scenes_text: List[str]) -> Dict:
        """Convert scenes to image generation format"""
        dataset = {"image_samples": []}
        
        for scene_text in scenes_text:
            try:
                elements = self.extract_scene_elements(scene_text)
                shots = self.generate_shots(elements)
                
                for shot in shots:
                    prompt = (
                        f"{shot['type']} of {shot['description']} in {elements['location']}. "
                        f"Camera: {shot['camera_movement']}, {shot['angle']}. "
                        f"Lighting: {shot['lighting']}. Time: {elements['time_of_day']}"
                    )
                    
                    sample = {
                        "scene_context": {
                            "location": elements["location"],
                            "time_of_day": elements["time_of_day"],
                            "characters": elements["characters"],
                            "props": elements["props"],
                            "shot_type": shot["type"],
                            "camera": shot["camera_movement"],
                            "angle": shot["angle"],
                            "lighting": shot["lighting"]
                        },
                        "prompt": prompt,
                        "image_path": f"scene_{self.scene_counter}_shot_{self.shot_counter}.png"
                    }
                    
                    dataset["image_samples"].append(sample)
                    self.shot_counter += 1
                
                self.scene_counter += 1
                
            except Exception as e:
                logging.error(f"Error in image generation: {str(e)}")
                continue
        
        return dataset

def convert_script_file(input_file: str, output_dir: str):
    """Convert a script file to all dataset formats"""
    try:
        # Validate input file
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        logging.info(f"Reading script file: {input_file}")
        
        # Read script file with error handling for different encodings
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                script_text = f.read()
        except UnicodeDecodeError:
            logging.warning("UTF-8 decode failed, trying with cp1252 encoding")
            with open(input_file, 'r', encoding='cp1252') as f:
                script_text = f.read()
        
        if not script_text.strip():
            raise ValueError("Script file is empty")
        
        # Initialize converter
        converter = ScriptConverter()
        
        # Split into scenes
        logging.info("Detecting scene boundaries...")
        scenes = converter.detect_scene_boundaries(script_text)
        logging.info(f"Detected {len(scenes)} scenes")
        
        if not scenes:
            raise ValueError("No scenes detected in the script")
        
        # Convert to each format
        logging.info("Converting to script analysis format...")
        script_analysis = converter.convert_to_script_analysis(scenes)
        
        logging.info("Converting to shot analysis format...")
        shot_analysis = converter.convert_to_shot_analysis(scenes)
        
        logging.info("Converting to image generation format...")
        image_generation = converter.convert_to_image_generation(scenes)
        
        # Save datasets
        formats = {
            'script_analysis.json': script_analysis,
            'shot_analysis.json': shot_analysis,
            'image_generation.json': image_generation
        }
        
        for filename, data in formats.items():
            output_path = os.path.join(output_dir, filename)
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                logging.info(f"Saved {filename}")
            except Exception as e:
                logging.error(f"Error saving {filename}: {str(e)}")
                raise
                
    except Exception as e:
        logging.error(f"Error converting {input_file}: {str(e)}")
        raise

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Process single file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_dir = os.path.dirname(script_dir)
    
    # Setup paths
    input_file = os.path.join(script_dir, 'data', 'A_Few_Good_Men_Script.txt')
    output_dir = os.path.join(workspace_dir, 'datasets', 'a_few_good_men')
    
    print(f"\nInput file: {input_file}")
    print(f"Output directory: {output_dir}\n")
    
    try:
        print(f"Processing: {os.path.basename(input_file)}")
        convert_script_file(input_file, output_dir)
        print("\nConversion completed successfully!")
        print(f"Output files are in: {output_dir}")
        print("\nGenerated files:")
        print("- script_analysis.json")
        print("- shot_analysis.json")
        print("- image_generation.json")
    except Exception as e:
        print(f"Error converting file: {str(e)}")
        logging.error(f"Error details: {str(e)}")
        sys.exit(1)