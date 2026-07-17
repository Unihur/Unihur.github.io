<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { useSiteStore } from '@/stores/site'
import { useTypewriter } from '@/composables/useTypewriter'
import gameRepository from '@/data/game_repository.json'

const route = useRoute()
const router = useRouter()
const siteStore = useSiteStore()
const { typewriterText } = useTypewriter(() => siteStore.siteConfig.signature)

const gameId = Number(route.params.slug)
const game = computed(() => gameRepository.find((g) => g.id === gameId) || null)

const tags = computed(() => {
  if (!game.value?.tag) return []
  return game.value.tag
    .split(/[,，]/)
    .map((t) => t.trim())
    .filter(Boolean)
})

const allImages = computed(() => {
  if (!game.value) return []
  return [
    game.value.img_big,
    game.value.img_1,
    game.value.img_2,
    game.value.img_3,
    game.value.img_4,
    game.value.img_5,
    game.value.img_6,
    game.value.img_7,
    game.value.img_8,
    game.value.img_9,
    game.value.img_10
  ].filter((n, i, arr) => n && arr.indexOf(n) === i)
})

const coverImage = computed(() => allImages.value[0] || '')

const activeImageIndex = ref(0)
const currentImage = computed(() => allImages.value[activeImageIndex.value] || allImages.value[0])

const thumbScrollRef = ref(null)
function scrollThumbs(dir) {
  if (thumbScrollRef.value) {
    thumbScrollRef.value.scrollBy({ left: dir * 160, behavior: 'smooth' })
  }
}

let autoTimer = null
const AUTO_INTERVAL = 4000

function nextImage() {
  if (allImages.value.length <= 1) return
  activeImageIndex.value = (activeImageIndex.value + 1) % allImages.value.length
}
function prevImage() {
  if (allImages.value.length <= 1) return
  activeImageIndex.value =
    (activeImageIndex.value - 1 + allImages.value.length) % allImages.value.length
}

function startAutoPlay() {
  stopAutoPlay()
  if (allImages.value.length <= 1) return
  autoTimer = setInterval(nextImage, AUTO_INTERVAL)
}
function stopAutoPlay() {
  if (autoTimer) {
    clearInterval(autoTimer)
    autoTimer = null
  }
}

onMounted(() => {
  startAutoPlay()
})
onUnmounted(() => {
  stopAutoPlay()
})

const imgUrl = (name) => `/game_banner/${name}.png`

function formatDate(timeStr) {
  if (!timeStr) return ''
  const d = timeStr.split(' ')[0]
  const [y, m, day] = d.split('/')
  return `${y}年${m}月${day}日`
}

function goBack() {
  router.back()
}
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

    <div
      class="main-content-wrapper"
      :style="{ paddingTop: siteStore.contentPaddingTop, marginTop: siteStore.contentMarginTop }"
    >
      <div v-if="game" class="game-detail-container glass-box">
        <button class="back-btn" @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
        </button>

        <h1 class="detail-name">{{ game.name }}</h1>

        <div class="detail-body">
          <div class="detail-gallery">
            <div class="gallery-main" @mouseenter="stopAutoPlay" @mouseleave="startAutoPlay">
              <button class="gallery-arrow gallery-prev" @click="prevImage">‹</button>
              <img :src="imgUrl(currentImage)" class="gallery-main-img" :alt="game.name" />
              <button class="gallery-arrow gallery-next" @click="nextImage">›</button>
            </div>
            <div v-if="allImages.length > 1" ref="thumbScrollRef" class="gallery-thumbs">
              <img
                v-for="(img, i) in allImages"
                :key="i"
                :src="imgUrl(img)"
                class="gallery-thumb"
                :class="{ active: i === activeImageIndex }"
                :alt="`截图 ${i + 1}`"
                @click="activeImageIndex = i"
              />
            </div>
            <div v-if="allImages.length > 5" class="thumb-nav">
              <button class="thumb-nav-btn" @click="scrollThumbs(-1)">‹</button>
              <div class="thumb-scroll-track">
                <div class="thumb-scroll-thumb"></div>
              </div>
              <button class="thumb-nav-btn" @click="scrollThumbs(1)">›</button>
            </div>
          </div>

          <div class="detail-info">
            <div class="info-cover">
              <img :src="imgUrl(coverImage)" :alt="game.name" />
            </div>

            <div class="info-desc">{{ game.des }}</div>

            <div class="info-meta">
              <div class="meta-item">
                <span class="meta-label">发行时间</span>
                <span class="meta-value">{{ formatDate(game.time) }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">用户评分</span>
                <span class="meta-value rating">{{ game.rating }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">开发商</span>
                <span class="meta-value">{{ game.developer || '-' }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">发行商</span>
                <span class="meta-value">{{ game.publisher || '-' }}</span>
              </div>
            </div>

            <div class="info-tags">
              <el-tag v-for="tag in tags" :key="tag" size="small">{{ tag }}</el-tag>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="game-not-found">
        <h2>游戏不存在</h2>
        <el-button @click="goBack">返回</el-button>
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

/* ===== 游戏详情样式 ===== */
.game-detail-container {
  max-width: 1100px;
  margin: 0 auto 20px;
  position: relative;
}
.game-detail-container.glass-box {
  padding: 32px 28px;
}

.back-btn {
  position: absolute;
  top: 16px;
  left: 20px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  font-size: 1.1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
  z-index: 10;
}
.back-btn:hover {
  background: rgba(0, 0, 0, 0.75);
}

.detail-name {
  font-size: 1.8rem;
  font-weight: 700;
  color: #333;
  margin: 0 0 24px 48px;
}
html.dark .detail-name {
  color: #eee;
}

.detail-body {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

/* ---- 左侧轮播图 ---- */
.detail-gallery {
  flex: 1;
  min-width: 0;
}

.gallery-main {
  position: relative;
  aspect-ratio: 16 / 9;
  border-radius: 10px;
  overflow: hidden;
  background: #1a1a2e;
}

.gallery-main-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.gallery-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.45);
  color: #fff;
  font-size: 1.5rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
  z-index: 5;
  line-height: 1;
}
.gallery-arrow:hover {
  background: rgba(0, 0, 0, 0.7);
}
.gallery-prev {
  left: 10px;
}
.gallery-next {
  right: 10px;
}

.gallery-thumbs {
  display: flex;
  gap: 8px;
  margin-top: 10px;
  overflow-x: auto;
  padding-bottom: 4px;
}
.gallery-thumb {
  width: 72px;
  height: 40px;
  object-fit: cover;
  border-radius: 4px;
  cursor: pointer;
  border: 2px solid transparent;
  opacity: 0.6;
  transition:
    opacity 0.2s,
    border-color 0.2s;
  flex-shrink: 0;
}
.gallery-thumb:hover {
  opacity: 0.85;
}
.gallery-thumb.active {
  border-color: var(--el-color-primary);
  opacity: 1;
}

.thumb-nav {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}
.thumb-nav-btn {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 1px solid rgba(0, 0, 0, 0.15);
  background: rgba(255, 255, 255, 0.6);
  color: #555;
  font-size: 0.9rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  flex-shrink: 0;
  transition: background 0.2s;
}
.thumb-nav-btn:hover {
  background: rgba(255, 255, 255, 0.9);
}
html.dark .thumb-nav-btn {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.15);
  color: #ccc;
}
html.dark .thumb-nav-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}
.thumb-scroll-track {
  flex: 1;
  height: 2px;
  border-radius: 1px;
  background: rgba(0, 0, 0, 0.08);
}
html.dark .thumb-scroll-track {
  background: rgba(255, 255, 255, 0.08);
}
.thumb-scroll-thumb {
  height: 100%;
  width: 30%;
  border-radius: 1px;
  background: rgba(0, 0, 0, 0.25);
  transition: margin-left 0.2s;
}
html.dark .thumb-scroll-thumb {
  background: rgba(255, 255, 255, 0.25);
}

/* ---- 右侧信息 ---- */
.detail-info {
  width: 340px;
  flex-shrink: 0;
}

.info-cover {
  aspect-ratio: 21 / 9;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 16px;
  background: #1a1a2e;
}
.info-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.info-desc {
  font-size: 0.92rem;
  color: #555;
  line-height: 1.7;
  margin-bottom: 20px;
}
html.dark .info-desc {
  color: #bbb;
}

.info-meta {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 16px;
  margin-bottom: 20px;
}
.meta-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.meta-label {
  font-size: 0.78rem;
  color: #909399;
}
.meta-value {
  font-size: 0.92rem;
  color: #333;
  font-weight: 500;
}
html.dark .meta-value {
  color: #ddd;
}
.meta-value.rating {
  color: #e6a23c;
  font-weight: 700;
}

.info-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.game-not-found {
  text-align: center;
  padding: 80px 20px;
}
.game-not-found h2 {
  color: #999;
  margin-bottom: 20px;
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
  .detail-name {
    font-size: 1.3rem;
    margin-left: 40px;
  }
  .detail-body {
    flex-direction: column;
  }
  .detail-info {
    width: 100%;
  }
  .gallery-thumb {
    width: 56px;
    height: 32px;
  }
}
</style>
