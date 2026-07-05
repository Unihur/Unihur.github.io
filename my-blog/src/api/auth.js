// 账号 / 用户相关接口
import request from './request'

/** 检测账号是否已注册 / 审核状态 */
export function checkUserStatus(username) {
  return request.get('/user/status', { params: { username } })
}

/** 登录（成功后端会返回 token、username、avatar、config 等） */
export function login(payload) {
  // payload: { username, password }
  return request.post('/login', payload)
}

/** 获取当前登录用户信息 + 绑定的配置 */
export function getMe() {
  return request.get('/user/me')
}

/** 上传新头像（multipart） */
export function uploadAvatar(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/user/avatar', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

/** 更新昵称 / 同步用户配置（同一个后端接口） */
export function updateUser(payload) {
  return request.post('/user/update', payload)
}
