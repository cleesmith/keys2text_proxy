import spacy
# Hypothetical GLiNER import (this name or usage may vary depending on the library)
from gliner import Gliner  

class SimpleAuthorHelper:
	def __init__(self):
		# Step 1: Load spaCy
		self.nlp = spacy.load("en_core_web_sm")

		# Step 2: Integrate GLiNER on top of spaCy (actual usage can differ)
		self.gliner = Gliner(self.nlp)

	def extract_entities(self, text: str):
		"""
		Identify characters, places, or other important items 
		in the text so an author can quickly 'catch up'.
		"""
		doc = self.nlp(text)
		
		# This can capture standard entities or custom ones, depending on your GLiNER setup
		entity_info = []
		for ent in doc.ents:
			entity_info.append({
				"text": ent.text,
				"label": ent.label_
			})

		return entity_info

# Example usage:
if __name__ == "__main__":
	text = """In the land of Suranthia, Queen Alarien has guarded 
			  the Shimmering Gate for centuries. Recently, a rogue 
			  mage named Faenor visited the palace with unknown intentions."""
	
	helper = SimpleAuthorHelper()
	found_entities = helper.extract_entities(text)
	print(found_entities)
