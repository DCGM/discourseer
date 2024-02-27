from __future__ import annotations
import pydantic
from typing import List, Tuple


class ExtractionPrompts(pydantic.BaseModel):
    name: str
    description: str
    options: List[ResultOption] = []

    def get_description(self) -> str:
        return self.description + " " + " ".join(str(option) for option in self.options)

    def list_options(self) -> str:
        return ", ".join([option.name for option in self.options])

    def list_options_details(self) -> str:
        return ", ".join([str(option) for option in self.options])


class ResultOption(pydantic.BaseModel):
    name: str
    description: str

    def __str__(self) -> str:
        return self.name + " (" + self.description + ")"


extraction_prompts = {
    "keywords": ExtractionPrompts(name="keywords", description="Keywords are words or phrases that capture the main ideas, themes, concepts, or subjects of the text."),
    "topics": ExtractionPrompts(name="topics", description="Topics are the main ideas, themes, concepts, or subjects. Topics are often generalizations of the text and often do not appear as words in the document."),
    "named_events": ExtractionPrompts(name="named events", description="Named events are specific occurrences or happenings at a particular time and place with associated unique name."),
    "general_events": ExtractionPrompts(name="general events", description="General events are unnamed occurrences or happenings at a particular time and place (e.g. car crash, football match, border clash, awakening)."),
    "named_places": ExtractionPrompts(name="places", description="Named places are for example buildings, locations, areas, or regions with a distinct identity and name."),
    "general_places": ExtractionPrompts(name="general places", description="General places are location types without a name (e.g. river, wilderness, city, underground, mountains)."),
    "named_people": ExtractionPrompts(name="named people", description="Named people are individuals who are mentioned by name in the text. Named people should be represented in the output by their full name if possible."),
    "roles": ExtractionPrompts(name="roles", description="Roles are the functions, positions, jobs, responsibilities or life roles of individuals or groups of people."),
    "organizations": ExtractionPrompts(name="organizations", description="Organizations include states, companies, institutions, associations, and other groups of people with a common purpose or identity."),
    "perpetrators": ExtractionPrompts(name="perpetrators", description="Perpetrators should include the exact words or phrases that identify the person or group of people who committed a crime, act of violence, or other harmful act."),
    "victims": ExtractionPrompts(name="victims", description="Victims should include the exact words or phrases that identify the person or group of people who were harmed by a crime, act of violence, or other harmful act."),

    "5-range": ExtractionPrompts(name="5-range", description="Number of paragraphs in the text.", examples=[]),
    "6-genre": ExtractionPrompts(name="6-genre", description="The genre of the text with these options:", examples=[],
                                 options=[ResultOption(name="1-report", description="Report is information about a current event answering questions: who, what, where."),
                                          ResultOption(name="2-extended_report", description="Report is information about a current event answering questions: who, what, where, when, how and why."),
                                          ResultOption(name="3-interview", description="Interview is a conversation between two or more people."),
                                          ResultOption(name="9-other", description="Other genre.")]),
    "8-message-trigger": ExtractionPrompts(name="8-message-trigger", description="The message trigger is the event or situation that causes the message to be sent. It has these options:", examples=[],
                                           options=[ResultOption(name="1-politician", description="The message reacts on actions of a politician"),
                                                    ResultOption(name="2-security-forces", description="The message reacts on action of security forces."),
                                                    ResultOption(name="4-public", description="The message reacts on action of public."),
                                                    ResultOption(name="9-other", description="Other message trigger.")]),
    "9-place": ExtractionPrompts(name="Country", description="The country where the event or situation occurs. Options:", examples=[],
                                 options=[ResultOption(name="1-czech-republic", description="The event or situation occurs in the Czech Republic."),
                                          ResultOption(name="2-slovakia", description="The event or situation occurs in Slovakia."),
                                          ResultOption(name="3-poland", description="The event or situation occurs in Poland."),
                                          ResultOption(name="4-germany", description="The event or situation occurs in Germany."),
                                          ResultOption(name="5-russia", description="The event or situation occurs in Russia."),
                                          ResultOption(name="6-ukraine", description="The event or situation occurs in Ukraine."),
                                          ResultOption(name="9-other", description="The event or situation occurs in other country."),
                                          ResultOption(name="0-unknown", description="The event or situation occurs in unknown country.")]),
}


if __name__ == "__main__":
    print('{')
    for prompt_tag, prompt in extraction_prompts.items():
        key = f'"{prompt_tag}": '
        print(key + prompt.model_dump_json(indent=2) + ',')
    print('}')
