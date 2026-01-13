<template>
  <div class="result" v-if="diagnosis">
    <!-- 鉴定卡片 -->
    <div class="species-card card fade-in" ref="cardRef">
      <!-- 物种图片区 -->
      <div class="species-image">
        <div class="image-wrapper">
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

      <!-- 物种名称 + 物种分类 -->
      <div class="species-identity">
        <h1 class="species-name">{{ diagnosis.display_name }}</h1>
        <!-- <span class="species-type">
          {{ diagnosis.object_name }}
        </span> -->
      </div>

      <!-- 关键词标签 -->
      <div class="keywords">
        <span 
          v-for="(keyword, index) in diagnosis.keywords" 
          :key="index"
          class="tag"
          :class="getTagClass(index)"
        >
          #{{ keyword }}
        </span>
      </div>

      <!-- 诊断文案 -->
      <div class="diagnosis-box">
        <p class="diagnosis-text">"{{ diagnosis.diagnosis }}"</p>
      </div>

      <!-- 计数器 -->
      <div class="counter">
        ✨ 样本序列：No. {{ String(diagnosis.sequence_no).padStart(4, '0') }} ✨
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="actions">
      <button class="btn btn-green" @click="saveCard">
        💾 保存图片
      </button>
      <button class="btn" @click="diagnoseAgain">
        🔄 再测一次
      </button>
    </div>

    <!-- 分享提示 -->
    <p class="share-hint">长按图片保存后分享到朋友圈 / 小红书</p>
  </div>

  <!-- 加载状态 -->
  <div class="loading-container" v-else>
    <div class="loading"></div>
    <p>正在解析你的灵魂物种...</p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import html2canvas from 'html2canvas'

interface DiagnosisResult {
  object_name: string
  display_name: string  // 个性化展示名，如 "过劳肥的陈年咸鱼"
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

const tagClasses = ['tag-pink', 'tag-yellow', 'tag-green']

// 辅助函数：确保 URL 有协议前缀
const ensureProtocol = (url: string) => {
  if (!url) return ''
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }
  return 'http://' + url
}

onMounted(() => {
  // 从 URL 参数解析诊断结果
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
  // 图片加载失败时显示 emoji
  (e.target as HTMLImageElement).style.display = 'none';
  currentEmoji.value = '🫠';
}

const getTagClass = (index: number) => {
  return tagClasses[index % tagClasses.length]
}

const saveCard = async () => {
  if (!cardRef.value || !diagnosis.value) return
  
  try {
    const canvas = await html2canvas(cardRef.value, {
      useCORS: true,
      scale: 2, // 提高清晰度
      backgroundColor: '#FFF8E7', // 确保背景色正确
    })
    
    const link = document.createElement('a')
    link.download = `soul-species-${diagnosis.value.object_name}.png`
    link.href = canvas.toDataURL('image/png')
    link.click()
  } catch (err) {
    console.error('保存失败:', err)
    alert('保存图片失败，可能由于跨域限制，请尝试直接截图~')
  }
}

const diagnoseAgain = () => {
  router.push('/')
}
</script>

<style scoped>
.result {
  min-height: 100vh;
  padding: 24px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.species-card {
  width: 100%;
  max-width: 360px;
  padding: 24px;
  background: var(--text-light);
}

.species-image {
  margin-bottom: 16px;
}

.image-wrapper {
  width: 220px;
  height: 220px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
}

.real-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  mix-blend-mode: multiply;
}

.image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 6rem;
}

.species-identity {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: var(--accent-yellow);
  border: var(--border-thick);
  border-radius: 12px;
}

.species-name {
  font-family: var(--font-title);
  font-size: 1.3rem;
  flex: 1;
}

.species-type {
  font-size: 0.75rem;
  color: #666;
  background: #f0f0f0;
  padding: 4px 8px;
  border-radius: 6px;
  border: 1px solid #ddd;
  white-space: nowrap;
}

.keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.diagnosis-box {
  padding: 16px;
  background: var(--bg-card);
  border: var(--border-thick);
  border-radius: 16px;
  margin-bottom: 16px;
}

.diagnosis-text {
  font-size: 1rem;
  line-height: 1.6;
  color: var(--text-dark);
}

.counter {
  text-align: center;
  font-size: 0.85rem;
  color: #666;
}

.actions {
  display: flex;
  gap: 12px;
  width: 100%;
  max-width: 360px;
}

.actions .btn {
  flex: 1;
}

.share-hint {
  font-size: 0.75rem;
  color: #999;
}

.loading-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.loading-container p {
  font-family: var(--font-title);
  color: #666;
}
</style>
