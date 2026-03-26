<script setup>
import { defineProps, computed, ref, onMounted } from 'vue'
import { View, User } from '@element-plus/icons-vue'

const props = defineProps({
  config: {
    type: Object,
    required: true
  },
  // 接收传过来的文章列表
  articles: {
    type: Array,
    default: () => []
  }
})

// 计算总浏览量
const totalViews = computed(() => {
  return props.articles.reduce((sum, article) => sum + (article.views || 0), 0)
})

// 简单访客模拟（基于访问此网站的次数）
const visitorCount = ref(0)
onMounted(() => {
  let count = parseInt(localStorage.getItem('global_visitor_count_v2') || '0')
  // 如果这台电脑/手机是第一次访问你的博客
  if (!localStorage.getItem('has_visited_flag')) {
    count += 1
    localStorage.setItem('global_visitor_count_v2', count)
    localStorage.setItem('has_visited_flag', 'true') // 永久打上标记
  }
  visitorCount.value = count
})

</script>

<template>
  <!-- 外层套用你定义的玻璃盒子样式 -->
  <div class="glass-box profile-card">
    
    <!-- 1. 方形大头像 (带圆角和悬浮放大效果) -->
    <div class="avatar-wrapper">
      <img :src="config.avatar" alt="avatar" class="profile-avatar" />
    </div>

    <!-- 2. 名字与下划线 -->
    <h2 class="profile-name">
      {{ config.name }}
      <div class="name-underline"></div>
    </h2>

    <!-- 3. 个性签名 -->
    <p class="profile-signature">{{ config.signature }}</p>

    <!-- 4. 分割线与社交图标 -->
    <div class="divider-line"></div>
    <div class="social-links">
      <!-- GitHub (黑色猫猫头) -->
      <el-tooltip content="GitHub 仓库" placement="top">
        <a href="https://github.com/Unihur" target="_blank" class="social-icon">
          <!-- 我们用一个简单的 SVG 绘制 GitHub 图标，这样不依赖外部字体库 -->
          <svg viewBox="0 0 16 16" width="24" height="24" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path></svg>
        </a>
      </el-tooltip>
      
      <!-- Gitee (红色的G) -->
      <el-tooltip content="Gitee 仓库" placement="top">
        <a href="https://gitee.com/unihur" target="_blank" class="social-icon" style="color: #c71d23;">
          <svg viewBox="0 0 1024 1024" width="24" height="24" fill="currentColor"><path d="M512 1024C229.222 1024 0 794.778 0 512S229.222 0 512 0s512 229.222 512 512-229.222 512-512 512zm259.149-568.883h-290.74a25.293 25.293 0 00-25.292 25.293l-.026 63.206c0 13.952 11.315 25.293 25.267 25.293h177.033c13.952 0 25.293 11.315 25.293 25.267v12.646a75.853 75.853 0 01-75.853 75.853h-240.23a25.293 25.293 0 01-25.267-25.293V417.203a75.853 75.853 0 0175.853-75.853h353.946a25.293 25.293 0 0025.267-25.292l.077-63.206a25.293 25.293 0 00-25.268-25.293H417.152a189.62 189.62 0 00-189.62 189.648v227.544a189.62 189.62 0 00189.62 189.648h227.544a189.62 189.62 0 00189.648-189.648V480.41a25.293 25.293 0 00-25.267-25.293z"></path></svg>
        </a>
      </el-tooltip>

      <!-- Bilibili (经典的粉色小电视) -->
      <el-tooltip content="B站 个人空间" placement="top">
        <a href="https://space.bilibili.com/1233420708" target="_blank" class="social-icon" style="color: #fb7299;">
          <svg viewBox="0 0 1024 1024" width="24" height="24" fill="currentColor"><path d="M777.514667 131.669333a53.333333 53.333333 0 0 1 71.338666 18.005334 53.333333 53.333333 0 0 1-18.005333 71.338666L750.677333 273.066667H853.333333a170.666667 170.666667 0 0 1 170.666667 170.666666v341.333334a170.666667 170.666667 0 0 1-170.666667 170.666666H170.666667A170.666667 170.666667 0 0 1 0 785.066667V443.733333A170.666667 170.666667 0 0 1 170.666667 273.066667h102.656L193.152 221.013333a53.333333 53.333333 0 0 1-18.005333-71.338666 53.333333 53.333333 0 0 1 71.338666-18.005334l129.365334 85.077334A53.333333 53.333333 0 0 1 385.109333 273.066667H638.890667a53.333333 53.333333 0 0 1 9.258666-56.32l129.365334-85.077334zM853.333333 379.733333H170.666667a64 64 0 0 0-64 64v341.333334a64 64 0 0 0 64 64h682.666666a64 64 0 0 0 64-64V443.733333a64 64 0 0 0-64-64z m-469.333333 128a53.333333 53.333333 0 0 1 53.333333 53.333334v42.666666a53.333333 53.333333 0 1 1-106.666666 0v-42.666666a53.333333 53.333333 0 0 1 53.333333-53.333334z m256 0a53.333333 53.333333 0 0 1 53.333333 53.333334v42.666666a53.333333 53.333333 0 1 1-106.666666 0v-42.666666a53.333333 53.333333 0 0 1 53.333333-53.333334z"></path></svg>
        </a>
      </el-tooltip>
    </div>

    <!-- 5. 分割线与统计数据 -->
    <div class="divider-line"></div>
    <div class="profile-stats">
      <div class="stat-item">
        <span class="stat-label"><el-icon><User /></el-icon> 访客数</span>
        <span class="stat-value">{{ visitorCount }}</span>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <span class="stat-label"><el-icon><View /></el-icon> 浏览量</span>
        <span class="stat-value">{{ totalViews }}</span>
      </div>
    </div>
    
  </div>
</template>

<style scoped>
.profile-card {
  text-align: center;
  padding: 20px;
  /* 让背景颜色在夜间模式下显得更深邃，符合你的参考图 */
  background: rgba(255, 255, 255, 0.7);
}
html.dark .profile-card {
  background: rgba(40, 42, 54, 0.8); /* 偏蓝紫的深灰色 */
  border-color: rgba(255, 255, 255, 0.05);
}

/* 头像外壳 */
.avatar-wrapper {
  width: 100%;
  aspect-ratio: 1 / 1; /* 强制正方形 */
  border-radius: 16px;
  overflow: hidden;
  margin-bottom: 15px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.profile-avatar {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s ease;
}
.profile-avatar:hover {
  transform: scale(1.05);
}

/* 名字和粉色下划线 */
.profile-name {
  margin: 10px 0;
  font-size: 1.5rem;
  font-weight: bold;
  color: #333;
  display: flex;
  flex-direction: column;
  align-items: center;
}
html.dark .profile-name { color: #fff; }

.name-underline {
  width: 30px;
  height: 4px;
  background-color: #ff79c6; /* 猛男粉 */
  border-radius: 2px;
  margin-top: 8px;
}

/* 个性签名 */
.profile-signature {
  color: #bd93f9; /* 浅紫色 */
  font-size: 0.95rem;
  margin-bottom: 20px;
  font-weight: 500;
}

/* 细分割线 */
.divider-line {
  width: 90%;
  height: 1px;
  background-color: rgba(0,0,0,0.1);
  margin: 15px auto;
}
html.dark .divider-line {
  background-color: rgba(255,255,255,0.1);
}

/* 社交图标 */
.social-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  color: #333; /* Github 默认黑色 */
  background: rgba(0,0,0,0.05);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
html.dark .social-icon { 
  background: rgba(255,255,255,0.05);
  color: #eee; 
}
.social-icon:hover {
  transform: translateY(-5px) scale(1.1); /* 鼠标悬浮向上起飞+放大 */
  box-shadow: 0 5px 15px rgba(0,0,0,0.15);
}

/* 修改外层盒子：让里面的三个图标居中，并留出25px的间隙 */
.social-links {
  display: flex;
  justify-content: center; /* 这里是实现居中的关键 */
  gap: 25px; /* 控制图标之间的距离 */
  padding: 10px 0;
}

/* 统计数据 */
.profile-stats {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 15px;
}
.stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.stat-label {
  font-size: 0.8rem;
  color: #ff79c6;
  margin-bottom: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}
.stat-label .el-icon {
  font-size: 1.1rem; /* 给定一个稍微大一点的绝对值 */
  -webkit-font-smoothing: antialiased;
  transform: translateZ(0); /* 开启硬件加速防模糊 */
}
.stat-value {
  font-size: 1.1rem;
  font-weight: bold;
  color: #333;
}
html.dark .stat-value { color: #eee; }

/* 统计中间的竖线 */
.stat-divider {
  width: 1px;
  height: 30px;
  background-color: rgba(0,0,0,0.1);
}
html.dark .stat-divider { background-color: rgba(255,255,255,0.1); }
</style>