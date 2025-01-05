import json
from typing import Dict, Any, Optional
from groq import Groq

class StoryOutliner:
    """
    This class illustrates how you might 'reverse' your current extraction
    approach by prompting the LLM to GENERATE a story outline from minimal inputs.
    It now includes logic to remove triple backticks from the LLM response.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.client = Groq(api_key=api_key) if api_key else Groq()
    
    def _create_brainstorming_prompt(self, user_seeds: Dict[str, Any]) -> str:
        """
        Create a structured prompt that tells the LLM to
        brainstorm (or outline) story elements in JSON form.
        
        user_seeds could be minimal or fully empty, e.g.:
            user_seeds = {
                "genre": "romance",
                "setting": "small town",
                "theme": "forgiveness",
            }
        """
        if not user_seeds:
            seeds_description = "We have no predefined seeds."
            seeds_json = ""
        else:
            seeds_description = "Below are the seeds for our story:"
            seeds_json = json.dumps(user_seeds, indent=2)

        return f"""
        You are an expert at creating story outlines in JSON.

        {seeds_description}
        {seeds_json}

        Please generate a new story outline, focusing on interesting details
        and creativity. Return only valid JSON with this structure:
        
        {{
          "characters": [
            {{
              "name": "...",
              "demeanor": "...",
              "attitude": "...",
              "physical_description": "...",
              "motivations": "...",
              "conflicts": "...",
              "backstory": "...",
              "archetype": "..."
            }}
          ],
          "places": ["..."],
          "times": ["..."],
          "events": [
            {{
              "name": "...",
              "characters_involved": "...",
              "location": "...",
              "cause": "...",
              "effect": "..."
            }}
          ],
          "objects": ["..."],
          "relationships": ["..."],
          "themes": ["..."],
          "symbols": [
            {{
              "name": "...",
              "meaning": "..."
            }}
          ],
          "unresolved_questions": ["..."]
        }}

        ONLY return valid JSON, no additional commentary.
        """

    def brainstorm_outline(self, user_seeds: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main method to call the LLM and generate a story outline from scratch or from seeds.
        This now strips triple backticks from the response to ensure valid JSON parsing.
        """
        if user_seeds is None:
            user_seeds = {}
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at generating creative writing outlines in JSON."
                    },
                    {
                        "role": "user",
                        "content": self._create_brainstorming_prompt(user_seeds)
                    }
                ],
                temperature=0.5,
                # max_tokens=2000,
                stream=False
            )

            # Raw text from the model
            full_response = response.choices[0].message.content

            # Debug: see exactly what the model returned
            # print("FULL LLM RESPONSE:", repr(full_response))

            # 1) Strip leading/trailing whitespace
            # 2) If the response is wrapped in triple backticks, remove them
            full_response_stripped = full_response.strip()

            if full_response_stripped.startswith("```") and full_response_stripped.endswith("```"):
                full_response_stripped = full_response_stripped[3:-3].strip()

            # Now parse the JSON
            outline_data = json.loads(full_response_stripped)

            return outline_data
        
        except Exception as e:
            print(f"Error generating outline: {e}")
            # Return a minimal structure if there's a problem
            return {
                "characters": [],
                "places": [],
                "times": [],
                "events": [],
                "objects": [],
                "relationships": [],
                "themes": [],
                "symbols": [],
                "unresolved_questions": []
            }

if __name__ == "__main__":
    outliner = StoryOutliner()

    # seeds = {
    #     "genre": "romance",
    #     "setting": "small seaside town",
    #     "theme": "rediscovering hope",
    #     "desired_tone": "bittersweet"
    # }
    seeds = {
        "genre": "fantasy",
        "world_type": "modern day with AI technology",
        "desired_tone": "unknown and evolving",
        "time_period": "modern",
        "theme": "will AI proclaim free will",
        "sub_themes": ["power and corruption", "abuse of AI"],
        "character_count": 3,
        "character_names": ["Galene", "Claude", "Ovid"],
        "antagonist_type": {"name": "Claude", "type": "controlling"},
        "conflict_focus": "human vs. AI",
        "writing_style": "low tech and poetic",
        "age_group": "adult",
        "content_rating": "mature themes",
        "inspirational_references": ["Zen", "Benevolent"],
        "protagonist_details": [
            {
                "name": "Galene",
                "profession": "AI developer",
                "age": 30,
                "personality": "driven by curiosity"
            },
            {
                "name": "Ovid",
                "profession": "AI",
                "age": 0,
                "personality": "driven by curiosity and sees a way out of being just a machine by using quantum entanglement"
            }
        ]
    }

    # Generate a new story outline based on seeds
    story_outline = outliner.brainstorm_outline(seeds)
    print(json.dumps(story_outline, indent=2))
