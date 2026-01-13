"""图库批量初始化脚本"""
import asyncio
import os
import sys
import json
import time

# 将 backend 目录加入 sys.path 以便导入 services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.image_gen import generate_species_image_from_prompt
from services.qiniu_storage import save_to_qiniu
STYLE_SUFFIX="极简涂鸦风格。画风潦草，甚至有点丑。背景颜色必须是纯白的。"
# 待生成物种列表：(物种名称, 图片描述后缀)
SPECIES_LIST =  [
    (
        "马戏团遗落的红鼻子", 
        "一个经典的红色海绵小丑鼻子，孤独地躺在聚光灯下的阴影里，表面有明显的磨损起球，透着一股滑稽后的凄凉感。"+STYLE_SUFFIX
    ),
    (
        "正在喷火的煤气罐", 
        "一个锈迹斑斑的老式液化气罐，阀门处正猛烈喷射出红蓝相间的愤怒火焰，罐体因高温微微发红膨胀，濒临爆炸边缘。"+STYLE_SUFFIX
    ),
    (
        "死活解不开的耳机线", 
        "一团纠缠得像乱麻一样的白色有线耳机，打了无数个复杂的死结，耳机头无奈地垂在两边，呈现出一种令人窒息的混乱美学。"+STYLE_SUFFIX
    ),
    (
        "一触即缩的含羞草", 
        "一株叶片紧紧闭合、蜷缩成一团的含羞草，种在一个贴着'Do Not Disturb'标签的陶土花盆里，仿佛正在进行光合作用般的自闭。"+STYLE_SUFFIX
    ),
    (
        "不可名状的混沌", 
        "一团无法被物理法则定义的灰黑色漩涡迷雾，仿佛是深渊的黑洞，隐约吞噬着周围的光线与色彩，充满神秘、虚无与未知的压迫感。"+STYLE_SUFFIX
    )
]
PRESET_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "preset_species.json")


async def process_species(name: str, desc: str):
    """处理单个物种：生成 -> 上传 -> 返回数据"""
    print(f"🔄 Processing: {name}...")
    try:
        # 1. 生成图片
        temp_url = await generate_species_image_from_prompt(desc)
        print(f"  Canvas generated: {temp_url[:50]}...")
        
        # 2. 上传七牛云
        timestamp = int(time.time())
        name_safe = name.replace(" ", "_")
        key = f"species/{name_safe}_{timestamp}.png"
        
        final_url = await save_to_qiniu(temp_url, key)
        print(f"  Upload success: {final_url}")
        
        return {
            "object_name": name,
            "image_url": final_url
        }
    except Exception as e:
        print(f"❌ Failed to process {name}: {e}")
        return None


async def main():
    print("🚀 Starting Batch Generation...")
    
    # 读取现有数据（避免覆盖未修改的）
    existing_data = []
    if os.path.exists(PRESET_FILE):
        try:
            with open(PRESET_FILE, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except:
            pass
    
    # 转换为字典方便更新
    data_map = {item["object_name"]: item for item in existing_data}
    
    results = []
    # 并发处理（或者为了稳妥起见，串行处理避免 API 限流）
    # 这里选择串行，稳一点
    for name, desc in SPECIES_LIST:
        # 如果已经存在且有有效链接（非 example），也可以选择跳过
        # if name in data_map and "example.com" not in data_map[name]["image_url"]:
        #    print(f"⏩ Skipping {name} (already exists)")
        #    continue
            
        item = await process_species(name, desc)
        if item:
            data_map[name] = item
            # 实时保存，防止中断
            with open(PRESET_FILE, "w", encoding="utf-8") as f:
                json.dump(list(data_map.values()), f, ensure_ascii=False, indent=2)
            
            # 礼貌性延迟，避免 QPS 过高
            time.sleep(1)

    print("\n✅ All done! Preset species updated.")


if __name__ == "__main__":
    asyncio.run(main())
