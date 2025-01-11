from typing import Dict, Any, Optional, List
import json
import re
from groq import Groq
from datetime import datetime

class EntityExtractor:
	def __init__(self, api_key: Optional[str] = None):
		"""Initialize the EntityExtractor with an optional API key."""
		self.client = Groq(api_key=api_key) if api_key else Groq()

		# Updated entity store with new fields:
		self.entity_store = {
			"characters": {},
			"places": set(),
			"times": set(),
			"events": [],
			"objects": set(),
			"relationships": set(),
			"themes": set(),
			"symbols": [],
			"unresolved_questions": [],
			"metadata": {}
		}

	def _create_extraction_prompt(self, text: str) -> str:
		"""Create a structured prompt for the LLM to extract entities."""
		return f"""
		Please analyze the following story and extract entities with extra details 
		that could help a writer. Provide them in a JSON object with these keys:

		{{
		  "characters": [
			{{
			  "name": "",
			  "demeanor": "",
			  "attitude": "",
			  "physical_description": "",
			  "motivations": "",
			  "conflicts": "",
			  "backstory": "",
			  "archetype": "",
			  "growth_opportunities": "",     # Additional field
			  "relationship_dynamics": ""     # Additional field
			}}
		  ],
		  "places": [],
		  "times": [],
		  "events": [
			{{
			  "name": "",
			  "characters_involved": [],
			  "location": "",
			  "cause": "",
			  "effect": "",
			  "thematic_role": ""           # Example extra field
			}}
		  ],
		  "objects": [],
		  "relationships": [],
		  "themes": [],
		  "symbols": [
			{{
			  "name": "",
			  "meaning": ""
			}}
		  ],
		  "unresolved_questions": []
		}}

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

	def _empty_structure(self) -> Dict[str, Any]:
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

	def _extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
		"""Extract and parse JSON from the LLM response text."""
		json_match = re.search(r'\{[\s\S]*\}', response_text)
		if not json_match:
			raise ValueError("No JSON structure found in response")
		
		try:
			return json.loads(json_match.group())
		except json.JSONDecodeError as e:
			print(f"Error parsing JSON: {e}")
			return self._empty_structure()

	def _update_entity_store(self, extracted_data: Dict[str, Any]) -> None:
		"""Update the entity store with newly extracted data."""
		# Characters
		if "characters" in extracted_data:
			for character in extracted_data["characters"]:
				name = character.get("name", "").strip()
				if not name:
					continue

				if name not in self.entity_store["characters"]:
					self.entity_store["characters"][name] = {
						"demeanor": character.get("demeanor", "unknown"),
						"attitude": character.get("attitude", "unknown"),
						"physical_description": character.get("physical_description", "unknown"),
						"motivations": character.get("motivations", "unknown"),
						"conflicts": character.get("conflicts", "unknown"),
						"backstory": character.get("backstory", "unknown"),
						"archetype": character.get("archetype", "unknown"),
						"growth_opportunities": character.get("growth_opportunities", "unknown"),
						"relationship_dynamics": character.get("relationship_dynamics", "unknown")
					}
				else:
					# Update existing character data
					current_char = self.entity_store["characters"][name]
					for key in current_char.keys():
						new_val = character.get(key)
						if new_val and new_val != "unknown":
							current_char[key] = new_val

		# Simple fields: places, times, objects, relationships, themes
		for category in ["places", "times", "objects", "relationships", "themes"]:
			if category in extracted_data and isinstance(extracted_data[category], list):
				self.entity_store[category].update(extracted_data[category])

		# Events
		if "events" in extracted_data and isinstance(extracted_data["events"], list):
			for event in extracted_data["events"]:
				self.entity_store["events"].append(event)

		# Symbols
		if "symbols" in extracted_data and isinstance(extracted_data["symbols"], list):
			for symbol in extracted_data["symbols"]:
				self.entity_store["symbols"].append(symbol)

		# Unresolved questions
		if "unresolved_questions" in extracted_data and isinstance(extracted_data["unresolved_questions"], list):
			self.entity_store["unresolved_questions"].extend(extracted_data["unresolved_questions"])

	def process_text(self, text: str, version: Optional[str] = None) -> None:
		"""Process a text and update the entity store."""
		try:
			response = self.client.chat.completions.create(
				model="llama-3.3-70b-versatile",
				messages=[
					{
						"role": "system",
						"content": "You are an expert at extracting structured data from text."
					},
					{
						"role": "user",
						"content": self._create_extraction_prompt(text)
					}
				],
				temperature=0.2,
				max_tokens=32768,
				stream=True
			)

			# Process the streaming response
			full_response = self._process_streaming_response(response)
			
			# Extract and parse the JSON data
			extracted_data = self._extract_json_from_response(full_response)
			
			# Update the entity store with the new data
			self._update_entity_store(extracted_data)

			# Optionally store metadata
			if version:
				self.entity_store["metadata"]["version"] = version
			self.entity_store["metadata"]["last_processed"] = datetime.utcnow().isoformat()
			
		except Exception as e:
			print(f"Error processing text: {e}")

	def get_consolidated_entities(self) -> Dict[str, Any]:
		"""Return the consolidated entity store in a JSON-serializable format."""
		return {
			"characters": self.entity_store["characters"],
			"places": list(self.entity_store["places"]),
			"times": list(self.entity_store["times"]),
			"events": self.entity_store["events"],
			"objects": list(self.entity_store["objects"]),
			"relationships": list(self.entity_store["relationships"]),
			"themes": list(self.entity_store["themes"]),
			"symbols": self.entity_store["symbols"],
			"unresolved_questions": self.entity_store["unresolved_questions"],
			"metadata": self.entity_store["metadata"]
		}

	def synthesize_outline(self) -> str:
		"""Create a simple outline from the consolidated entities."""
		outline = "Story Outline:\n"
		
		# Characters
		if self.entity_store["characters"]:
			outline += "\nCharacters:\n"
			for name, info in self.entity_store["characters"].items():
				outline += f" - {name} ({info.get('archetype', 'N/A')}): {info.get('demeanor', '')}\n"
		
		# Events
		if self.entity_store["events"]:
			outline += "\nKey Events:\n"
			for event in self.entity_store["events"]:
				outline += f" - {event.get('name')}, Location: {event.get('location', '')}\n"
				outline += f"   Cause: {event.get('cause', '')}, Effect: {event.get('effect', '')}\n"

		# Themes
		if self.entity_store["themes"]:
			outline += "\nThemes:\n"
			for theme in self.entity_store["themes"]:
				outline += f" - {theme}\n"

		# Symbols
		if self.entity_store["symbols"]:
			outline += "\nSymbols:\n"
			for symbol in self.entity_store["symbols"]:
				outline += f" - {symbol.get('name')} (Meaning: {symbol.get('meaning')})\n"

		# Unresolved Questions
		if self.entity_store["unresolved_questions"]:
			outline += "\nUnresolved Questions:\n"
			for question in self.entity_store["unresolved_questions"]:
				outline += f" - {question}\n"
		
		return outline

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
	print(f"words in story: {len(story.split())}")

	extractor.process_text(story, version="draft_2025")
	print(json.dumps(extractor.get_consolidated_entities(), indent=2))
	print(extractor.synthesize_outline())

