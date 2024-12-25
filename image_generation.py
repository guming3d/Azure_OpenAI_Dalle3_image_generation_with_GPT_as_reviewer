import base64
import os
import json
import requests
from dotenv import load_dotenv
from openai import AzureOpenAI
from datetime import datetime

load_dotenv()

client = AzureOpenAI(
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_API_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
)
GPT_4O_API_URL = os.getenv("GPT_4O_API_URL")
OUTPUT_DIRECTORY = os.path.join(os.getcwd(), os.getenv("OUTPUT_DIRECTORY", "output"))

def generate_image(prompt):
    """
    生成图像。

    参数:
        prompt (str): 图像生成的提示文本。

    返回:
        str: 生成图像的URL。
    """
    result = client.images.generate(
        model="Dalle3",
        prompt=prompt,
        n=1,
        quality="hd",
        style="natural"
    )
    image_url = json.loads(result.model_dump_json())['data'][0]['url']
    return image_url

def download_image(image_url):
    """
    下载图像。

    参数:
        image_url (str): 图像的URL。

    返回:
        bytes: 图像的二进制数据。
    """
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {e}")
        return None

def encode_image_to_base64(image_data):
    """
    将图像数据编码为Base64格式。

    参数:
        image_data (bytes): 图像的二进制数据。

    返回:
        str: Base64编码的图像字符串。
    """
    return base64.b64encode(image_data).decode('ascii')

def prepare_chat_prompt(encoded_image):
    """
    准备聊天提示。

    参数:
        encoded_image (str): Base64编码的图像字符串。

    返回:
        list: 聊天消息列表。
    """
    SYSTEM_PROMPT = """
    You are a professional image editor that helps me check whether the content of the input image follows three critical standards below:
    - The dish is in the center of the image
    - The dish is complete and has space on all sides (up/down/left/right)
    - There are no other items around the dish, just pure white with no shadow

    If both the previous standards are met, please output "True", otherwise, output "False". The quality of the image is very important to me.
    Following is the output format JSON example:
    {
    "is_good": "False",
    "reason": ##description of the reason##,
    }
    """
    return [
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT
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

def check_image_quality(image_url):
    """
    检查图像质量。

    参数:
        image_url (str): 图像的URL。

    返回:
        tuple: 包含图像质量检查结果和原因的元组。
    """
    image_data = download_image(image_url)
    if not image_data:
        return "False", "Image download failed"

    encoded_image = encode_image_to_base64(image_data)
    messages = prepare_chat_prompt(encoded_image)

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=300,
        temperature=0.6,
        top_p=0.8,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
        stream=False
    )

    completion_content = completion.choices[0].message.content
    completion_data = json.loads(completion_content)
    result = completion_data.get("is_good", "False")
    reason = completion_data.get("reason", "Unknown")
    print(f"Image check result: {result}")
    print(f"Reason: {reason}")

    return result, reason

def save_image(image_data, directory, filename):
    """
    保存图像到指定目录。

    参数:
        image_data (bytes): 图像的二进制数据。
        directory (str): 保存图像的目录。
        filename (str): 图像的文件名。
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
    image_path = os.path.join(directory, filename)
    with open(image_path, "wb") as image_file:
        image_file.write(image_data)
    print(f"Saving image to {image_path}")

def main():
    """
    主函数，生成并检查图像质量。
    """
    prompt = "A dish of Spicy Chinese Tomato Chicken on center of the white desk, view from the top, professional editorial photography, 4k, make sure only show plate without any other items around the dish"
    if not os.path.exists(OUTPUT_DIRECTORY):
        os.makedirs(OUTPUT_DIRECTORY)

    while True:
        image_url = generate_image(prompt)
        result, reason = check_image_quality(image_url)
        image_data = download_image(image_url)
        if not image_data:
            continue

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if result == "True":
            save_image(image_data, OUTPUT_DIRECTORY, f"generated_image_{timestamp}.png")
            break
        else:
            bad_output_dir = os.path.join(OUTPUT_DIRECTORY, "_bad_images")
            save_image(image_data, bad_output_dir, f"generated_image_{timestamp}.png")
            print(f"Image not met our standard due to {reason}, generating a new one...")

if __name__ == "__main__":
    main()
