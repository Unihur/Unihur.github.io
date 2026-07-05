// 管理员：访客管理接口
import request from './request'

/** 获取所有访客（待审核 + 已通过） */
export function listVisitors() {
  return request.get('/admin/visitors')
}

/** 审核通过 */
export function approveVisitor(id) {
  return request.put(`/admin/visitors/${id}/approve`, {})
}

/** 删除访客账号 */
export function deleteVisitor(id) {
  return request.delete(`/admin/visitors/${id}`)
}

/** 设置用户自定义称号 + 颜色 */
export function setVisitorTitle(id, title, titleColor) {
  return request.put(`/admin/visitors/${id}/title`, {
    title: title || '',
    title_color: titleColor || ''
  })
}
