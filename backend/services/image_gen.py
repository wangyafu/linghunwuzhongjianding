"""图像生成服务 - Seedream"""
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

ARK_API_KEY = os.getenv("ARK_API_KEY", "")
ARK_API_URL = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
MODEL_NAME = "doubao-seedream-4-5-251128"
async def generate_species_image_from_prompt(prompt:str) -> str:
    """
    使用 Seedream 生成物种图片
    
    Args:
        prompt: 提示词
    
    Returns:
        生成的图片临时 URL
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            ARK_API_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {ARK_API_KEY}"
            },
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
        
                "response_format": "url",
                "watermark": False
            }
        )
        if response.status_code != 200:
            print(f"❌ API Error Response: {response.text}")
        response.raise_for_status()
        result = response.json()
        print(result)
        return result["data"][0]["url"]


