<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import gameRepository from '@/data/game_repository.json'

const route = useRoute()
const router = useRouter()

const gameId = Number(route.params.slug)
const game = computed(() => gameRepository.find((g) => g.id === gameId) || null)

const tags = computed(() => {
  if (!game.value?.tag) return []
  return game.value.tag
    .split(/[,，]/)
    .map((t) => t.trim())
    .filter(Boolean)
})

const isFree = computed(() => !game.value?.cost)
const discounted = computed(() => !isFree.value && game.value.count < 1)
const discountPct = computed(() =>
  discounted.value ? Math.round((1 - game.value.count) * 100) : 0
)
const currentPrice = computed(() =>
  isFree.value ? 0 : Math.round((game.value?.cost || 0) * (game.value?.count || 1))
)

const allImages = computed(() => {
  if (!game.value) return []
  return [
    game.value.img_big,
    game.value.img_1,
    game.value.img_2,
    game.value.img_3,
    game.value.img_4
  ].filter((n, i, arr) => n && arr.indexOf(n) === i)
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
  <div v-if="game" class="game-detail-container">
    <div class="detail-hero">
      <img :src="imgUrl(game.img_big)" class="hero-img" :alt="game.name" />
      <button class="back-btn" @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
      </button>
    </div>

    <div class="detail-body">
      <div class="detail-header">
        <h1 class="detail-name">{{ game.name }}</h1>
        <div class="detail-price">
          <span v-if="isFree" class="price-value is-free">免费</span>
          <template v-else-if="discounted">
            <span class="discount-tag">-{{ discountPct }}%</span>
            <span class="origin-price">¥{{ game.cost }}</span>
            <span class="price-value is-discount">¥{{ currentPrice }}</span>
          </template>
          <span v-else class="price-value">¥{{ game.cost }}</span>
        </div>
      </div>

      <div class="detail-tags">
        <el-tag v-for="tag in tags" :key="tag" size="default">{{ tag }}</el-tag>
      </div>

      <div class="detail-time">{{ formatDate(game.time) }}</div>

      <div class="detail-description">
        <p>{{ game.des }}</p>
      </div>

      <div v-if="allImages.length > 1" class="detail-gallery">
        <img
          v-for="(img, i) in allImages"
          :key="i"
          :src="imgUrl(img)"
          class="gallery-img"
          :alt="`${game.name} 截图 ${i + 1}`"
        />
      </div>
    </div>
  </div>

  <div v-else class="game-not-found">
    <h2>游戏不存在</h2>
    <el-button @click="goBack">返回</el-button>
  </div>
</template>

<style scoped>
.game-detail-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 0 20px 40px;
}

.detail-hero {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  aspect-ratio: 16 / 9;
  margin-top: 20px;
}

.hero-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.back-btn {
  position: absolute;
  top: 16px;
  left: 16px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  font-size: 1.2rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}
.back-btn:hover {
  background: rgba(0, 0, 0, 0.75);
}

.detail-body {
  padding: 24px 0;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  flex-wrap: wrap;
}

.detail-name {
  font-size: 1.8rem;
  font-weight: 700;
  color: #333;
  margin: 0;
}
html.dark .detail-name {
  color: #eee;
}

.detail-price {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.75);
  font-size: 1.1rem;
  font-weight: bold;
  flex-shrink: 0;
}
html.dark .detail-price {
  background: rgba(0, 0, 0, 0.6);
}

.discount-tag {
  color: #67c23a;
  font-size: 0.9rem;
}
.origin-price {
  color: #999;
  text-decoration: line-through;
  font-size: 0.95rem;
  font-weight: normal;
}
.price-value {
  color: #fff;
  font-size: 1.1rem;
}
.price-value.is-discount {
  color: #67c23a;
}
.price-value.is-free {
  color: #67c23a;
  font-size: 1.1rem;
}

.detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}

.detail-time {
  font-size: 0.88rem;
  color: #909399;
  margin-top: 12px;
}

.detail-description {
  margin-top: 24px;
  font-size: 1rem;
  color: #555;
  line-height: 1.8;
}
html.dark .detail-description {
  color: #bbb;
}

.detail-gallery {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  margin-top: 32px;
}
.gallery-img {
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  border-radius: 8px;
  display: block;
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
  .detail-name {
    font-size: 1.3rem;
  }
  .detail-gallery {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
