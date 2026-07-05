// 全局 axios 实例：
// - 统一 baseURL（来自 VITE_API_BASE_URL）
// - 请求拦截器：自动注入本地 token，保留兼容性同时使用 Authorization + token 两种头
// - 响应拦截器：统一错误处理（401 自动登出、422/403 提示等）
import axios from 'axios'
import { ElMessage } from 'element-plus'

export const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 20000
})

// 请求拦截：注入鉴权头
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      // 同时携带 token 和 Authorization，兼容后端不同中间件
      config.headers.token = token
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截：统一错误处理
let unauthorizedHandler = null
// 允许在应用启动时注册一个 401 处理回调（用于触发 user store 退出登录）
export function setUnauthorizedHandler(fn) {
  unauthorizedHandler = fn
}

request.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail

    if (status === 401) {
      // token 失效：交给应用层的处理器统一处理（避免循环依赖）
      if (typeof unauthorizedHandler === 'function') unauthorizedHandler(error)
    } else if (status === 403) {
      // 权限相关错误在调用方一般会自行处理，这里只兜底
      ElMessage.warning(detail || '权限不足')
    }

    return Promise.reject(error)
  }
)

export default request
