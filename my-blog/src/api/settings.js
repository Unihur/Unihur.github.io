// 全站公开设置 + 访客统计接口
// 这些都不需要登录鉴权
import axios from 'axios'

// 注意：历史上这两个接口使用绝对路径 https://unihur.xyz/api，这里改为通过相对 /api 走
// 统一 vite 代理 / 生产构建时由 env 注入的实际 baseURL
const PUBLIC_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

/** 读取全站公开设置（banner_mode / is_dark 等） */
export async function getPublicSettings() {
  // 注意：这里用原生 axios（避免触发 request 拦截器的 token 注入，无伤大雅但更纯粹）
  const res = await axios.get(`${PUBLIC_BASE}/settings`)
  return res.data
}

/** 保存全站公开设置（管理员身份由后端判断） */
export async function savePublicSettings(payload) {
  // payload: { banner_mode, is_dark }
  await axios.post(`${PUBLIC_BASE}/settings`, payload, {
    headers: { 'Content-Type': 'application/json' }
  })
}

/** 老访客查询当前访客数 */
export async function getSiteVisitorCount() {
  const res = await axios.get(`${PUBLIC_BASE}/site/visitor-count`)
  return res.data // { visitor_count }
}

/** 新设备首次访问自增 */
export async function incrementSiteVisitorCount() {
  const res = await axios.post(`${PUBLIC_BASE}/site/visitor-count/increment`)
  return res.data
}
