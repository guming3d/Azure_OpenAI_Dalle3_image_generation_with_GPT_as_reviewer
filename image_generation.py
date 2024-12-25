import base64
import os
import json
import requests
from dotenv import load_dotenv
from openai import AzureOpenAI
import os
from datetime import datetime

load_dotenv()

client = AzureOpenAI(
    api_version="2024-05-01-preview",
    azure_endpoint="https://minggu-aoai.openai.azure.com/",
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
)
GPT_4O_API_URL = os.getenv("GPT_4O_API_URL")
OUTPUT_DIRECTORY = os.path.join(os.getcwd(), os.getenv("OUTPUT_DIRECTORY", "output"))

def generate_image(prompt):
    result = client.images.generate(
        model="Dalle3",
        prompt=prompt,
        n=1,
        quality="hd",
        style="natural"
    )
    image_url = json.loads(result.model_dump_json())['data'][0]['url']
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
                    "text": """
    You are an professional image editor that helps me check whether the content of the input image is follow three critical standard below:
    - The dish of in the exact center of the image
    - The dish is complete and has space in both sides(up/down/left/right))
    - There is no other items arround the dish, just pure white and with no shadow 

    If both the previous standards are met, please output "True", otherwise, output "False". The quality of the image is very important to me.
    following is output format json example:
    {
    "is_good": "False",
    "reason": "The dish is not in the center of the image"
    }
    """
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
        max_tokens=300,
        temperature=0.8,
        top_p=0.8,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
        stream=False
    )

    # print(f"call gpt-4o with response:{completion}")

    # Assuming the completion contains the information about image centering
    completion_data = json.loads(completion.choices[0].message.content)
    completion_data = json.loads(completion_data)
    messages = chat_prompt
    
    # Generate the completion
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=300,
        temperature=0.8,
        top_p=0.8,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
        stream=False
    )
    
    # print(f"call gpt-4o with response:{completion}")
    
    # Assuming the completion contains the information about image centering
    completion_content = completion.choices[0].message['content']
    completion_data = json.loads(completion_content)
    result = completion_data.get("is_good", "False")
    reason = completion_data.get("reason", "Unknown")
    print(f"Image check result: {result}")
    print(f"Reason: {reason}")    # Include speech result if speech is enabled
    messages = chat_prompt
    
    # Generate the completion
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=300,
        temperature=0.8,
        top_p=0.8,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
        stream=False
    )
    
    # print(f"call gpt-4o with response:{completion}")
    
    # Assuming the completion contains the information about image centering
    completion_content = completion.choices[0].message['content']
    completion_data = json.loads(completion_content)
    result = completion_data.get("is_good", "False")
    reason = completion_data.get("reason", "Unknown")
    print(f"Image check result: {result}")
    print(f"Reason: {reason}")
    reason = completion_data.get("reason", "Unknown")
    print(f"Image check result: {result}")
    print(f"Reason: {reason}")
    return result, reason 

def main():
    # prompt = "food photography, minimalist style, Spicy Chinese Tomato Chicken, editorial photography, photography, from top view, only show plate on top of the white desk without any other items arround the dish"
    prompt = "A dish of Spicy Chinese Tomato Chicken on center of the white desk, view from the top, professional editorial photography, 4k,make sure only show plate without any other items arround the dish"
    if not os.path.exists(OUTPUT_DIRECTORY):
        os.makedirs(OUTPUT_DIRECTORY)
    # print(f"Output directory: {OUTPUT_DIRECTORY}")
    while True:
        image_url = generate_image(prompt)
        # print(f"Checking if image is good quality with URL: {image_url}")
        result, reason = check_image_center(image_url)
        if result == "True":
            try:
                response = requests.get(image_url)
                response.raise_for_status()
                image_data = response.content
            except requests.exceptions.RequestException as e:
                print(f"Error downloading image: {e}")
                continue

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_path = os.path.join(OUTPUT_DIRECTORY, f"generated_image_{timestamp}.png")
            print(f"Saving image to {image_path}")
            with open(image_path, "wb") as image_file:
                image_file.write(image_data)
            break
        else:
            try:
                response = requests.get(image_url)
                response.raise_for_status()
                image_data = response.content
            except requests.exceptions.RequestException as e:
                print(f"Error downloading image: {e}")
                continue

            bad_output_dir = os.path.join(OUTPUT_DIRECTORY, "_bad_images")
            if not os.path.exists(bad_output_dir):
                os.makedirs(bad_output_dir)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            bad_image_path = os.path.join(bad_output_dir, f"generated_image_{timestamp}.png")
            print(f"Saving image to {bad_image_path}")
            with open(bad_image_path, "wb") as image_file:
                image_file.write(image_data)
            print(f"Image not met our standard due to {reason}, generating a new one...")

if __name__ == "__main__":
    main()
