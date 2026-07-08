<script setup>
// 娱乐页：复用首页外壳（Banner + 左侧栏），仅中间区域替换为娱乐内容（待实装）
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowDown,
  ArrowUp,
  Folder,
  PriceTag,
  Edit,
  Delete,
  Plus,
  VideoPlay
} from '@element-plus/icons-vue'

import ProfileCard from '@/components/ProfileCard.vue'
import MusicPlayer from '@/components/MusicPlayer.vue'

import { useSiteStore } from '@/stores/site'
import { useUserStore } from '@/stores/user'
import { useTypewriter } from '@/composables/useTypewriter'

import { listArticles } from '@/api/article'
import { listCategories, createCategory, renameCategory, deleteCategory } from '@/api/category'

const siteStore = useSiteStore()
const userStore = useUserStore()
const { typewriterText } = useTypewriter(() => siteStore.siteConfig.signature)

// ===== 分类 =====
const selectedCategory = ref('')
const categories = ref([])
const fetchCategories = async () => {
  try {
    const res = await listCategories()
    categories.value = res.data
  } catch (error) {
    console.error('获取分类失败', error)
  }
}

// 管理员：新建分类
const handleAddCategory = async () => {
  try {
    const { value } = await ElMessageBox.prompt('请输入新分类名称', '添加分类', {
      confirmButtonText: '确定',
      cancelButtonText: '取消'
    })
    if (value) {
      await createCategory(value)
      ElMessage.success('添加成功')
      fetchCategories()
    }
  } catch (_) {
    /* 用户取消 */
  }
}

// 管理员：重命名分类
const handleRenameCategory = async (oldName) => {
  try {
    const { value } = await ElMessageBox.prompt('请输入新名称', '重命名分类', {
      inputValue: oldName,
      confirmButtonText: '确定',
      cancelButtonText: '取消'
    })
    if (value && value !== oldName) {
      await renameCategory(oldName, value)
      ElMessage.success('重命名成功')
      fetchCategories()
      fetchArticles()
    }
  } catch (_) {
    /* 用户取消 */
  }
}

// 管理员：删除分类
const handleDeleteCategory = async (name) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除分类 "${name}" 吗？该分类下的文章将变为无分类。`,
      '警告',
      { type: 'warning' }
    )
    await deleteCategory(name)
    ElMessage.success('删除成功')
    if (selectedCategory.value === name) selectedCategory.value = ''
    fetchCategories()
    fetchArticles()
  } catch (_) {
    /* 用户取消 */
  }
}

const toggleCategory = (name) => {
  selectedCategory.value = selectedCategory.value === name ? '' : name
}

// ===== 文章列表（仅用于左侧栏 ProfileCard 浏览量统计 + 标签展示） =====
const articleList = ref([])

const fetchArticles = async () => {
  try {
    const res = await listArticles()
    articleList.value = res.data
  } catch (error) {
    console.error('获取文章列表失败:', error)
    ElMessage.error('无法连接到服务器，请检查后端是否开启！')
  }
}

// ===== 标签筛选 =====
const selectedTags = ref([])
const showAllTags = ref(false)

const allTags = computed(() => {
  const tags = new Set()
  articleList.value.forEach((article) => {
    if (article.tags && Array.isArray(article.tags)) {
      article.tags.forEach((t) => tags.add(t))
    }
  })
  return Array.from(tags).sort((a, b) => a.localeCompare(b))
})

const toggleTag = (tag) => {
  const index = selectedTags.value.indexOf(tag)
  if (index > -1) selectedTags.value.splice(index, 1)
  else selectedTags.value.push(tag)
}

onMounted(() => {
  fetchArticles()
  fetchCategories()
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

    <!-- 主体内容区 -->
    <div
      class="main-content-wrapper"
      :style="{ paddingTop: siteStore.contentPaddingTop, marginTop: siteStore.contentMarginTop }"
    >
      <el-row :gutter="20">
        <!-- 左侧栏 -->
        <el-col :xs="24" :md="6">
          <ProfileCard :articles="articleList" />

          <!-- 分类 -->
          <div class="glass-box">
            <h3 style="padding: 0 10px">文章分类</h3>
            <ul class="category-list">
              <li
                v-for="cat in categories"
                :key="cat.name"
                class="category-item-box"
                :class="{ 'is-active-cat': selectedCategory === cat.name }"
                @click="toggleCategory(cat.name)"
              >
                <div class="cat-left">
                  <el-icon><Folder /></el-icon>
                  <span>{{ cat.name }}</span>
                </div>
                <div class="cat-right-info">
                  <div v-if="userStore.isAdmin" class="cat-admin-ops" @click.stop>
                    <el-tooltip content="重命名分类" placement="top">
                      <el-icon class="admin-icon" @click.stop="handleRenameCategory(cat.name)"
                        ><Edit
                      /></el-icon>
                    </el-tooltip>
                    <el-tooltip content="删除分类" placement="top">
                      <el-icon class="admin-icon" @click.stop="handleDeleteCategory(cat.name)"
                        ><Delete
                      /></el-icon>
                    </el-tooltip>
                  </div>
                  <span class="cat-count">({{ cat.count }})</span>
                </div>
              </li>
              <li
                v-if="categories.length === 0"
                style="color: #999; font-size: 0.9rem; justify-content: center; border: none"
              >
                暂无分类
              </li>
            </ul>

            <div v-if="userStore.isAdmin" style="text-align: center; margin-top: 15px">
              <el-button type="warning" plain size="small" @click="handleAddCategory">
                <el-icon><Plus /></el-icon> 添加分类
              </el-button>
            </div>
          </div>

          <!-- 标签筛选 -->
          <div class="glass-box">
            <h3 style="padding: 0 10px">标签筛选</h3>
            <div
              class="post-tags-row tag-collapse-container"
              :class="{ 'is-expanded': showAllTags }"
            >
              <div
                v-for="tag in allTags"
                :key="tag"
                class="meta-box tag-box"
                :class="{ 'is-active': selectedTags.includes(tag) }"
                style="cursor: pointer; transition: all 0.3s; margin-bottom: 5px"
                @click="toggleTag(tag)"
              >
                <el-icon><PriceTag /></el-icon>
                <span>{{ tag }}</span>
              </div>
              <div
                v-if="allTags.length === 0"
                style="color: #999; font-size: 0.9rem; padding: 0 10px"
              >
                暂无标签
              </div>
            </div>

            <div class="expand-arrow-wrapper" @click="showAllTags = !showAllTags">
              <el-icon><component :is="showAllTags ? ArrowUp : ArrowDown" /></el-icon>
            </div>
          </div>
        </el-col>

        <!-- 右侧栏：娱乐内容区域（中间区域，待实装） -->
        <el-col :xs="24" :md="18">
          <MusicPlayer />

          <!-- TODO: 此处为娱乐中间内容区域，待后续实装具体内容 -->
          <div class="glass-box entertainment-placeholder">
            <el-icon class="placeholder-icon"><VideoPlay /></el-icon>
            <h2 class="placeholder-title">娱乐</h2>
            <p class="placeholder-desc">娱乐内容正在筹备中，敬请期待！</p>
          </div>
        </el-col>
      </el-row>
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

.category-list {
  list-style: none;
  padding: 0 10px;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.category-item-box {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
  background: rgba(230, 162, 60, 0.05);
  color: #e6a23c;
  border: 1px solid rgba(230, 162, 60, 0.5);
  font-size: 0.9rem;
  font-weight: bold;
}
.category-item-box:hover {
  transform: translateY(-2px);
  background: rgba(230, 162, 60, 0.15);
}
.category-item-box.is-active-cat {
  background: #e6a23c;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(230, 162, 60, 0.3);
}
.cat-left {
  display: flex;
  align-items: center;
  gap: 6px;
}
.cat-right-info {
  display: flex;
  align-items: center;
  gap: 10px;
}
.cat-count {
  color: #888;
  font-size: 0.8rem;
  opacity: 0.9;
}
html.dark .cat-count {
  color: #bbb;
}
.cat-admin-ops {
  display: inline-flex;
  gap: 8px;
  margin-left: 4px;
}
.cat-admin-ops .el-icon {
  font-size: 14px;
  transition:
    color 0.3s,
    transform 0.3s;
  opacity: 0.7;
}
.cat-admin-ops .el-icon:hover {
  color: #f56c6c;
  opacity: 1;
  transform: scale(1.1);
}
.category-item-box.is-active-cat .cat-admin-ops .el-icon:hover {
  color: #fff;
}

.post-tags-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 15px;
}
.meta-box {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: bold;
  background: transparent;
  line-height: 1;
}
.category-box {
  background: rgba(230, 162, 60, 0.05);
  color: #e6a23c;
  border: 1px solid rgba(230, 162, 60, 0.3);
  transition: all 0.3s;
}
.category-box:hover {
  background: rgba(230, 162, 60, 0.15);
  border-color: rgba(230, 162, 60, 0.6);
  transform: translateY(-2px);
}
.tag-box {
  color: #67c23a;
  border: 1px solid rgba(103, 194, 58, 0.5);
  background: transparent;
  transition: all 0.3s;
}
.tag-box:hover {
  background: rgba(103, 194, 58, 0.1);
}
.tag-box.is-active {
  background: #67c23a;
  color: white;
  border-color: #67c23a;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(103, 194, 58, 0.3);
}

.tag-collapse-container {
  max-height: 125px;
  overflow: hidden;
  transition: max-height 0.4s ease;
  padding: 4px 10px 0 10px;
}
.tag-collapse-container.is-expanded {
  max-height: 1000px;
}
.expand-arrow-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 10px auto 0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.05);
  color: #666;
  cursor: pointer;
  font-size: 1.2rem;
  font-weight: bold;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.expand-arrow-wrapper:hover {
  background: #409eff;
  color: #fff;
  transform: translateY(2px);
  box-shadow: 0 4px 10px rgba(64, 158, 255, 0.3);
}
html.dark .expand-arrow-wrapper {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
}
html.dark .expand-arrow-wrapper:hover {
  background: #409eff;
}

/* 娱乐内容占位区域（待实装） */
.entertainment-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 30px;
  text-align: center;
}
.placeholder-icon {
  font-size: 4rem;
  color: #409eff;
  margin-bottom: 16px;
}
.placeholder-title {
  font-size: 1.8rem;
  font-weight: bold;
  margin: 0 0 10px 0;
  color: #333;
}
html.dark .placeholder-title {
  color: #eee;
}
.placeholder-desc {
  font-size: 1rem;
  color: #999;
  margin: 0;
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
  .post-tags-row {
    gap: 6px;
  }
  .meta-box {
    font-size: 0.75rem;
    padding: 3px 8px;
  }
}
</style>
