# vision

## models
https://huggingface.co/nvidia/LocateAnything-3B

https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct-FP8

https://huggingface.co/JEILDLWLRMA/Qwen3-VL-8B-Instruct-NVFP4


## setup

### to download the model
cd /models
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv --python 3.12 --seed --managed-python
source .venv/bin/activate
uv pip install --upgrade huggingface_hub
hf download JEILDLWLRMA/Qwen3-VL-8B-Instruct-NVFP4 --local-dir /models/qwen3-vl/JEILDLWLRMA_Qwen3-VL-8B-Instruct-NVFP4

### vllm
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update
sudo apt-get -y install cuda-toolkit-13-3 gcc build-essential python3.12-dev wget ninja-build

cd workspace/vllm
uv venv --python 3.12 --seed --managed-python
source .venv/bin/activate
uv pip install vllm --torch-backend=auto
uv pip install instanttensor

## testing

curl http://ai-utils.home.lan:8000/v1/chat/completions \
-H "Content-Type: application/json" \
-d '{
  "model": "Qwen3VL-8B-Instruct-NVFP4",
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "Describe this local image."},
        {"type": "image_url", "image_url": {"url": "file:///home/ole/pictures/image.png"}}
      ]
    }
  ]
}'