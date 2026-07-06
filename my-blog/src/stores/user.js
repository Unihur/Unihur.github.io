// 用户/登录状态 store
// 统一管理 token、用户信息、管理员判定；
// 管理员标识优先来自后端 /user/me 的 is_admin 字段，未提供时回退到环境变量配置的管理员用户名
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import {
  login as apiLogin,
  getMe,
  updateUser as apiUpdateUser,
  uploadAvatar as apiUploadAvatar
} from '../api/auth'
import { setUnauthorizedHandler } from '../api/request'

// 通过环境变量配置管理员用户名（避免在源码里硬编码 'unihur'）
const ADMIN_USERNAME = import.meta.env.VITE_ADMIN_USERNAME || ''

// localStorage 键名常量
const LS = {
  token: 'token',
  username: 'username',
  avatar: 'avatar',
  rememberUser: 'saved_username',
  rememberPass: 'saved_password',
  isDark: 'is-dark'
}

export const useUserStore = defineStore('user', () => {
  // ===== state =====
  const token = ref(localStorage.getItem(LS.token) || '')
  const username = ref(localStorage.getItem(LS.username) || '')
  const avatar = ref(localStorage.getItem(LS.avatar) || '')
  // is_admin 字段由后端 /user/me 返回；未提供则为 null
  const isAdminFromBackend = ref(null)

  // ===== getters =====
  const isLoggedIn = computed(() => !!token.value)
  // 管理员判定：账号名为 unihur（唯一管理员）。
  // 不依赖后端 is_admin 字段，避免后端未返回时回退逻辑出问题。
  const isAdmin = computed(() => {
    if (!isLoggedIn.value) return false
    return username.value === ADMIN_USERNAME
  })

  // ===== actions =====
  /** 应用登录返回结果到状态 + localStorage */
  function applyLoginResponse(res) {
    const data = res.data || {}
    token.value = data.token || ''
    username.value = data.username || ''
    avatar.value = data.avatar || ''
    isAdminFromBackend.value = typeof data.is_admin === 'boolean' ? data.is_admin : null

    if (token.value) localStorage.setItem(LS.token, token.value)
    if (username.value) localStorage.setItem(LS.username, username.value)
    if (avatar.value) localStorage.setItem(LS.avatar, avatar.value)
  }

  /**
   * 登录
   * @param {{username:string,password:string,remember:boolean}} form
   */
  async function login(form) {
    const res = await apiLogin({ username: form.username, password: form.password })

    // 安全策略：仅记住账号（用户名），不存储密码明文。
    // 历史遗留的 saved_password 若存在也一并清除。
    localStorage.removeItem(LS.rememberPass)
    if (form.remember) {
      localStorage.setItem(LS.rememberUser, form.username)
    } else {
      localStorage.removeItem(LS.rememberUser)
    }

    applyLoginResponse(res)
    return res
  }

  /** 退出登录：清状态 + 清 localStorage */
  function logout() {
    token.value = ''
    username.value = ''
    avatar.value = ''
    isAdminFromBackend.value = null
    localStorage.removeItem(LS.token)
    localStorage.removeItem(LS.username)
    localStorage.removeItem(LS.avatar)
  }

  /** 拉取最新的用户信息（刷新页面时调用）；401 时会触发的全局拦截器会调用 logout */
  async function refreshProfile() {
    if (!token.value) return false
    try {
      const res = await getMe()
      const data = res.data || {}
      if (typeof data.is_admin === 'boolean') isAdminFromBackend.value = data.is_admin
      // 后端现在返回 username / avatar，同步到本地（纠正 localStorage 中可能过期的值）
      if (data.username) {
        username.value = data.username
        localStorage.setItem(LS.username, data.username)
      }
      if (data.avatar !== undefined) {
        avatar.value = data.avatar || ''
        localStorage.setItem(LS.avatar, data.avatar || '')
      }
      return data
    } catch (error) {
      if (error.response?.status === 401) {
        // token 已失效（账号被管理员删除或登录已过期）
        try {
          const { ElMessage } = await import('element-plus')
          ElMessage.warning('您的账号已被管理员删除或登录已过期，已回退为游客状态')
        } catch (_) {
          /* ignore */
        }
        logout()
      } else {
        console.error('刷新用户信息失败', error)
      }
      return false
    }
  }

  /** 修改昵称 / 同步个人配置到后端（同一接口） */
  async function updateUser(payload) {
    await apiUpdateUser(payload)
    if (payload.new_username) {
      username.value = payload.new_username
      localStorage.setItem(LS.username, payload.new_username)
    }
  }

  /** 上传新头像 */
  async function uploadAvatar(file) {
    const res = await apiUploadAvatar(file)
    avatar.value = res.data.avatar
    localStorage.setItem(LS.avatar, res.data.avatar)
    return res.data.avatar
  }

  return {
    // state
    token,
    username,
    avatar,
    isAdminFromBackend,
    // getters
    isLoggedIn,
    isAdmin,
    // actions
    login,
    applyLoginResponse,
    logout,
    refreshProfile,
    updateUser,
    uploadAvatar,
    // 暴露常量给组件使用
    LS
  }
})

// 注册 401 自动登出处理器（避免在 request.js 中引入 store 导致循环依赖）
setUnauthorizedHandler(() => {
  try {
    useUserStore().logout()
  } catch (_) {
    /* pinia 尚未安装时忽略 */
  }
})
