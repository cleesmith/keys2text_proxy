from typing import Dict, Set, Any, Optional, List
import json
import re
from groq import Groq

class EntityExtractor:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the EntityExtractor with an optional API key."""
        self.client = Groq(api_key=api_key) if api_key else Groq()

        # Updated entity store with new fields:
        self.entity_store = {
            "characters": {},  # Dictionary keyed by character name
            "places": set(),
            "times": set(),
            "events": [],  # Will store a list of event dicts
            "objects": set(),
            "relationships": set(),
            "themes": set(),
            "symbols": [],  # Will store a list of symbol dicts
            "unresolved_questions": []  # Will store a list of strings
        }

    def _create_extraction_prompt(self, text: str) -> str:
        """Create a structured prompt for the LLM to extract entities."""
        return f"""
        Please analyze the following story and extract entities with extra details 
        that could help a writer. Provide them in a JSON object with these keys:

        - characters: (array of objects)
            - name
            - demeanor
            - attitude
            - physical_description
            - motivations
            - conflicts
            - backstory
            - archetype
        - places: (array of strings)
        - times: (array of strings)
        - events: (array of objects)
            - name
            - characters_involved
            - location
            - cause
            - effect
        - objects: (array of strings)
        - relationships: (array of strings)
        - themes: (array of strings)
        - symbols: (array of objects)
            - name
            - meaning
        - unresolved_questions: (array of strings)

        ONLY return JSON. Do not include any extra commentary.

        Story to analyze:
        {text}
        """

    def _process_streaming_response(self, response) -> str:
        """Process the streaming response from the LLM and return the complete content."""
        full_response = ""
        for chunk in response:
            if hasattr(chunk.choices[0], 'delta') and chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
        return full_response

    def _extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """Extract and parse JSON from the LLM response text."""
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if not json_match:
            raise ValueError("No JSON structure found in response")
        
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            # Return an empty structure if JSON can't be parsed
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

    def _update_entity_store(self, extracted_data: Dict[str, Any]) -> None:
        """Update the entity store with newly extracted data."""
        # ----------------------
        # 1) Handle CHARACTERS
        # ----------------------
        if "characters" in extracted_data:
            for character in extracted_data["characters"]:
                name = character.get("name", "").strip()
                if not name:
                    continue  # Skip if no valid name

                # If character does NOT exist in store, create a new entry
                if name not in self.entity_store["characters"]:
                    self.entity_store["characters"][name] = {
                        "demeanor": character.get("demeanor", "unknown"),
                        "attitude": character.get("attitude", "unknown"),
                        "physical_description": character.get("physical_description", "unknown"),
                        "motivations": character.get("motivations", "unknown"),
                        "conflicts": character.get("conflicts", "unknown"),
                        "backstory": character.get("backstory", "unknown"),
                        "archetype": character.get("archetype", "unknown")
                    }
                else:
                    # Update existing character info if new details are found
                    current_char = self.entity_store["characters"][name]
                    for key in [
                        "demeanor",
                        "attitude",
                        "physical_description",
                        "motivations",
                        "conflicts",
                        "backstory",
                        "archetype"
                    ]:
                        # Only update if not "unknown" or if new data is more informative
                        new_val = character.get(key)
                        if new_val and new_val != "unknown":
                            current_char[key] = new_val

        # ----------------------
        # 2) Handle SIMPLE FIELDS (places, times, objects, relationships, themes)
        # ----------------------
        # Just union all items into the respective sets
        for category in ["places", "times", "objects", "relationships", "themes"]:
            if category in extracted_data and isinstance(extracted_data[category], list):
                self.entity_store[category].update(extracted_data[category])

        # ----------------------
        # 3) Handle EVENTS (list of objects)
        # ----------------------
        if "events" in extracted_data and isinstance(extracted_data["events"], list):
            for event in extracted_data["events"]:
                # An example structure: 
                # {
                #   "name": "Delta finds a half-full bucket",
                #   "characters_involved": ["Delta"],
                #   "location": "the swamp",
                #   "cause": "Heard a strange noise",
                #   "effect": "Delta obtains dinner"
                # }
                # You can add logic to merge events if needed; 
                # here we just append new events to the list.
                self.entity_store["events"].append(event)

        # ----------------------
        # 4) Handle SYMBOLS (list of objects)
        # ----------------------
        if "symbols" in extracted_data and isinstance(extracted_data["symbols"], list):
            for symbol in extracted_data["symbols"]:
                # E.g., symbol = {"name": "rusty bucket", "meaning": "represents survival"}
                self.entity_store["symbols"].append(symbol)

        # ----------------------
        # 5) Handle UNRESOLVED QUESTIONS (list of strings)
        # ----------------------
        if "unresolved_questions" in extracted_data and isinstance(extracted_data["unresolved_questions"], list):
            self.entity_store["unresolved_questions"].extend(extracted_data["unresolved_questions"])

    def process_text(self, text: str) -> None:
        """Process a text and update the entity store."""
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an expert at extracting structured data from text."},
                    {"role": "user", "content": self._create_extraction_prompt(text)}
                ],
                temperature=0.2,  # Lower temperature for more consistent structured output
                max_tokens=32768,
                stream=True
            )

            # Process the streaming response
            full_response = self._process_streaming_response(response)
            
            # Extract and parse the JSON data
            extracted_data = self._extract_json_from_response(full_response)
            
            # Update the entity store with the new data
            self._update_entity_store(extracted_data)
            
        except Exception as e:
            print(f"Error processing text: {e}")

    def get_consolidated_entities(self) -> Dict[str, Any]:
        """
        Return the consolidated entity store in a JSON-serializable format.
        Ensure we convert sets to lists so the JSON serialization doesn't fail.
        """
        return {
            "characters": self.entity_store["characters"],
            "places": list(self.entity_store["places"]),
            "times": list(self.entity_store["times"]),
            "events": self.entity_store["events"],  # Already a list
            "objects": list(self.entity_store["objects"]),
            "relationships": list(self.entity_store["relationships"]),
            "themes": list(self.entity_store["themes"]),
            "symbols": self.entity_store["symbols"],  # Already a list
            "unresolved_questions": self.entity_store["unresolved_questions"]
        }

if __name__ == "__main__":
    extractor = EntityExtractor()
    
    story = """
    I went in for an oil change and came out with a change of life. Spoiler alert; never marry your mechanic! After the jump-start of a honeymoon, he and his gym bag moved into my house. It only took me a few more days to realize he’s just a boy, yes, a boy trapped inside a man's overcoat of all muscles covered in oily grease. A real stunner in the dim lights of an auto repair shop, emphasis on the dim lighting. Surely I wasn’t this gullible at forty-five years of age, but I fell in. Every day, he morphed into more of a son, at twenty years old, and not the husband I desired, but an undomesticated creature who never did much of anything. 
    Despite the rose-colored glasses, I should have noticed a few of the red flags all around me, with the biggest and reddest being my own apparent cougar nature. Not a complimentary slang term, that word cougar; meaning an older woman in a romantic relationship with a younger man. I’ve only ever lived in this old house, my entire life, from birth then home schooled within its walls, and now I wondered what the neighbors thought. Once I thought they expected to see me gardening odd plants, or herding cats, but never having a young stud of a husband.
    What the hell had happened? I thought, looking back; it seemed I had manifested a real puzzle, yet despite the changes, my actual day-to-day existence remained unchanged. Unchanged, unless he wanted something: food, laundry, sleep, or all three. Mostly though, every day continued on as before; reading, doing crossword puzzles (passionately), and trial-and-error knitting that resulted in enormous stacks of oddly shaped blankets. Well, that continued as the story of my life, but before him, there had been a dash of longing for the greener pastures of romance. Perhaps wanting was better than having, because it turned out that “dash”, aka hubby, and his “greener pastures” enclosed me like an invisible barbed wire fence, different but just as sharp as the real thing. Even with his ever-lessening morning and evening presence, my life seemed to remain much ado about nothing.
    Then “the something” arrived obliterating “the nothing” entirely, oh no not on little cat’s feet, but dropped off, or in, by a fabled stork. Suddenly, every day I awoke to a bloated face staring back at me in the bathroom mirror. Both the baby and my head grew, as my tolerance and temper grew in opposite directions. I felt like the Hindenburg looked, well, before the fire. But I was a blimp firmly anchored to the ground by a passenger on board, and rarely by another passenger that is briefly on board, so to speak, if less than 30 seconds could be called boarding. I thought that the Big Bang Theory as it was called might be true, something from nothing, given how close to nothing that “less than 30 seconds” seemed to me. The hubby, named Doofus in my head, not out loud, not yet, had somehow procreated itself; he got me pregnant. Again, in my head, I had tried out other names for him: Sofa (since the shop mechanics are always sitting on it), Wingnut, Spanner, Grease Monkey, Banger or Lube Job (so not appropriate for him), Monkey Beating an Engine with a Hammer (I liked this one, a contender), Oil Burner, and Cletus (so close but not quite Doofus).
    With lessening tolerance and rising temper, Doofus now gave me a wide berth. I was pretty sure that someone younger had punched his ticket, and lowered their gangplank for him to board. There was that tug of an imminent launch, geez, this nautical speak derived from my bloating, I was certain. Of course, a baby will not stay around to help another baby. My wish, please don’t let this baby in my belly be a boy, sure I will love it, but I just couldn’t mother the two of them. Did I forget to mention, my car remained unreliable and started only when it felt like it. He was not even a decent mechanic. His only solution, “I’ll jump it for you, hun!” which took him an hour as he wrestled with the theory of jumper cables, red-to-red or red-to-black, as sparks flew. 
    In the end he started none of my engines, so our break up happened, divorce in the mail, so on and so forth. Now, Doofus seemed happy, which he always was, no matter what, with a new woman who appeared just about old enough to be his daughter. The baby continued growing inside me. Doofus wanted no contact. Maybe that was for the best, but time will tell. Sometimes the baby reminded me of him when my belly felt like a jungle with a Tarzan in there, swinging on that cord and planting both feet down hard on my kidneys. I peed often, yet another chore on an ever increasing to-do list. I still hoped for a Sheena, a queen of the jungle, and not another swinging you know what.
    The tummy scan said it was a girl, and a girl came out. After all of that, the birth was easy-peasy. Time passed, Doofus exited stage left, yet I still spend much of my days reading and doing crosswords, but I replaced knitting with child care. It turned out that “the nothing” of my life acted like an elixir that manifested a beautiful something. She became a bundle of love, but occasionally there flashed a fleeting glimpse of a future wild child in her eyes—dad.    
    """
    # word_count = len(re.findall(r'\w+', story)) # e.g. can't becomes can t = 2 words not 1
    # print(f"words in story: {word_count}")
    print(f"words in story: {len(story.split())}")

    extractor.process_text(story)
    print(json.dumps(extractor.get_consolidated_entities(), indent=2))

'''
(keys2text_proxy) cleesmith:~$ python -B zzz3.py
words in story: 733
{
  "characters": {
    "Delta": {
      "demeanor": "resourceful, determined",
      "attitude": "optimistic, open-minded",
      "physical_description": "not specified",
      "motivations": "catching crawdads, exploring the swamp, seeking adventure",
      "conflicts": "disappointment, empty bucket, lack of luck",
      "backstory": "has experience catching crawdads, has met a trapper named Pierre in the past",
      "archetype": "the hunter/gatherer"
    },
    "Pierre": {
      "demeanor": "charismatic, mysterious",
      "attitude": "confident, secretive",
      "physical_description": "not specified",
      "motivations": "trapping animals, sharing his knowledge",
      "conflicts": "none specified",
      "backstory": "has a way with animals, claims to have a special whisper to call them",
      "archetype": "the trickster"
    }
  },
  "places": [
    "home",
    "the swamp",
    "the shore",
    "the bayou"
  ],
  "times": [
    "morning",
    "tomorrow",
    "long ago",
    "today"
  ],
  "events": [
    {
      "name": "Delta's failed crawdad catch",
      "characters_involved": [
        "Delta"
      ],
      "location": "the swamp",
      "cause": "bad luck",
      "effect": "disappointment, empty bucket"
    },
    {
      "name": "Discovery of the alligator and the bucket of crawdads",
      "characters_involved": [
        "Delta"
      ],
      "location": "the swamp",
      "cause": "Delta's curiosity, the alligator's presence",
      "effect": "Delta finds a bucket of crawdads, has a successful catch"
    },
    {
      "name": "Delta's meeting with Pierre",
      "characters_involved": [
        "Delta",
        "Pierre"
      ],
      "location": "the swamp",
      "cause": "chance encounter",
      "effect": "Delta learns about Pierre's special whisper, tries it out"
    },
    {
      "name": "Delta's attempt to recreate the experience with Pierre",
      "characters_involved": [
        "Delta"
      ],
      "location": "the swamp",
      "cause": "Delta's nostalgia, desire to relive the experience",
      "effect": "nothing happens, Delta is disappointed"
    }
  ],
  "objects": [
    "the canoe",
    "the paddle",
    "the coffee",
    "the rusty bucket",
    "the bacon",
    "the twine",
    "the fire"
  ],
  "relationships": [
    "Delta and the swamp (love and appreciation)",
    "Delta and Pierre (acquaintances)"
  ],
  "themes": [
    "the importance of perseverance",
    "luck vs. skill",
    "the allure of the unknown",
    "the power of nature"
  ],
  "symbols": [
    {
      "name": "the crawdads",
      "meaning": "good luck, abundance, the cycle of life"
    },
    {
      "name": "the swamp",
      "meaning": "the unknown, the subconscious, the past"
    },
    {
      "name": "the alligator",
      "meaning": "danger, opportunity, the unexpected"
    }
  ],
  "unresolved_questions": [
    "What happened to Pierre after Delta met him?",
    "Will Delta ever be able to recreate the experience with Pierre?",
    "What is the significance of the special whisper and its effects on the animals?"
  ]
}

'''