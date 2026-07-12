<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useSiteStore } from '@/stores/site'
import { useTypewriter } from '@/composables/useTypewriter'

const siteStore = useSiteStore()
const { typewriterText } = useTypewriter(() => siteStore.siteConfig.signature)

const engines = [
  { label: 'Bing', value: 'bing', url: 'https://cn.bing.com/search?q=' },
  { label: '百度', value: 'baidu', url: 'https://www.baidu.com/s?wd=' }
]
const selectedEngine = ref(engines[0])
const engineDropdownOpen = ref(false)
const searchQuery = ref('')
const engineBtnRef = ref()
const engineDropdownRef = ref()

function selectEngine(e) {
  selectedEngine.value = e
  engineDropdownOpen.value = false
}

function handleSearch() {
  const q = searchQuery.value.trim()
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

onMounted(() => document.addEventListener('click', handleClickOutside))
onUnmounted(() => document.removeEventListener('click', handleClickOutside))
</script>

<template>
  <div class="home-container">
    <!-- Banner -->
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

    <!-- 主体内容区 -->
    <div
      class="main-content-wrapper"
      :style="{ paddingTop: siteStore.contentPaddingTop, marginTop: siteStore.contentMarginTop }"
    >
      <div class="glass-box search-block">
        <div class="search-row">
          <button ref="engineBtnRef" type="button" class="engine-btn" @click="toggleDropdown">
            <svg
              v-if="selectedEngine.value === 'bing'"
              class="engine-icon"
              viewBox="0 0 24 24"
              width="24"
              height="24"
            >
              <path
                fill="#008373"
                d="M5.71 3.7l2.56 7.18L3 13.44l7.67 1.1 2.59 7.18 2.58-7.18L23.5 13.44l-5.27-2.56 2.56-7.18-5.28 2.54z"
              />
            </svg>
            <svg v-else class="engine-icon" viewBox="0 0 24 24" width="24" height="24">
              <path
                fill="#2932E1"
                d="M12 2c-1.5 0-3 .5-4 1.5C6.5 5 6 7 6 9c0 1.5.5 3 1.5 4.5C9 15 10.5 16 12 16c1.5 0 3-.5 4.5-1.5 1-1 2-2 2.5-3.5H13v-2h7c.5-1 .5-2 .5-3 0-2-.5-3.5-1.5-4.5C17.5 2.5 15 2 12 2zm-2 2.5c.5-.5 1.2-.8 2-.8s1.5.3 2 .8c.5.5.8 1.2.8 2s-.3 1.5-.8 2c-.5.5-1.2.8-2 .8s-1.5-.3-2-.8c-.5-.5-.8-1.2-.8-2s.3-1.5.8-2zM6 7c0-.5 0-1 .2-1.5l1 3L6 8c-.5.5-1 1.2-1 2s.5 1.5 1 2c.5.5 1 .8 1.5 1l-1 3c-.5-.5-1-1-1.5-2C4 11.5 3.5 10 3.5 8.5 3.5 7 4 5.8 5 5c.3-.3.6-.5 1-.7V7z"
              />
            </svg>
            <svg class="engine-arrow" viewBox="0 0 12 12" width="10" height="10">
              <path fill="none" d="M3 4.5l3 3 3-3" stroke="#999" stroke-width="1.5" />
            </svg>
          </button>

          <div class="search-divider"></div>

          <el-input
            v-model="searchQuery"
            size="large"
            placeholder="输入关键词，搜索你想要的内容..."
            class="search-input-body"
            clearable
            @keydown.enter="handleSearch"
          />
        </div>

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
            <svg
              v-if="e.value === 'bing'"
              class="engine-opt-icon"
              viewBox="0 0 24 24"
              width="32"
              height="32"
            >
              <path
                fill="#008373"
                d="M5.71 3.7l2.56 7.18L3 13.44l7.67 1.1 2.59 7.18 2.58-7.18L23.5 13.44l-5.27-2.56 2.56-7.18-5.28 2.54z"
              />
            </svg>
            <svg v-else class="engine-opt-icon" viewBox="0 0 24 24" width="32" height="32">
              <path
                fill="#2932E1"
                d="M12 2c-1.5 0-3 .5-4 1.5C6.5 5 6 7 6 9c0 1.5.5 3 1.5 4.5C9 15 10.5 16 12 16c1.5 0 3-.5 4.5-1.5 1-1 2-2 2.5-3.5H13v-2h7c.5-1 .5-2 .5-3 0-2-.5-3.5-1.5-4.5C17.5 2.5 15 2 12 2zm-2 2.5c.5-.5 1.2-.8 2-.8s1.5.3 2 .8c.5.5.8 1.2.8 2s-.3 1.5-.8 2c-.5.5-1.2.8-2 .8s-1.5-.3-2-.8c-.5-.5-.8-1.2-.8-2s.3-1.5.8-2zM6 7c0-.5 0-1 .2-1.5l1 3L6 8c-.5.5-1 1.2-1 2s.5 1.5 1 2c.5.5 1 .8 1.5 1l-1 3c-.5-.5-1-1-1.5-2C4 11.5 3.5 10 3.5 8.5 3.5 7 4 5.8 5 5c.3-.3.6-.5 1-.7V7z"
              />
            </svg>
            <span class="engine-opt-label">{{ e.label }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home-container {
  width: 100%;
}

/* ===== Banner 样式 ===== */
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

/* ===== 搜索区 ===== */
.search-block {
  position: relative;
  max-width: 720px;
  margin: 0 auto;
}

.search-row {
  display: flex;
  align-items: center;
  gap: 0;
}

.engine-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
  padding: 8px 12px;
  border: none;
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
  transition: background 0.2s;
  font-size: 0.9rem;
  font-weight: 500;
  color: #333;
  line-height: 1;
}
.engine-btn:hover {
  background: rgba(0, 0, 0, 0.05);
}
html.dark .engine-btn {
  color: #eee;
}
html.dark .engine-btn:hover {
  background: rgba(255, 255, 255, 0.08);
}

.engine-icon {
  flex-shrink: 0;
}

.engine-arrow {
  flex-shrink: 0;
  transition: transform 0.2s;
}

.search-divider {
  width: 1px;
  height: 28px;
  background: rgba(0, 0, 0, 0.12);
  flex-shrink: 0;
  margin: 0 4px;
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
}

/* ===== 引擎下拉菜单 ===== */
.engine-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  left: 8px;
  display: flex;
  gap: 8px;
  padding: 12px;
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
  gap: 6px;
  padding: 12px 18px;
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
  flex-shrink: 0;
}

.engine-opt-label {
  font-size: 0.85rem;
  font-weight: 500;
  white-space: nowrap;
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
  .engine-option {
    padding: 10px 14px;
  }
}
</style>
