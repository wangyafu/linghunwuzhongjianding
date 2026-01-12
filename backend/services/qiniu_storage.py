"""七牛云存储服务 - 异步抓取"""
import os
import time
from qiniu import Auth, BucketManager
from dotenv import load_dotenv

load_dotenv()

QINIU_ACCESS_KEY = os.getenv("QINIU_ACCESS_KEY", "")
QINIU_SECRET_KEY = os.getenv("QINIU_SECRET_KEY", "")
QINIU_BUCKET = os.getenv("QINIU_BUCKET", "species-images")
QINIU_DOMAIN = os.getenv("QINIU_DOMAIN", "https://cdn.example.com")


async def save_to_qiniu(source_url: str, key: str) -> str:
    """
    将远程图片抓取到七牛云 (使用官方 SDK)
    
    Args:
        source_url: 源图片 URL
        key: 存储的 key
    
    Returns:
        CDN 访问链接
    """
    # 构建鉴权对象
    q = Auth(QINIU_ACCESS_KEY, QINIU_SECRET_KEY)
    
    # 构建 BucketManager 对象
    bucket = BucketManager(q)
    
    # 调用 fetch 方法 grab 远程资源
    # 注意：SDK 的 fetch 方法是同步的，但在 async 函数中调用通常问题不大，
    # 除非并发量极高需要完全非阻塞。
    # fetch(url, bucket, key)
    ret, info = bucket.fetch(source_url, QINIU_BUCKET, key)
    
    if info.status_code == 200:
        return f"{QINIU_DOMAIN}/{key}"
    else:
        error_msg = f"Qiniu Fetch Failed: {info.text_body}"
        print(f"❌ {error_msg}")
        raise Exception(error_msg)


def get_image_url(key: str) -> str:
    """获取图片的 CDN 访问链接"""
    return f"{QINIU_DOMAIN}/{key}"
