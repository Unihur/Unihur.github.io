<script setup>
// 娱乐页：仅保留首页 Banner + 单个全宽娱乐板块
// 娱乐板块顶端对齐原音乐/个人信息板块最高点，宽度等于两者宽度之和（主体内容区满宽）
// 轮播图每页：左侧 16:9 主图 + 右侧信息区（名字 / 2×2 缩略图 / 标签 / 价格右下角）
// 左右翻页箭头置于图片外；下方胶囊指示器无数字、更小更紧凑
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import { useSiteStore } from '@/stores/site'
import { useTypewriter } from '@/composables/useTypewriter'

const siteStore = useSiteStore()
const { typewriterText } = useTypewriter(() => siteStore.siteConfig.signature)

// ===== 娱乐轮播数据：暂用 banner 图片，名字/标签/价格为占位，后续改读本地 JSON =====
const slides = computed(() =>
  siteStore.bannerImages.map((img, index) => ({
    image: img,
    name: `作品 ${index + 1}`,
    tags: ['标签一', '标签二', '标签三'],
    price: (index + 1) * 10
  }))
)

const carouselRef = ref()
const activeIndex = ref(0)
const carouselHeight = ref('380px')

// el-carousel change 事件参数：(newIndex, oldIndex)
const handleCarouselChange = (newIndex) => {
  activeIndex.value = newIndex
}

// 点击胶囊指示器：立刻跳转至对应顺序的图片
const goToSlide = (index) => {
  carouselRef.value?.setActiveItem(index)
}

const prevSlide = () => {
  carouselRef.value?.prev()
}

const nextSlide = () => {
  carouselRef.value?.next()
}

// 响应式高度：移动端改为纵向布局，需更高
const updateCarouselHeight = () => {
  carouselHeight.value = window.innerWidth <= 768 ? '460px' : '380px'
}

onMounted(() => {
  updateCarouselHeight()
  window.addEventListener('resize', updateCarouselHeight)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateCarouselHeight)
})
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

      <!-- 波浪特效 -->
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

    <!-- 主体内容区：仅娱乐板块，满宽，顶端对齐原音乐/个人信息板块最高点 -->
    <div
      class="main-content-wrapper"
      :style="{ paddingTop: siteStore.contentPaddingTop, marginTop: siteStore.contentMarginTop }"
    >
      <div class="glass-box entertainment-block">
        <!-- 轮播图：左箭头(图片外) + 轮播 + 右箭头(图片外) -->
        <div class="carousel-row">
          <el-button class="nav-arrow" circle :icon="ArrowLeft" @click="prevSlide" />
          <el-carousel
            ref="carouselRef"
            :interval="4000"
            arrow="never"
            indicator-position="none"
            :height="carouselHeight"
            @change="handleCarouselChange"
          >
            <el-carousel-item v-for="(slide, index) in slides" :key="index">
              <div class="slide-layout">
                <!-- 左：16:9 主图 -->
                <div class="main-image-area">
                  <img :src="slide.image" class="main-img" :alt="slide.name" />
                </div>
                <!-- 右：信息区（名字 / 2×2 缩略图 / 标签 / 价格右下角） -->
                <div class="info-area">
                  <div class="slide-name">{{ slide.name }}</div>
                  <div class="thumb-grid">
                    <div v-for="i in 4" :key="i" class="thumb">
                      <img :src="slide.image" class="thumb-img" :alt="`${slide.name} 缩略图${i}`" />
                    </div>
                  </div>
                  <div class="slide-tags">
                    <el-tag v-for="(tag, i) in slide.tags" :key="i" size="small" effect="plain">{{
                      tag
                    }}</el-tag>
                  </div>
                  <div class="slide-price">¥{{ slide.price }}</div>
                </div>
              </div>
            </el-carousel-item>
          </el-carousel>
          <el-button class="nav-arrow" circle :icon="ArrowRight" @click="nextSlide" />
        </div>

        <!-- 胶囊指示器：无数字、更小更紧凑 -->
        <div class="capsule-nav">
          <button
            v-for="(slide, index) in slides"
            :key="index"
            type="button"
            class="capsule-dot"
            :class="{ 'is-active': activeIndex === index }"
            @click="goToSlide(index)"
          ></button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
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

/* 娱乐板块：满宽 glass-box */
.entertainment-block {
  display: flex;
  flex-direction: column;
}

/* 轮播行：左右箭头(图片外) + 轮播 */
.carousel-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.carousel-row :deep(.el-carousel) {
  flex: 1;
  min-width: 0;
}
.nav-arrow {
  flex-shrink: 0;
}

/* 单页布局：左主图 + 右信息区 */
.slide-layout {
  display: flex;
  height: 100%;
  gap: 12px;
  padding: 10px;
  box-sizing: border-box;
}
.main-image-area {
  height: 100%;
  aspect-ratio: 16 / 9;
  flex-shrink: 0;
  border-radius: 8px;
  overflow: hidden;
}
.main-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

/* 右侧信息区 */
.info-area {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.slide-name {
  font-size: 1.05rem;
  font-weight: bold;
  color: #333;
}
html.dark .slide-name {
  color: #eee;
}
.thumb-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.thumb {
  aspect-ratio: 16 / 9;
  border-radius: 6px;
  overflow: hidden;
}
.thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.slide-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.slide-price {
  margin-top: auto;
  align-self: flex-end;
  font-size: 1.15rem;
  font-weight: bold;
  color: #f56c6c;
}

/* 胶囊指示器：无数字、更小、更紧凑 */
.capsule-nav {
  display: flex;
  justify-content: center;
  gap: 5px;
  margin-top: 10px;
}
.capsule-dot {
  width: 16px;
  height: 5px;
  padding: 0;
  border: none;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.2);
  cursor: pointer;
  transition: all 0.3s;
}
.capsule-dot:hover {
  background: rgba(64, 158, 255, 0.5);
}
.capsule-dot.is-active {
  width: 22px;
  background: #409eff;
}
html.dark .capsule-dot {
  background: rgba(255, 255, 255, 0.25);
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
  /* 移动端单页改为纵向布局，主图在上、信息区在下 */
  .slide-layout {
    flex-direction: column;
    overflow-y: auto;
  }
  .main-image-area {
    width: 100%;
    height: auto;
  }
}
</style>
