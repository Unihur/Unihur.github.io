<script setup>  
import { inject, ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import ProfileCard from './ProfileCard.vue' 
import MusicPlayer from './MusicPlayer.vue'
import { useRouter } from 'vue-router'
const router = useRouter()

// 接收从 App.vue 传过来的全局配置
const siteConfig = inject('siteConfig')
const bannerMode = inject('bannerMode')
const bannerImages = inject('bannerImages')
const bannerWrapperHeight = inject('bannerWrapperHeight')
const carouselHeight = inject('carouselHeight')
const typewriterText = inject('typewriterText')
const contentPaddingTop = inject('contentPaddingTop')
const contentMarginTop = inject('contentMarginTop')

// ================= 新增：从后端获取文章列表的逻辑 =================
const articleList = ref([]) // 用来存后端返回的文章数组
const isLoading = ref(true) // 加载状态，可以让页面看起来更流畅

// 点击卡片，跳转到详情页，并把 slug 传过去
const goToDetail = (slug) => {
  router.push(`/post/${slug}`)
}

const fetchArticles = async () => {
  try {
    isLoading.value = true
    // 请求我们刚才写好的 Python 后端接口
    const res = await axios.get('http://127.0.0.1:8000/api/articles')
    // 把拿到的真实数据赋值给变量
    articleList.value = res.data
  } catch (error) {
    console.error('获取文章列表失败:', error)
    ElMessage.error('无法连接到服务器，请检查后端是否开启！')
  } finally {
    isLoading.value = false
  }
}

// 页面一加载，就去拉取文章数据
onMounted(() => {
  fetchArticles()
})

// 一个把时间字符串格式化为 YYYY-MM-DD 的小工具函数
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

</script>

<template>
    <div class="home-container">
        <header v-if="bannerMode !== 'hidden'" :class="['banner', bannerMode]" :style="{ height: bannerWrapperHeight }">
      <el-carousel :interval="4000" arrow="always" class="banner-carousel" :height="carouselHeight">
        <el-carousel-item v-for="(img, index) in bannerImages" :key="index">
          <img :src="img" class="carousel-img" alt="banner">
        </el-carousel-item>
      </el-carousel>

      <div v-if="bannerMode === 'background'" class="banner-overlay"></div>
      
      <!-- 解答2：在这里调标题的上下位置 (看 style 中的 .blog-title) -->
      <h1 v-if="bannerMode !== 'background'" class="blog-title">
        {{ siteConfig.name }}'s Blog
        
        <p class="blog-subtitle">
          {{ typewriterText }}<span class="cursor">|</span>
        </p>
      </h1>

      <!-- 波浪特效 -->
      <div class="waves-container" v-if="bannerMode === 'banner' || bannerMode === 'fullscreen'">
        <svg class="waves" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 24 150 28" preserveAspectRatio="none">
          <defs><path id="gentle-wave" d="M-160 44c30 0 58-18 88-18s 58 18 88 18 58-18 88-18 58 18 88 18 v44h-352z" /></defs>
          <g class="parallax">
            <use xlink:href="#gentle-wave" x="48" y="0" class="wave wave1" />
            <use xlink:href="#gentle-wave" x="48" y="3" class="wave wave2" />
            <use xlink:href="#gentle-wave" x="48" y="5" class="wave wave3" />
            <use xlink:href="#gentle-wave" x="48" y="7" class="wave wave4" />
          </g>
        </svg>
      </div>
    </header>

    <!-- 3. 主体内容区 -->
    <div class="main-content-wrapper" :style="{ paddingTop: contentPaddingTop, marginTop: contentMarginTop }">
      <el-row :gutter="20">
        <!-- ================= 左侧栏 (引入了新的 ProfileCard 组件) ================= -->
        <el-col :span="6">
          <ProfileCard :config="siteConfig" />
          
          <div class="glass-box">
            <h3>分类</h3>
            <ul class="category-list">
              <li><span>前端开发</span> <span>(5)</span></li>
              <li><span>生活日记</span> <span>(3)</span></li>
            </ul>
          </div>
          <div class="glass-box">
            <h3>标签</h3>
            <div class="tag-list">
              <el-tag class="custom-tag">Vue3</el-tag>
              <el-tag class="custom-tag" type="success">Vite</el-tag>
            </div>
          </div>
        </el-col>

        <!-- ================= 右侧栏 ================= -->
        <el-col :span="18">
          <MusicPlayer />

          <div class="glass-box search-bar">
            <el-input placeholder="搜索博客内容..." prefix-icon="Search" size="large" style="width: 100%; opacity: 0.8;" />
          </div>

          <div v-if="isLoading" class="glass-box post-card" style="justify-content: center; padding: 40px;">
            拼命加载文章中...
          </div>
          <div v-else-if="articleList.length === 0" class="glass-box post-card" style="justify-content: center; padding: 40px;">
            暂无文章，快去发布第一篇吧！
          </div>
          
          <div 
            v-else 
            class="glass-box post-card" 
            v-for="item in articleList"
            :key="item.id"
            @click="$router.push(`/post/${item.slug}`)" 
            style="cursor: pointer;" 
          >
            <div class="post-info">
              <!-- 真实标题 -->
              <h2>{{ item.title }}</h2>
              <div class="post-meta">
                <!-- 真实时间，字数先简单用内容的长度模拟 -->
                <span>📅 {{ formatDate(item.publishTime) }}</span> | 
                <span>👁️ 浏览: 0</span> | 
                <span>📝 字数: {{ item.content?.length || 0 }}</span>
              </div>
              <!-- 真实简介 -->
              <p class="post-desc">
                {{ item.intro || '这篇作者很懒，没有写简介...' }}
              </p>
              <!-- 真实标签循环 -->
              <div class="post-tags" v-if="item.tags && item.tags.length">
                <el-tag 
                  size="small" 
                  v-for="(tag, index) in item.tags" 
                  :key="index"
                  :type="index % 2 === 0 ? 'primary' : 'success'"
                  style="margin-right: 5px;"
                >
                  {{ tag }}
                </el-tag>
              </div>
            </div>
            <!-- 真实封面图，如果没有就用默认占位图 -->
            <div class="post-cover">
              <img :src="item.cover || '/banner/1.png'" alt="cover">
            </div>
          </div>
        </el-col>
      </el-row>
    </div>
   </div>
</template>

<style scoped>
/* 样式部分基本保持不变，新增了头像和分割线样式 */
.app-root { width: 100%; }

.nav-container { position: absolute; top: 20px; left: 0; width: 100%; display: flex; justify-content: center; z-index: 999; padding: 0 20px; box-sizing: border-box; }
.navbar { width: 100%; max-width: 1160px; display: flex; justify-content: space-between; align-items: center; border-radius: 50px; padding: 10px 30px; margin: 0; background: rgba(255, 255, 255, 0.6); }
.nav-links { display: flex; gap: 20px; }
.nav-links span { font-weight: bold; cursor: pointer; transition: color 0.3s; }
.nav-links span:hover { color: #409EFF; }
.nav-icons { display: flex; gap: 15px; align-items: center; }
.icon-btn { font-size: 22px; cursor: pointer; outline: none; transition: all 0.3s; }
.icon-btn:hover { color: #409EFF; transform: scale(1.1); }

/* 新增：导航栏右侧登录头像样式 */
.divider { width: 1px; height: 20px; background-color: rgba(0,0,0,0.2); margin: 0 5px; }
html.dark .divider { background-color: rgba(255,255,255,0.2); }
.login-avatar { cursor: pointer; border: 2px solid transparent; transition: border-color 0.3s, transform 0.3s; }
.login-avatar:hover { transform: scale(1.1); border-color: #409EFF; }

.banner { position: relative; width: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; overflow: hidden; transition: height 0.5s ease; }
.banner.background { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 0; }
.banner.banner, .banner.fullscreen { z-index: 1; }
.banner-carousel { position: absolute; top: 0; left: 0; width: 100%; z-index: 1; }
.carousel-img { width: 100%; height: 100%; object-fit: cover; }
.banner-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.2); z-index: 2; pointer-events: none; }

/* 解答2：博客标题位置调整 */
.blog-title {
  position: relative; z-index: 3; font-size: 6rem; font-weight: 900; color: #fff; text-shadow: 2px 2px 8px rgba(0,0,0,0.5); text-align: center;
  /* 如果你想让标题往下移，就把这里的 -80px 改成 0px，或者正数比如 50px */
  margin-top: -60px; 
}
.blog-subtitle { font-size: 2rem; font-weight: normal; margin-top: 10px; text-shadow: 1px 1px 5px rgba(0,0,0,0.8); }

.waves-container { position: absolute; bottom: 0px; left: 0; width: 100%; height: 6vw; min-height: 100px; z-index: 10; line-height: 0; }
.waves { width: 100%; height: 100%; display: block; }
.wave1, .wave2, .wave3, .wave4 { transition: fill 0.3s ease; }
.wave1 { fill: rgba(244, 244, 245, 0.3); } .wave2 { fill: rgba(244, 244, 245, 0.5); } .wave3 { fill: rgba(244, 244, 245, 0.7); } .wave4 { fill: #f4f4f5; } 

/* 原来的夜间波浪是 20, 20, 20 的灰色，改成带紫调的颜色 */
html.dark .wave1 { fill: rgba(43, 34, 61, 0.3); } /* #2b223d 半透明 */
html.dark .wave2 { fill: rgba(43, 34, 61, 0.5); }
html.dark .wave3 { fill: rgba(43, 34, 61, 0.7); }
html.dark .wave4 { fill: #1a1525; } /* 必须和 body 背景色一样，消除分界线 */

.parallax > use { animation: move-forever 25s cubic-bezier(.55,.5,.45,.5) infinite; }
.parallax > use:nth-child(1) { animation-delay: -2s; animation-duration: 7s; }
.parallax > use:nth-child(2) { animation-delay: -3s; animation-duration: 10s; }
.parallax > use:nth-child(3) { animation-delay: -4s; animation-duration: 13s; }
.parallax > use:nth-child(4) { animation-delay: -5s; animation-duration: 20s; }
@keyframes move-forever { 0% { transform: translate3d(-90px,0,0); } 100% { transform: translate3d(85px,0,0); } }

.main-content-wrapper { max-width: 1200px; margin: 0 auto; padding: 0 20px 40px 20px; position: relative; z-index: 10; transition: padding-top 0.5s ease, margin-top 0.5s ease; }

.category-list { list-style: none; padding: 0; }
.category-list li { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px dashed rgba(0,0,0,0.1); }
html.dark .category-list li { border-bottom-color: rgba(255,255,255,0.1); }
.tag-list .custom-tag { margin: 5px; }
.music-player { text-align: center; font-weight: bold; color: inherit; }

.post-card { display: flex; justify-content: space-between; align-items: stretch;padding: 20px; transition: transform 0.3s; }
.post-card:hover { transform: translateY(-5px); }
.post-info { flex: 1; padding-right: 30px; }
.post-meta { font-size: 0.8rem; color: #666; margin-bottom: 10px; }
html.dark .post-meta { color: #aaa; }
.post-desc { color: #444; line-height: 1.6; }
html.dark .post-desc { color: #ccc; }
.post-cover { width: 280px; height: 180px; border-radius: 8px; overflow: hidden;flex-shrink: 0; }
.post-cover img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.5s; }
.post-cover img:hover { transform: scale(1.1); }

/* ================= 魔法 CSS 区域 ================= */
/* 强制覆盖 oh-my-live2d 的默认位置，实现左/右切换 */
:global(html[data-l2d-pos="right"] #oml2d-stage) {
  left: auto !important;
  right: 0 !important; 
}
:global(html[data-l2d-pos="left"] #oml2d-stage) {
  left: 0 !important;
  right: auto !important; 
}

/* 强制读取我们在 JS 中设定的 --l2d-scale 变量，实现缩放 */
:global(#oml2d-stage) {
  transform: scale(var(--l2d-scale, 1));
  transform-origin: bottom; /* 以脚底为准缩放，防止模型飘起来 */
  transition: transform 0.3s ease, left 0.5s ease, right 0.5s ease;
}

.blog-title { position: relative; z-index: 3; font-size: 5rem; font-weight: 900; color: #fff; text-shadow: 2px 2px 8px rgba(0,0,0,0.5); text-align: center; margin-top: -60px; }

/* 保证副标题有固定的最小高度，防止打字机删除到 0 时高度塌陷导致页面抖动 */
.blog-subtitle { 
  font-size: 2rem; 
  font-weight: normal; 
  margin-top: 10px; 
  text-shadow: 1px 1px 5px rgba(0,0,0,0.8);
  min-height: 2.2rem; /* 给定一个最小高度 */
}

/* 👇 新增：闪烁的光标特效 */
.cursor {
  display: inline-block;
  width: 3px;
  background-color: transparent;
  animation: blink 1s infinite;
  margin-left: 2px;
  color: #fff; /* 光标颜色 */
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
</style>