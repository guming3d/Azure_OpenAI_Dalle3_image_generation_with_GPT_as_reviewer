import base64
import os
import json
import requests
from dotenv import load_dotenv
from openai import AzureOpenAI
import os

load_dotenv()

client = AzureOpenAI(
    api_version="2024-02-01",
    azure_endpoint="https://minggu-aoai.openai.azure.com/",
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
)
GPT_4O_API_URL = os.getenv("GPT_4O_API_URL")
OUTPUT_DIRECTORY = os.path.join(os.getcwd(), os.getenv("OUTPUT_DIRECTORY", "output"))

def generate_image(prompt):
    result = client.images.generate(
        model="Dalle3",
        prompt=prompt,
        n=1
    )
    image_url = json.loads(result.model_dump_json())['data'][0]['url']
    print(f"Generated image URL: {image_url}")
    return image_url

def check_image_center(image_url):
    # Encode the image from the URL
    try:
        response = requests.get(image_url)
        response.raise_for_status()  # Raise an error for bad responses
        image_data = response.content
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {e}")
        return None
    encoded_image = base64.b64encode(image_data).decode('ascii')

    # Prepare the chat prompt
    chat_prompt = [
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": "You are an AI assistant that helps me check whether the dish of input image is in the center of the image. just return an json contains the \"is_centered\" field and value "
                }
                
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                           "url": f"data:image/jpeg;base64,{encoded_image}"
                        }
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
    completion_data = json.loads(completion.to_json())
    return completion_data.get("is_centered", False)

def main():
    prompt = "food photography, Spicy Chinese Tomato Chicken, editorial photography, photography, from top view, only show plate with 'spicy Chinese Tomato Chicken' without any other items"
    if not os.path.exists(OUTPUT_DIRECTORY):
        os.makedirs(OUTPUT_DIRECTORY)
    print(f"Output directory: {OUTPUT_DIRECTORY}")
    while True:
        image_url = generate_image(prompt)
        print(f"Checking if image is centered for URL: {image_url}")
        if check_image_center(image_url):
            try:
                response = requests.get(image_url)
                response.raise_for_status()  # Raise an error for bad responses
                image_data = response.content
            except requests.exceptions.RequestException as e:
                print(f"Error downloading image: {e}")
                continue
            image_path = os.path.join(OUTPUT_DIRECTORY, "generated_image.png")
            print(f"Saving image to {image_path}")
            with open(image_path, "wb") as image_file:
                image_file.write(image_data)
            print(f"Image saved to {image_path}")
            break
        else:
            print("Image not centered, generating a new one...")

if __name__ == "__main__":
    main()
