import base64
import os
import json
import requests
from openai import AzureOpenAI
import os

client = AzureOpenAI(
    api_version="2024-02-01",
    azure_endpoint="https://minggu-aoai.openai.azure.com/",
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
)
GPT_4O_API_URL = "https://<your-gpt4o-endpoint>"
API_KEY = "<your-api-key>"
OUTPUT_DIRECTORY = "<your-output-directory>"

def generate_image(prompt):
    result = client.images.generate(
        model="Dalle3",
        prompt=prompt,
        n=1
    )
    return json.loads(result.model_dump_json())['data'][0]['url']

def check_image_center(image_url):
    # Encode the image from the URL
    image_data = requests.get(image_url).content
    encoded_image = base64.b64encode(image_data).decode('ascii')

    # Prepare the chat prompt
    chat_prompt = [
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": "You are an AI assistant that helps people find information."
                }
            ]
        }
    ]

    # Include speech result if speech is enabled
    messages = chat_prompt

    # Generate the completion
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=800,
        temperature=0.7,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
        stream=False
    )

    # Assuming the completion contains the information about image centering
    return completion.to_json().get("is_centered", False)

def main():
    prompt = "A food dish on a table from a top view"
    while True:
        image_url = generate_image(prompt)
        if check_image_center(image_url):
            image_data = requests.get(image_url).content
            image_path = os.path.join(OUTPUT_DIRECTORY, "generated_image.png")
            with open(image_path, "wb") as image_file:
                image_file.write(image_data)
            print(f"Image saved to {image_path}")
            break
        else:
            print("Image not centered, generating a new one...")

if __name__ == "__main__":
    main()
