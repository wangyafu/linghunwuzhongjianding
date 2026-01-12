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


async def generate_species_image(object_name: str, prompt_suffix: str = "") -> str:
    """
    使用 Seedream 生成物种图片
    
    Args:
        object_name: 物种名称
        prompt_suffix: 提示词后缀（用于补充描述细节）
    
    Returns:
        生成的图片临时 URL
    """
    prompt = f"""可爱粗野主义风格插画，{object_name}，{prompt_suffix}
粗线条手绘，高饱和糖果色填充，
简约卡通表情，白色纯净背景，
无衬线字体标注，扁平化设计，
适合社交媒体分享的正方形构图"""

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
                "size": "2048x2048",
                "response_format": "url",
                "watermark": False
            }
        )
        if response.status_code != 200:
            print(f"❌ API Error Response: {response.text}")
        response.raise_for_status()
        result = response.json()
        return result["data"][0]["url"]
