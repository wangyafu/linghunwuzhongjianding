<template>
  <div class="result" v-if="diagnosis">
    <!-- 预览用鉴定卡片 (带视觉效果) -->
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
          <div class="footer-left">
            <div class="stamp-box">
              <span class="stamp-label">SAMPLE NO.</span>
              <span class="stamp-number">{{ String(diagnosis.sequence_no).padStart(4, '0') }}</span>
            </div>
            <div class="site-tag">jingshenwuzhong.pages.dev</div>
          </div>
          <div class="date-stamp">
            {{ new Date().toLocaleDateString() }}
          </div>
        </div>
      </div>
    </div>

    <!-- ========== 导出专用卡片（隐藏，无视觉效果）========== -->
    <div class="export-card-wrapper" ref="exportCardRef">
      <div class="export-card">
        <!-- 1. 物种图片区 -->
        <div class="export-card-header">
          <div class="export-image-frame">
            <img 
              v-if="diagnosis.image_url" 
              :src="ensureProtocol(diagnosis.image_url)" 
              :alt="diagnosis.object_name"
              class="export-image"
              crossorigin="anonymous"
            />
            <div v-else class="export-image-placeholder">
              {{ currentEmoji }}
            </div>
          </div>
        </div>

        <div class="export-card-body">
          <!-- 2. 标题区 -->
          <div class="export-identity">
            <h1 class="export-name">{{ diagnosis.object_name }}</h1>
          </div>

          <!-- 3. 正文区 -->
          <div class="export-diagnosis">
            <p class="export-diagnosis-text">{{ diagnosis.diagnosis }}</p>
          </div>

          <!-- 4. 标签区 -->
          <div class="export-keywords">
            <span 
              v-for="(keyword, index) in diagnosis.keywords" 
              :key="'export-' + index"
              class="export-tag"
            >
              #{{ keyword }}
            </span>
          </div>

          <!-- 5. 底部 -->
          <div class="export-footer">
            <div class="export-footer-left">
              <div class="export-stamp-box">
                <span class="export-stamp-label">SAMPLE NO.</span>
                <span class="export-stamp-number">{{ String(diagnosis.sequence_no).padStart(4, '0') }}</span>
              </div>
              <div class="export-site-tag">jingshenwuzhong.pages.dev</div>
            </div>
            <div class="export-date">
              {{ new Date().toLocaleDateString() }}
            </div>
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
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import html2canvas from 'html2canvas'
import { API_ENDPOINTS, type SSEEvent } from '@/config/api'

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
const exportCardRef = ref<HTMLElement | null>(null)  // 导出专用卡片引用
const diagnosis = ref<DiagnosisResult | null>(null)
const currentEmoji = ref('❓')
const isComplete = ref(false) // 标记是否已完成接收

let eventSource: EventSource | null = null

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

// 缓存相关函数
const getCacheKey = (symptom: string) => `diagnosis_cache_${symptom}`

const getCachedDiagnosis = (symptom: string): DiagnosisResult | null => {
  try {
    const cached = sessionStorage.getItem(getCacheKey(symptom))
    if (cached) {
      return JSON.parse(cached)
    }
  } catch (e) {
    console.error('读取缓存失败:', e)
  }
  return null
}

const saveDiagnosisToCache = (symptom: string, data: DiagnosisResult) => {
  try {
    sessionStorage.setItem(getCacheKey(symptom), JSON.stringify(data))
  } catch (e) {
    console.error('保存缓存失败:', e)
  }
}

onMounted(() => {
  const symptomParam = route.query.symptom as string
  const speciesDataParam = route.query.speciesData as string
  
  if (!symptomParam || !speciesDataParam) {
    // 缺少必要参数，返回首页
    router.push('/')
    return
  }

  // 1. 先检查缓存
  const cached = getCachedDiagnosis(symptomParam)
  if (cached && cached.diagnosis && cached.sequence_no > 0) {
    // 有完整的缓存数据，直接使用
    diagnosis.value = cached
    isComplete.value = true
    return
  }

  try {
    // 2. 无缓存，解析species数据并发起SSE请求
    const speciesData = JSON.parse(decodeURIComponent(speciesDataParam))
    
    // 立即显示物种卡片框架
    diagnosis.value = {
      object_name: speciesData.object_name || '',
      display_name: speciesData.display_name || speciesData.object_name || '',
      keywords: speciesData.keywords || [],
      diagnosis: '', // 诊断文案初始为空，等待流式接收
      image_url: speciesData.image_url || '', // 可能有预置图片
      sequence_no: 0 // 初始序号为0
    }
    
    // 建立SSE连接，接收后续数据
    const url = `${API_ENDPOINTS.diagnoseStream}?symptom=${encodeURIComponent(symptomParam)}`
    eventSource = new EventSource(url)
    
    eventSource.addEventListener('message', (event) => {
      try {
        const data: SSEEvent = JSON.parse(event.data)
        
        if (data.type === 'species') {
          // 忽略重复的species事件（因为我们已经有了初始数据）
          // 但如果有更新的信息也可以覆盖
          if (diagnosis.value) {
            // 更新可能缺失的字段
            if (data.image_url && !diagnosis.value.image_url) {
              diagnosis.value.image_url = data.image_url
            }
          }
        } else if (data.type === 'diagnosis_chunk') {
          // 追加诊断文案片段（打字机效果）
          if (diagnosis.value) {
            diagnosis.value.diagnosis += data.chunk
          }
        } else if (data.type === 'image') {
          // 更新图片URL
          if (diagnosis.value) {
            diagnosis.value.image_url = data.url
          }
        } else if (data.type === 'done') {
          // 接收完成，更新序号
          if (diagnosis.value) {
            diagnosis.value.sequence_no = data.sequence_no
            // 保存到缓存
            saveDiagnosisToCache(symptomParam, diagnosis.value)
          }
          isComplete.value = true
          eventSource?.close()
        } else if (data.type === 'error') {
          // 错误处理
          console.error('SSE错误:', data.message)
          alert(data.message || '诊断过程出了点问题')
          eventSource?.close()
        }
      } catch (e) {
        console.error('解析SSE数据失败:', e)
      }
    })
    
    eventSource.addEventListener('error', () => {
      console.error('SSE连接错误')
      eventSource?.close()
      // 即使连接出错，也允许用户查看已接收到的部分数据
      isComplete.value = true
    })
    
  } catch (e) {
    console.error('解析初始数据失败:', e)
    router.push('/')
  }
})

onUnmounted(() => {
  // 组件销毁时关闭SSE连接
  if (eventSource) {
    eventSource.close()
  }
})

const handleImageError = (e: Event) => {
  (e.target as HTMLImageElement).style.display = 'none';
  currentEmoji.value = '🫠';
}

const saveCard = async () => {
  if (!exportCardRef.value || !diagnosis.value) return
  
  // 使用导出专用卡片（隐藏的干净版本）
  const exportCard = exportCardRef.value.querySelector('.export-card') as HTMLElement
  if (!exportCard) return
  
  try {
    const canvas = await html2canvas(exportCard, {
      useCORS: true,
      scale: 2,
      backgroundColor: '#fffdf5',
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

.footer-left {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
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

.site-tag {
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.55rem;
  color: #999;
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 6px;
  border-radius: 2px;
  letter-spacing: 0.5px;
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

/* ========== 导出专用卡片样式 ========== */
/* 这个卡片完全独立于预览卡片，使用干净的样式便于 html2canvas 渲染 */

.export-card-wrapper {
  position: absolute;
  left: -9999px;
  top: 0;
  pointer-events: none;
  /* 确保在屏幕外但仍然被渲染 */
}

.export-card {
  width: 320px;
  background: #fffdf5;
  padding: 24px 20px 32px;
  border-radius: 2px;
  font-family: 'Courier New', Courier, monospace;
}

.export-card-header {
  margin-bottom: 24px;
  display: flex;
  justify-content: center;
}

.export-image-frame {
  width: 240px;
  height: 240px;
  border: 2px solid #1a1a1a;
  background: #fff;
  padding: 8px;
}

.export-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  /* 无滤镜，无混合模式 */
}

.export-image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 4rem;
  background: #f0f0f0;
}

.export-card-body {
  /* 内容区 */
}

.export-identity {
  text-align: center;
  margin-bottom: 20px;
  border-bottom: 1px solid rgba(0,0,0,0.1);
  padding-bottom: 16px;
}

.export-name {
  font-family: "Songti SC", "SimSun", "STSong", serif;
  font-size: 1.6rem;
  font-weight: 900;
  color: #1a1a1a;
  margin: 0;
  letter-spacing: 1px;
}

.export-diagnosis {
  margin-bottom: 20px;
  padding: 0 8px;
}

.export-diagnosis-text {
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.95rem;
  line-height: 1.8;
  color: #333;
  text-align: justify;
  white-space: pre-wrap;
  margin: 0;
}

.export-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 28px;
  padding: 0 8px;
  justify-content: flex-start;
}

.export-tag {
  font-family: sans-serif;
  font-size: 0.85rem;
  color: #8b0000;
  font-weight: bold;
}

.export-footer {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  padding-top: 16px;
  border-top: 2px dashed #ddd;
}

.export-footer-left {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
}

.export-stamp-box {
  border: 2px solid #d32f2f;
  color: #d32f2f;
  padding: 4px 8px;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  align-items: center;
  line-height: 1;
}

.export-stamp-label {
  font-size: 0.6rem;
  font-weight: bold;
}

.export-stamp-number {
  font-family: 'Courier New', Courier, monospace;
  font-size: 1.2rem;
  font-weight: 900;
  letter-spacing: 2px;
}

.export-site-tag {
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.55rem;
  color: #999;
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 6px;
  border-radius: 2px;
  letter-spacing: 0.5px;
}

.export-date {
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.75rem;
  color: #999;
}
</style>
