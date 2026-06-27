import json
from dotenv import load_dotenv
from modules.llm import get_llm_client

load_dotenv()

class ContentBrain:
    def __init__(self, provider_id=None):
        self.llm = get_llm_client(provider_id)

    def get_trending_topic(self):
        prompts = "Give me 1 specific, viral, and engaging topic for a Short Documentary. It should be a 'Engaging Did you know' fact or a 'Fun/intriguing Engaging News'. return ONLY the topic name."
        topic = self.llm.generate(prompts)
        print(f"[Topic] {topic}")
        return topic

    def generate_script(self, topic):
        print(f"[Script] Writing script for: {topic}...")
        prompt = f"""
    You are the lead scriptwriter for a high-retention "Edutainment" YouTube Shorts channel.
    Topic: {topic}

    ### GOAL:
    Create a script where every sentence has a "Visual Switch". 
    To keep retention high, we need TWO different stock videos for every single scene.

    ### 1. SCRIPT REQUIREMENTS (The Voiceover):
    - **Perspective:** Strictly **3rd Person** ("Scientists found...", "The ocean hides...").
    - **Tone:** Engaging, fast-paced, logical. No fluff.
    - **Structure:** 8-9 Scenes total.
    - **Flow:** Hook -> Context -> Mechanism (How it works) -> Twist -> Outro.

    ### 2. VISUAL REQUIREMENTS (Dual Visuals):
    - For EVERY scene, provide TWO distinct search terms:
      - **visual_1:** Matches the *start* of the sentence.
      - **visual_2:** Matches the *end* of the sentence or provides a reaction/context.
    - **Strictly Literal:** If the text is "The economy crashed," do NOT search "sad man". Search "Stock market red chart".

    ### OUTPUT FORMAT (Strict JSON):
    [
        {{
            "id": 1,
            "text": "In 1995, fourteen wolves were released into Yellowstone Park, and they changed the rivers.",
            "visual_1": "wolves running snow aerial",
            "visual_2": "river flowing forest drone",
            "mood": "intriguing" 
        }},
        {{
            "id": 2,
            "text": "It sounds impossible, but the biology is actually simple math.",
            "visual_1": "person shocked looking at camera",
            "visual_2": "blackboard math equations chalk",
            "mood": "educational"
        }}
    ]
    """

        response = self.llm.generate(prompt)
        clean_text = response.replace('```json', '').replace('```', '').strip()

        try:
            script_data = json.loads(clean_text)
            return script_data
        except json.JSONDecodeError:
            print("[ERROR] Error parsing JSON. Raw output:")
            print(clean_text)
            return None

    @staticmethod
    def parse_manual_script(text):
        clean = text.replace('```json', '').replace('```', '').strip()
        try:
            data = json.loads(clean)
            if not isinstance(data, list):
                raise ValueError("Script must be a JSON array of scenes.")
            for i, scene in enumerate(data):
                if not all(k in scene for k in ("id", "text", "visual_1", "visual_2")):
                    raise ValueError(
                        f"Scene {i} is missing one of: id, text, visual_1, visual_2"
                    )
            return data
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[ERROR] Invalid script format: {e}")
            return None

    def expand_script(self, user_script, topic):
        print(f"[Script] Expanding your ideas into a full script...")
        user_json = json.dumps(user_script, indent=2)
        prompt = f"""
    You are the lead scriptwriter for a high-retention "Edutainment" YouTube Shorts channel.
    Topic: {topic}

    A user has provided their rough ideas below. Expand them into a polished
    8-9 scene script following the exact format required.

    ### RULES:
    - **Perspective:** Strictly **3rd Person** ("Scientists found...", "The ocean hides...").
    - **Tone:** Engaging, fast-paced, logical. No fluff.
    - **Structure:** 8-9 Scenes total.
    - **Flow:** Hook -> Context -> Mechanism (How it works) -> Twist -> Outro.
    - For EVERY scene, provide TWO distinct search terms:
      - **visual_1:** Matches the *start* of the sentence.
      - **visual_2:** Matches the *end* of the sentence or provides a reaction/context.
    - **Strictly Literal:** If the text is "The economy crashed," do NOT search "sad man". Search "Stock market red chart".

    Keep the feel and direction of the user's ideas, but improve structure,
    pacing, and visual hooks.

    ### USER'S IDEAS:
    {user_json}

    ### OUTPUT FORMAT (Strict JSON):
    [
        {{
            "id": 1,
            "text": "Your scene text here.",
            "visual_1": "search term for first half",
            "visual_2": "search term for second half",
            "mood": "intriguing | educational | ominous | mysterious"
        }}
    ]
    """

        response = self.llm.generate(prompt)
        clean_text = response.replace('```json', '').replace('```', '').strip()

        try:
            script_data = json.loads(clean_text)
            return script_data
        except json.JSONDecodeError:
            print("[ERROR] Error parsing expanded script JSON. Raw output:")
            print(clean_text)
            return None
