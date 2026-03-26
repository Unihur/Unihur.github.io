<script setup>
import { ref, reactive, computed, onMounted, watch, provide } from 'vue' 
import { Search, Setting, Brush, Picture, Sunny, Moon, HomeFilled, Edit, Box, VideoPlay, ChatDotSquare, Guide, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

import MouseTrail from './components/MouseTrail.vue'
import SettingDrawer from './components/SettingDrawer.vue'

import { loadOml2d } from 'oh-my-live2d'
import { useRouter } from 'vue-router'

import axios from 'axios'

// ================= 全局状态：网站配置 =================
const siteConfig = reactive({
  name: 'UniHur',
  signature: '✨ 纸上得来终觉浅，绝知此事要躬行！ ✨',
  avatar: '/avatar.png',
  favicon: '/favicon.png',

  live2dEnabled: true, 
  live2dPath: '/ulk/ulk.model3.json',
  live2dScale: 0.4,
  live2dPosition: 'right'
})

// ================= 增加：打字机特效逻辑 =================
const typewriterText = ref('') // 页面上实际显示的文字
let typeTimer = null

const startTypewriter = () => {
  if (typeTimer) clearTimeout(typeTimer)
  
  let i = 0;
  let isDeleting = false;
  const fullText = siteConfig.signature

  const loop = () => {
    if (!siteConfig.signature) {
      typewriterText.value = ''
      return
    }

    const currentFullText = siteConfig.signature

    if (!isDeleting) {
      typewriterText.value = currentFullText.substring(0, i + 1)
      i++
      
      if (i === currentFullText.length) {
        isDeleting = true
        typeTimer = setTimeout(loop, 2000)
        return
      }
      typeTimer = setTimeout(loop, Math.random() * 100 + 100)
      
    } else {
      typewriterText.value = currentFullText.substring(0, i - 1)
      i--
      
      if (i === 0) {
        isDeleting = false
        typeTimer = setTimeout(loop, 500)
        return
      }
      typeTimer = setTimeout(loop, 50)
    }
  }
  
  loop()
}

onMounted(async () => {

  if (localStorage.getItem('admin_token')) {
    isLoggedIn.value = true
  }

  startTypewriter()
  if (siteConfig.live2dEnabled) {
    loadLive2D()
  }

  // ========== 新增：页面加载时从数据库读取设置 ==========
  try {
    const res = await fetch('http://116.62.218.51:8000/api/settings')
    if (res.ok) {
      const data = await res.json()
      // 1. 恢复 Banner 模式
      if (data.banner_mode) {
        bannerMode.value = data.banner_mode
      }
      // 2. 恢复 夜间/日间 模式
      isDark.value = data.is_dark
      if (isDark.value) {
        document.documentElement.classList.add('dark')
      } else {
        document.documentElement.classList.remove('dark')
      }
    }
  } catch (error) {
    console.error("加载设置失败，使用默认设置", error)
  }
})

const handleLogout = () => {
  localStorage.removeItem('admin_token')
  isLoggedIn.value = false
}

watch(() => siteConfig.signature, () => {
  startTypewriter()
})

// ================= 深度监听配置，让网页实时变化 =================
watch(siteConfig, (newVal) => {
  document.title = `${newVal.name}'s Blog`

  let link = document.querySelector("link[rel~='icon']");
  if (!link) {
    link = document.createElement('link');
    link.rel = 'icon';
    document.head.appendChild(link);
  }
  link.href = newVal.favicon;

  document.documentElement.setAttribute('data-l2d-pos', newVal.live2dPosition)
  document.documentElement.style.setProperty('--l2d-scale', newVal.live2dScale)
}, { deep: true, immediate: true })

// ================= 看板娘初始化 =================
let oml2dInstance = null 

const loadLive2D = () => {
  if (oml2dInstance) return 
  oml2dInstance = loadOml2d({
    models: [{ 
      path: siteConfig.live2dPath,
      scale: siteConfig.live2dScale
    }],
    primaryColor: '#ff79c6',
    menus: { disable: true }
  })
}

const handleConfigUpdate = (newConfig) => {
  Object.assign(siteConfig, newConfig)

  if (newConfig.live2dEnabled && !oml2dInstance) {
    loadLive2D() 
  } else if (!newConfig.live2dEnabled && oml2dInstance) {
    ElMessage.warning('关闭看板娘需刷新页面才能清理内存哦！')
    setTimeout(() => window.location.reload(), 1500)
  } else if (newConfig.live2dEnabled && oml2dInstance) {
    oml2dInstance.loadNextModel({ path: newConfig.live2dPath })
  }
}

// ================= 抽屉和登录逻辑 =================
const showSettingDrawer = ref(false)
const openSetting = () => {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先点击右侧头像登录管理员账号！')
    showLoginDialog.value = true 
    return
  }
  showSettingDrawer.value = true
}

const router = useRouter()

// 写作按钮点击逻辑
const handleWriteClick = () => {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先点击右侧头像登录管理员账号！')
    showLoginDialog.value = true 
    return
  }
  router.push('/write')
}

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
const doLogin = async () => {
  try {
    const res = await axios.post('http://116.62.218.51:8000/api/login', loginForm)
    if (res.data.status === 'success') {
      localStorage.setItem('admin_token', res.data.token) // 把门禁卡存进浏览器
      isLoggedIn.value = true
      showLoginDialog.value = false
      ElMessage.success('管理员登录成功！')
    }
  } catch (error) {
    ElMessage.error('账号或密码错误')
  }
}

// ================= 把设置保存到数据库的函数 =================
const saveSettingsToDB = async () => {
  try {
    await fetch('http://116.62.218.51:8000/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        banner_mode: bannerMode.value, 
        is_dark: isDark.value 
      })
    })
  } catch (error) {
    console.error("保存设置失败", error)
  }
}

// ================= 夜间模式 =================
const isDark = ref(false)
const toggleDarkMode = () => {
  isDark.value = !isDark.value
  if (isDark.value) document.documentElement.classList.add('dark')
  else document.documentElement.classList.remove('dark')
  
  // 新增：切换完模式后，立即保存到数据库
  saveSettingsToDB()
}

// ================= Banner 高度和布局计算 =================
const bannerImages = ref([
  '/banner/1.png', '/banner/2.jpg', '/banner/3.jpg', '/banner/4.jpeg',
  '/banner/5.jpg', '/banner/6.jpg', '/banner/7.jpg'
])

const bannerMode = ref('banner')
const changeBannerMode = (command) => { 
  bannerMode.value = command 
  
  // 新增：切换完Banner后，立即保存到数据库
  saveSettingsToDB()
}

const bannerHeightValue = '30vw' 

// 👇 必须先定义所有的 computed 变量
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

// 👇 最后！在所有的变量和函数都定义完毕后，再统一把它们 provide 出去给 Home.vue 用
provide('siteConfig', siteConfig)
provide('bannerMode', bannerMode)
provide('bannerImages', bannerImages)
provide('bannerWrapperHeight', bannerWrapperHeight)
provide('carouselHeight', carouselHeight)
provide('typewriterText', typewriterText)
provide('contentPaddingTop', contentPaddingTop)
provide('contentMarginTop', contentMarginTop)
provide('isLoggedIn', isLoggedIn)

</script>
<template>
  <div class="app-root">
    
    <!-- 1. 顶部导航栏 -->
    <div class="nav-container">
      <nav class="glass-box navbar">
        <div class="nav-links">
          <router-link to="/" custom v-slot="{ navigate }">
            <span @click="navigate"><el-icon><HomeFilled /></el-icon>首页</span>
          </router-link>
          <span @click="handleWriteClick"><el-icon><Edit /></el-icon>写作</span>
          <span><el-icon><Box /></el-icon>项目</span>
          <span><el-icon><VideoPlay /></el-icon>娱乐</span>
          <span><el-icon><ChatDotSquare /></el-icon>留言</span>
          <span><el-icon><Guide /></el-icon>导航</span>
          <span><el-icon><InfoFilled /></el-icon>关于</span>
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

    <!-- 👇 魔法标签：路由匹配到的组件会显示在这里！ -->
    <router-view />

    <!-- 登录弹窗对话框 (临时用 el-dialog 模拟) -->
    <el-dialog v-model="showLoginDialog" title="登录 / 管理员入口" width="400px" center>
      <el-input v-model="loginForm.username" placeholder="账号" style="margin-bottom: 15px;" />
      <el-input v-model="loginForm.password" placeholder="密码" type="password" show-password />
      <template #footer>
        <el-button round @click="showLoginDialog = false">取 消</el-button>
        <!-- 加上自定义的粉色 class -->
        <el-button type="primary" round class="pink-login-btn" @click="doLogin">登 录</el-button>
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

.nav-container { 
  position: fixed; /* 👈 将 absolute 改为 fixed 即可吸顶跟随 */
  top: 15px; 
  left: 0; 
  width: 100%; 
  display: flex; 
  justify-content: center; 
  z-index: 999; 
  padding: 0 20px; 
  box-sizing: border-box; 
}
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

/* 自定义粉色登录按钮 */
.pink-login-btn {
  background: linear-gradient(135deg, #ff79c6, #ff9a9e);
  border: none;
  box-shadow: 0 4px 15px rgba(255, 121, 198, 0.4);
  transition: all 0.3s;
  font-weight: bold;
}
.pink-login-btn:hover {
  background: linear-gradient(135deg, #ff9a9e, #ff79c6);
  box-shadow: 0 6px 20px rgba(255, 121, 198, 0.6);
  transform: translateY(-2px);
}

</style>