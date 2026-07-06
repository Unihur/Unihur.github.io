// 文章 CRUD + 互动接口
import request from './request'

/** 列表（主页用）；后端默认 limit=10，这里传一个足够大的值避免截断 */
export function listArticles() {
  return request.get('/articles', { params: { limit: 1000 } })
}

/** 单篇详情；兼容新旧两版返回结构（{ article, prev, next } 或直接数据） */
export function getArticle(slug) {
  return request.get(`/articles/${slug}`)
}

/** 新建文章 */
export function createArticle(payload) {
  return request.post('/articles', payload)
}

/** 更新文章 */
export function updateArticle(originalSlug, payload) {
  return request.put(`/articles/${originalSlug}`, payload)
}

/** 删除文章 */
export function deleteArticle(slug) {
  return request.delete(`/articles/${slug}`)
}

/** 点赞 */
export function likeArticle(slug) {
  return request.post(`/articles/${slug}/like`)
}

/** 分享 / 转发 */
export function shareArticle(slug) {
  return request.post(`/articles/${slug}/share`)
}

// ===== 文章审核（管理员）=====

/** 获取待审核文章列表 */
export function listPendingArticles() {
  return request.get('/admin/pending-articles')
}

/** 审核通过：发布文章 */
export function publishArticle(articleId) {
  return request.put(`/admin/articles/${articleId}/publish`, {})
}

/** 审核拒绝：删除文章 */
export function rejectArticle(articleId) {
  return request.delete(`/admin/articles/${articleId}`)
}
