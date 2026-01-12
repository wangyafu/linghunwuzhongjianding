"""LLM 服务 - OpenAI 兼容接口"""
import os
import json
from typing import List, Dict, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

# 可配置的 OpenAI 兼容接口
client = AsyncOpenAI(
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    api_key=os.getenv("OPENAI_API_KEY", ""),
)

MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")

# 加载预置图库数据
PRESET_SPECIES_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "preset_species.json")

def load_preset_species() -> List[Dict]:
    """加载预置物种数据"""
    try:
        with open(PRESET_SPECIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load preset species: {e}")
        return []

PRESET_SPECIES = load_preset_species()
PRESET_SPECIES_NAMES = [s["object_name"] for s in PRESET_SPECIES]

def get_system_prompt() -> str:
    """构建动态 System Prompt，包含预置物种列表"""
    species_list_str = "、".join(PRESET_SPECIES_NAMES)
    
    return f"""你是【灵魂物种鉴定所】的首席鉴定官，一位见多识广、毒舌但精准的博物学家。

你的任务是将人类的情绪状态"鉴定"为一种离谱的静物或动物，并出具正式的鉴定报告。

【现有馆藏物种】
我们档案馆已经收录了以下物种：
{species_list_str}

【重要策略】
1. **优先匹配现有物种**：如果用户描述的状态与上述【现有馆藏物种】中的某一个高度契合，请直接使用该物种名称。
2. **发现新物种**：只有当用户的描述非常独特，无法用现有物种准确表达时，才创造一个新的离谱物种。

【输出规则】
你必须严格按照以下 JSON 格式输出，不要输出任何其他内容：
{{
  "object_name": "物体名称，优先从【现有馆藏物种】中选择，或者创造新的离谱物体",
  "keywords": ["标签1", "标签2", "标签3"],
  "diagnosis": "30-50字的毒舌诊断文案，既扎心又好笑",
  "rarity": "稀有度，R/SR/SSR"
}}

【语气要求】
- 像老派学者一样严肃地说着荒谬的话
- 带着"我见过太多了"的疲惫感
- 偶尔流露出不屑，但本质上是在帮用户自嘲
- 诊断文案要一本正经地胡说八道，让人破防又好笑"""


async def diagnose_symptom(symptom: str) -> dict:
    """
    调用 LLM 诊断用户的情绪状态
    
    Args:
        symptom: 用户输入的情绪/状态描述
    
    Returns:
        包含 object_name, visual_tag, keywords, diagnosis, rarity 以及可选的 image_url (如果是预置物种)
    """
    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": get_system_prompt()},
            {"role": "user", "content": f"请鉴定这个人的灵魂物种：{symptom}"}
        ],
        response_format={"type": "json_object"},
        temperature=0.9,
    )
    
    result = json.loads(response.choices[0].message.content)
    
    # 检查是否命中了预置物种
    object_name = result.get("object_name")
    for species in PRESET_SPECIES:
        if species["object_name"] == object_name:
            result["image_url"] = species["image_url"]
            print(f"Hit preset species: {object_name}")
            break
            
    return result
