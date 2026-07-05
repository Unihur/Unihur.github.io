// 文章分类接口（管理员具有写权限）
import request from './request'

/** 获取所有分类（附带 count） */
export function listCategories() {
  return request.get('/categories')
}

/** 新建分类 */
export function createCategory(name) {
  return request.post('/categories', { name })
}

/** 重命名分类 */
export function renameCategory(oldName, newName) {
  return request.put(`/categories/${oldName}`, { name: newName })
}

/** 删除分类 */
export function deleteCategory(name) {
  return request.delete(`/categories/${name}`)
}
