from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
import os
import logging
import traceback
import json
import asyncio
import time

from services.llm import diagnose_symptom
from services.llm_streaming import diagnose_symptom_streaming, get_preset_image_url
from services.image_gen import generate_species_image_from_prompt
from services.qiniu_storage import save_to_qiniu

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="精神物种鉴定所 API",
    description="基于 AI 的情绪诊断工具",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","https://jingshenwuzhong.pages.dev"],
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


# 计数器持久化文件路径
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
COUNTER_FILE = os.path.join(DATA_DIR, "diagnosis_counter.txt")

def get_next_sequence_no() -> int:
    """
    获取下一个诊断序号（带持久化）
    """
    current_count = 0
    
    # 1. 尝试读取现有计数
    if os.path.exists(COUNTER_FILE):
        try:
            with open(COUNTER_FILE, "r") as f:
                content = f.read().strip()
                if content:
                    current_count = int(content)
        except Exception as e:
            logger.error(f"读取计数器文件失败: {e}")
            
    # 2. 增加计数
    next_count = current_count + 1
    
    # 3. 保存新计数
    try:
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        with open(COUNTER_FILE, "w") as f:
            f.write(str(next_count))
    except Exception as e:
        logger.error(f"保存计数器文件失败: {e}")
        
    return next_count


@app.get("/")
async def root():
    return {"message": "欢迎来到精神物种鉴定所 🧬"}


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


@app.get("/api/diagnose/stream")
async def diagnose_stream(symptom: str):
    """
    流式诊断接口，使用 SSE 返回结果
    
    事件类型：
    - species: 物种基础信息 (object_name, display_name, keywords, image_url)
    - diagnosis_chunk: 诊断文案片段
    - image: 生成的图片 URL（如果需要生成）
    - done: 完成，包含 sequence_no
    - error: 错误信息
    """
    logger.info(f"收到流式诊断请求: symptom='{symptom}'")
    
    if len(symptom) < 5 or len(symptom) > 50:
        async def error_generator():
            yield f"data: {json.dumps({'type': 'error', 'message': '症状描述需要在5-50字之间'})}\n\n"
        return StreamingResponse(
            error_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
    
    async def event_generator():
        object_name = None
        has_preset_image = False
        
        try:
            # 流式调用 LLM
            async for event in diagnose_symptom_streaming(symptom):
                event_type = event.get("type")
                
                if event_type == "species":
                    object_name = event.get("object_name")
                    has_preset_image = bool(event.get("image_url"))
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                    
                elif event_type == "diagnosis_chunk":
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                    
                elif event_type == "error":
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                    return
            
            # 如果没有预置图片，需要生成
            if object_name and not has_preset_image:
                try:
                    logger.info(f"未命中预置图库，准备生成新图: object_name='{object_name}'")
                    prompt = f"""极简涂鸦风格。画风潦草，甚至有点丑。{object_name}，
粗线条手绘，简约卡通表情，背景颜色必须是纯白的。
适合社交媒体分享的正方形构图"""
                    
                    temp_url = await generate_species_image_from_prompt(prompt)
                    logger.info(f"图片生成成功，临时 URL: {temp_url}")
                    
                    # 上传到七牛云
                    timestamp = int(time.time())
                    object_name_safe = object_name.replace(" ", "_")
                    key = f"species/{object_name_safe}_{timestamp}.png"
                    
                    image_url = await save_to_qiniu(temp_url, key)
                    logger.info(f"七牛云上传成功: {image_url}")
                    
                    yield f"data: {json.dumps({'type': 'image', 'url': image_url}, ensure_ascii=False)}\n\n"
                    
                except Exception as img_error:
                    logger.error(f"图片生成/上传失败: {img_error}")
                    # 发送占位图
                    yield f"data: {json.dumps({'type': 'image', 'url': 'https://placeholder.com/species/unknown.png'}, ensure_ascii=False)}\n\n"
            
            # 获取序号并发送完成事件
            sequence_no = get_next_sequence_no()
            yield f"data: {json.dumps({'type': 'done', 'sequence_no': sequence_no}, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            logger.error(f"流式诊断失败: {type(e).__name__}: {str(e)}")
            logger.error(f"完整错误堆栈:\n{traceback.format_exc()}")
            yield f"data: {json.dumps({'type': 'error', 'message': f'诊断失败: {str(e)}'}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


@app.post("/api/diagnose", response_model=DiagnoseResponse)
async def diagnose(request: DiagnoseRequest):
    """
    诊断用户的情绪状态，返回对应的"物种"信息
    """
    logger.info(f"收到诊断请求: symptom='{request.symptom}'")
    
    if len(request.symptom) < 5 or len(request.symptom) > 50:
        logger.warning(f"症状描述长度不符合要求: {len(request.symptom)}字")
        raise HTTPException(status_code=400, detail="症状描述需要在5-50字之间")
    
    try:
        # 1. 调用 LLM 诊断
        logger.info("开始调用 LLM 诊断...")
        result = await diagnose_symptom(request.symptom)
        logger.info(f"LLM 诊断结果: {result}")
        
        # 获取序号（持久化）
        sequence_no = get_next_sequence_no()
        logger.info(f"诊断计数器: {sequence_no}")
        
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
            diagnosis=result.get("diagnosis", "你的精神物种正在鉴定中..."),
            image_url=image_url,
            sequence_no=sequence_no
        )
        logger.info(f"诊断成功，返回结果: sequence_no={sequence_no}")
        return response
        
    except Exception as e:
        # 记录详细的错误信息
        logger.error(f"诊断失败: {type(e).__name__}: {str(e)}")
        logger.error(f"完整错误堆栈:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"诊断失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9002)
