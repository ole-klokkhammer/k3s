import base64
import argparse
from openai import OpenAI

# Initialize the client to point to your vLLM server
# Assuming the default vLLM port 8000
client = OpenAI(api_key="empty", base_url="http://ai-utils.home.lan:8000/v1")


def encode_image(image_path):
    """Convert a local image file to a base64 string for the VLM API."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def reason_about_image(image_path, prompt):
    """Sends an image and a prompt to the vLLM server and returns the reasoning."""
    base64_image = encode_image(image_path)

    response = client.chat.completions.create(
        model="Qwen3VL-8B-Instruct-NVFP4",  # This should match the model in your vllm.service
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            }
        ],
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reason about an image using vLLM")
    parser.add_argument(
        "--image", type=str, required=True, help="Path to the image file"
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default="What is in this image?",
        help="The prompt to send to the VLM",
    )

    args = parser.parse_args()

    print(f"Processing image: {args.image}...")
    result = reason_about_image(args.image, args.prompt)
    print(f"\nReasoning:\n{result}")
