"""流式 LLM 服务 - 支持 SSE 输出"""
import os
import json
from typing import AsyncGenerator
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

# 可配置的 OpenAI 兼容接口
client = AsyncOpenAI(
    base_url=base_url,
    api_key=api_key
)

MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")

# 加载预置图库数据
PRESET_SPECIES_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "preset_species.json")
SYSTEM_PROMPT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", "system_prompt_streaming.md")

def load_preset_species() -> list:
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
        return """你是精神物种鉴定所的首席鉴定官。请将用户的情绪状态鉴定为一种离谱的物种。

现有馆藏物种：
{species_list}

请严格按照要求的格式输出结果。"""

PRESET_SPECIES = load_preset_species()
PRESET_SPECIES_NAMES = [s["object_name"] for s in PRESET_SPECIES]
SYSTEM_PROMPT_TEMPLATE = load_system_prompt_template()

def get_system_prompt() -> str:
    """构建动态 System Prompt，包含预置物种列表"""
    species_list_str = "、".join(PRESET_SPECIES_NAMES)
    return SYSTEM_PROMPT_TEMPLATE.replace("{species_list}", species_list_str)


def get_preset_image_url(object_name: str) -> str | None:
    """检查是否命中预置物种，返回图片 URL"""
    for species in PRESET_SPECIES:
        if species["object_name"] == object_name:
            return species["image_url"]
    return None


async def diagnose_symptom_streaming(symptom: str) -> AsyncGenerator[dict, None]:
    """
    流式调用 LLM 诊断用户的情绪状态
    
    分两阶段输出：
    1. 先输出物种基础信息（object_name, display_name, keywords）
    2. 再流式输出诊断文案（diagnosis）
    
    Yields:
        dict: 包含 type 字段的事件数据
    """
    logger.info(f"开始流式调用 LLM，模型: {MODEL_NAME}")
    
    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": get_system_prompt()},
            {"role": "user", "content": f"请鉴定这个人的精神物种：{symptom}"}
        ],
        temperature=1.0,
        stream=True,
    )
    
    # 用于累积完整响应
    full_content = ""
    species_info_sent = False
    diagnosis_started = False
    diagnosis_buffer = ""
    
    async for chunk in response:
        if not chunk.choices:
            continue
            
        delta = chunk.choices[0].delta
        if not delta.content:
            continue
            
        full_content += delta.content
        
        # 尝试解析已累积的内容
        if not species_info_sent:
            # 尝试提取物种信息（在 diagnosis 字段之前）
            try:
                # 清理 markdown 代码块标记
                clean_content = full_content
                if clean_content.startswith("```json"):
                    clean_content = clean_content.replace("```json", "", 1)
                if clean_content.startswith("```"):
                    clean_content = clean_content.replace("```", "", 1)
                
                # 检查是否已经有了 diagnosis 字段的开始部分
                if '"diagnosis"' in clean_content:
                    # 提取 diagnosis 之前的部分，构造有效 JSON
                    diagnosis_idx = clean_content.index('"diagnosis"')
                    before_diagnosis = clean_content[:diagnosis_idx].rstrip().rstrip(',')
                    
                    # 尝试构造完整的 JSON 对象来提取物种信息
                    try:
                        # 添加闭合括号尝试解析
                        partial_json = before_diagnosis + "}"
                        partial_data = json.loads(partial_json)
                        
                        # 成功解析，发送物种基础信息
                        object_name = partial_data.get("object_name", "未知物种")
                        display_name = partial_data.get("display_name") or object_name
                        keywords = partial_data.get("keywords", ["神秘", "未知", "待鉴定"])
                        
                        # 检查是否命中预置图库
                        preset_image = get_preset_image_url(object_name)
                        
                        yield {
                            "type": "species",
                            "object_name": object_name,
                            "display_name": display_name,
                            "keywords": keywords,
                            "image_url": preset_image  # 如果命中预置图库则直接返回
                        }
                        
                        species_info_sent = True
                        diagnosis_started = True
                        
                        # 提取 diagnosis 字段已经生成的内容
                        after_diagnosis_key = clean_content[diagnosis_idx + len('"diagnosis"'):]
                        # 跳过冒号和引号
                        colon_idx = after_diagnosis_key.find(':')
                        if colon_idx != -1:
                            after_colon = after_diagnosis_key[colon_idx + 1:].lstrip()
                            if after_colon.startswith('"'):
                                diagnosis_buffer = after_colon[1:]  # 跳过开头引号
                                # 移除结尾引号（如果有）
                                if diagnosis_buffer.endswith('"'):
                                    diagnosis_buffer = diagnosis_buffer[:-1]
                                if diagnosis_buffer.endswith('"}'):
                                    diagnosis_buffer = diagnosis_buffer[:-2]
                                if diagnosis_buffer:
                                    yield {"type": "diagnosis_chunk", "chunk": diagnosis_buffer}
                        
                    except json.JSONDecodeError:
                        # 还不够完整，继续累积
                        pass
                        
            except Exception as e:
                logger.warning(f"解析物种信息时出错: {e}")
                
        elif diagnosis_started:
            # 流式输出 diagnosis 内容
            # 直接输出新增的 delta
            new_text = delta.content
            
            # 过滤掉 JSON 结构字符
            if '"}' in new_text or '```' in new_text:
                # 到达结尾，清理
                new_text = new_text.replace('"}', '').replace('```', '').replace('"', '')
            
            # 额外清理仅包含 } 或 ] 的残留
            if new_text.strip() in ['}', ']', '"}', '"]']:
                new_text = ""
            
            # 清理末尾可能的残留
            if new_text.endswith('"}'):
                 new_text = new_text[:-2]
            elif new_text.endswith('}'):
                 new_text = new_text[:-1]

            if new_text.strip():
                yield {"type": "diagnosis_chunk", "chunk": new_text}
    
    # 如果没有成功流式解析，尝试解析完整响应
    if not species_info_sent:
        logger.warning("流式解析失败，尝试解析完整响应")
        try:
            clean_content = full_content
            if clean_content.startswith("```json"):
                clean_content = clean_content.replace("```json", "").replace("```", "").strip()
            elif clean_content.startswith("```"):
                clean_content = clean_content.replace("```", "").strip()
            
            result = json.loads(clean_content)
            object_name = result.get("object_name", "未知物种")
            display_name = result.get("display_name") or object_name
            preset_image = get_preset_image_url(object_name)
            
            yield {
                "type": "species",
                "object_name": object_name,
                "display_name": display_name,
                "keywords": result.get("keywords", ["神秘", "未知", "待鉴定"]),
                "image_url": preset_image
            }
            
            # 一次性发送完整诊断
            diagnosis = result.get("diagnosis", "你的精神物种正在鉴定中...")
            yield {"type": "diagnosis_chunk", "chunk": diagnosis}
            
        except json.JSONDecodeError as e:
            logger.error(f"完整响应解析失败: {e}")
            logger.error(f"原始内容: {full_content}")
            yield {"type": "error", "message": "诊断解析失败，请重试"}
