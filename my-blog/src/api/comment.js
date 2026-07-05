// 评论及其互动接口
import request from './request'

/** 拉取指定文章的评论列表（携带 token 以判定当前用户点赞状态） */
export function listComments(slug) {
  return request.get(`/comments/${slug}`)
}

/** 发布评论 / 回复评论（parentId 为 null 表示根评论） */
export function createComment(payload) {
  // payload: { article_slug, author, content, parent_id, reply_to? }
  return request.post('/comments', payload)
}

/** 删除评论 */
export function deleteComment(id) {
  return request.delete(`/comments/${id}`)
}

/** 置顶 / 取消置顶评论（管理员） */
export function pinComment(id) {
  return request.post(`/comments/${id}/pin`, {})
}

/** 点赞 / 点踩评论（互斥） */
export function commentAction(id, action) {
  return request.post(`/comments/${id}/action`, { action })
}
