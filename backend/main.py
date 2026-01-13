from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os
import logging
import traceback

from services.llm import diagnose_symptom
from services.image_gen import generate_species_image_from_prompt
from services.qiniu_storage import save_to_qiniu

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="灵魂物种鉴定所 API",
    description="基于 AI 的情绪诊断工具",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","http://jinshenwuzhong.pages.dev"],
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
    display_name: str  # 个性化展示名，如 "过劳肥的陈年咸鱼"
    keywords: List[str]
    diagnosis: str
    image_url: str
    sequence_no: int


# 简单的计数器（生产环境应使用数据库）
diagnosis_counter = 0


@app.get("/")
async def root():
    return {"message": "欢迎来到灵魂物种鉴定所 🧬"}


class PresetSpeciesItem(BaseModel):
    """预置物种项"""
    object_name: str
    image_url: str


@app.get("/api/preset-species", response_model=List[PresetSpeciesItem])
async def get_preset_species():
    """
    获取预置物种列表，用于前端轮播展示
    """
    import json
    preset_file = os.path.join(os.path.dirname(__file__), "data", "preset_species.json")
    try:
        with open(preset_file, "r", encoding="utf-8") as f:
            species_list = json.load(f)
        return species_list
    except Exception as e:
        print(f"Failed to load preset species: {e}")
        return []


@app.post("/api/diagnose", response_model=DiagnoseResponse)
async def diagnose(request: DiagnoseRequest):
    """
    诊断用户的情绪状态，返回对应的"物种"信息
    """
    global diagnosis_counter
    
    logger.info(f"收到诊断请求: symptom='{request.symptom}'")
    
    if len(request.symptom) < 5 or len(request.symptom) > 50:
        logger.warning(f"症状描述长度不符合要求: {len(request.symptom)}字")
        raise HTTPException(status_code=400, detail="症状描述需要在5-50字之间")
    
    try:
        # 1. 调用 LLM 诊断
        logger.info("开始调用 LLM 诊断...")
        result = await diagnose_symptom(request.symptom)
        logger.info(f"LLM 诊断结果: {result}")
        
        # 更新计数器
        diagnosis_counter += 1
        logger.info(f"诊断计数器: {diagnosis_counter}")
        
        image_url = result.get("image_url")
        
        # 2. 如果没有命中预置图库，则生成新图
        if not image_url:
            object_name = result.get("object_name", "未知物种")
            logger.info(f"未命中预置图库，准备生成新图: object_name='{object_name}'")
            try:
                # Seedream 生成
                prompt = f"""极简涂鸦风格。画风潦草，甚至有点丑。{object_name}，
粗线条手绘，简约卡通表情，背景颜色必须是纯白的。
适合社交媒体分享的正方形构图"""
                logger.info(f"图片生成 Prompt: {prompt}")
                temp_url = await generate_species_image_from_prompt(prompt)
                logger.info(f"图片生成成功，临时 URL: {temp_url}")
                
                # 七牛云抓取存储
                # 构造存储 key: species/{object_name}_{timestamp}.png
                import time
                timestamp = int(time.time())
                object_name_safe = result.get('object_name', 'unknown').replace(" ", "_")
                key = f"species/{object_name_safe}_{timestamp}.png"
                
                logger.info(f"开始上传到七牛云: key={key}")
                image_url = await save_to_qiniu(temp_url, key)
                logger.info(f"七牛云上传成功: {image_url}")
                
            except Exception as img_error:
                logger.error(f"图片生成/上传失败: {type(img_error).__name__}: {str(img_error)}")
                logger.error(f"完整错误堆栈:\n{traceback.format_exc()}")
                # 降级方案：使用占位图
                image_url = "https://placeholder.com/species/unknown.png"
                logger.warning(f"使用占位图: {image_url}")
        else:
            logger.info(f"命中预置图库: {image_url}")
        
        # 获取 display_name，如果没有则使用 object_name
        object_name = result.get("object_name", "未知物种")
        display_name = result.get("display_name") or object_name
        logger.info(f"display_name: {display_name}, object_name: {object_name}")
        
        response = DiagnoseResponse(
            object_name=object_name,
            display_name=display_name,
            keywords=result.get("keywords", ["神秘", "未知", "待鉴定"]),
            diagnosis=result.get("diagnosis", "你的灵魂物种正在鉴定中..."),
            image_url=image_url,
            sequence_no=diagnosis_counter
        )
        logger.info(f"诊断成功，返回结果: sequence_no={diagnosis_counter}")
        return response
        
    except Exception as e:
        # 记录详细的错误信息
        logger.error(f"诊断失败: {type(e).__name__}: {str(e)}")
        logger.error(f"完整错误堆栈:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"诊断失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9002)
