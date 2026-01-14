<template>
  <div class="home">
    <!-- 标题区 -->
    <header class="header">
      <h1 class="title">灵魂物种鉴定中心</h1>
      <p class="subtitle">Institute of Spiritual Speciation</p>
    </header>

    <!-- 馆藏物种展示 -->
    <div class="species-showcase" v-if="presetSpecies.length > 0 && currentSpecies">
      <div class="species-image-container">
        <img 
          :src="currentSpecies?.image_url" 
          :alt="currentSpecies?.object_name"
          class="species-image"
          :class="{ 'fade-in': !isTransitioning }"
        />
      </div>
  
      
    </div>

    <!-- 输入区 -->
    <div class="input-section">
      <label class="input-label">状态主诉</label>
      <div class="input-wrapper">
        <textarea
          v-model="symptom"
          class="input symptom-input"
          placeholder="描述你现在的状态或情绪..."
          maxlength="50"
          @keydown.enter.prevent="handleDiagnose"
        ></textarea>
        <button class="dice-btn" @click="randomSymptom" title="随机填入">
          🎲
        </button>
      </div>
      <p class="char-count">{{ symptom.length }}/50</p>
    </div>

    <!-- 盖章按钮 -->
    <button class="btn stamp-btn btn-pink" @click="handleDiagnose" :disabled="isLoading">
      <span v-if="!isLoading">🔬 开始鉴定</span>
      <span v-else class="loading"></span>
    </button>

    <!-- 底部信息区 -->
    <div class="footer-info">
      <p class="disclaimer">仅供娱乐，如有雷同纯属巧合 ✨</p>
      <div class="footer-links">
        <button class="footer-link" @click="openContact">📮 联系作者</button>
        <button class="footer-link" @click="toggleDonateModal">🥤 请我喝奶茶</button>
      </div>
    </div>

    <!-- 打赏弹窗 -->
    <div v-if="showDonateModal" class="modal-overlay" @click.self="toggleDonateModal">
      <div class="donate-modal">
        <button class="modal-close" @click="toggleDonateModal">✕</button>
        <h3 class="modal-title">感谢您的支持</h3>
        <p class="modal-subtitle">如果觉得有趣，可以请作者喝杯奶茶~</p>
        <div class="qr-codes">
          <div class="qr-item">
            <img src="../assets/微信收款码.png" alt="微信收款码" class="qr-image" />
            <span class="qr-label">微信</span>
          </div>
          <div class="qr-item">
            <img src="../assets/支付宝收款码.jpg" alt="支付宝收款码" class="qr-image" />
            <span class="qr-label">支付宝</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { API_ENDPOINTS } from '@/config/api'

const router = useRouter()

const symptom = ref('')
const isLoading = ref(false)

// 预置物种数据
interface SpeciesItem {
  object_name: string
  image_url: string
}

const presetSpecies = ref<SpeciesItem[]>([])
const speciesIndex = ref(0)  // 改为 ref 以保持响应性
let speciesInterval: number | null = null
const isTransitioning = ref(false)

// 辅助函数：处理图片 URL
const ensureProtocol = (url: string) => {
  if (!url) return ''

  // 1. 如果是 HTTPS，直接返回
  if (url.startsWith('https://')) {
    return url
  }

  // 2. 补全协议
  let fullUrl = url
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    fullUrl = 'http://' + url
  }

  // 3. 针对 HTTP 图片，使用 wsrv.nl 代理转为 HTTPS
  if (fullUrl.startsWith('http://')) {
    return `https://wsrv.nl/?url=${encodeURIComponent(fullUrl)}`
  }

  return fullUrl
}

// 当前展示的物种
const currentSpecies = computed(() => {
  if (presetSpecies.value.length === 0) {
    return { object_name: '加载中...', image_url: '' }
  }
  const species = presetSpecies.value[speciesIndex.value]
  return {
    object_name: species?.object_name ?? '',
    image_url: ensureProtocol(species?.image_url ?? '')
  }
})

// 加载预置物种列表
const fetchPresetSpecies = async () => {
  try {
    const response = await fetch(API_ENDPOINTS.presetSpecies)
    if (response.ok) {
      presetSpecies.value = await response.json()
    }
  } catch (error) {
    console.error('Failed to fetch preset species:', error)
  }
}

// 预设的"发疯文案"
const presetSymptoms = [
  '上班如上坟，心如死灰',
  '社恐到极致，连呼吸都怕打扰别人',
  '摆烂第365天，专业练习生',
  '明明很累却睡不着，脑子里演完一整部电视剧',
  '又在假装合群了，笑得脸都僵硬',
  '工资不涨物价涨，我是韭菜我骄傲',
  '感觉自己是个无用的成年人',
  '每天都在等一个不会来的人',
  '对什么都提不起兴趣，只想躺着',
  '表面风平浪静，内心已经崩溃'
]

onMounted(async () => {
  // 加载预置物种
  await fetchPresetSpecies()
  
  // 启动物种图片轮播
  speciesInterval = window.setInterval(() => {
    if (presetSpecies.value.length > 0) {
      isTransitioning.value = true
      setTimeout(() => {
        speciesIndex.value = (speciesIndex.value + 1) % presetSpecies.value.length
        isTransitioning.value = false
      }, 300)
    }
  }, 3000)
})

onUnmounted(() => {
  if (speciesInterval) {
    clearInterval(speciesInterval)
  }
})

const randomSymptom = () => {
  const randomIndex = Math.floor(Math.random() * presetSymptoms.length)
  symptom.value = presetSymptoms[randomIndex] ?? ''
}

const handleDiagnose = async () => {
  if (symptom.value.length < 5) {
    alert('请至少输入5个字描述你的状态~')
    return
  }
  
  isLoading.value = true
  
  try {
    // 构建SSE URL
    const url = `${API_ENDPOINTS.diagnoseStream}?symptom=${encodeURIComponent(symptom.value)}`
    const eventSource = new EventSource(url)
    
    // 监听消息事件
    eventSource.addEventListener('message', (event) => {
      try {
        const data = JSON.parse(event.data)
        
        if (data.type === 'species') {
          // 收到物种信息，关闭连接并跳转到Result页面
          eventSource.close()
          isLoading.value = false
          
          router.push({
            name: 'result',
            query: {
              symptom: symptom.value,
              speciesData: encodeURIComponent(JSON.stringify(data))
            }
          })
        } else if (data.type === 'error') {
          // 收到错误
          eventSource.close()
          isLoading.value = false
          alert(data.message || '诊断过程出了点问题，请稍后再试~')
        }
      } catch (e) {
        console.error('解析SSE数据失败:', e)
      }
    })
    
    // 监听错误事件
    eventSource.addEventListener('error', () => {
      eventSource.close()
      isLoading.value = false
      alert('连接失败，请检查网络后重试~')
    })
    
  } catch (error) {
    console.error('诊断出错:', error)
    alert('诊断过程出了点问题，请稍后再试~')
    isLoading.value = false
  }
}
const CONTACT_URL = 'https://www.xiaohongshu.com/user/profile/635f85b9002000001901fe43'
const showDonateModal = ref(false)

const openContact = () => {
  window.open(CONTACT_URL, '_blank')
}

const toggleDonateModal = () => {
  showDonateModal.value = !showDonateModal.value
}

// Previous code ends here...
</script>

<style scoped>
.home {
  min-height: 100vh;
  padding: 40px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}

.header {
  text-align: center;
}

/* 物种展示区 */
.species-showcase {
  width: 100%;
  max-width: 280px;
  padding: 24px;
  text-align: center;

}

.species-image-container {
  width: 180px;
  height: 180px;
  margin: 0 auto 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.species-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0;
  transition: opacity 0.3s ease;
  mix-blend-mode: multiply;  /* 让白色背景融入页面背景 */
}

.species-image.fade-in {
  opacity: 1;
}

.species-name {
  font-family: var(--font-title);
  font-size: 1.2rem;
  color: var(--text-dark);
  margin-bottom: 8px;
}

.species-hint {
  font-size: 0.8rem;
  color: #888;
}

.title {
  font-family: var(--font-title);
  font-size: 2rem;
  color: var(--text-dark);
  margin-bottom: 4px;
}

.subtitle {
  font-size: 0.9rem;
  color: #666;
  font-style: italic;
}

.specimen-frame {
  width: 100%;
  max-width: 280px;
  padding: 24px;
  text-align: center;
  background: var(--text-light);
}

.specimen-container {
  width: 120px;
  height: 120px;
  margin: 0 auto 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
  border: var(--border-thick);
  border-radius: 50%;
}

.specimen {
  font-size: 4rem;
  transition: transform 0.3s ease;
}

.specimen-hint {
  font-size: 0.85rem;
  color: #888;
}

.input-section {
  width: 100%;
  max-width: 360px;
}

.input-label {
  display: block;
  font-family: var(--font-title);
  font-size: 1.1rem;
  margin-bottom: 8px;
}

.input-wrapper {
  position: relative;
}

.symptom-input {
  min-height: 80px;
  padding-right: 50px;
  resize: none;
}

.dice-btn {
  position: absolute;
  right: 12px;
  top: 12px;
  width: 36px;
  height: 36px;
  font-size: 1.5rem;
  background: var(--accent-yellow);
  border: 3px solid var(--text-dark);
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.15s ease;
}

.dice-btn:hover {
  transform: scale(1.1) rotate(15deg);
}

.dice-btn:active {
  transform: scale(0.95);
}

.char-count {
  text-align: right;
  font-size: 0.8rem;
  color: #888;
  margin-top: 4px;
}

.stamp-btn {
  width: 100%;
  max-width: 360px;
  padding: 16px 32px;
  font-size: 1.3rem;
}

.stamp-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.disclaimer {
  font-size: 0.75rem;
  color: #999;
  text-align: center;
}

/* 底部功能区 */
.footer-info {
  width: 100%;
  margin-top: auto;
  padding-top: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.footer-links {
  display: flex;
  justify-content: center;
  gap: 16px;
  flex-wrap: wrap;
}

.footer-link {
  padding: 8px 16px;
  font-size: 0.85rem;
  background: transparent;
  border: 1px solid #ddd;
  border-radius: 20px;
  color: #666;
  cursor: pointer;
  transition: all 0.2s ease;
}

.footer-link:hover {
  border-color: var(--accent-purple);
  color: var(--accent-purple);
  background: white;
  transform: translateY(-2px);
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
  padding: 20px;
}

.donate-modal {
  background: white;
  border-radius: 20px;
  padding: 32px;
  max-width: 400px;
  width: 100%;
  position: relative;
  text-align: center;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  animation: modalPop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes modalPop {
  from { opacity: 0; transform: scale(0.9); }
  to { opacity: 1; transform: scale(1); }
}

.modal-close {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 32px;
  height: 32px;
  border: none;
  background: #f5f5f5;
  border-radius: 50%;
  cursor: pointer;
  font-size: 14px;
  color: #999;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close:hover {
  background: #eee;
  color: #666;
}

.modal-title {
  font-family: var(--font-title);
  font-size: 1.5rem;
  color: var(--text-dark);
  margin-bottom: 8px;
}

.modal-subtitle {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 24px;
}

.qr-codes {
  display: flex;
  gap: 20px;
  justify-content: center;
}

.qr-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.qr-image {
  width: 140px;
  height: 140px;
  object-fit: cover;
  border-radius: 12px;
  border: 1px solid #eee;
}

.qr-label {
  font-size: 0.8rem;
  color: #888;
}

/* 响应式调整 */
@media (max-width: 480px) {
  .qr-image {
    width: 120px;
    height: 120px;
  }
}
</style>
