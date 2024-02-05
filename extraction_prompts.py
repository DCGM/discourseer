import pydantic
from typing import List, Tuple


class ExtractionPrompts(pydantic.BaseModel):
    name: str
    description: str
    examples: List[Tuple[str, str]]


extraction_prompts = {
    "keywords": ExtractionPrompts(name="keywords", description="Keywords are words or phrases that capture the main ideas, themes, concepts, or subjects of the text.", examples=[]),
    "topics": ExtractionPrompts(name="topics", description="Topics are the main ideas, themes, concepts, or subjects. Topics are often generalizations of the text and often do not appear as words in the document.", examples=[]),
    "named_events": ExtractionPrompts(name="named events", description="Named events are specific occurrences or happenings at a particular time and place with associated unique name.", examples=[]),
    "general_events": ExtractionPrompts(name="general events", description="General events are unnamed occurrences or happenings at a particular time and place (e.g. car crash, football match, border clash, awakening).", examples=[]),
    "named_places": ExtractionPrompts(name="places", description="Named places are for example buildings, locations, areas, or regions with a distinct identity and name.", examples=[]),
    "general_places": ExtractionPrompts(name="general places", description="General places are location types without a name (e.g. river, wilderness, city, underground, mountains).", examples=[]),
    "named_people": ExtractionPrompts(name="named people", description="Named people are individuals who are mentioned by name in the text. Named people should be represented in the output by their full name if possible.", examples=[]),
    "roles": ExtractionPrompts(name="roles", description="Roles are the functions, positions, jobs, responsibilities or life roles of individuals or groups of people.", examples=[]),
    "organizations": ExtractionPrompts(name="organizations", description="Organizations include states, companies, institutions, associations, and other groups of people with a common purpose or identity.", examples=[]),
    "perpetrators": ExtractionPrompts(name="perpetrators", description="Perpetrators should include the exact words or phrases that identify the person or group of people who committed a crime, act of violence, or other harmful act.", examples=[]),
    "victims": ExtractionPrompts(name="victims", description="Victims should include the exact words or phrases that identify the person or group of people who were harmed by a crime, act of violence, or other harmful act.", examples=[]),
}