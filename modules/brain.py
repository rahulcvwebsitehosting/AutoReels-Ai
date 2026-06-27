import json
import re
from dotenv import load_dotenv
from modules.llm import get_llm_client

load_dotenv()


def _extract_json(text):
    """Strip markdown fences and trailing content, return only the JSON."""
    cleaned = text.replace('```json', '').replace('```', '').strip()
    # Try array first
    start = cleaned.find('[')
    end = cleaned.rfind(']')
    if start != -1 and end != -1 and end > start:
        return cleaned[start:end+1]
    # Fallback: try object
    start = cleaned.find('{')
    end = cleaned.rfind('}')
    if start != -1 and end != -1 and end > start:
        return cleaned[start:end+1]
    return cleaned


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
    You are an investigative scriptwriter for a high-retention YouTube Shorts channel.

    Topic: {topic}

    ### YOUR JOB:
    Write a script that is FACT-BACKED, not generic. Every claim must include
    its source (e.g., "Amnesty International reported...", "The ICJ found...",
    "According to UN data..."). Do NOT make unsourced assertions.

    ### STRUCTURE:
    - Hook -> Context -> Evidence -> Counterpoint -> Outro
    - 8-9 scenes total
    - Strictly 3rd Person perspective
    - Fast-paced, engaging, no fluff

    ### VISUAL RULES (CRITICAL):
    Every scene has TWO visual keywords. These MUST be:
    1. **Reasoned** — directly tied to the specific claim in that scene.
       Example: if the text says "Amnesty International found apartheid",
       search "Amnesty International report cover" or "apartheid map".
       NOT generic "courtroom" or "people arguing".
    2. **Topic-anchored** — include the topic name/context.
    3. **Literal** — if text says "market crashed", search "stock market crash chart",
       not "sad man".
    4. **Pexels-searchable** — use concrete nouns, not abstract concepts.

    ### OUTPUT FORMAT (Strict JSON):
    [
        {{
            "id": 1,
            "text": "Fact-backed narration with source citation.",
            "visual_1": "specific keyword tied to this claim",
            "visual_2": "specific keyword tied to this claim",
            "mood": "intriguing | educational | ominous | mysterious | factual"
        }}
    ]

    IMPORTANT: Output ONLY the JSON array above. Do NOT add any text,
    notes, explanations, or summaries before or after the JSON.
    """

        try:
            response = self.llm.generate(prompt)
        except Exception as e:
            print(f"[ERROR] Script generation failed: {e}")
            return None
        clean_text = _extract_json(response)

        try:
            script_data = json.loads(clean_text)
            return script_data
        except json.JSONDecodeError:
            print(f"[ERROR] Script generation JSON error. Raw:")
            print(clean_text)
            return None

    def refine_script(self, user_text, topic):
        print(f"[Script] Understanding, extracting claims, and condensing...")
        word_count = len(user_text.split())
        length_note = ""
        if word_count > 300:
            length_note = f"""
    The user's document is {word_count} words. You MUST:
    - Extract EVERY distinct claim/fact from the document — do NOT drop any.
    - Condense each claim into 1 punchy sentence while preserving source attribution.
    - Group related claims into 8 scenes.
    - If you cannot fit all claims, prioritize the most impactful ones that 
      together tell a complete story, but note what was cut in a summary.
    """
        prompt = f"""
    You are an investigative script editor for a high-retention YouTube Shorts channel.

    Topic: {topic}

    A user has provided a research document below. Your job:
    1. Read and UNDERSTAND every claim in the document.
    2. Extract ALL distinct facts/arguments — do not cherry-pick only one side.
    3. Condense each claim into 1-2 punchy, source-backed sentences.
    4. The narration text MUST include the source for each claim (e.g., 
       "Amnesty International reported...", "The ICJ advisory opinion stated...", 
       "According to the UN Special Rapporteur...").
    5. Restructure into a tight 8-scene narrative.
    {length_note}

    ### LENGTH CONSTRAINT:
    YouTube Short = ~40-60 seconds narration. Every word must count.

    ### VISUAL RULES (CRITICAL):
    Every scene has TWO visual keywords. These MUST be:
    1. **Reasoned** — directly tied to the specific claim in that scene.
       Example: text about "UN finding apartheid" -> "UN report document" or
       "apartheid comparison map". NOT generic unrelated footage.
    2. **Topic-anchored** — include the topic name/context.
    3. **Literal** — match the specific noun in the text.
    4. **Pexels-searchable** — concrete nouns, not abstract concepts.

    ### RULES:
    - Perspective: Strictly 3rd Person.
    - Tone: Fast-paced, factual, no fluff.
    - Structure: 8 scenes. Flow: Hook -> Context -> Evidence -> Counterpoint -> Outro.
    - Keep the user's original claims intact — do not fabricate or exaggerate.

    ### USER'S DOCUMENT:
    {user_text}

    ### OUTPUT FORMAT (Strict JSON):
    [
        {{
            "id": 1,
            "text": "Source-backed narration sentence.",
            "visual_1": "keyword tied to this claim",
            "visual_2": "keyword tied to this claim",
            "mood": "intriguing | educational | ominous | mysterious | factual"
        }}
    ]

    IMPORTANT: Output ONLY the JSON array above. Do NOT add any text,
    notes, explanations, or summaries before or after the JSON.
    """

        try:
            response = self.llm.generate(prompt)
        except Exception as e:
            print(f"[ERROR] Script refinement failed: {e}")
            return None
        clean_text = _extract_json(response)

        try:
            script_data = json.loads(clean_text)
            return script_data
        except json.JSONDecodeError:
            print(f"[ERROR] Script refinement JSON error. Raw:")
            print(clean_text)
            return None

    def expand_script(self, user_text, topic):
        print(f"[Script] Expanding your ideas with research-backed script...")
        word_count = len(user_text.split())
        length_note = ""
        if word_count > 300:
            length_note = f"""
    The user's material is {word_count} words. Select the best ideas and 
    condense them into 8 scenes that tell a complete, source-backed story.
    """
        prompt = f"""
    You are an investigative scriptwriter for a high-retention YouTube Shorts channel.

    Topic: {topic}

    A user has provided their rough ideas below. Expand them into a polished,
    FACT-BACKED 8-scene script.

    ### YOUR JOB:
    - Take the user's ideas as inspiration.
    - Research and write each claim with source attribution.
    - If the user makes a claim, include its source (e.g., "According to the 
      UN...", "Human Rights Watch documented...").
    - Do NOT make unsourced assertions.
    {length_note}

    ### LENGTH CONSTRAINT:
    YouTube Short = ~40-60 seconds narration. Every word must count.

    ### VISUAL RULES (CRITICAL):
    Every scene has TWO visual keywords. These MUST be:
    1. **Reasoned** — directly tied to the specific claim in that scene.
    2. **Topic-anchored** — include the topic name/context.
    3. **Literal** — match the specific noun in the text.
    4. **Pexels-searchable** — concrete nouns, not abstract concepts.

    ### RULES:
    - Perspective: Strictly 3rd Person.
    - Tone: Fast-paced, factual, no fluff.
    - Structure: 8 scenes. Flow: Hook -> Context -> Evidence -> Counterpoint -> Outro.

    ### USER'S IDEAS:
    {user_text}

    ### OUTPUT FORMAT (Strict JSON):
    [
        {{
            "id": 1,
            "text": "Source-backed narration sentence.",
            "visual_1": "keyword tied to this claim",
            "visual_2": "keyword tied to this claim",
            "mood": "intriguing | educational | ominous | mysterious | factual"
        }}
    ]

    IMPORTANT: Output ONLY the JSON array above. Do NOT add any text,
    notes, explanations, or summaries before or after the JSON.
    """

        try:
            response = self.llm.generate(prompt)
        except Exception as e:
            print(f"[ERROR] Script expansion failed: {e}")
            return None
        clean_text = _extract_json(response)

        try:
            script_data = json.loads(clean_text)
            return script_data
        except json.JSONDecodeError:
            print(f"[ERROR] Script expansion JSON error. Raw:")
            print(clean_text)
            return None
