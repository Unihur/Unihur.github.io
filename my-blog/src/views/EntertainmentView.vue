<script setup>
// 娱乐页：仅保留首页 Banner + 单个全宽娱乐板块
// 轮播数据来自 src/data/game_banner.json（Vite HMR，支持实时修改）
// 每页：左侧 16:9 主图 + 右侧信息区（名字 / 2×2 缩略图 / 简介 / 标签 / 价格右下角）
// 左右翻页箭头置于图片外；下方胶囊指示器数量 = JSON 的 max，居中
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { ArrowLeft, ArrowRight, Refresh, Search } from '@element-plus/icons-vue'
import { useSiteStore } from '@/stores/site'
import { useUserStore } from '@/stores/user'
import { useTypewriter } from '@/composables/useTypewriter'
import gameBannerData from '@/data/game_banner.json'

const siteStore = useSiteStore()
const userStore = useUserStore()
const { typewriterText } = useTypewriter(() => siteStore.siteConfig.signature)

// 图片资源在 /game_banner/ 下（public/game_banner，构建落到 dist/game_banner）
// JSON 只填资源名（不带扩展名），这里按 png→jpg→jpeg→webp 顺序自动匹配实际文件
const IMG_EXTENSIONS = ['png', 'jpg', 'jpeg', 'webp']
const imgExtIdx = reactive({}) // 资源名 -> 当前尝试的扩展名下标
const imgUrl = (name) => `/game_banner/${name}.${IMG_EXTENSIONS[imgExtIdx[name] || 0]}`
const handleImgError = (name) => {
  const next = (imgExtIdx[name] || 0) + 1
  if (next < IMG_EXTENSIONS.length) imgExtIdx[name] = next
}

// 悬浮缩略图时左侧大图临时显示对应小图，移走恢复原大图（按 slide.id 隔离，避免多页串扰）
const bigImgOverride = reactive({}) // slide.id -> 悬浮的小图资源名
const bigImgName = (slide) => bigImgOverride[slide.id] || slide.img_big
const onThumbEnter = (slide, name) => {
  bigImgOverride[slide.id] = name
}
const onThumbLeave = (slide) => {
  delete bigImgOverride[slide.id]
}

// 轮播数据：按 order 排序；拆分 tag、预计算折扣
const slides = computed(() =>
  [...gameBannerData]
    .sort((a, b) => a.order - b.order)
    .map((item) => {
      const isFree = !item.cost
      const discounted = !isFree && item.count < 1
      return {
        ...item,
        thumbs: [item.img_1, item.img_2, item.img_3, item.img_4].filter(Boolean),
        tags: item.tag
          ? item.tag
              .split(/[,，]/)
              .map((t) => t.trim())
              .filter(Boolean)
          : [],
        isFree,
        discounted,
        discountPct: discounted ? Math.round((1 - item.count) * 100) : 0,
        currentPrice: isFree ? 0 : Math.round(item.cost * item.count)
      }
    })
)

// 胶囊数量 = max（允许实时修改），取首项 max，回退到 slides 长度
const capsuleCount = computed(() => slides.value[0]?.max || slides.value.length)

const carouselRef = ref()
const activeIndex = ref(0)
const carouselHeight = ref('440px')

// el-carousel change 事件参数：(newIndex, oldIndex)
const handleCarouselChange = (newIndex) => {
  activeIndex.value = newIndex
}

// 点击胶囊指示器：立刻跳转至对应顺序的图片
const goToSlide = (index) => {
  carouselRef.value?.setActiveItem(index)
}

const prevSlide = () => carouselRef.value?.prev()
const nextSlide = () => carouselRef.value?.next()

// ---- 本周热门 ----
const hotGames = ref(
  Array.from({ length: 8 }, (_, i) => ({
    id: i + 1,
    title: `游戏标题${i + 1}`,
    likes: Math.floor(Math.random() * 9000) + 100
  }))
)
const refreshHot = () => {
  hotGames.value = hotGames.value.map((g) => ({
    ...g,
    likes: Math.floor(Math.random() * 9000) + 100
  }))
}

// ---- 高分口碑榜 ----
const highScoreGames = [
  { id: 1, name: '游戏名称1' },
  { id: 2, name: '游戏名称2' },
  { id: 3, name: '游戏名称3' },
  { id: 4, name: '游戏名称4' },
  { id: 5, name: '游戏名称5' }
]

// 六个分类标签
const gameTags = ['国产独游', '像素复古', '剧情叙事', '休闲治愈', '免费Demo', '肉鸽挑战']

// ---- 关注系统（按账号保存到 localStorage） ----
function loadFavs() {
  try {
    const raw = localStorage.getItem(`game_favs_${userStore.username}`)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}
function saveFavs(ids) {
  localStorage.setItem(`game_favs_${userStore.username}`, JSON.stringify(ids))
}
const favGameIds = ref(loadFavs())
function isFav(gameId) {
  return favGameIds.value.includes(gameId)
}
function toggleFav(gameId) {
  const idx = favGameIds.value.indexOf(gameId)
  if (idx >= 0) favGameIds.value.splice(idx, 1)
  else favGameIds.value.push(gameId)
  saveFavs(favGameIds.value)
}

// ---- 筛选/视图（暂不实装功能） ----
const gameTypes = ['全部类型', '动作', '冒险', '角色扮演', '策略', '模拟', '休闲', '独立']
const releaseFilters = ['最新', '最热', '推荐', '关注']
const selectedType = ref('全部类型')
const selectedRelease = ref('最新')
const viewMode = ref('large') // large | small | list
const searchKeyword = ref('')

// 响应式高度：移动端纵向布局需更高
const updateCarouselHeight = () => {
  carouselHeight.value = window.innerWidth <= 768 ? '540px' : '440px'
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
            <el-carousel-item v-for="slide in slides" :key="slide.id">
              <div class="slide-layout">
                <!-- 左：16:9 主图 -->
                <div class="main-image-area">
                  <img
                    :src="imgUrl(bigImgName(slide))"
                    class="main-img"
                    :alt="slide.name"
                    @error="handleImgError(bigImgName(slide))"
                  />
                </div>
                <!-- 右：信息区 名字 / 2×2 缩略图 / 简介 / 标签 / 价格(右下角) -->
                <div class="info-area">
                  <div class="slide-name">{{ slide.name }}</div>
                  <div class="thumb-grid">
                    <div v-for="(t, i) in slide.thumbs" :key="i" class="thumb">
                      <img
                        :src="imgUrl(t)"
                        class="thumb-img"
                        :alt="`${slide.name} 缩略图${i + 1}`"
                        @error="handleImgError(t)"
                        @mouseenter="onThumbEnter(slide, t)"
                        @mouseleave="onThumbLeave(slide)"
                      />
                    </div>
                  </div>
                  <div class="slide-des">{{ slide.des }}</div>
                  <div class="slide-tags">
                    <el-tag v-for="(tag, i) in slide.tags" :key="i" size="small" effect="plain">{{
                      tag
                    }}</el-tag>
                  </div>
                  <div class="slide-price">
                    <span v-if="slide.isFree" class="price-value is-free">免费</span>
                    <template v-else-if="slide.discounted">
                      <span class="discount-tag">-{{ slide.discountPct }}%</span>
                      <span class="origin-price">¥{{ slide.cost }}</span>
                      <span class="price-value is-discount">¥{{ slide.currentPrice }}</span>
                    </template>
                    <span v-else class="price-value">¥{{ slide.cost }}</span>
                  </div>
                </div>
              </div>
            </el-carousel-item>
          </el-carousel>
          <el-button class="nav-arrow" circle :icon="ArrowRight" @click="nextSlide" />
        </div>

        <!-- 胶囊指示器：数量 = max，居中 -->
        <div class="capsule-nav">
          <button
            v-for="n in capsuleCount"
            :key="n"
            type="button"
            class="capsule-dot"
            :class="{ 'is-active': activeIndex === n - 1 }"
            @click="goToSlide(n - 1)"
          ></button>
        </div>

        <!-- 六标签按钮行 -->
        <div class="game-tag-row">
          <button v-for="tag in gameTags" :key="tag" type="button" class="game-tag-btn">
            {{ tag }}
          </button>
        </div>

        <!-- 本周热门 + 高分口碑榜 两栏 -->
        <div class="cols-row">
          <!-- 左侧 3/4：本周热门 -->
          <div class="hot-section">
            <div class="section-head">
              <div class="section-head-left">
                <span class="label-week">本周</span><span class="label-hot">热门</span>
              </div>
              <div class="section-head-right" @click="refreshHot">
                <span>换一批</span>
                <el-icon><Refresh /></el-icon>
              </div>
            </div>
            <div class="hot-grid">
              <div v-for="g in hotGames" :key="g.id" class="hot-card">
                <img src="/game_banner/2.png" class="hot-card-img" alt="game cover" />
                <div class="hot-card-bottom">
                  <span class="hot-card-title">{{ g.title }}</span>
                  <span class="hot-card-likes">{{ g.likes }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 右侧 1/4：高分口碑榜 -->
          <div class="score-section">
            <div class="section-head">
              <div class="section-head-left"><span class="label-score">高分口碑榜</span></div>
              <div class="section-head-right"><span class="label-top">Top5</span></div>
            </div>
            <div class="score-list">
              <div v-for="g in highScoreGames" :key="g.id" class="score-item">
                <img src="/game_banner/2.png" class="score-img" alt="game cover" />
                <span class="score-name">{{ g.name }}</span>
                <span class="score-rank">TOP{{ g.id }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 筛选 + 视图切换行 -->
        <div class="filter-toolbar">
          <el-input
            v-model="searchKeyword"
            class="search-input"
            placeholder="搜索游戏名"
            :prefix-icon="Search"
            clearable
          />
          <div class="filter-right">
            <el-select v-model="selectedType" class="filter-select" size="default">
              <el-option v-for="t in gameTypes" :key="t" :label="t" :value="t" />
            </el-select>
            <el-select v-model="selectedRelease" class="filter-select" size="default">
              <el-option v-for="r in releaseFilters" :key="r" :label="r" :value="r" />
            </el-select>
            <div class="view-toggles">
              <el-tooltip content="大卡片" placement="top">
                <button
                  type="button"
                  class="view-btn"
                  :class="{ active: viewMode === 'large' }"
                  @click="viewMode = 'large'"
                >
                  <span class="vi vi-grid-lg"></span>
                </button>
              </el-tooltip>
              <el-tooltip content="小卡片" placement="top">
                <button
                  type="button"
                  class="view-btn"
                  :class="{ active: viewMode === 'small' }"
                  @click="viewMode = 'small'"
                >
                  <span class="vi vi-grid-sm"></span>
                </button>
              </el-tooltip>
              <el-tooltip content="列表" placement="top">
                <button
                  type="button"
                  class="view-btn"
                  :class="{ active: viewMode === 'list' }"
                  @click="viewMode = 'list'"
                >
                  <span class="vi vi-list"></span>
                </button>
              </el-tooltip>
            </div>
          </div>
        </div>

        <!-- 游戏卡片网格：一行四列 -->
        <div class="game-cards-grid">
          <div v-for="g in slides" :key="g.id" class="game-card">
            <!-- 封面 + 爱心 -->
            <div class="game-card-cover">
              <img
                :src="imgUrl(g.img_big)"
                class="gc-cover-img"
                :alt="g.name"
                @error="handleImgError(g.img_big)"
              />
              <button
                type="button"
                class="gc-fav-btn"
                :title="isFav(g.id) ? '取消关注' : '关注'"
                @click.stop="toggleFav(g.id)"
              >
                <svg
                  class="gc-heart"
                  :class="{ filled: isFav(g.id) }"
                  viewBox="0 0 24 24"
                  width="18"
                  height="18"
                >
                  <path
                    d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5
                       2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09
                       C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42
                       22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"
                  />
                </svg>
              </button>
            </div>
            <!-- 信息 -->
            <div class="game-card-info">
              <div class="gc-name">{{ g.name }}</div>
              <div class="gc-des">{{ g.des }}</div>
              <div class="gc-tags">
                <el-tag v-for="(tag, i) in g.tags" :key="i" size="small" effect="plain">
                  {{ tag }}
                </el-tag>
              </div>
            </div>
          </div>
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
.slide-des {
  font-size: 0.85rem;
  color: #666;
  line-height: 1.5;
  word-break: break-word;
}
html.dark .slide-des {
  color: #aaa;
}
.slide-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

/* 价格：右下角，深色标签底（保证白色/绿色字可读）；有折扣时绿色并左侧显示折扣百分比 */
.slide-price {
  margin-top: auto;
  align-self: flex-end;
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.75);
  font-size: 1.05rem;
  font-weight: bold;
}
html.dark .slide-price {
  background: rgba(0, 0, 0, 0.6);
}
.discount-tag {
  color: #67c23a;
  font-size: 0.85rem;
}
.origin-price {
  color: #999;
  text-decoration: line-through;
  font-size: 0.9rem;
  font-weight: normal;
}
.price-value {
  color: #fff;
}
.price-value.is-discount {
  color: #67c23a;
}
.price-value.is-free {
  color: #67c23a;
}

/* 胶囊指示器：居中、更小更紧凑、高度略高 */
.capsule-nav {
  display: flex;
  justify-content: center;
  gap: 5px;
  margin-top: 10px;
}
.capsule-dot {
  width: 18px;
  height: 8px;
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
  width: 26px;
  background: #409eff;
}
html.dark .capsule-dot {
  background: rgba(255, 255, 255, 0.25);
}

/* ---- 六标签按钮 ---- */
.game-tag-row {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
  margin-top: 16px;
  padding: 0 8px;
}
.game-tag-btn {
  padding: 5px 16px;
  border: 1px solid #c0c4cc;
  border-radius: 999px;
  background: transparent;
  color: #606266;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.25s;
}
.game-tag-btn:hover {
  color: #409eff;
  border-color: #409eff;
}
html.dark .game-tag-btn {
  color: #c8c8c8;
  border-color: #555;
}
html.dark .game-tag-btn:hover {
  color: #409eff;
  border-color: #409eff;
}

/* ---- 两栏布局 ---- */
.cols-row {
  display: flex;
  gap: 20px;
  margin-top: 20px;
  padding: 0 8px;
}
.hot-section {
  flex: 3;
  min-width: 0;
}
.score-section {
  flex: 1;
  min-width: 200px;
  display: flex;
  flex-direction: column;
}

/* ---- section 通用头部 ---- */
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.section-head-left {
  font-size: 1.05rem;
  font-weight: bold;
  color: #333;
}
html.dark .section-head-left {
  color: #eee;
}
.section-head-right {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.82rem;
  color: #909399;
  cursor: pointer;
  user-select: none;
}
.section-head-right:hover {
  color: #409eff;
}
.label-week {
  color: #409eff;
  margin-right: 4px;
}
.label-hot {
  color: #333;
}
html.dark .label-hot {
  color: #eee;
}
.label-score {
  color: #333;
}
html.dark .label-score {
  color: #eee;
}
.label-top {
  color: #e6a23c;
  font-weight: bold;
}

/* ---- 本周热门 grid ---- */
.hot-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
.hot-card {
  border-radius: 8px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.03);
  transition: transform 0.2s;
}
.hot-card:hover {
  transform: translateY(-2px);
}
html.dark .hot-card {
  background: rgba(255, 255, 255, 0.04);
}
.hot-card-img {
  width: 100%;
  aspect-ratio: 16 / 10;
  object-fit: cover;
  display: block;
}
.hot-card-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 8px;
  font-size: 0.85rem;
}
.hot-card-title {
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
html.dark .hot-card-title {
  color: #ddd;
}
.hot-card-likes {
  color: #909399;
  flex-shrink: 0;
  margin-left: 6px;
}

/* ---- 高分口碑榜 ---- */
.score-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.score-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 8px;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.02);
  transition: background 0.2s;
}
.score-item:hover {
  background: rgba(64, 158, 255, 0.06);
}
html.dark .score-item {
  background: rgba(255, 255, 255, 0.03);
}
.score-img {
  width: 56px;
  height: 40px;
  border-radius: 4px;
  object-fit: cover;
  flex-shrink: 0;
}
.score-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.88rem;
  color: #333;
}
html.dark .score-name {
  color: #ddd;
}
.score-rank {
  flex-shrink: 0;
  font-weight: bold;
  font-size: 0.85rem;
  color: #e6a23c;
}

/* ---- 筛选工具栏 ---- */
.filter-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 24px;
  padding: 0 8px;
}
.search-input {
  flex: 1;
  min-width: 0;
  max-width: 360px;
}
.filter-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
  margin-left: auto;
}
.filter-select {
  width: 110px;
}

/* 视图切换按钮 */
.view-toggles {
  display: flex;
  gap: 4px;
  padding-left: 6px;
  border-left: 1px solid #dcdfe6;
}
html.dark .view-toggles {
  border-left-color: #4c4d4f;
}
.view-btn {
  width: 32px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
  padding: 0;
  transition: all 0.2s;
}
.view-btn:hover {
  border-color: #409eff;
}
.view-btn.active {
  border-color: #409eff;
  background: rgba(64, 158, 255, 0.08);
}
html.dark .view-btn {
  background: #2a2a2a;
  border-color: #4c4d4f;
}

/* 视图图标（纯 CSS 绘制） */
.vi {
  display: block;
}
.vi-grid-lg {
  width: 14px;
  height: 14px;
  border: 2px solid #909399;
  border-radius: 2px;
  background: #909399;
}
.view-btn.active .vi-grid-lg {
  border-color: #409eff;
  background: #409eff;
}
.vi-grid-sm {
  width: 14px;
  height: 14px;
  background:
    linear-gradient(#909399, #909399) 0 0 / 5px 5px,
    linear-gradient(#909399, #909399) 9px 0 / 5px 5px,
    linear-gradient(#909399, #909399) 0 9px / 5px 5px,
    linear-gradient(#909399, #909399) 9px 9px / 5px 5px;
  background-repeat: no-repeat;
}
.view-btn.active .vi-grid-sm {
  background-image:
    linear-gradient(#409eff, #409eff), linear-gradient(#409eff, #409eff),
    linear-gradient(#409eff, #409eff), linear-gradient(#409eff, #409eff);
}
.vi-list {
  width: 14px;
  height: 14px;
  background:
    linear-gradient(#909399, #909399) 0 1px / 100% 2px,
    linear-gradient(#909399, #909399) 0 6px / 100% 2px,
    linear-gradient(#909399, #909399) 0 11px / 100% 2px;
  background-repeat: no-repeat;
}
.view-btn.active .vi-list {
  background-image:
    linear-gradient(#409eff, #409eff), linear-gradient(#409eff, #409eff),
    linear-gradient(#409eff, #409eff);
}

/* ---- 游戏卡片网格 ---- */
.game-cards-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-top: 20px;
  padding: 0 8px;
}
.game-card {
  border-radius: 10px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.03);
  transition:
    transform 0.25s,
    box-shadow 0.25s;
}
.game-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
}
html.dark .game-card {
  background: rgba(255, 255, 255, 0.04);
}
.game-card-cover {
  position: relative;
}
.gc-cover-img {
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  display: block;
}
.gc-fav-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.45);
  cursor: pointer;
  padding: 0;
  transition: background 0.2s;
}
.gc-fav-btn:hover {
  background: rgba(0, 0, 0, 0.7);
}
.gc-heart {
  fill: transparent;
  stroke: #fff;
  stroke-width: 2;
  transition:
    fill 0.25s,
    stroke 0.25s;
}
.gc-heart.filled {
  fill: #f56c6c;
  stroke: #f56c6c;
}
.game-card-info {
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.gc-name {
  font-size: 0.95rem;
  font-weight: 600;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
html.dark .gc-name {
  color: #eee;
}
.gc-des {
  font-size: 0.8rem;
  color: #888;
  line-height: 1.45;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
html.dark .gc-des {
  color: #aaa;
}
.gc-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
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
  .cols-row {
    flex-direction: column;
  }
  .hot-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .filter-toolbar {
    flex-wrap: wrap;
  }
  .search-input {
    max-width: 100%;
  }
  .filter-right {
    flex-wrap: wrap;
  }
  .game-cards-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
