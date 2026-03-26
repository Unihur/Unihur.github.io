<script setup>
import { ref, onMounted, inject, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Calendar, Folder, PriceTag, Share, Edit } from '@element-plus/icons-vue'

import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

import ProfileCard from './ProfileCard.vue'

const route = useRoute()
const router = useRouter()

// 注入全局 UI 配置，保持和首页一样的横幅效果
const siteConfig = inject('siteConfig')
const bannerMode = inject('bannerMode')
const bannerImages = inject('bannerImages')
const bannerWrapperHeight = inject('bannerWrapperHeight')
const carouselHeight = inject('carouselHeight')
const contentPaddingTop = inject('contentPaddingTop')
const contentMarginTop = inject('contentMarginTop')
const typewriterText = inject('typewriterText')
const isLoggedIn = inject('isLoggedIn', ref(false))

// Markdown 配置
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try { return hljs.highlight(str, { language: lang }).value } catch (__) {}
    }
    return ''
  }
})

// 点击编辑按钮跳转到写作页（并���上当前文章的 slug，方便写作页读取数据）
const editArticle = () => {
  router.push(`/write?slug=${article.value.slug}`)
}

// 数据状态
const article = ref(null) // 初始值必须是 null
const renderedHtml = ref('')
const prevPost = ref(null)
const nextPost = ref(null)
const isLoading = ref(true)
const likes = ref(0) 
const shares = ref(0)
const floatingHearts = ref([]) 

let heartIdCounter = 0

// 全新的点赞函数 (合并了特效 + 后端请求)
const handleLike = async () => {
  // 1. 前端先立刻让点赞数 +1，让用户感觉反应很快（乐观更新）
  likes.value++
  
  // 2. 播放爱心特效
  const newHeart = {
    id: heartIdCounter++,
    size: Math.random() * 10 + 15,
    color: ['#ff79c6', '#ff4d4f', '#f56c6c', '#e0b0ff', '#ff6b81'][Math.floor(Math.random() * 5)],
    leftOffset: (Math.random() - 0.5) * 40
  }
  floatingHearts.value.push(newHeart)
  setTimeout(() => {
    floatingHearts.value = floatingHearts.value.filter(h => h.id !== newHeart.id)
  }, 1500)

  // 3. 异步发送请求给后端保存点赞数
  try {
    // 假设文章的 slug 存在，告诉后端这篇文章被点赞了
    if (article.value && article.value.slug) {
      await axios.post(`http://116.62.218.51:8000/api/articles/${article.value.slug}/like`)
    }
  } catch (error) {
    console.error('点赞保存到后端失败:', error)
    // 如果想要严谨点，失败了可以把 likes.value 减回来，这里简单处理仅打印错误
  }
}

// ================= 新增：动态目录功能 =================
const tocList = ref([]) // 用于存放提取出来的目录

const generateTOC = () => {
  const container = document.querySelector('.markdown-body')
  if (!container) {
    console.log("没找到 .markdown-body 容器") // 用于排错
    return
  }
  
  // 👇 修改这里：增加 h4, h5, h6，以防你文章里用的是四级或五级标题
  const headers = container.querySelectorAll('h1, h2, h3, h4, h5, h6')
  const toc = []
  
  headers.forEach((header, index) => {
    const id = `heading-${index}`
    header.id = id 
    
    // 取出标题级别
    const level = parseInt(header.tagName.replace('H', ''))
    
    toc.push({
      id: id,
      text: header.innerText,
      level: level
    })
  })
  
  tocList.value = toc 
  console.log("成功提取目录：", tocList.value) // 用于看控制台是否成功抓到了
}

// 点击目录跳转的方法
const scrollToAnchor = (id) => {
  const element = document.getElementById(id)
  if (element) {
    // 减去80是为了给顶部的导航栏留点空间，不会被挡住
    const top = element.offsetTop - 80 
    window.scrollTo({ top, behavior: 'smooth' })
  }
}

// 复制链接功能
const handleShare = async () => {
  // 1. 复制当前链接到剪贴板
  navigator.clipboard.writeText(window.location.href)
  ElMessage.success('🔗 链接已复制！感谢您的分享~')
  
  // 2. 页面立刻展示转发数 +1
  shares.value++
  
  // 3. 告诉后端记录这条转发
  try {
    if (article.value && article.value.slug) {
      await axios.post(`http://116.62.218.51:8000/api/articles/${article.value.slug}/share`)
    }
  } catch (error) {
    console.error('转发保存到后端失败:', error)
  }
}

// ================= 真实的评论功能 =================
const comments = ref([])
const newComment = ref('')

// 新增：从后端读取当前文章的评论
const loadComments = async (slug) => {
  try {
    const res = await axios.get(`http://116.62.218.51:8000/api/comments/${slug}`)
    // 给所有后端返回的评论加上一个随机的游客头像
    comments.value = res.data.map(comment => ({
      ...comment,
      avatar: '/ciel.png' + comment.author + comment.id
    }))
  } catch (error) {
    console.error('获取评论失败:', error)
  }
}

// 获取文章数据
const fetchArticle = async (slug) => {
  try {
    isLoading.value = true
    const res = await axios.get(`http://116.62.218.51:8000/api/articles/${slug}`)
    
    // 👇【关键修改点】不管后端返回的是嵌套的，还是没嵌套的，我们都能拿到！
    const data = res.data
    const articleData = data.article || data // 兼容新旧两版 API
    
    if (articleData && articleData.title) {
      article.value = articleData
      
      likes.value = articleData.likes || 0
      shares.value = articleData.shares || 0
      
      // 提取上一篇和下一篇（如果是旧格式，这里取不到就是 null，很安全）
      prevPost.value = data.prev || null
      nextPost.value = data.next || null
      
      // 渲染 Markdown
      renderedHtml.value = md.render(article.value.content || '*无内容*')
      document.title = `${article.value.title} - UniHur's Blog`
      
      // 👇 清空旧目录，确保产生数据变动
      tocList.value = []
      
      // 👇 把 generateTOC 的触发放在数据确实赋完值、DOM刷新后
      setTimeout(() => {
        generateTOC()
      }, 300) // 把延迟稍微调长一点到 300ms，确保文章主体已经彻底显示出来
      
    } else {
      ElMessage.error('文章数据格式错误: 找不到标题')
    }
  } catch (error) {
    console.error('获取文章失败:', error)
    ElMessage.error('获取文章失败或文章不存在')
  } finally {
    isLoading.value = false
  }
}

// 监听路由参数变化（用于点击“上一篇/下一篇”时刷新内容和评论）
watch(() => route.params.slug, (newSlug) => {
  if (newSlug) {
    // 切换文章时，也把原目录清空
    tocList.value = []
    fetchArticle(newSlug)
    loadComments(newSlug) 
  }
})

onMounted(() => {
  fetchArticle(route.params.slug)
  loadComments(route.params.slug) // 👉 新增：第一次进页面时，拉取评论
})

const submitComment = async () => {
  if (!newComment.value.trim()) {
    ElMessage.warning('评论不能为空！')
    return
  }
  
  try {
    // 告诉后端我们要发评论啦
    await axios.post('http://116.62.218.51:8000/api/comments', {
      article_slug: route.params.slug,
      content: newComment.value,
      author: '游客' // 以游客身份
    })
    
    ElMessage.success('评论发表成功！')
    newComment.value = '' // 清空输入框
    
    // 重新从数据库拉取最新评论列表，让页面刷新出刚才发的评论
    loadComments(route.params.slug) 
  } catch (error) {
    console.error('评论失败:', error)
    ElMessage.error('评论失败！')
  }
}

const navigateTo = (slug) => {
  router.push(`/post/${slug}`)
}
</script>

<template>
  <div class="article-detail-container">
    <!-- 1. 博客大标题 Banner (完全复用主页的逻辑，显示全局的 Blog 标题) -->
    <header v-if="bannerMode !== 'hidden'" :class="['banner', bannerMode]" :style="{ height: bannerWrapperHeight }">
      <el-carousel :interval="4000" arrow="always" class="banner-carousel" :height="carouselHeight">
        <el-carousel-item v-for="(img, index) in bannerImages" :key="index">
          <img :src="img" class="carousel-img" alt="banner">
        </el-carousel-item>
      </el-carousel>
      
      <div v-if="bannerMode === 'background'" class="banner-overlay"></div>
      
      <!-- 这里显示全局的 Blog 标题和打字机，不是文章标题 -->
      <h1 v-if="bannerMode !== 'background'" class="blog-title">
        {{ siteConfig.name }}'s Blog
        <p class="blog-subtitle">
          {{ typewriterText }}<span class="cursor">|</span>
        </p>
      </h1>

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

    <!-- 2. 主体内容区 -->
    <div class="main-content-wrapper" :style="{ paddingTop: contentPaddingTop, marginTop: contentMarginTop }">
      
      <!-- 加载中提示 -->
      <div v-if="isLoading" class="glass-box" style="padding: 50px; text-align: center; margin-top: 20px;">
        <h2>拼命加载文章中...</h2>
      </div>

      <el-row :gutter="20" v-else-if="article">
        <!-- ================= 左侧栏 (包含个人信息、分类标签、目录) ================= -->
        <el-col :span="6">
          <ProfileCard :config="siteConfig" />

          <!-- 修改后的：文章目录 -->
          <div class="glass-box toc-box" v-if="tocList && tocList.length > 0">
            <h3>📖 文章目录</h3>
            <ul class="toc-list">
              <!-- 用 v-for 循环我们提取出来的目录 -->
              <li 
                v-for="item in tocList" 
                :key="item.id"
                :style="{ paddingLeft: (item.level - 1) * 15 + 'px' }"
              >
                <!-- 点击时阻止默认跳转，使用我们自己写的滚动函数 -->
                <a href="#" @click.prevent="scrollToAnchor(item.id)">
                  {{ item.text }}
                </a>
              </li>
            </ul>
          </div>
        </el-col>

        <!-- ================= 右侧：文章展示区 ================= -->
        <el-col :span="18" >
          
          <!-- 核心文章卡片 -->
          <div class="glass-box article-main-card">
            
            <!-- 顶部：文章封面图，标题悬浮在左下角 -->
            <div class="article-hero">
              <!-- 如果没有传封面，用一张默认的高清图代替 -->
              <img :src="article.cover || '/banner/1.png'" class="hero-img">
              <div class="hero-title-box">
                <h1 class="hero-title">{{ article.title }}</h1>
              </div>
            </div>

            <!-- 元信息：时间、分类、标签 (带图标) -->
            <div class="article-meta">
              <!-- 第一行：时间 -->
              <div class="meta-row">
                <div class="meta-item time">
                  <el-icon><Calendar /></el-icon>
                  <span>发布于: {{ new Date(article.publishTime).toLocaleDateString() }}</span>
                </div>
              </div>
              
              <div class="meta-row tags-row" v-if="article.category || (article.tags && article.tags.length > 0)">
                <!-- 分类框 (黄色) -->
                <div class="meta-box category-box" v-if="article.category">
                  <el-icon><Folder /></el-icon>
                  <span>{{ article.category }}</span>
                </div>

                <!-- 标签框 (绿色，循环生成) -->
                <template v-if="article.tags && article.tags.length > 0">
                  <div class="meta-box tag-box" v-for="tag in article.tags" :key="tag">
                    <el-icon><PriceTag /></el-icon>
                    <span>{{ tag }}</span>
                  </div>
                </template>

                <!-- 👇 新增：编辑按钮 (只在管理员登录时显示) -->
                <div class="edit-btn-wrapper" v-if="isLoggedIn">
                  <el-button round size="small" class="pink-edit-btn" @click="editArticle">
                    <el-icon><Edit /></el-icon> 编辑文章
                  </el-button>
                </div>

              </div>
            </div>

            <el-divider border-style="dashed" />

            <!-- 正文渲染区 -->
            <div class="markdown-body" v-html="renderedHtml"></div>
            
            <!-- 点赞按钮 -->
            <div class="action-center">
              
              <!-- 点赞模块（包含按钮和漂浮爱心的容器） -->
              <div class="like-wrapper">
                <!-- 漂浮爱心渲染区 -->
                <transition-group name="heart-float" tag="div" class="hearts-container">
                  <div 
                    v-for="heart in floatingHearts" 
                    :key="heart.id" 
                    class="floating-heart"
                    :style="{ 
                      fontSize: heart.size + 'px', 
                      color: heart.color,
                      left: `calc(50% + ${heart.leftOffset}px)`
                    }"
                  >
                    ❤️
                  </div>
                </transition-group>
                
                <el-button type="danger" plain round size="large" @click="handleLike" class="action-btn">
                  ❤️ 点赞 ({{ likes }})
                </el-button>
              </div>

              <!-- 分享/转发按钮 -->
              <el-button type="primary" plain round size="large" @click="handleShare" class="action-btn">
                <el-icon style="margin-right: 5px;"><Share /></el-icon> 分享文章 ({{ shares }})
              </el-button>
              
            </div>
          </div>

          <!-- 下方：上一篇 / 下一篇 -->
          <div class="prev-next-nav">
            <div class="nav-item prev glass-box" @click="prevPost ? navigateTo(prevPost.slug) : null" :class="{ disabled: !prevPost }">
              <div class="nav-label">上一篇</div>
              <div class="nav-title">{{ prevPost ? prevPost.title : '没有了' }}</div>
            </div>
            <div class="nav-item next glass-box" @click="nextPost ? navigateTo(nextPost.slug) : null" :class="{ disabled: !nextPost }">
              <div class="nav-label" style="text-align: right;">下一篇</div>
              <div class="nav-title" style="text-align: right;">{{ nextPost ? nextPost.title : '没有了' }}</div>
            </div>
          </div>

          <!-- 下方：评论区 -->
          <div class="glass-box comments-section">
            <h3>💬 评论区</h3>
            <div class="comment-input">
              <el-input v-model="newComment" type="textarea" :rows="3" placeholder="写下你的评论..." />
              <div class="comment-btn-row">
                <el-button type="primary" @click="submitComment" style="margin-top: 10px;">发表评论</el-button>
              </div>
            </div>
            
            <div class="comment-list">
              <div class="comment-item" v-for="comment in comments" :key="comment.id">
                <el-avatar :src="comment.avatar" :size="40" />
                <div class="comment-content-box">
                  <div class="comment-header">
                    <span class="comment-author">{{ comment.author }}</span>
                    <span class="comment-time">{{ comment.time }}</span>
                  </div>
                  <div class="comment-text">{{ comment.content }}</div>
                </div>
              </div>
            </div>
          </div>

        </el-col>
      </el-row>
    </div>
  </div>
</template>

<style scoped>
.main-content-wrapper { max-width: 1200px; margin: 0 auto; padding: 0 20px 40px 20px; position: relative; z-index: 10; }
.banner { position: relative; width: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; overflow: hidden; }
.banner-carousel { position: absolute; top: 0; left: 0; width: 100%; z-index: 1; }
.carousel-img { width: 100%; height: 100%; object-fit: cover; }
.blog-title { position: relative; z-index: 3; font-size: 4rem; font-weight: 900; color: #fff; text-shadow: 2px 2px 8px rgba(0,0,0,0.5); text-align: center; margin-top: -60px; }
.blog-subtitle { font-size: 2rem; font-weight: normal; margin-top: 10px; text-shadow: 1px 1px 5px rgba(0,0,0,0.8); }

.waves-container { position: absolute; bottom: 0; left: 0; width: 100%; height: 6vw; min-height: 100px; z-index: 10; line-height: 0; }
.waves { width: 100%; height: 100%; display: block; }
.wave1 { fill: rgba(244, 244, 245, 0.3); } .wave2 { fill: rgba(244, 244, 245, 0.5); } .wave3 { fill: rgba(244, 244, 245, 0.7); } .wave4 { fill: #f4f4f5; } 
html.dark .wave1 { fill: rgba(43, 34, 61, 0.3); } html.dark .wave2 { fill: rgba(43, 34, 61, 0.5); } html.dark .wave3 { fill: rgba(43, 34, 61, 0.7); } html.dark .wave4 { fill: #1a1525; } 

/* ================= 修复波浪动画 ================= */
.parallax > use { 
  animation: move-forever 25s cubic-bezier(.55,.5,.45,.5) infinite; 
}
.parallax > use:nth-child(1) { animation-delay: -2s; animation-duration: 7s; }
.parallax > use:nth-child(2) { animation-delay: -3s; animation-duration: 10s; }
.parallax > use:nth-child(3) { animation-delay: -4s; animation-duration: 13s; }
.parallax > use:nth-child(4) { animation-delay: -5s; animation-duration: 20s; }

@keyframes move-forever {
  0% { transform: translate3d(-90px, 0, 0); }
  100% { transform: translate3d(85px, 0, 0); }
}

/* 左侧分���和标签列表样式 */
.category-list { list-style: none; padding: 0; }
.category-list li { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px dashed rgba(0,0,0,0.1); }
html.dark .category-list li { border-bottom-color: rgba(255,255,255,0.1); }
.tag-list .custom-tag { margin: 5px; }

/* 目录样式 */
.toc-box { padding: 20px; margin-top: 20px; position: sticky; top: 80px; }
.toc-box h3 { margin-top: 0; border-bottom: 1px dashed rgba(0,0,0,0.1); padding-bottom: 10px; }
html.dark .toc-box h3 { border-bottom-color: rgba(255,255,255,0.1); color: #fff; } /* 夜间模式标题变白 */

.toc-list { list-style: none; padding-left: 0; }
.toc-list li { margin: 10px 0; }

.toc-list a { text-decoration: none; color: #555; transition: color 0.3s; }
html.dark .toc-list a { color: #ccc; } /* 夜间模式默认浅灰白 */

.toc-list a:hover { color: #409eff; }
html.dark .toc-list a:hover { color: #66b1ff; } /* 夜间模式悬浮时用更亮的蓝色 */

/* ================= 右侧核心文章区域 (已去重并修复对齐) ================= */
.article-main-card {
  /* 必须加 !important 来强制覆盖全局 glass-box 的 padding，这是对齐的关键！ */
  padding: 0 !important; 
  margin-top: 0 !important; 
  overflow: hidden; 
  min-height: calc(100vh - 200px); 
  display: flex;
  flex-direction: column;
}

/* 顶部封面图与悬浮标题 */
.article-hero {
  position: relative;
  width: 100%;
  height: 300px;
}
.hero-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: brightness(0.8);
  /* 保证顶格后不会因为直角把外框的圆角覆盖住 */
  border-radius: 8px 8px 0 0; 
}
.hero-title-box {
  position: absolute;
  bottom: 20px;
  left: 30px;
  right: 30px;
  background: rgba(0, 0, 0, 0.5); 
  padding: 10px 20px;
  border-radius: 8px;
  backdrop-filter: blur(4px);
}
.hero-title {
  color: white;
  margin: 0;
  font-size: 2rem;
  font-weight: bold;
}

/* 元信息和框框样式 */
.article-meta {
  padding: 20px 30px 0;
  color: #666;
}
html.dark .article-meta { color: #aaa; }

/* 新增：让编辑按钮靠最右边显示 */
.tags-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  position: relative;
  width: 100%;
}
.edit-btn-wrapper {
  margin-left: auto; /* 核心魔法：把按钮推到最右边 */
}

.meta-row {
  display: flex;
  align-items: center;
  margin-bottom: 15px; 
}

.tags-row {
  flex-wrap: wrap;
  gap: 12px; 
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.95rem;
}

/* 分类和标签的统一框框基础样式 */
.meta-box {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 8px; 
  font-size: 0.85rem;
  font-weight: bold;
  transition: transform 0.3s;
  cursor: pointer;
}
.meta-box:hover {
  transform: translateY(-2px); 
}

/* 分类框专属样式 (黄色) */
.category-box {
  background: rgba(230, 162, 60, 0.1);
  color: #e6a23c;
  border: 1px solid rgba(230, 162, 60, 0.3);
}

/* 标签框专属样式 (绿色) */
.tag-box {
  background: rgba(103, 194, 58, 0.1);
  color: #67c23a;
  border: 1px solid rgba(103, 194, 58, 0.3);
}

/* 正文渲染区 */
.markdown-body {
  padding: 0 30px 30px;
  font-family: sans-serif; 
  font-size: 16px; 
  line-height: 1.8; 
  color: #333; 
  flex: 1; /* 让内容太少时，把点赞按钮自动推到最底部 */
}
html.dark .markdown-body { color: #ddd; }
.markdown-body :deep(pre) { background: #f6f8fa; padding: 15px; border-radius: 8px; overflow: auto; }
html.dark .markdown-body :deep(pre) { background: #2d2d2d; }
.markdown-body :deep(img) { max-width: 100%; border-radius: 8px; margin: 10px 0;}
.markdown-body :deep(blockquote) { border-left: 4px solid #409eff; margin: 0; padding-left: 15px; color: #666; background: rgba(64,158,255,0.05); padding: 10px 15px; border-radius: 0 4px 4px 0; }

.action-center { 
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px; /* 两个按钮的间距 */
  padding-bottom: 40px; 
}

.action-btn {
  font-weight: bold;
  font-size: 1.1rem;
  padding: 12px 30px;
  height: auto;
  transition: transform 0.2s, box-shadow 0.2s;
}
.action-btn:hover {
  transform: translateY(-2px) scale(1.05); /* 鼠标悬浮微微放大 */
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

/* 点赞外层包裹，用来做相对定位 */
.like-wrapper {
  position: relative;
}

/* 漂浮爱心的容器，定位���点赞按钮正上方 */
.hearts-container {
  position: absolute;
  bottom: 100%; /* 在按钮顶部 */
  left: 0;
  width: 100%;
  height: 100px;
  pointer-events: none; /* 让鼠标穿透，防止挡住按钮点击 */
  z-index: 10;
}

/* 每颗漂浮的爱心基础样式 */
.floating-heart {
  position: absolute;
  bottom: 0;
  transform: translateX(-50%); /* 因为我们在内联样式用了 left: 50%，这里拉回中心对齐 */
  opacity: 1;
}

/* Vue 的 transition-group 动画类名 (入场和离开过程) */
.heart-float-enter-active {
  animation: floatUp 1.5s ease-out forwards;
}
.heart-float-leave-active {
  opacity: 0;
  transition: opacity 0.3s;
}

/* 定义“向上飘散并渐渐消失”的关键帧动画 */
@keyframes floatUp {
  0% {
    bottom: 0;
    opacity: 1;
    transform: translateX(-50%) scale(0.5); /* 刚出现时有点小 */
  }
  50% {
    opacity: 1;
    transform: translateX(-50%) scale(1.2); /* 飘到一半放大 */
  }
  100% {
    bottom: 80px; /* 向上飘的高度 */
    opacity: 0;   /* 最终完全透明 */
    transform: translateX(-50%) scale(1);
  }
}

/* 上下篇导航 */
.prev-next-nav { display: flex; justify-content: space-between; gap: 20px; margin-top: 20px; }
.nav-item { flex: 1; padding: 20px; cursor: pointer; transition: transform 0.3s, box-shadow 0.3s; }
.nav-item:hover:not(.disabled) { transform: translateY(-3px); color: #409eff; }
.nav-item.disabled { cursor: not-allowed; opacity: 0.5; }
.nav-label { font-size: 0.85rem; color: #888; margin-bottom: 5px; }
.nav-title { font-size: 1.1rem; font-weight: bold; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* 评论区样式 */
.comments-section { padding: 30px; margin-top: 20px; }
.comment-btn-row { display: flex; justify-content: flex-end; }
.comment-list { margin-top: 30px; }
.comment-item { display: flex; gap: 15px; margin-bottom: 20px; border-bottom: 1px solid rgba(0,0,0,0.05); padding-bottom: 20px; }
html.dark .comment-item { border-bottom-color: rgba(255,255,255,0.05); }
.comment-content-box { flex: 1; }
.comment-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
.comment-author { font-weight: bold; color: #333; }
html.dark .comment-author { color: #ddd; }
.comment-time { font-size: 0.8rem; color: #999; }
.comment-text { line-height: 1.5; color: #555; }
html.dark .comment-text { color: #bbb; }

/* 自定义粉色编辑按钮 */
.pink-edit-btn {
  background: linear-gradient(135deg, #ff79c6, #ff9a9e);
  border: none;
  color: #fff;
  font-weight: bold;
  box-shadow: 0 4px 15px rgba(255, 121, 198, 0.4);
  transition: all 0.3s;
}
.pink-edit-btn:hover {
  background: linear-gradient(135deg, #ff9a9e, #ff79c6);
  box-shadow: 0 6px 20px rgba(255, 121, 198, 0.6);
  transform: translateY(-2px);
  color: #fff;
}

</style>