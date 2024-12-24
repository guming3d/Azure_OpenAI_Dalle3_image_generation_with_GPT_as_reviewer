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
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    data = {
        "image_url": image_url,
        "task": "check_center"
    }
    response = requests.post(GPT_4O_API_URL, headers=headers, json=data)
    response.raise_for_status()
    return response.json()["is_centered"]

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
