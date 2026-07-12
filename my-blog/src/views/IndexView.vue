<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { useSiteStore } from '@/stores/site'
import { useTypewriter } from '@/composables/useTypewriter'

const siteStore = useSiteStore()
const { typewriterText } = useTypewriter(() => siteStore.siteConfig.signature)

const engines = [
  { label: 'Bing', value: 'bing', icon: '/icon/bing.ico', url: 'https://cn.bing.com/search?q=' },
  { label: '百度', value: 'baidu', icon: '/icon/baidu.ico', url: 'https://www.baidu.com/s?wd=' }
]
const selectedEngine = ref(engines[0])
const engineDropdownOpen = ref(false)
const searchQuery = ref('')
const engineBtnRef = ref()
const engineDropdownRef = ref()
const searchBarRef = ref()

function selectEngine(e) {
  selectedEngine.value = e
  engineDropdownOpen.value = false
}

function handleSearch(queryStr) {
  const q = (queryStr || searchQuery.value).trim()
  if (!q) return
  window.open(selectedEngine.value.url + encodeURIComponent(q), '_blank')
}

function toggleDropdown() {
  engineDropdownOpen.value = !engineDropdownOpen.value
}

function handleClickOutside(e) {
  if (
    engineDropdownRef.value &&
    !engineDropdownRef.value.contains(e.target) &&
    engineBtnRef.value &&
    !engineBtnRef.value.contains(e.target)
  ) {
    engineDropdownOpen.value = false
  }
}

let suggestTimer = null
function fetchSuggestions(queryStr, cb) {
  if (!queryStr || !queryStr.trim()) {
    cb([])
    return
  }
  clearTimeout(suggestTimer)
  suggestTimer = setTimeout(() => {
    loadSuggestions(queryStr.trim(), cb)
  }, 250)
}

let jsonpIdx = 0
function jsonp(url, cbName) {
  return new Promise((resolve, reject) => {
    const id = 'jsonp_' + jsonpIdx++
    const script = document.createElement('script')
    const timeout = setTimeout(() => {
      cleanup()
      reject(new Error('timeout'))
    }, 3000)
    function cleanup() {
      clearTimeout(timeout)
      if (script.parentNode) script.parentNode.removeChild(script)
      delete window[id]
    }
    window[id] = (data) => {
      cleanup()
      resolve(data)
    }
    script.src = url + '&' + cbName + '=' + id
    script.onerror = () => {
      cleanup()
      reject(new Error('network error'))
    }
    document.head.appendChild(script)
  })
}

async function loadSuggestions(q, cb) {
  try {
    const data = await jsonp('https://suggestion.baidu.com/su?wd=' + encodeURIComponent(q), 'cb')
    const items = (data.s || []).map((s) => ({ value: s }))
    cb(items)
  } catch (_) {
    cb([])
  }
}

function handleSelect(item) {
  handleSearch(item.value)
}

// ===== 日历小组件 =====
const now = new Date()
const calYear = ref(now.getFullYear())
const calMonth = ref(now.getMonth())
const today = now.getDate()
const todayYear = now.getFullYear()
const todayMonth = now.getMonth()

const WEEKDAYS = ['一', '二', '三', '四', '五', '六', '日']

const calDays = computed(() => {
  const firstDay = new Date(calYear.value, calMonth.value, 1)
  const startDow = firstDay.getDay()
  const adjustedStart = startDow === 0 ? 6 : startDow - 1
  const daysInMonth = new Date(calYear.value, calMonth.value + 1, 0).getDate()
  const prevMonthDays = new Date(calYear.value, calMonth.value, 0).getDate()

  const cells = []
  for (let i = adjustedStart - 1; i >= 0; i--) {
    cells.push({ day: prevMonthDays - i, type: 'prev' })
  }
  for (let d = 1; d <= daysInMonth; d++) {
    const isToday = calYear.value === todayYear && calMonth.value === todayMonth && d === today
    cells.push({ day: d, type: isToday ? 'today' : 'cur' })
  }
  const remaining = 7 - (cells.length % 7 || 7)
  if (remaining < 7) {
    for (let d = 1; d <= remaining; d++) {
      cells.push({ day: d, type: 'next' })
    }
  }
  return cells
})

function prevMonth() {
  if (calMonth.value === 0) {
    calYear.value--
    calMonth.value = 11
  } else {
    calMonth.value--
  }
}
function nextMonth() {
  if (calMonth.value === 11) {
    calYear.value++
    calMonth.value = 0
  } else {
    calMonth.value++
  }
}

const blockMinHeight = computed(() => {
  if (siteStore.bannerWrapperHeight === '100vh') return 'calc(100vh - 80px)'
  return 'calc(100vh - 120px)'
})

onMounted(() => document.addEventListener('click', handleClickOutside))
onUnmounted(() => document.removeEventListener('click', handleClickOutside))
</script>

<template>
  <div class="home-container">
    <header
      v-if="siteStore.bannerMode !== 'hidden'"
      :class="['banner', siteStore.bannerMode]"
      :style="{ height: siteStore.bannerWrapperHeight }"
    >
      <el-carousel
        :interval="4000"
        arrow="always"
        class="banner-carousel"
        :height="siteStore.carouselHeight"
      >
        <el-carousel-item v-for="(img, index) in siteStore.bannerImages" :key="index">
          <img :src="img" class="carousel-img" alt="banner" />
        </el-carousel-item>
      </el-carousel>

      <div v-if="siteStore.bannerMode === 'background'" class="banner-overlay"></div>

      <h1 v-if="siteStore.bannerMode !== 'background'" class="blog-title">
        {{ siteStore.siteConfig.name }}'s Blog
        <p class="blog-subtitle">{{ typewriterText }}<span class="cursor">|</span></p>
      </h1>

      <div
        v-if="siteStore.bannerMode === 'banner' || siteStore.bannerMode === 'fullscreen'"
        class="waves-container"
      >
        <svg
          class="waves"
          xmlns="http://www.w3.org/2000/svg"
          xmlns:xlink="http://www.w3.org/1999/xlink"
          viewBox="0 24 150 28"
          preserveAspectRatio="none"
        >
          <defs>
            <path
              id="gentle-wave"
              d="M-160 44c30 0 58-18 88-18s 58 18 88 18 58-18 88-18 58 18 88 18 v44h-352z"
            />
          </defs>
          <g class="parallax">
            <use xlink:href="#gentle-wave" x="48" y="0" class="wave wave1" />
            <use xlink:href="#gentle-wave" x="48" y="3" class="wave wave2" />
            <use xlink:href="#gentle-wave" x="48" y="5" class="wave wave3" />
            <use xlink:href="#gentle-wave" x="48" y="7" class="wave wave4" />
          </g>
        </svg>
      </div>
    </header>

    <div
      class="main-content-wrapper"
      :style="{ paddingTop: siteStore.contentPaddingTop, marginTop: siteStore.contentMarginTop }"
    >
      <div class="glass-box search-block" :style="{ minHeight: blockMinHeight }">
        <div class="search-area">
          <div ref="searchBarRef" class="search-bar-wrapper">
            <button ref="engineBtnRef" type="button" class="engine-btn" @click="toggleDropdown">
              <img :src="selectedEngine.icon" class="engine-icon" :alt="selectedEngine.label" />
              <svg class="engine-arrow" viewBox="0 0 12 12" width="10" height="10">
                <path fill="none" d="M3 4.5l3 3 3-3" stroke="#999" stroke-width="1.5" />
              </svg>
            </button>

            <div class="search-divider"></div>

            <el-autocomplete
              v-model="searchQuery"
              :fetch-suggestions="fetchSuggestions"
              :trigger-on-focus="false"
              clearable
              size="large"
              placeholder="输入关键词，搜索你想要的内容..."
              class="search-input-body"
              :popper-append-to-body="false"
              @select="handleSelect"
              @keydown.enter="handleSearch()"
            />

            <!-- 引擎下拉菜单 -->
            <div v-show="engineDropdownOpen" ref="engineDropdownRef" class="engine-dropdown">
              <button
                v-for="e in engines"
                :key="e.value"
                type="button"
                class="engine-option"
                :class="{ active: e.value === selectedEngine.value }"
                @click="selectEngine(e)"
              >
                <img :src="e.icon" class="engine-opt-icon" :alt="e.label" />
                <span class="engine-opt-label">{{ e.label }}</span>
              </button>
            </div>
          </div>
        </div>

        <!-- 小组件网格区 -->
        <div class="widget-grid">
          <div class="widget-cell widget-add">
            <el-icon :size="28"><Plus /></el-icon>
            <span>添加</span>
          </div>

          <div class="widget-cell widget-calendar cell-2x2">
            <div class="cal-header">
              <button class="cal-nav" @click="prevMonth">&lt;</button>
              <span class="cal-title">{{ calYear }}年 {{ calMonth + 1 }}月</span>
              <button class="cal-nav" @click="nextMonth">&gt;</button>
            </div>
            <div class="cal-weekdays">
              <span v-for="w in WEEKDAYS" :key="w" class="cal-wd">{{ w }}</span>
            </div>
            <div class="cal-grid">
              <span
                v-for="(cell, i) in calDays"
                :key="i"
                class="cal-day"
                :class="{
                  'is-prev': cell.type === 'prev',
                  'is-next': cell.type === 'next',
                  'is-today': cell.type === 'today'
                }"
              >
                {{ cell.day }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home-container {
  width: 100%;
}

/* ===== Banner ===== */
.banner {
  position: relative;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  transition: height 0.5s ease;
}
.banner.background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 0;
}
.banner.banner,
.banner.fullscreen {
  z-index: 1;
}
.banner-carousel {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  z-index: 1;
}
.carousel-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.banner-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.2);
  z-index: 2;
  pointer-events: none;
}
.blog-title {
  position: relative;
  z-index: 3;
  font-size: 5rem;
  font-weight: 900;
  color: #fff;
  text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.5);
  text-align: center;
  margin-top: -60px;
}
.blog-subtitle {
  font-size: 2rem;
  font-weight: normal;
  margin-top: 10px;
  text-shadow: 1px 1px 5px rgba(0, 0, 0, 0.8);
  min-height: 2.2rem;
}
.cursor {
  display: inline-block;
  width: 3px;
  background-color: transparent;
  animation: blink 1s infinite;
  margin-left: 2px;
  color: #fff;
}
@keyframes blink {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0;
  }
}
.waves-container {
  position: absolute;
  bottom: 0px;
  left: 0;
  width: 100%;
  height: 6vw;
  min-height: 100px;
  z-index: 10;
  line-height: 0;
}
.waves {
  width: 100%;
  height: 100%;
  display: block;
}
.wave1,
.wave2,
.wave3,
.wave4 {
  transition: fill 0.3s ease;
}
.wave1 {
  fill: rgba(244, 244, 245, 0.3);
}
.wave2 {
  fill: rgba(244, 244, 245, 0.5);
}
.wave3 {
  fill: rgba(244, 244, 245, 0.7);
}
.wave4 {
  fill: #f4f4f5;
}
html.dark .wave1 {
  fill: rgba(43, 34, 61, 0.3);
}
html.dark .wave2 {
  fill: rgba(43, 34, 61, 0.5);
}
html.dark .wave3 {
  fill: rgba(43, 34, 61, 0.7);
}
html.dark .wave4 {
  fill: #1a1525;
}
.parallax > use {
  animation: move-forever 25s cubic-bezier(0.55, 0.5, 0.45, 0.5) infinite;
}
.parallax > use:nth-child(1) {
  animation-delay: -2s;
  animation-duration: 7s;
}
.parallax > use:nth-child(2) {
  animation-delay: -3s;
  animation-duration: 10s;
}
.parallax > use:nth-child(3) {
  animation-delay: -4s;
  animation-duration: 13s;
}
.parallax > use:nth-child(4) {
  animation-delay: -5s;
  animation-duration: 20s;
}
@keyframes move-forever {
  0% {
    transform: translate3d(-90px, 0, 0);
  }
  100% {
    transform: translate3d(85px, 0, 0);
  }
}

.main-content-wrapper {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px 40px 20px;
  position: relative;
  z-index: 10;
  transition:
    padding-top 0.5s ease,
    margin-top 0.5s ease;
}

/* ===== 搜索板块 ===== */
.search-block {
  position: relative;
  display: flex;
  flex-direction: column;
  overflow: visible;
}

.search-area {
  display: flex;
  justify-content: center;
  padding: 32px 0 24px 0;
}

.search-bar-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
  max-width: 640px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.5);
  transition: border-color 0.2s;
}
.search-bar-wrapper:focus-within {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.15);
}
html.dark .search-bar-wrapper {
  border-color: rgba(255, 255, 255, 0.1);
  background: rgba(0, 0, 0, 0.2);
}
html.dark .search-bar-wrapper:focus-within {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.25);
}

.engine-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
  padding: 6px 10px;
  border: none;
  background: transparent;
  cursor: pointer;
  transition: background 0.2s;
  line-height: 1;
}
.engine-btn:hover {
  background: rgba(0, 0, 0, 0.05);
}
html.dark .engine-btn:hover {
  background: rgba(255, 255, 255, 0.06);
}

.engine-icon {
  width: 22px;
  height: 22px;
  flex-shrink: 0;
}

.engine-arrow {
  flex-shrink: 0;
  transition: transform 0.2s;
  opacity: 0.5;
}

.search-divider {
  width: 1px;
  height: 22px;
  background: rgba(0, 0, 0, 0.12);
  flex-shrink: 0;
}
html.dark .search-divider {
  background: rgba(255, 255, 255, 0.12);
}

.search-input-body {
  flex: 1;
  min-width: 0;
}
.search-input-body :deep(.el-input__wrapper) {
  box-shadow: none;
  background: transparent;
  padding: 1px 11px;
  border-radius: 0;
}
.search-input-body :deep(.el-autocomplete__suggestions) {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  border-radius: 10px;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
}

/* ===== 引擎下拉菜单 ===== */
.engine-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  left: 4px;
  display: flex;
  gap: 8px;
  padding: 10px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
  z-index: 100;
  border: 1px solid rgba(0, 0, 0, 0.06);
}
html.dark .engine-dropdown {
  background: #2a2a2a;
  border-color: rgba(255, 255, 255, 0.08);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
}

.engine-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px 16px;
  border: 2px solid transparent;
  border-radius: 10px;
  background: transparent;
  cursor: pointer;
  transition: all 0.2s;
  color: #333;
}
.engine-option:hover {
  background: rgba(0, 0, 0, 0.04);
}
.engine-option.active {
  border-color: #409eff;
  background: rgba(64, 158, 255, 0.06);
}
html.dark .engine-option {
  color: #eee;
}
html.dark .engine-option:hover {
  background: rgba(255, 255, 255, 0.06);
}

.engine-opt-icon {
  width: 28px;
  height: 28px;
  flex-shrink: 0;
}

.engine-opt-label {
  font-size: 0.82rem;
  font-weight: 500;
  white-space: nowrap;
}

/* ===== 小组件网格区 ===== */
.widget-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  grid-auto-rows: 120px;
  gap: 16px;
  padding: 0 8px 8px 8px;
  flex: 1;
}

.widget-cell {
  border-radius: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.35);
  border: 1px solid rgba(0, 0, 0, 0.06);
  transition:
    transform 0.2s,
    box-shadow 0.2s;
  overflow: hidden;
}
.widget-cell:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}
html.dark .widget-cell {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.06);
}

.widget-add {
  color: #909399;
  gap: 4px;
  cursor: pointer;
  font-size: 0.85rem;
}
.widget-add:hover {
  color: #409eff;
}

.cell-2x2 {
  grid-row: span 2;
  grid-column: span 2;
}

/* ===== 日历小组件 ===== */
.widget-calendar {
  align-items: stretch;
  justify-content: flex-start;
  padding: 10px 12px 8px 12px;
}

.cal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.cal-title {
  font-size: 0.88rem;
  font-weight: 600;
  color: #333;
}
html.dark .cal-title {
  color: #eee;
}

.cal-nav {
  width: 22px;
  height: 22px;
  border: none;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.04);
  color: #666;
  font-size: 0.75rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  transition: background 0.2s;
}
.cal-nav:hover {
  background: rgba(0, 0, 0, 0.1);
}
html.dark .cal-nav {
  background: rgba(255, 255, 255, 0.06);
  color: #ccc;
}

.cal-weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  text-align: center;
  margin-bottom: 2px;
}

.cal-wd {
  font-size: 0.65rem;
  color: #999;
  padding: 2px 0;
}

.cal-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  text-align: center;
  flex: 1;
}

.cal-day {
  font-size: 0.72rem;
  padding: 2px 0;
  color: #444;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}
html.dark .cal-day {
  color: #ccc;
}

.cal-day.is-prev,
.cal-day.is-next {
  color: #ccc;
}
html.dark .cal-day.is-prev,
html.dark .cal-day.is-next {
  color: #555;
}

.cal-day.is-today {
  background: #409eff;
  color: #fff;
  font-weight: 600;
  border-radius: 50%;
}

@media screen and (max-width: 768px) {
  .blog-title {
    font-size: 2rem !important;
    margin-top: 10px !important;
    padding: 0 10px;
  }
  .blog-subtitle {
    font-size: 1rem !important;
    margin-top: 5px !important;
    min-height: 1.5rem !important;
  }
  .banner-carousel,
  .banner {
    height: 300px !important;
  }
  .waves-container {
    bottom: -15px !important;
  }
  .main-content-wrapper {
    padding: 20px 10px 20px 10px !important;
  }
  .search-area {
    padding: 16px 0 12px 0;
  }
  .widget-grid {
    grid-template-columns: repeat(3, 1fr);
    grid-auto-rows: 100px;
    gap: 10px;
  }
  .engine-option {
    padding: 8px 12px;
  }
}
</style>
