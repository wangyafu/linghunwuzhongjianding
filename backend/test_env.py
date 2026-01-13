"""测试环境变量加载"""
import os
from dotenv import load_dotenv

print("=" * 50)
print("环境变量测试")
print("=" * 50)

# 加载 .env
load_dotenv()

# 读取所有相关环境变量
env_vars = {
    "OPENAI_BASE_URL": os.getenv("OPENAI_BASE_URL"),
    "OPENAI_MODEL_NAME": os.getenv("OPENAI_MODEL_NAME"),
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "ARK_API_KEY": os.getenv("ARK_API_KEY"),
}

for key, value in env_vars.items():
    if key.endswith("_KEY") and value:
        # 对于 API key，只显示前后几个字符
        masked = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
        print(f"{key}: {masked} (长度: {len(value)})")
    else:
        print(f"{key}: {value}")

print("=" * 50)

# 检查 .env 文件是否存在
env_file = os.path.join(os.path.dirname(__file__), ".env")
print(f".env 文件存在: {os.path.exists(env_file)}")
if os.path.exists(env_file):
    print(f".env 文件路径: {env_file}")
