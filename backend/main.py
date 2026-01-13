from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os

from services.llm import diagnose_symptom
from services.image_gen import generate_species_image_from_prompt
from services.qiniu_storage import save_to_qiniu

app = FastAPI(
    title="灵魂物种鉴定所 API",
    description="基于 AI 的情绪诊断工具",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DiagnoseRequest(BaseModel):
    """诊断请求"""
    symptom: str


class DiagnoseResponse(BaseModel):
    """诊断响应"""
    object_name: str
    keywords: List[str]
    diagnosis: str
    rarity: str
    image_url: str
    sequence_no: int


# 简单的计数器（生产环境应使用数据库）
diagnosis_counter = 0


@app.get("/")
async def root():
    return {"message": "欢迎来到灵魂物种鉴定所 🧬"}


@app.post("/api/diagnose", response_model=DiagnoseResponse)
async def diagnose(request: DiagnoseRequest):
    """
    诊断用户的情绪状态，返回对应的"物种"信息
    """
    global diagnosis_counter
    
    if len(request.symptom) < 5 or len(request.symptom) > 50:
        raise HTTPException(status_code=400, detail="症状描述需要在5-50字之间")
    
    try:
        # 1. 调用 LLM 诊断
        result = await diagnose_symptom(request.symptom)
        
        # 更新计数器
        diagnosis_counter += 1
        
        image_url = result.get("image_url")
        
        # 2. 如果没有命中预置图库，则生成新图
        if not image_url:
            print(f"New species detected: {result.get('object_name')}, generating image...")
            try:
                # Seedream 生成
                object_name = result.get("object_name", "未知物种")
                prompt = f"""极简涂鸦风格。画风潦草，甚至有点丑。{object_name}，
粗线条手绘，简约卡通表情，背景颜色必须是纯白的。
适合社交媒体分享的正方形构图"""
                temp_url = await generate_species_image_from_prompt(prompt)
                
                # 七牛云抓取存储
                # 构造存储 key: species/{object_name}_{timestamp}.png
                import time
                timestamp = int(time.time())
                object_name_safe = result.get('object_name', 'unknown').replace(" ", "_")
                key = f"species/{object_name_safe}_{timestamp}.png"
                
                image_url = await save_to_qiniu(temp_url, key)
                print(f"Image saved to Qiniu: {image_url}")
                
            except Exception as img_error:
                print(f"Image generation failed: {img_error}")
                # 降级方案：使用占位图
                image_url = "https://placeholder.com/species/unknown.png"
        
        return DiagnoseResponse(
            object_name=result.get("object_name", "未知物种"),
            keywords=result.get("keywords", ["神秘", "未知", "待鉴定"]),
            diagnosis=result.get("diagnosis", "你的灵魂物种正在鉴定中..."),
            rarity=result.get("rarity", "R"),
            image_url=image_url,
            sequence_no=diagnosis_counter
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"诊断失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
