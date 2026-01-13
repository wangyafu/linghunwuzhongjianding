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
SPECIES_LIST = [
   
    ("主打嘴硬的鸭子", "一只线条极其简单、画得歪歪扭扭的鸭子，全身只有几根毛，但嘴巴画得特别大且厚实，像两块砖头叠在一起，眼神充满倔强" + STYLE_SUFFIX),
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
