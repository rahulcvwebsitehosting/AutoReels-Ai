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
    - **CRITICAL - Topic Anchoring:** Every visual keyword MUST include the topic's 
      name or context. For example, if the topic is "Madurai culture", search 
      "Madurai Meenakshi temple" not just "temple", "Madurai street food" not 
      just "street food". This ensures stock footage is specific to the subject.

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

    def refine_script(self, user_text, topic):
        print(f"[Script] Understanding and refining your script...")
        word_count = len(user_text.split())
        length_note = ""
        if word_count > 500:
            length_note = f"""
    NOTE: The user's script is {word_count} words, which is too long for a single 
    YouTube Short (max ~60 seconds / ~150 words of narration). You MUST:
    - Summarize and condense the most important parts.
    - Prioritize the hook, key facts, and the twist/outro.
    - Cut repetitive or次要 details.
    - Output exactly 8-9 scenes that cover the essential story.
    """
        prompt = f"""
    You are a professional script editor for a high-retention "Edutainment" YouTube Shorts channel.
    Topic: {topic}

    A user has written a script below. Your job is to:
    1. Understand the story they want to tell.
    2. Fix any grammar, tone, or pacing issues.
    3. Restructure into well-flowing scenes (Hook -> Context -> Mechanism -> Twist -> Outro).
    4. Generate appropriate Pexels-optimised search terms for each scene.
    5. Keep the user's original story, facts, and narrative intact — do not change the core content.

    ### LENGTH CONSTRAINT:
    A YouTube Short has ~40-60 seconds of narration, roughly 8-9 short scenes.
    {length_note}
    If the source fits in 8-9 scenes, use it fully. If not, prioritize the 
    most engaging parts — the hook, the key revelation, and the strong outro.

    ### RULES:
    - **Perspective:** Strictly **3rd Person** ("Scientists found...", "The ocean hides..."). Convert any 1st/2nd person to 3rd.
    - **Tone:** Engaging, fast-paced, logical. No fluff.
    - **Structure:** 8-9 Scenes.
    - **Flow:** Hook -> Context -> Mechanism -> Twist -> Outro.
    - For EVERY scene, provide TWO distinct search terms:
      - **visual_1:** Matches the *start* of the sentence.
      - **visual_2:** Matches the *end* of the sentence or provides a reaction/context.
    - **Strictly Literal:** If the text is "The economy crashed," do NOT search "sad man". Search "Stock market red chart".
    - **CRITICAL - Topic Anchoring:** Every visual keyword MUST include the topic's 
      name or context. For example, if the topic is "Madurai culture", search 
      "Madurai Meenakshi temple" not just "temple", "Madurai street food" not 
      just "street food". This ensures stock footage is specific to the subject.

    ### USER'S SCRIPT:
    {user_text}

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
            print("[ERROR] Error parsing refined script JSON. Raw output:")
            print(clean_text)
            return None

    def expand_script(self, user_text, topic):
        print(f"[Script] Expanding your ideas into a full script...")
        word_count = len(user_text.split())
        length_note = ""
        if word_count > 500:
            length_note = f"""
    NOTE: The user's material is {word_count} words, which is too long for a
    single YouTube Short. Select the best ideas and condense them into 
    8-9 scenes that capture the essence.
    """
        prompt = f"""
    You are the lead scriptwriter for a high-retention "Edutainment" YouTube Shorts channel.
    Topic: {topic}

    A user has provided their rough ideas below. Expand them into a polished
    8-9 scene script following the exact format required.

    ### LENGTH CONSTRAINT:
    A YouTube Short has ~40-60 seconds of narration, roughly 8-9 short scenes.
    {length_note}
    If the source fits, use it fully. If it's too long, pick the best ideas
    and condense them into a tight, engaging narrative.

    ### RULES:
    - **Perspective:** Strictly **3rd Person** ("Scientists found...", "The ocean hides...").
    - **Tone:** Engaging, fast-paced, logical. No fluff.
    - **Structure:** 8-9 Scenes total.
    - **Flow:** Hook -> Context -> Mechanism (How it works) -> Twist -> Outro.
    - For EVERY scene, provide TWO distinct search terms:
      - **visual_1:** Matches the *start* of the sentence.
      - **visual_2:** Matches the *end* of the sentence or provides a reaction/context.
    - **Strictly Literal:** If the text is "The economy crashed," do NOT search "sad man". Search "Stock market red chart".
    - **CRITICAL - Topic Anchoring:** Every visual keyword MUST include the topic's 
      name or context. For example, if the topic is "Madurai culture", search 
      "Madurai Meenakshi temple" not just "temple", "Madurai street food" not 
      just "street food". This ensures stock footage is specific to the subject.

    Keep the feel and direction of the user's ideas, but improve structure,
    pacing, and visual hooks.

    ### USER'S IDEAS:
    {user_text}

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
