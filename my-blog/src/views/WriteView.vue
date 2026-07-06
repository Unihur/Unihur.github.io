<script setup>
// 写作 / 编辑文章页（管理员或被授权用户）
// - 新建：调用 POST /articles（管理员直接发布，普通用户待审核）
// - 编辑：根据 query.slug 读取后端数据回填，调用 PUT /articles/:slug
// - 删除：DELETE /articles/:slug
// - 支持 .md 文件导入、Markdown 预览、封面上传 / 从历史图库选择
import { ref, reactive, onMounted } from 'vue'
import { UploadFilled, Close, Picture } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'

import { md } from '@/utils/markdown'
import { useUserStore } from '@/stores/user'

import { getArticle, createArticle, updateArticle, deleteArticle } from '@/api/article'
import { listCategories } from '@/api/category'
import { uploadImage, listImages, deleteImage } from '@/api/upload'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const isEditMode = ref(false)
const originalSlug = ref('')

// ===== 表单数据 =====
const article = reactive({
  title: '',
  slug: '',
  content: '',
  intro: '',
  author_name: '', // 作者显示名，默认填充当前登录用户名
  tags: [],
  category: '',
  publishTime: new Date(),
  isHidden: false,
  isPinned: false,
  cover: ''
})

// ===== 编辑模式：拉取原文章 =====
onMounted(async () => {
  fetchCategoryOptions()

  const querySlug = route.query.slug
  if (querySlug) {
    isEditMode.value = true
    originalSlug.value = querySlug
    try {
      const res = await getArticle(querySlug)
      const data = res.data.article || res.data // 兼容新旧格式
      article.title = data.title
      article.slug = data.slug
      article.content = data.content
      article.intro = data.intro || ''
      article.tags = data.tags || []
      article.category = data.category || ''
      article.cover = data.cover || ''
      article.isHidden = data.isHidden || false
      article.isPinned = data.isPinned || false
      article.author_name = data.author_name || userStore.username || ''
    } catch (error) {
      ElMessage.error('读取旧文章数据失败！')
    }
  } else {
    // 新建模式：默认填入当前登录用户名作为作者
    article.author_name = userStore.username || ''
  }
})

// ===== 标签 =====
const tagInput = ref('')
const handleAddTag = () => {
  const v = tagInput.value.trim()
  if (v && !article.tags.includes(v)) article.tags.push(v)
  tagInput.value = ''
}
const handleRemoveTag = (tag) => {
  article.tags = article.tags.filter((t) => t !== tag)
}

// ===== 分类 =====
const categoryOptions = ref([])
const fetchCategoryOptions = async () => {
  try {
    const res = await listCategories()
    categoryOptions.value = res.data.map((cat) => ({ value: cat.name, label: cat.name }))
  } catch (error) {
    console.error('获取分类失败', error)
  }
}

// ===== 预览 / 导入 =====
const showPreview = ref(false)
const renderedHtml = ref('')
const fileInput = ref(null)

const handleImport = () => {
  fileInput.value?.click()
}
const onFileChange = (e) => {
  const file = e.target.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (event) => {
    article.content = event.target.result
    if (!article.title) article.title = file.name.replace(/\.md$/i, '')
    ElMessage.success('导入 .md 文件成功！')
  }
  reader.readAsText(file)
  e.target.value = ''
}
const handlePreview = () => {
  renderedHtml.value = md.render(article.content || '*(暂无内容)*')
  showPreview.value = true
}

// ===== 删除 =====
const handleDelete = async () => {
  try {
    await ElMessageBox.confirm('确定要永久删除这篇文章吗？操作不可恢复！', '警告', {
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    const res = await deleteArticle(originalSlug.value)
    if (res.data.status === 'success') {
      ElMessage.success('🗑️ 文章已成功删除！')
      setTimeout(() => router.push('/'), 1000)
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败，权限不足或登录已过期')
    }
  }
}

// ===== 封面上传 / 图库 =====
const showGallery = ref(false)
const galleryImages = ref([])

const handleCoverUpload = async (options) => {
  try {
    const res = await uploadImage(options.file)
    if (res.data.status === 'success') {
      article.cover = res.data.url
      ElMessage.success('封面上传成功！')
    }
  } catch (error) {
    ElMessage.error('上传图片失败')
  }
}

const openGallery = async () => {
  try {
    const res = await listImages()
    galleryImages.value = res.data
    showGallery.value = true
  } catch (error) {
    ElMessage.error('获取图库失败')
  }
}

const selectCoverFromGallery = (url) => {
  article.cover = url
  showGallery.value = false
  ElMessage.success('已选择该图片作为封面！')
}

const deleteGalleryImage = async (url) => {
  try {
    await ElMessageBox.confirm('确定要从服务器彻底删除这张图片吗？', '删除确认', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消'
    })
    const filename = url.split('/').pop()
    const res = await deleteImage(filename)
    if (res.data.status === 'success') {
      ElMessage.success('🗑️ 图片已删除')
      galleryImages.value = galleryImages.value.filter((img) => img !== url)
      if (article.cover === url) article.cover = ''
    }
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('删除失败，可能没有权限或图片已不存在')
  }
}

// ===== 发布 / 更新 =====
const handlePublish = async () => {
  if (!article.title || !article.slug) {
    ElMessage.error('文章标题和 Slug 别名不能为空！')
    return
  }
  try {
    let pubRes
    if (isEditMode.value) {
      pubRes = await updateArticle(originalSlug.value, article)
    } else {
      pubRes = await createArticle(article)
    }
    if (pubRes.data.status === 'success') {
      // 管理员直接发布；普通用户待审核，给不同提示
      const isPublished = pubRes.data.is_published
      if (isEditMode.value) {
        ElMessage.success(isPublished ? '🎉 文章更新成功！' : '✅ 文章已更新，等待管理员审核！')
      } else {
        ElMessage.success(isPublished ? '🎉 文章发布成功！' : '✅ 文章已提交，等待管理员审核！')
      }
      if (isEditMode.value) originalSlug.value = article.slug
      setTimeout(() => {
        // 待审核的文章不能直接跳详情页（详情页只显示已发布的），跳回首页
        router.push(isPublished && isEditMode.value ? `/post/${article.slug}` : '/')
      }, 1200)
    }
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error(error.response?.data?.detail || '网络请求失败或权限不足')
  }
}
</script>

<template>
  <div class="write-container">
    <!-- 顶部操作按钮 -->
    <div class="action-bar">
      <el-button v-if="isEditMode" type="danger" style="margin-right: auto" @click="handleDelete"
        >删除</el-button
      >
      <el-button @click="handleImport">导入</el-button>
      <input
        ref="fileInput"
        type="file"
        accept=".md, .markdown, text/markdown"
        style="display: none"
        @change="onFileChange"
      />
      <el-button @click="handlePreview">预览</el-button>
      <el-button type="primary" @click="handlePublish">{{
        isEditMode ? '更新' : '发布'
      }}</el-button>
    </div>

    <!-- 主体编辑区 -->
    <div class="editor-layout">
      <!-- 左侧：Markdown 编辑区 -->
      <div class="left-panel glass-box">
        <div class="title-row">
          <el-input v-model="article.title" placeholder="标题" size="large" class="title-input" />
          <el-input
            v-model="article.slug"
            placeholder="slug (URL别名)"
            size="large"
            class="slug-input"
          />
        </div>
        <el-input
          v-model="article.content"
          type="textarea"
          placeholder="在此输入 Markdown 内容..."
          :rows="30"
          resize="none"
          class="markdown-input"
        />
      </div>

      <!-- 右侧：属性设置区 -->
      <div class="right-panel">
        <div class="glass-box panel-section cover-section">
          <div v-if="article.cover" style="text-align: center; margin-bottom: 10px">
            <img
              :src="article.cover"
              style="
                width: 100%;
                border-radius: 8px;
                margin-bottom: 10px;
                object-fit: cover;
                max-height: 180px;
              "
            />
            <el-button type="danger" size="small" @click="article.cover = ''">移除封面</el-button>
          </div>
          <el-upload
            v-else
            class="cover-uploader"
            drag
            action="#"
            :http-request="handleCoverUpload"
            :show-file-list="false"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">拖拽图片到此处，或 <em>点击上传</em></div>
          </el-upload>
          <div style="text-align: center; margin-top: 15px">
            <el-button type="primary" plain style="width: 100%" @click="openGallery">
              <el-icon style="margin-right: 5px"><Picture /></el-icon> 从历史图库中选择
            </el-button>
          </div>
        </div>

        <div class="glass-box panel-section settings-section">
          <div class="setting-item">
            <div class="label">作者</div>
            <el-input v-model="article.author_name" placeholder="输入作者名字" clearable />
          </div>

          <div class="setting-item">
            <div class="label">简介</div>
            <el-input
              v-model="article.intro"
              type="textarea"
              :rows="3"
              placeholder="输入文章简介"
            />
          </div>

          <div class="setting-item">
            <div class="label">添加标签</div>
            <el-input
              v-model="tagInput"
              placeholder="输入标签后按回车"
              @keyup.enter="handleAddTag"
            />
            <div v-if="article.tags.length > 0" class="tags-container">
              <el-tag
                v-for="tag in article.tags"
                :key="tag"
                closable
                class="article-tag"
                @close="handleRemoveTag(tag)"
              >
                {{ tag }}
              </el-tag>
            </div>
          </div>

          <div class="setting-item">
            <div class="label">分类</div>
            <el-select
              v-model="article.category"
              filterable
              allow-create
              default-first-option
              placeholder="选择或新建分类"
              style="width: 100%"
            >
              <el-option
                v-for="item in categoryOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </div>

          <div class="setting-item">
            <div class="label">时间设置</div>
            <el-date-picker
              v-model="article.publishTime"
              type="datetime"
              placeholder="选择发布时间"
              style="width: 100%"
            />
          </div>

          <div class="setting-item toggle-row">
            <span>隐藏 (设为草稿)</span>
            <el-switch v-model="article.isHidden" />
          </div>
          <div class="setting-item toggle-row">
            <span>置顶文章</span>
            <el-switch v-model="article.isPinned" />
          </div>
        </div>
      </div>
    </div>

    <!-- 预览抽屉 -->
    <el-drawer v-model="showPreview" title="文章预览" direction="rtl" size="50%">
      <div class="markdown-body" v-html="renderedHtml"></div>
    </el-drawer>

    <!-- 图库选择弹窗 -->
    <el-dialog v-model="showGallery" title="选择历史封面" width="50%">
      <div v-if="galleryImages.length === 0" style="text-align: center; color: #999">
        暂无历史图片
      </div>
      <el-row v-else :gutter="10">
        <el-col v-for="url in galleryImages" :key="url" :span="6" style="margin-bottom: 10px">
          <div
            style="
              position: relative;
              border-radius: 6px;
              overflow: hidden;
              cursor: pointer;
              border: 2px solid transparent;
              transition: border-color 0.3s;
            "
            :style="article.cover === url ? 'border-color: #409eff;' : ''"
            @click="selectCoverFromGallery(url)"
          >
            <img :src="url" style="width: 100%; height: 100px; object-fit: cover; display: block" />
            <div class="delete-img-btn" @click.stop="deleteGalleryImage(url)">
              <el-icon><Close /></el-icon>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-dialog>
  </div>
</template>

<style scoped>
.write-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 100px 20px 40px;
}

.action-bar {
  display: flex;
  justify-content: flex-end;
  gap: 15px;
  margin-bottom: 20px;
}

.editor-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.left-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
  min-height: 80vh;
}

.title-row {
  display: flex;
  gap: 20px;
}
.title-input {
  flex: 2;
}
.slug-input {
  flex: 1;
}

:deep(.markdown-input) {
  flex: 1;
}
:deep(.markdown-input .el-textarea__inner) {
  height: 100% !important;
  border: none;
  background: transparent;
  box-shadow: none;
  font-family: monospace;
  font-size: 15px;
  padding: 0;
}
:deep(.markdown-input .el-textarea__inner:focus) {
  box-shadow: none;
}

.right-panel {
  width: 300px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.panel-section {
  padding: 20px;
}

.cover-section :deep(.el-upload-dragger) {
  background: transparent;
  border-color: rgba(0, 0, 0, 0.2);
}
html.dark .cover-section :deep(.el-upload-dragger) {
  border-color: rgba(255, 255, 255, 0.2);
}

.settings-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.setting-item .label {
  font-weight: bold;
  margin-bottom: 8px;
  font-size: 0.95rem;
}

.tags-container {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.toggle-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.markdown-body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
  font-size: 16px;
  line-height: 1.6;
  color: #333;
}
html.dark .markdown-body {
  color: #ddd;
}
.markdown-body h1,
.markdown-body h2,
.markdown-body h3 {
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
  margin-top: 24px;
}
html.dark .markdown-body h1,
html.dark .markdown-body h2,
html.dark .markdown-body h3 {
  border-bottom-color: #444;
}
.markdown-body blockquote {
  padding: 0 1em;
  color: #6a737d;
  border-left: 0.25em solid #dfe2e5;
  margin: 0;
}
html.dark .markdown-body blockquote {
  color: #999;
  border-left-color: #555;
}
.markdown-body pre {
  background-color: #f6f8fa;
  border-radius: 6px;
  padding: 16px;
  overflow: auto;
}
html.dark .markdown-body pre {
  background-color: #2d2d2d;
}
.markdown-body code {
  background-color: rgba(27, 31, 35, 0.05);
  border-radius: 3px;
  padding: 0.2em 0.4em;
}
html.dark .markdown-body code {
  background-color: rgba(255, 255, 255, 0.1);
}
.markdown-body pre code {
  background-color: transparent;
  padding: 0;
}

.delete-img-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 22px;
  height: 22px;
  background-color: rgba(245, 108, 108, 0.85);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  transition:
    transform 0.2s,
    background-color 0.2s;
  z-index: 10;
}
.delete-img-btn:hover {
  background-color: #f56c6c;
  transform: scale(1.15);
}
</style>
