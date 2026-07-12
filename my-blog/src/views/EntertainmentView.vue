<script setup>
// 娱乐页：仅保留首页 Banner + 单个全宽娱乐板块
// 轮播数据来自 src/data/game_banner.json（Vite HMR，支持实时修改）
// 每页：左侧 16:9 主图 + 右侧信息区（名字 / 2×2 缩略图 / 简介 / 标签 / 价格右下角）
// 左右翻页箭头置于图片外；下方胶囊指示器数量 = JSON 的 max，居中
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, ArrowRight, Refresh, Search, View } from '@element-plus/icons-vue'
import { useSiteStore } from '@/stores/site'
import { useUserStore } from '@/stores/user'
import { useTypewriter } from '@/composables/useTypewriter'
import gameBannerData from '@/data/game_banner.json'
import gameRepository from '@/data/game_repository.json'

const siteStore = useSiteStore()
const userStore = useUserStore()
const router = useRouter()
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

// ---- 仓库查找表 ----
const repoMap = computed(() => {
  const map = {}
  for (const g of gameRepository) map[g.id] = g
  return map
})

function toDisplayItem(repo) {
  const tags = repo.tag
    ? repo.tag
        .split(/[,，]/)
        .map((t) => t.trim())
        .filter(Boolean)
    : []
  const isFree = !repo.cost
  const discounted = !isFree && repo.count < 1
  return {
    ...repo,
    tags,
    isFree,
    discounted,
    discountPct: discounted ? Math.round((1 - repo.count) * 100) : 0,
    currentPrice: isFree ? 0 : Math.round(repo.cost * repo.count)
  }
}

// 轮播数据：顺序来自 banner json，数据来自仓库
const slides = computed(() =>
  [...gameBannerData]
    .sort((a, b) => a.order - b.order)
    .map((item) => {
      const repo = repoMap.value[item.game_id] || {}
      return {
        ...item,
        ...toDisplayItem(repo),
        thumbs: [repo.img_1, repo.img_2, repo.img_3, repo.img_4].filter(Boolean)
      }
    })
)

// 全部游戏（从仓库）
const allGames = computed(() => gameRepository.map(toDisplayItem))

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
const goToGame = (id) => {
  recordView(id)
  router.push(`/game/${id}`)
}

// ---- 周统计追踪（localStorage） ----
const WEEKLY_VIEWS_KEY = 'game_weekly_views'
const WEEKLY_FAVS_KEY = 'game_weekly_favs'

function getWeekKey() {
  const now = new Date()
  const day = now.getDay()
  const diff = now.getDate() - day + (day === 0 ? -6 : 1)
  const monday = new Date(now.getFullYear(), now.getMonth(), diff)
  const y = monday.getFullYear()
  const m = String(monday.getMonth() + 1).padStart(2, '0')
  const d = String(monday.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function loadWeeklyData(key) {
  try {
    return JSON.parse(localStorage.getItem(key) || '{}')
  } catch {
    return {}
  }
}

function saveWeeklyData(key, data) {
  localStorage.setItem(key, JSON.stringify(data))
}

function recordView(gameId) {
  const weekKey = getWeekKey()
  const data = loadWeeklyData(WEEKLY_VIEWS_KEY)
  if (!data[weekKey]) data[weekKey] = {}
  data[weekKey][gameId] = (data[weekKey][gameId] || 0) + 1
  saveWeeklyData(WEEKLY_VIEWS_KEY, data)
}

function recordWeeklyFav(gameId) {
  const weekKey = getWeekKey()
  const data = loadWeeklyData(WEEKLY_FAVS_KEY)
  if (!data[weekKey]) data[weekKey] = {}
  data[weekKey][gameId] = (data[weekKey][gameId] || 0) + 1
  saveWeeklyData(WEEKLY_FAVS_KEY, data)
}

function getAllTimeViews() {
  const data = loadWeeklyData(WEEKLY_VIEWS_KEY)
  const totals = {}
  for (const week of Object.values(data)) {
    for (const [gid, cnt] of Object.entries(week)) {
      totals[gid] = (totals[gid] || 0) + cnt
    }
  }
  return totals
}

// ---- 本周热门 ----
const randomSeed = ref(Math.random())
const refreshHot = () => {
  randomSeed.value = Math.random()
}

const hotGames = computed(() => {
  const weekKey = getWeekKey()
  const viewsData = loadWeeklyData(WEEKLY_VIEWS_KEY)
  const favsData = loadWeeklyData(WEEKLY_FAVS_KEY)
  const weekViews = viewsData[weekKey] || {}
  const weekFavs = favsData[weekKey] || {}

  const allIds = new Set([...Object.keys(weekViews), ...Object.keys(weekFavs)])
  const scored = []
  for (const idStr of allIds) {
    const gid = Number(idStr)
    const repo = repoMap.value[gid]
    if (!repo) continue
    const total = (weekViews[idStr] || 0) + (weekFavs[idStr] || 0)
    scored.push({ ...toDisplayItem(repo), hotScore: total })
  }
  scored.sort((a, b) => b.hotScore - a.hotScore)

  if (scored.length > 0) {
    return scored.slice(0, 8)
  }
  void randomSeed.value
  const shuffled = [...allGames.value].sort(() => Math.random() - 0.5)
  return shuffled.slice(0, 8)
})

// ---- 高分口碑榜：点进详情页最高 Top5 ----
const highScoreGames = computed(() => {
  const allViews = getAllTimeViews()
  const scored = []
  for (const [gidStr, cnt] of Object.entries(allViews)) {
    const gid = Number(gidStr)
    const repo = repoMap.value[gid]
    if (!repo) continue
    scored.push({ ...toDisplayItem(repo), viewCount: cnt })
  }
  scored.sort((a, b) => b.viewCount - a.viewCount)
  if (scored.length >= 5) return scored.slice(0, 5)
  // 不足 5 个时，用仓库中浏览量最高的补足（随机填充未浏览过的）
  const existing = new Set(scored.map((g) => g.id))
  const rest = [...allGames.value]
    .filter((g) => !existing.has(g.id))
    .sort(() => Math.random() - 0.5)
  return [...scored, ...rest].slice(0, 5)
})

// ---- 关注系统（按账号保存到 localStorage） ----
function formatGameDate(timeStr) {
  if (!timeStr) return ''
  const d = timeStr.split(' ')[0]
  const [y, m, day] = d.split('/')
  return `${y}年${m}月${day}日`
}
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
  else {
    favGameIds.value.push(gameId)
    recordWeeklyFav(gameId)
  }
  saveFavs(favGameIds.value)
}

// ---- 筛选/视图 ----
const releaseFilters = ['最新', '最热', '推荐', '关注']
const selectedType = ref('全部类型')
const selectedRelease = ref('最新')
const viewMode = ref('large')
const searchKeyword = ref('')

// 从仓库收集所有类型
const allTypes = computed(() => {
  const set = new Set()
  for (const g of gameRepository) {
    if (g.type) {
      g.type.split(/[,，]/).forEach((t) => set.add(t.trim()))
    }
  }
  return Array.from(set).sort()
})

// 筛选用类型选项
const gameTypes = computed(() => ['全部类型', ...allTypes.value])

// 按搜索/类型/发布筛选全部游戏
const filteredGames = computed(() => {
  let games = allGames.value

  const kw = searchKeyword.value.trim().toLowerCase()
  if (kw) {
    games = games.filter(
      (g) => g.name.toLowerCase().includes(kw) || g.tags.some((t) => t.toLowerCase().includes(kw))
    )
  }

  if (selectedType.value !== '全部类型') {
    games = games.filter((g) => {
      const types = (g.type || '').split(/[,，]/).map((t) => t.trim())
      return types.includes(selectedType.value)
    })
  }

  if (selectedRelease.value === '推荐') {
    games = games.filter((g) => g.is_recommended === 1)
  } else if (selectedRelease.value === '最新') {
    games = [...games].sort((a, b) => new Date(b.time || 0) - new Date(a.time || 0))
  } else if (selectedRelease.value === '关注') {
    games = games.filter((g) => favGameIds.value.includes(g.id))
  }
  // '最热' 暂无排序逻辑

  return games
})

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
              <div class="slide-layout" @click="goToGame(slide.id)">
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
              <div v-for="g in hotGames" :key="g.id" class="hot-card" @click="goToGame(g.id)">
                <img
                  :src="imgUrl(g.img_big)"
                  class="hot-card-img"
                  :alt="g.name"
                  @error="handleImgError(g.img_big)"
                />
                <div class="hot-card-bottom">
                  <span class="hot-card-title">{{ g.name }}</span>
                  <span class="hot-card-likes">
                    <el-icon><View /></el-icon>
                    {{ g.hotScore }}
                  </span>
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
              <div
                v-for="(g, i) in highScoreGames"
                :key="g.id"
                class="score-item"
                @click="goToGame(g.id)"
              >
                <img
                  :src="imgUrl(g.img_big)"
                  class="score-img"
                  :alt="g.name"
                  @error="handleImgError(g.img_big)"
                />
                <span class="score-name">{{ g.name }}</span>
                <span class="score-rank">TOP{{ i + 1 }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 筛选 + 视图切换行 -->
        <div class="filter-toolbar">
          <el-input
            v-model="searchKeyword"
            class="search-input"
            placeholder="搜索游戏名/标签"
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

        <!-- 游戏卡片：大卡片 / 小卡片 / 列表 过渡 -->
        <Transition name="mode-fade" mode="out-in">
          <div
            v-if="viewMode !== 'list'"
            :key="'grid'"
            :class="['game-cards-grid', { 'grid-sm': viewMode === 'small' }]"
          >
            <div v-for="g in filteredGames" :key="g.id" class="game-card" @click="goToGame(g.id)">
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
                <template v-if="viewMode !== 'small'">
                  <div class="gc-des">{{ g.des }}</div>
                  <div class="gc-tags">
                    <el-tag v-for="(tag, i) in g.tags" :key="i" size="small" effect="plain">
                      {{ tag }}
                    </el-tag>
                  </div>
                </template>
                <div class="gc-bottom-row">
                  <span class="gc-time">{{ formatGameDate(g.time) }}</span>
                  <div class="game-card-price">
                    <span v-if="g.isFree" class="price-value is-free">免费</span>
                    <template v-else-if="g.discounted">
                      <span class="discount-tag">-{{ g.discountPct }}%</span>
                      <span class="origin-price">¥{{ g.cost }}</span>
                      <span class="price-value is-discount">¥{{ g.currentPrice }}</span>
                    </template>
                    <span v-else class="price-value">¥{{ g.cost }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 游戏卡片：列表模式 -->
          <div v-else key="list" class="game-cards-list">
            <div v-for="g in filteredGames" :key="g.id" class="list-card" @click="goToGame(g.id)">
              <div class="list-card-cover">
                <img :src="imgUrl(g.img_big)" :alt="g.name" @error="handleImgError(g.img_big)" />
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
              <div class="list-card-info">
                <div class="list-name">{{ g.name }}</div>
                <div class="list-tags">
                  <el-tag v-for="(tag, i) in g.tags" :key="i" size="small" effect="plain">
                    {{ tag }}
                  </el-tag>
                </div>
                <div class="list-bottom-row">
                  <span class="list-time">{{ formatGameDate(g.time) }}</span>
                  <div class="game-card-price list-price">
                    <span v-if="g.isFree" class="price-value is-free">免费</span>
                    <template v-else-if="g.discounted">
                      <span class="discount-tag">-{{ g.discountPct }}%</span>
                      <span class="origin-price">¥{{ g.cost }}</span>
                      <span class="price-value is-discount">¥{{ g.currentPrice }}</span>
                    </template>
                    <span v-else class="price-value">¥{{ g.cost }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Transition>
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
  gap: 2px;
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
  gap: 0;
  padding: 10px;
  box-sizing: border-box;
  cursor: pointer;
}
.main-image-area {
  height: 100%;
  aspect-ratio: 16 / 9;
  flex-shrink: 0;
  border-radius: 8px 0 0 8px;
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
  background: rgba(0, 0, 0, 0.025);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 0 8px 8px 0;
  padding: 12px;
}
html.dark .info-area {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.08);
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
  font-size: 0.9rem;
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
  font-size: 0.9rem;
}
.price-value.is-discount {
  color: #67c23a;
  font-size: 0.9rem;
}
.price-value.is-free {
  color: #67c23a;
  font-size: 0.9rem;
}

/* 大/小卡片内售价 -- 复用轮播图售价样式，用 margin 推到底部右侧 */
.game-card-price {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.75);
  font-size: 0.9rem;
  font-weight: bold;
  flex-shrink: 0;
}
html.dark .game-card-price {
  background: rgba(0, 0, 0, 0.6);
}

/* 小卡片网格：5列 */
.game-cards-grid.grid-sm {
  grid-template-columns: repeat(5, 1fr);
}

/* 列表模式 */
.game-cards-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 20px;
  padding: 0 8px;
}
.list-card {
  display: flex;
  gap: 16px;
  border-radius: 10px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.03);
  transition:
    transform 0.25s,
    box-shadow 0.25s;
  cursor: pointer;
}
.list-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
}
html.dark .list-card {
  background: rgba(255, 255, 255, 0.04);
}
.list-card-cover {
  position: relative;
  flex-shrink: 0;
  width: 280px;
  aspect-ratio: 21 / 9;
  overflow: hidden;
  border-radius: 6px 0 0 6px;
}
.list-card-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.list-card-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px 16px 12px 0;
}
.list-name {
  font-size: 1.05rem;
  font-weight: 600;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
html.dark .list-name {
  color: #eee;
}
.list-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.list-bottom-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: auto;
}
.list-time {
  font-size: 0.82rem;
  color: #909399;
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

/* ---- 两栏布局 ---- */
.cols-row {
  display: flex;
  gap: 20px;
  margin-top: 32px;
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
  cursor: pointer;
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
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 0.8rem;
}
.hot-card-likes .el-icon {
  font-size: 0.85rem;
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
  cursor: pointer;
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
  margin-top: 48px;
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

/* 视图模式切换过渡动画 */
.mode-fade-enter-active,
.mode-fade-leave-active {
  transition: all 0.25s ease;
}
.mode-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.mode-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
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
  display: flex;
  flex-direction: column;
  border-radius: 10px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.03);
  transition:
    transform 0.25s,
    box-shadow 0.25s;
  cursor: pointer;
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
  left: 8px;
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
  flex: 1;
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
  line-clamp: 2;
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

.gc-bottom-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: auto;
}

.gc-time {
  font-size: 0.78rem;
  color: #909399;
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
    border-radius: 8px 8px 0 0;
  }
  .info-area {
    border-radius: 0 0 8px 8px;
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
  .game-cards-grid.grid-sm {
    grid-template-columns: repeat(3, 1fr);
  }
  .list-card {
    flex-direction: column;
  }
  .list-card-cover {
    width: 100%;
    border-radius: 6px 6px 0 0;
    aspect-ratio: 21 / 9;
  }
  .list-card-info {
    padding: 10px 12px;
  }
}
</style>
