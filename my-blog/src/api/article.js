// 文章 CRUD + 互动接口
import request from './request'

/** 列表（主页用） */
export function listArticles() {
  return request.get('/articles')
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
