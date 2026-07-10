<script setup>
// 娱乐页：仅保留首页 Banner + 单个全宽娱乐板块
// 娱乐板块顶端对齐原音乐/个人信息板块最高点，宽度等于两者宽度之和（主体内容区满宽）
// 当前内容：顶部轮播图（暂用 banner 图片）+ 下方胶囊按钮（点击跳转对应顺序）+ 左右翻页箭头
import { onMounted, onUnmounted, ref } from 'vue'
import { useSiteStore } from '@/stores/site'
import { useTypewriter } from '@/composables/useTypewriter'

const siteStore = useSiteStore()
const { typewriterText } = useTypewriter(() => siteStore.siteConfig.signature)

// ===== 娱乐轮播 =====
const carouselRef = ref()
const activeIndex = ref(0)
const carouselHeight = ref('420px')

// el-carousel change 事件参数：(newIndex, oldIndex)
const handleCarouselChange = (newIndex) => {
  activeIndex.value = newIndex
}

// 点击胶囊按钮：立刻跳转至对应顺序的图片
const goToSlide = (index) => {
  carouselRef.value?.setActiveItem(index)
}

// 响应式高度：移动端用较矮的高度
const updateCarouselHeight = () => {
  carouselHeight.value = window.innerWidth <= 768 ? '220px' : '420px'
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
        <!-- 顶部轮播图（暂用 banner 图片资源） -->
        <el-carousel
          ref="carouselRef"
          :interval="4000"
          arrow="always"
          indicator-position="none"
          :height="carouselHeight"
          @change="handleCarouselChange"
        >
          <el-carousel-item v-for="(img, index) in siteStore.bannerImages" :key="index">
            <img :src="img" class="ent-carousel-img" alt="娱乐轮播图" />
          </el-carousel-item>
        </el-carousel>

        <!-- 胶囊形状按钮：点击后轮播图立刻跳转至对应顺序的图片 -->
        <div class="capsule-nav">
          <el-button
            v-for="(img, index) in siteStore.bannerImages"
            :key="index"
            round
            size="small"
            :type="activeIndex === index ? 'primary' : 'default'"
            @click="goToSlide(index)"
          >
            {{ index + 1 }}
          </el-button>
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

/* 娱乐板块：满宽 glass-box，内部仅轮播图 + 胶囊按钮 */
.entertainment-block {
  display: flex;
  flex-direction: column;
}
.ent-carousel-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.capsule-nav {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 16px;
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
}
</style>
