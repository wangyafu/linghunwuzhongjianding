<template>
  <div class="result" v-if="diagnosis">
    <!-- 鉴定卡片 (Archive Card Style) -->
    <div class="species-card archive-card fade-in" ref="cardRef">
      
      <!-- 1. 物种图片区 (The Specimen) -->
      <div class="card-header">
        <div class="species-image-frame">
          <img 
            v-if="diagnosis.image_url" 
            :src="ensureProtocol(diagnosis.image_url)" 
            :alt="diagnosis.object_name"
            class="real-image"
            @error="handleImageError"
          />
          <div v-else class="image-placeholder">
            {{ currentEmoji }}
          </div>
        </div>
      </div>

      <div class="card-body">
        <!-- 2. 标题区 (The Identify) -->
        <div class="species-identity">
          <h1 class="species-name"> {{ diagnosis.object_name }} </h1>
      
        </div>

        <!-- 3. 正文区 (The Diagnosis) -->
        <div class="diagnosis-content">
          <p class="diagnosis-text">
            {{ diagnosis.diagnosis }}
          </p>
        </div>

        <!-- 4. 标签区 (The Tags) -->
        <div class="keywords">
          <span 
            v-for="(keyword, index) in diagnosis.keywords" 
            :key="index"
            class="archive-tag"
          >
            #{{ keyword }}
          </span>
        </div>

        <!-- 5. 底部 (The Footer) -->
        <div class="card-footer">
          <div class="stamp-box">
            <span class="stamp-label">SAMPLE NO.</span>
            <span class="stamp-number">{{ String(diagnosis.sequence_no).padStart(4, '0') }}</span>
          </div>
          <div class="date-stamp">
            {{ new Date().toLocaleDateString() }}
          </div>
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="actions">
      <button class="btn btn-primary" @click="saveCard">
        💾 收藏档案
      </button>
      <button class="btn btn-secondary" @click="diagnoseAgain">
        🔄 重启诊断
      </button>
    </div>

    <!-- 分享提示 -->
    <p class="share-hint">长按卡片保存，归档你的精神样本</p>
  </div>

  <!-- 加载状态 -->
  <div class="loading-container" v-else>
    <div class="loader-spinner"></div>
    <p class="loader-text">正在检索灵魂档案库...</p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import html2canvas from 'html2canvas'

interface DiagnosisResult {
  object_name: string
  display_name: string
  keywords: string[]
  diagnosis: string
  image_url: string
  sequence_no: number
}

const route = useRoute()
const router = useRouter()
const cardRef = ref<HTMLElement | null>(null)
const diagnosis = ref<DiagnosisResult | null>(null)
const currentEmoji = ref('❓')

// 辅助函数：处理图片 URL
const ensureProtocol = (url: string) => {
  if (!url) return ''

  // 1. 如果是 HTTPS，直接返回
  if (url.startsWith('https://')) {
    return url
  }

  // 2. 补全协议（如果是无协议的链接，默认为 http）
  let fullUrl = url
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    fullUrl = 'http://' + url
  }

  // 3. 针对七牛云测试域名（HTTP Only），使用 wsrv.nl 进行 HTTPS 代理
  // 只有这样才能在 HTTPS 网站（如 Pages）上显示 HTTP 图片
  if (fullUrl.startsWith('http://')) {
    return `https://wsrv.nl/?url=${encodeURIComponent(fullUrl)}`
  }

  return fullUrl
}

onMounted(() => {
  const dataParam = route.query.data as string
  if (dataParam) {
    try {
      diagnosis.value = JSON.parse(decodeURIComponent(dataParam))
    } catch (e) {
      console.error('解析诊断结果失败:', e)
      router.push('/')
    }
  } else {
    router.push('/')
  }
})

const handleImageError = (e: Event) => {
  (e.target as HTMLImageElement).style.display = 'none';
  currentEmoji.value = '🫠';
}

const saveCard = async () => {
  if (!cardRef.value || !diagnosis.value) return
  
  try {
    const canvas = await html2canvas(cardRef.value, {
      useCORS: true,
      scale: 2,
      backgroundColor: null, // 透明背景，保留卡片的圆角和阴影
    })
    
    const link = document.createElement('a')
    link.download = `specimen-${String(diagnosis.value.sequence_no).padStart(4, '0')}.png`
    link.href = canvas.toDataURL('image/png')
    link.click()
  } catch (err) {
    console.error('保存失败:', err)
    alert('保存失败，请手动截图留念')
  }
}

const diagnoseAgain = () => {
  router.push('/')
}
</script>

<style scoped>
/* 全局容器 */
.result {
  min-height: 100vh;
  padding: 40px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  background-color: #f4f1ea; /* 页面的背景色，区别于卡片 */
  font-family: 'Courier New', Courier, monospace;
}

/* 档案卡片主体 */
.archive-card {
  width: 100%;
  max-width: 320px; /* 拍立得尺寸感 */
  background: #fffdf5; /* 米黄色纸张 */
  background-image: 
    linear-gradient(#eee .1em, transparent .1em),
    radial-gradient(#f0f0f0 10%, transparent 10%); /* 极其细微的噪点/纹理 */
  background-size: 100% 100%, 3px 3px;
  
  padding: 24px 20px 32px;
  box-shadow: 
    0 4px 6px -1px rgba(0, 0, 0, 0.1), 
    0 2px 4px -1px rgba(0, 0, 0, 0.06),
    0 0 0 1px rgba(0,0,0,0.05); /* 纸张边缘 */
  border-radius: 2px;
  margin-bottom: 32px;
  position: relative;
  
  /* 纸张质感 */
  filter: contrast(0.98);
}

/* 1. 图片区 */
.card-header {
  margin-bottom: 24px;
  display: flex;
  justify-content: center;
}

.species-image-frame {
  width: 240px;
  height: 240px;
  border: 2px solid #1a1a1a; /* 黑色细框 */
  background: #fff;
  padding: 8px; /* 相框留白 */
  box-shadow: 2px 2px 0 rgba(0,0,0,0.1);
  transform: rotate(-1deg); /* 微微歪斜的手工感 */
}

.real-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: sepia(0.2) contrast(1.1); /* 复古滤镜 */
  mix-blend-mode: multiply; /* 融入纸张 */
}

.image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 4rem;
  background: #f0f0f0;
}

/* 2. 标题区 */
.species-identity {
  text-align: center;
  margin-bottom: 20px;
  border-bottom: 1px solid rgba(0,0,0,0.1);
  padding-bottom: 16px;
}

.species-name {
  font-family: "Songti SC", "SimSun", "STSong", serif; /* 宋体 */
  font-size: 1.6rem;
  font-weight: 900;
  color: #1a1a1a;
  margin: 0 0 8px 0;
  letter-spacing: 1px;
}

.species-latin {
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.8rem;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 2px;
}

/* 3. 正文区 */
.diagnosis-content {
  margin-bottom: 20px;
  padding: 0 8px;
}

.diagnosis-text {
  font-family: 'Courier New', Courier, monospace; /* 打字机字体 */
  font-size: 0.95rem;
  line-height: 1.8;
  color: #333;
  text-align: justify;
  white-space: pre-wrap;
}

/* 4. 标签区 */
.keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 28px;
  padding: 0 8px;
  justify-content: flex-start;
}

.archive-tag {
  font-family: sans-serif;
  font-size: 0.85rem;
  color: #8b0000; /* 深红印泥色 */
  font-weight: bold;
  opacity: 0.8;
}

/* 5. 底部 */
.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  padding-top: 16px;
  border-top: 2px dashed #ddd;
}

.stamp-box {
  border: 2px solid #d32f2f; /* 红色印章框 */
  color: #d32f2f;
  padding: 4px 8px;
  border-radius: 4px;
  transform: rotate(-2deg);
  display: flex;
  flex-direction: column;
  align-items: center;
  line-height: 1;
}

.stamp-label {
  font-size: 0.6rem;
  font-weight: bold;
}

.stamp-number {
  font-family: 'Courier New', Courier, monospace;
  font-size: 1.2rem;
  font-weight: 900;
  letter-spacing: 2px;
}

.date-stamp {
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.75rem;
  color: #999;
  transform: rotate(1deg);
}

/* 按钮样式 */
.actions {
  display: flex;
  gap: 16px;
  width: 100%;
  max-width: 320px;
}

.btn {
  flex: 1;
  padding: 12px;
  border: 2px solid #1a1a1a;
  background: transparent;
  font-family: 'Courier New', Courier, monospace;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s;
  border-radius: 8px;
}

.btn-primary {
  background: #1a1a1a;
  color: #fff;
}

.btn-primary:active {
  transform: translateY(2px);
}

.btn-secondary {
  background: #fff;
  color: #1a1a1a;
}

.btn-secondary:active {
  background: #f0f0f0;
}

.share-hint {
  font-size: 0.8rem;
  color: #888;
  font-family: 'Courier New', Courier, monospace;
  margin-top: 16px;
}

/* Loading */
.loader-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #ddd;
  border-top-color: #1a1a1a;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.loader-text {
  font-family: 'Courier New', Courier, monospace;
  margin-top: 16px;
  color: #666;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
