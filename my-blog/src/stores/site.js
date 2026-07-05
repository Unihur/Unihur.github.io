// 站点配置 / 主题 / Banner / 公开设置 store
// 管理博客的基础元信息、玻璃材质+主题色、夜间模式、Banner 模式；
// 同时负责把公开设置同步到后端 / 读取后端设置，以及应用主题类到 <html> 上
import { defineStore } from 'pinia'
import { computed, reactive, ref, watch } from 'vue'
import { getPublicSettings, savePublicSettings } from '../api/settings'

const LS = {
  glassType: 'glass-type',
  themeColor: 'theme-color',
  isDark: 'is-dark'
}

// 主题颜色（与 style.css 中 html.theme-color-xxx 对应）
const THEME_COLORS = ['white', 'blue', 'pink', 'green', 'purple', 'orange']

export const useSiteStore = defineStore('site', () => {
  // ===== state =====
  // 博主基础信息（管理员可在高级设置里改）
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

  const isDark = ref(localStorage.getItem(LS.isDark) === 'true')
  const bannerMode = ref('banner')

  // 主题材质 (default / liquid / liquid_clear)
  const glassType = ref(localStorage.getItem(LS.glassType) || 'default')
  // 主题颜色（white / blue / ... ）
  const themeColor = ref(localStorage.getItem(LS.themeColor) || 'white')

  // ===== getters =====
  const bannerImages = ref([
    '/banner/1.png',
    '/banner/2.jpg',
    '/banner/3.jpg',
    '/banner/4.jpeg',
    '/banner/5.jpg',
    '/banner/6.jpg',
    '/banner/7.jpg'
  ])

  const bannerWrapperHeight = computed(() => {
    if (bannerMode.value === 'fullscreen' || bannerMode.value === 'background') return '100vh'
    return '30vw'
  })
  const carouselHeight = computed(() => bannerWrapperHeight.value)
  const contentPaddingTop = computed(() => {
    return bannerMode.value === 'background' || bannerMode.value === 'hidden' ? '120px' : '0px'
  })
  const contentMarginTop = computed(() => '0px')

  // ===== actions =====
  /** 把主题类名同步到 <html> 上 */
  function applyThemeConfig() {
    const root = document.documentElement

    // 1. 材质
    root.classList.remove('liquid-glass', 'liquid-glass-clear')
    if (glassType.value === 'liquid') root.classList.add('liquid-glass')
    else if (glassType.value === 'liquid_clear') root.classList.add('liquid-glass-clear')

    // 2. 颜色
    root.classList.remove(...THEME_COLORS.map((c) => `theme-color-${c}`))
    root.classList.add(`theme-color-${themeColor.value}`)

    // 3. 夜间模式
    if (isDark.value) root.classList.add('dark')
    else root.classList.remove('dark')
  }

  function setTheme({ glass, color } = {}) {
    if (glass) {
      glassType.value = glass
      localStorage.setItem(LS.glassType, glass)
    }
    if (color) {
      themeColor.value = color
      localStorage.setItem(LS.themeColor, color)
    }
    applyThemeConfig()
  }

  function toggleDarkMode() {
    isDark.value = !isDark.value
    localStorage.setItem(LS.isDark, String(isDark.value))
    applyThemeConfig()
    savePublicSettings({ banner_mode: bannerMode.value, is_dark: isDark.value })
  }

  function changeBannerMode(mode) {
    bannerMode.value = mode
    savePublicSettings({ banner_mode: bannerMode.value, is_dark: isDark.value })
  }

  /** 修改 siteConfig 任意字段（来自 SettingDrawer 的更新） */
  function updateSiteConfig(patch) {
    Object.assign(siteConfig, patch)
  }

  /** 恢复登录用户绑定的个性化配置（来自 /login 或 /user/me 的 config 字段） */
  function applyUserConfig(config = {}) {
    if (config.banner_mode) bannerMode.value = config.banner_mode
    if (config.is_dark !== undefined) {
      isDark.value = !!config.is_dark
      localStorage.setItem(LS.isDark, String(isDark.value))
    }
    applyThemeConfig()
  }

  /** 首屏加载：从后端拉取全站公开设置，覆盖未登录态显示 */
  async function loadPublicSettings() {
    try {
      const data = await getPublicSettings()
      return data
    } catch (e) {
      console.error('加载公共设置失败', e)
      return null
    }
  }

  /** 用户已登录时：把用户自己的配置覆盖到本地显示 */
  async function applyLoggedInSettings() {
    try {
      const data = await getPublicSettings()
      if (data) {
        if (data.banner_mode) bannerMode.value = data.banner_mode
        if (data.is_dark !== undefined) {
          isDark.value = !!data.is_dark
          localStorage.setItem(LS.isDark, String(isDark.value))
        }
      }
    } catch (e) {
      console.error('加载用户设置失败', e)
    }
  }

  // 同步站点名称 / favicon / live2dPos 到 DOM
  watch(
    siteConfig,
    (newVal) => {
      document.title = `${newVal.name}'s Blog`
      let link = document.querySelector("link[rel~='icon']")
      if (!link) {
        link = document.createElement('link')
        link.rel = 'icon'
        document.head.appendChild(link)
      }
      link.href = newVal.favicon
      document.documentElement.setAttribute('data-l2d-pos', newVal.live2dPosition)
      document.documentElement.style.setProperty('--l2d-scale', newVal.live2dScale)
    },
    { deep: true, immediate: true }
  )

  return {
    // state
    siteConfig,
    isDark,
    bannerMode,
    glassType,
    themeColor,
    bannerImages,
    // getters
    bannerWrapperHeight,
    carouselHeight,
    contentPaddingTop,
    contentMarginTop,
    // actions
    applyThemeConfig,
    setTheme,
    toggleDarkMode,
    changeBannerMode,
    updateSiteConfig,
    applyUserConfig,
    loadPublicSettings,
    applyLoggedInSettings,
    LS,
    THEME_COLORS
  }
})
