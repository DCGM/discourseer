from openai import OpenAI
import argparse
import logging
import os
import json


def parse_args():
    parser = argparse.ArgumentParser(description='Extract topics from text files in a directory using OpenAI GPT-3 and save the results to a file."'
                                                 ' You must have an OpenAI API key to use this script. Specify environment variable OPENAI_API_KEY.')
    parser.add_argument('--input-dir', type=str, required=True, help='The directory containing the text files to process.')
    parser.add_argument('--output-file', default="result.csv", help='The file to save the results to.')
    parser.add_argument('--log', default="INFO", help='The logging level to use.')

    return parser.parse_args()


class TopicExtractor:
    def __init__(self):
        self.client = OpenAI()

    def extract_topics(self, text):
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[
                {
                    "role": "system",
                    "content": "You are a media content analyst. You are analyzing the following text to extract topics, events, places, people, and oter named entities."
                               " You will provide list of topics, places, people, and other named entities as a JSON object with keys: topics, places, people, and other_entities. "
                               " Text will be in Czech language."
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            temperature=0.5,
            max_tokens=512,
            top_p=1,
            response_format={"type": "json_object"}
        )
        response = json.loads(response.choices[0].message.content)
        return response


def main():
    args = parse_args()
    logging.basicConfig(level=args.log)
    files = os.listdir(args.input_dir)

    topic_extractor = TopicExtractor()
    output_file = open(args.output_file, 'w', encoding='utf-8')

    for file in files:
        with open(os.path.join(args.input_dir, file), 'r', encoding='utf-8') as f:
            text = f.read()
            response = topic_extractor.extract_topics(text)
            # write the result to the output file
            # each line will contain the filename,response_key,elements of the response value as a comma-separated list
            for key, value in response.items():
                output_file.write(f"{file},{key},{','.join(value)}\n")


if __name__ == "__main__":
    main()

