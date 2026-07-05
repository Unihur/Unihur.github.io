<script setup>
// 应用外壳：
// - 负责挂载 AppHeader / 路由出口 / MouseTrail
// - 统一初始化 theme、打字机、Live2D
// - 首屏恢复：登录用户的配置 + 全站公开设置
// - 监听 siteConfig 中 Live2D 字段变化，动态加载 / 换模型 / 提示刷新
import { onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'

import { useSiteStore } from '@/stores/site'
import { useUserStore } from '@/stores/user'
import { useTypewriter } from '@/composables/useTypewriter'
import { useLive2d } from '@/composables/useLive2d'

import AppHeader from '@/components/AppHeader.vue'
import MouseTrail from '@/components/MouseTrail.vue'

const siteStore = useSiteStore()
const userStore = useUserStore()

// 打字机单例：signature 变化会自动重启
const { start: startTypewriter } = useTypewriter(() => siteStore.siteConfig.signature)

// Live2D
const live2d = useLive2d(siteStore.siteConfig)

onMounted(async () => {
  // 应用本地保存的主题
  siteStore.applyThemeConfig()

  // 启动打字机（仅一次）
  startTypewriter()

  // Live2D 懒加载
  if (siteStore.siteConfig.live2dEnabled) {
    live2d.load()
  }

  // 已登录用户：拉取最新个人配置
  if (userStore.token) {
    const me = await userStore.refreshProfile()
    if (me) {
      siteStore.applyUserConfig(me.config || {})
    }
  }

  // 全站公开设置（覆盖未登录态的 banner / 夜间模式）
  try {
    const data = await siteStore.loadPublicSettings()
    if (data && !userStore.isLoggedIn) {
      if (data.banner_mode) siteStore.bannerMode = data.banner_mode
      if (data.is_dark !== undefined) {
        siteStore.isDark = !!data.is_dark
      }
      siteStore.applyThemeConfig()
    }
  } catch (_) {
    /* 已在 store 内打印错误 */
  }
})

// 监听 Live2D 相关字段变化（来自 SettingDrawer 的修改）
watch(
  () => siteStore.siteConfig.live2dEnabled,
  (enabled) => {
    if (enabled && !live2d.getInstance()) {
      live2d.load()
    } else if (!enabled && live2d.getInstance()) {
      // 关闭需要刷新页面才能彻底清理内存
      ElMessage.warning('关闭看板娘需刷新页面才能清理内存哦！')
      setTimeout(() => window.location.reload(), 1500)
    }
  }
)
watch(
  () => siteStore.siteConfig.live2dPath,
  (newPath) => {
    if (siteStore.siteConfig.live2dEnabled && live2d.getInstance() && newPath) {
      live2d.changeModel(newPath)
    }
  }
)
</script>

<template>
  <div class="app-root">
    <AppHeader />
    <router-view />
    <MouseTrail />
  </div>
</template>

<style scoped>
.app-root {
  width: 100%;
}

/* Live2D 全局位置 / 缩放覆盖（保持原 App.vue 中的魔法 CSS） */
:global(html[data-l2d-pos='right'] #oml2d-stage) {
  left: auto !important;
  right: 0 !important;
}
:global(html[data-l2d-pos='left'] #oml2d-stage) {
  left: 0 !important;
  right: auto !important;
}
:global(#oml2d-stage) {
  transform: scale(var(--l2d-scale, 1));
  transform-origin: bottom;
  transition:
    transform 0.3s ease,
    left 0.5s ease,
    right 0.5s ease;
}
</style>
