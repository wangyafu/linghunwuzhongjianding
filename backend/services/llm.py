"""LLM 服务 - OpenAI 兼容接口"""
import os
import json
from typing import List, Dict, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# 获取环境变量
base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
api_key = os.getenv("OPENAI_API_KEY", "")

# 日志输出配置信息用于调试
logger.info(f"OpenAI Base URL: {base_url}")
logger.info(f"API Key 已{'设置' if api_key else '未设置'}")



# 可配置的 OpenAI 兼容接口
client = AsyncOpenAI(
    base_url=base_url,
    api_key=api_key
)

MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")

# 加载预置图库数据
PRESET_SPECIES_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "preset_species.json")
SYSTEM_PROMPT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", "system_prompt.md")

def load_preset_species() -> List[Dict]:
    """加载预置物种数据"""
    try:
        with open(PRESET_SPECIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load preset species: {e}")
        return []

def load_system_prompt_template() -> str:
    """加载 System Prompt 模板"""
    try:
        with open(SYSTEM_PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Warning: Failed to load system prompt template: {e}")
        # 返回一个基础的提示词作为后备
        return """你是灵魂物种鉴定所的首席鉴定官。请将用户的情绪状态鉴定为一种离谱的物种。
        
现有馆藏物种：
{species_list}

请以 JSON 格式输出结果。"""

PRESET_SPECIES = load_preset_species()
PRESET_SPECIES_NAMES = [s["object_name"] for s in PRESET_SPECIES]
SYSTEM_PROMPT_TEMPLATE = load_system_prompt_template()

def get_system_prompt() -> str:
    """构建动态 System Prompt，包含预置物种列表"""
    species_list_str = "、".join(PRESET_SPECIES_NAMES)
    # 替换模板中的占位符
    return SYSTEM_PROMPT_TEMPLATE.replace("{species_list}", species_list_str)


async def diagnose_symptom(symptom: str) -> dict:
    """
    调用 LLM 诊断用户的情绪状态
    
    Args:
        symptom: 用户输入的情绪/状态描述
    
    Returns:
        包含 object_name, display_name, keywords, diagnosis 以及可选的 image_url (如果是预置物种)
    """
    logger.info(f"开始调用 LLM，模型: {MODEL_NAME}")
    
    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": get_system_prompt()},
            {"role": "user", "content": f"请鉴定这个人的灵魂物种：{symptom}\n\n请严格按照 JSON 格式输出，不要添加任何其他文字。"}
        ],
        temperature=0.9,
    )
    
    logger.info("LLM 调用成功，开始解析响应")
    content = response.choices[0].message.content
    logger.info(f"LLM 原始响应: {content[:200]}...")  # 只打印前200字符
    
    # 尝试解析 JSON（可能需要清理响应）
    try:
        # 移除可能的 markdown 代码块标记
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
        elif content.startswith("```"):
            content = content.replace("```", "").strip()
        
        result = json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败: {e}")
        logger.error(f"原始内容: {content}")
        raise ValueError(f"LLM 返回的内容不是有效的 JSON: {e}")
    
    # 检查是否命中了预置物种
    object_name = result.get("object_name")
    for species in PRESET_SPECIES:
        if species["object_name"] == object_name:
            result["image_url"] = species["image_url"]
            print(f"Hit preset species: {object_name}")
            break
            
    return result
