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
      <a href="#" class="social-icon" title="GitHub">
        <!-- 临时用 Element 图标代替自定义 SVG -->
        <i class="iconfont">🐙</i> 
      </a>
      <a href="#" class="social-icon" title="Bilibili">
        <i class="iconfont">📺</i>
      </a>
      <a href="#" class="social-icon" title="Tiktok">
        <i class="iconfont">🎵</i>
      </a>
      <a href="#" class="social-icon" title="Weibo">
        <i class="iconfont">🌐</i>
      </a>
    </div>

    <!-- 5. 分割线与统计数据 -->
    <div class="divider-line"></div>
    <div class="profile-stats">
      <div class="stat-item">
        <span class="stat-label">👁️ 访问量</span>
        <span class="stat-value">88.6k</span>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <span class="stat-label">👤 访客数</span>
        <span class="stat-value">12.3k</span>
      </div>
    </div>
    
  </div>
</template>

<script setup>
import { defineProps } from 'vue'

// 接收从父组件 (App.vue) 传过来的配置数据
defineProps({
  config: {
    type: Object,
    required: true
  }
})
</script>

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
.social-links {
  display: flex;
  justify-content: space-around;
  padding: 0 10px;
}
.social-icon {
  color: #666;
  text-decoration: none;
  font-size: 1.2rem;
  transition: color 0.3s;
}
html.dark .social-icon { color: #ccc; }
.social-icon:hover { color: #ff79c6; }

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
  color: #ff79c6; /* 粉色文字 */
  margin-bottom: 5px;
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