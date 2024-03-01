from __future__ import annotations
import pydantic
from typing import List, Dict


class ExtractionTopics(pydantic.BaseModel):
    topics: Dict[str, ExtractionTopic]

    def select_subset(self, subset: List[str] = None) -> ExtractionTopics:
        if not subset:
            return self
        return ExtractionTopics(topics={key: value for key, value in self.topics.items() if key in subset})

    def topic_keys(self) -> str:
        return ", ".join(self.topics.keys())

    def topic_names(self) -> str:
        return ", ".join([topic.name for topic in self.topics.values()])

    def topic_descriptions(self) -> str:
        return " ".join([topic.description for topic in self.topics.values()])

    def topic_names_and_descriptions_colon(self) -> str:
        return ", ".join([f'{topic.name}: {topic.description}' for topic in self.topics.values()])

    def topic_names_and_descriptions_parentheses(self) -> str:
        return ", ".join([f'{topic.name} ({topic.description})' for topic in self.topics.values()])


class ExtractionTopic(pydantic.BaseModel):
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


# extraction_topics = ExtractionTopics(topics={
#     "keywords": ExtractionTopic(name="keywords", description="Keywords are words or phrases that capture the main ideas, themes, concepts, or subjects of the text."),
#     "topics": ExtractionTopic(name="topics", description="Topics are the main ideas, themes, concepts, or subjects. Topics are often generalizations of the text and often do not appear as words in the document."),
#     "named_events": ExtractionTopic(name="named events", description="Named events are specific occurrences or happenings at a particular time and place with associated unique name."),
#     "general_events": ExtractionTopic(name="general events", description="General events are unnamed occurrences or happenings at a particular time and place (e.g. car crash, football match, border clash, awakening)."),
#     "named_places": ExtractionTopic(name="places", description="Named places are for example buildings, locations, areas, or regions with a distinct identity and name."),
#     "general_places": ExtractionTopic(name="general places", description="General places are location types without a name (e.g. river, wilderness, city, underground, mountains)."),
#     "named_people": ExtractionTopic(name="named people", description="Named people are individuals who are mentioned by name in the text. Named people should be represented in the output by their full name if possible."),
#     "roles": ExtractionTopic(name="roles", description="Roles are the functions, positions, jobs, responsibilities or life roles of individuals or groups of people."),
#     "organizations": ExtractionTopic(name="organizations", description="Organizations include states, companies, institutions, associations, and other groups of people with a common purpose or identity."),
#     "perpetrators": ExtractionTopic(name="perpetrators", description="Perpetrators should include the exact words or phrases that identify the person or group of people who committed a crime, act of violence, or other harmful act."),
#     "victims": ExtractionTopic(name="victims", description="Victims should include the exact words or phrases that identify the person or group of people who were harmed by a crime, act of violence, or other harmful act."),
#
#     "5-range": ExtractionTopic(name="5-range", description="Number of paragraphs in the text."),
#     "6-genre": ExtractionTopic(name="6-genre", description="The genre of the text with these options:",
#                                options=[ResultOption(name="1-report", description="Report is information about a current event answering questions: who, what, where."),
#                                         ResultOption(name="2-extended_report", description="Report is information about a current event answering questions: who, what, where, when, how and why."),
#                                         ResultOption(name="3-interview", description="Interview is a conversation between two or more people."),
#                                         ResultOption(name="9-other", description="Other genre.")]),
#     "8-message-trigger": ExtractionTopic(name="8-message-trigger", description="The message trigger is the event or situation that causes the message to be sent. It has these options:",
#                                          options=[ResultOption(name="1-politician", description="The message reacts on actions of a politician"),
#                                                   ResultOption(name="2-security-forces", description="The message reacts on action of security forces."),
#                                                   ResultOption(name="4-public", description="The message reacts on action of public."),
#                                                   ResultOption(name="9-other", description="Other message trigger.")]),
#     "9-place": ExtractionTopic(name="Country", description="The country where the event or situation occurs. Options:",
#                                options=[ResultOption(name="1-czech-republic", description="The event or situation occurs in the Czech Republic."),
#                                         ResultOption(name="2-slovakia", description="The event or situation occurs in Slovakia."),
#                                         ResultOption(name="3-poland", description="The event or situation occurs in Poland."),
#                                         ResultOption(name="4-germany", description="The event or situation occurs in Germany."),
#                                         ResultOption(name="5-russia", description="The event or situation occurs in Russia."),
#                                         ResultOption(name="6-ukraine", description="The event or situation occurs in Ukraine."),
#                                         ResultOption(name="9-other", description="The event or situation occurs in other country."),
#                                         ResultOption(name="0-unknown", description="The event or situation occurs in unknown country.")]),
# })


def print_schema():
    print(ExtractionTopics.schema_json(indent=2))


def print_extract_topics():
    # print(extraction_topics.model_dump_json(indent=2))

    # print('{')
    # for topic_tag, topic in extraction_topics.topics.items():
    #     key = f'"{topic_tag}": '
    #     print(key + topic.model_dump_json(indent=2) + ',')
    # print('}')
    ...


if __name__ == "__main__":
    print_schema()
    # print_extract_prompts()
