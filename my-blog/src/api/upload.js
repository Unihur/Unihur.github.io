// 图片上传 / 图库管理接口（管理员）
import request from './request'

/** 上传一张图片（用作文章封面等） */
export function uploadImage(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/upload/image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

/** 获取已上传的所有图片 */
export function listImages() {
  return request.get('/images')
}

/** 删除一张图片（filename 是 url 末尾文件名） */
export function deleteImage(filename) {
  return request.delete(`/images/${filename}`)
}
