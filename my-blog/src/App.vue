<script setup>
import { ref, reactive, computed, onMounted,watch } from 'vue' 
import { Search, Setting, Brush, Picture, Sunny, Moon } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

import ProfileCard from './components/ProfileCard.vue' 
import MouseTrail from './components/MouseTrail.vue'
import SettingDrawer from './components/SettingDrawer.vue'
import MusicPlayer from './components/MusicPlayer.vue' 

import { loadOml2d } from 'oh-my-live2d'

// ================= 全局状态：网站配置 =================
const siteConfig = reactive({
  name: 'UniHur',
  signature: '✨ 纸上得来终觉浅，绝知此事要躬行！ ✨',
  avatar: '/ciel.png',
  favicon: '/favicon.png',

  live2dEnabled: true, 
  live2dPath: '/ulk/ulk.model3.json',
  live2dScale: 0.5,
  live2dPosition: 'right'
})

// ================= 增加：打字机特效逻辑 =================
const typewriterText = ref('') // 页面上实际显示的文字
let typeTimer = null

const startTypewriter = () => {
  // 清除旧定时器防止重复执行
  if (typeTimer) clearTimeout(typeTimer)
  
  let i = 0;
  let isDeleting = false;
  const fullText = siteConfig.signature

  const loop = () => {
    // 如果设置里把签名清空了，就停止动画
    if (!siteConfig.signature) {
      typewriterText.value = ''
      return
    }

    // 防止在设置里修改了文字导致越界
    const currentFullText = siteConfig.signature

    if (!isDeleting) {
      // 正在打字
      typewriterText.value = currentFullText.substring(0, i + 1)
      i++
      
      if (i === currentFullText.length) {
        // 打字完成，停顿 2000 毫秒后开始删除
        isDeleting = true
        typeTimer = setTimeout(loop, 2000)
        return
      }
      // 打字速度 (随机 100~200ms)
      typeTimer = setTimeout(loop, Math.random() * 100 + 100)
      
    } else {
      // 正在删除
      typewriterText.value = currentFullText.substring(0, i - 1)
      i--
      
      if (i === 0) {
        // 删除完成，停顿 500 毫秒后开始重新打字
        isDeleting = false
        typeTimer = setTimeout(loop, 500)
        return
      }
      // 删除速度 (固定 50ms)
      typeTimer = setTimeout(loop, 50)
    }
  }
  
  loop()
}

// 当网页加载时，启动打字机
onMounted(() => {
  startTypewriter()
  if (siteConfig.live2dEnabled) {
    loadLive2D()
  }
})

// 当我们在设置抽屉里修改了签名时，重置打字机动画
watch(() => siteConfig.signature, () => {
  startTypewriter()
})

// ================= 深度监听配置，让网页实时变化 =================
watch(siteConfig, (newVal) => {
  // 1. 实时改网页标题
  document.title = `${newVal.name}'s Blog`

  // 2. 实时改浏览器图标 (Favicon)
  let link = document.querySelector("link[rel~='icon']");
  if (!link) {
    link = document.createElement('link');
    link.rel = 'icon';
    document.head.appendChild(link);
  }
  link.href = newVal.favicon;

  // 3. 实时通知 CSS 去改变 Live2D 的大小和位置
  document.documentElement.setAttribute('data-l2d-pos', newVal.live2dPosition)
  document.documentElement.style.setProperty('--l2d-scale', newVal.live2dScale)
}, { deep: true, immediate: true })

// ================= 看板娘初始化 =================
let oml2dInstance = null // 用来存看板娘的实例

onMounted(() => {
  // 如果默认开启，才去加载
  if (siteConfig.live2dEnabled) {
    loadLive2D()
  }
})

// 封装一个加载函数
const loadLive2D = () => {
  if (oml2dInstance) return // 如果已经有了就不重复加载
  oml2dInstance = loadOml2d({
    models: [{ 
      path: siteConfig.live2dPath,
      scale: siteConfig.live2dScale
    }],
    primaryColor: '#ff79c6',
    menus: { disable: true }
  })
}

// 接收子组件传回来的数据，并合并到主数据中
const handleConfigUpdate = (newConfig) => {
  Object.assign(siteConfig, newConfig)

  // 处理看板娘加载和换装
  if (newConfig.live2dEnabled && !oml2dInstance) {
    loadLive2D() 
  } else if (!newConfig.live2dEnabled && oml2dInstance) {
    ElMessage.warning('关闭看板娘需刷新页面才能清理内存哦！')
    setTimeout(() => window.location.reload(), 1500)
  } else if (newConfig.live2dEnabled && oml2dInstance) {
    oml2dInstance.loadNextModel({ path: newConfig.live2dPath })
  }
}

// 👇 2. 新增：控制设置抽屉显示的变量和逻辑
const showSettingDrawer = ref(false)

const openSetting = () => {
  // 加上权限判断：如果还没登录，就不让进设置
  if (!isLoggedIn.value) {
    ElMessage.warning('请先点击右侧头像登录管理员账号！')
    showLoginDialog.value = true // 直接弹出登录框
    return
  }
  showSettingDrawer.value = true
}

// ================= 登录逻辑 =================
const isLoggedIn = ref(false)
const showLoginDialog = ref(false)
const loginForm = reactive({ username: '', password: '' })

const handleLoginClick = () => {
  if (isLoggedIn.value) {
    ElMessage.success('你已经是管理员了，这里以后会跳转到后台设置界面！')
  } else {
    showLoginDialog.value = true
  }
}
const doLogin = () => {
  if (loginForm.username === 'admin') {
    isLoggedIn.value = true
    showLoginDialog.value = false
    ElMessage.success('管理员登录成功！')
  } else {
    ElMessage.error('账号或密码错误 (测试账号是 admin)')
  }
}

// ================= 夜间模式 =================
const isDark = ref(false)
const toggleDarkMode = () => {
  isDark.value = !isDark.value
  if (isDark.value) document.documentElement.classList.add('dark')
  else document.documentElement.classList.remove('dark')
}

// ================= Banner 高度和布局计算 =================
const bannerImages = ref([
  '/banner/1.png',
  '/banner/2.jpg',
  '/banner/3.jpg',
  '/banner/4.jpeg',
  '/banner/5.jpg',
  '/banner/6.jpg',
  '/banner/7.jpg'
])

const bannerMode = ref('banner')
const changeBannerMode = (command) => { bannerMode.value = command }

// 解答1：如何调整横幅图的高度？
// 把下面的 '45vw' 改小（比如 35vw），横幅就会变矮，下面的博客内容就会露出来更多！
const bannerHeightValue = '30vw' 

const carouselHeight = computed(() => {
  if (bannerMode.value === 'fullscreen' || bannerMode.value === 'background') return '100vh'
  return bannerHeightValue
})
const bannerWrapperHeight = computed(() => {
  if (bannerMode.value === 'fullscreen' || bannerMode.value === 'background') return '100vh'
  return bannerHeightValue
})
const contentPaddingTop = computed(() => {
  return (bannerMode.value === 'background' || bannerMode.value === 'hidden') ? '120px' : '0px'
})
const contentMarginTop = computed(() => {
  return (bannerMode.value === 'banner' || bannerMode.value === 'fullscreen') ? '0px' : '0px'
})
</script>

<template>
  <div class="app-root">
    
    <!-- 1. 顶部导航栏 -->
    <div class="nav-container">
      <nav class="glass-box navbar">
        <div class="nav-links">
          <span>首页</span><span>写作</span><span>项目</span>
          <span>娱乐</span><span>留言</span><span>导航</span><span>关于</span>
        </div>
        
        <div class="nav-icons">
          <el-tooltip content="设置" placement="bottom">
            <el-icon class="icon-btn" @click="openSetting"><Setting /></el-icon>
          </el-tooltip>

          <el-tooltip content="主题颜色" placement="bottom"><el-icon class="icon-btn"><Brush /></el-icon></el-tooltip>
          <el-dropdown @command="changeBannerMode" trigger="click">
            <span class="el-dropdown-link">
              <el-tooltip content="Banner设置" placement="bottom"><el-icon class="icon-btn"><Picture /></el-icon></el-tooltip>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="banner">横幅图模式</el-dropdown-item>
                <el-dropdown-item command="fullscreen">填充屏幕</el-dropdown-item>
                <el-dropdown-item command="background">背景图片模式</el-dropdown-item>
                <el-dropdown-item command="hidden">隐藏</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-tooltip :content="isDark ? '日间模式' : '夜间模式'" placement="bottom">
            <el-icon class="icon-btn" @click="toggleDarkMode"><component :is="isDark ? Sunny : Moon" /></el-icon>
          </el-tooltip>

          <!-- 新增：用户登录头像 -->
          <div class="divider"></div>
          <el-tooltip :content="isLoggedIn ? '个人中心' : '点击登录'" placement="bottom">
            <el-avatar 
              :size="36" 
              :src="siteConfig.avatar" 
              class="login-avatar"
              @click="handleLoginClick"
            />
          </el-tooltip>
        </div>
      </nav>
    </div>

    <!-- 2. 博客大标题 Banner -->
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
          <div class="glass-box post-card" v-for="i in 3" :key="i">
            <div class="post-info">
              <h2>Mathematical Formulas in Markdown {{ i }}</h2>
              <div class="post-meta"><span>📅 2026-03-23</span> | <span>👁️ 浏览: 120</span> | <span>📝 字数: 2.5k</span></div>
              <p class="post-desc">这是博客的内容简介。展示了如何在 Markdown 中使用 LaTeX 渲染数学公式...</p>
              <div class="post-tags"><el-tag size="small">Documentation</el-tag><el-tag size="small" type="info">LaTeX</el-tag></div>
            </div>
            <div class="post-cover">
              <img src="https://images.unsplash.com/photo-1555066931-4365d14bab8c?q=80&w=400&auto=format&fit=crop" alt="cover">
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 登录弹窗对话框 (临时用 el-dialog 模拟) -->
    <el-dialog v-model="showLoginDialog" title="登录 / 管理员入口" width="400px" center>
      <el-input v-model="loginForm.username" placeholder="账号" style="margin-bottom: 15px;" />
      <el-input v-model="loginForm.password" placeholder="密码" type="password" show-password />
      <template #footer>
        <el-button @click="showLoginDialog = false">取消</el-button>
        <el-button type="primary" @click="doLogin">登录</el-button>
      </template>
    </el-dialog>

    <SettingDrawer 
      v-model:visible="showSettingDrawer" 
      :config="siteConfig" 
      @updateConfig="handleConfigUpdate"
    />

    <MouseTrail />
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

.post-card { display: flex; justify-content: space-between; align-items: center; transition: transform 0.3s; }
.post-card:hover { transform: translateY(-5px); }
.post-info { flex: 1; padding-right: 20px; }
.post-meta { font-size: 0.8rem; color: #666; margin-bottom: 10px; }
html.dark .post-meta { color: #aaa; }
.post-desc { color: #444; line-height: 1.6; }
html.dark .post-desc { color: #ccc; }
.post-cover { width: 200px; height: 140px; border-radius: 8px; overflow: hidden; }
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