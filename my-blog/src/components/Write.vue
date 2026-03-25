<script setup>
import { ref, reactive, onMounted } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'

import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const isEditMode = ref(false)   // 标记当前是新建还是编辑
const originalSlug = ref('')    // 保存旧的 slug（修改文章时用）

// 页面一加载，看有没有传 slug 过来，有的话就是编辑模式，去后端要数据
onMounted(async () => {
  const querySlug = route.query.slug
  if (querySlug) {
    isEditMode.value = true
    originalSlug.value = querySlug
    
    try {
      // 这里的接口是之前你写好的获取单篇文章接口
      const res = await axios.get(`http://127.0.0.1:8000/api/articles/${querySlug}`)
      const data = res.data.article || res.data // 兼容格式
      
      // 把后端拿到的数据塞进表单里
      article.title = data.title
      article.slug = data.slug
      article.content = data.content
      article.intro = data.intro || ''
      article.tags = data.tags || []
      article.category = data.category || ''
      article.cover = data.cover || ''
      article.isHidden = data.isHidden || false
      article.isPinned = data.isPinned || false
      // 注意日期格式可能需要稍微处理，简单起见直接用后端的也可以
    } catch (error) {
      ElMessage.error('读取旧文章数据失败！')
    }
  }
})

// 配置 markdown-it
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  // 加上代码高亮功能
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, { language: lang }).value
      } catch (__) {}
    }
    return '' // 使用额外的默认转义
  }
})

// 表单数据
const article = reactive({
  title: '',
  slug: '',
  content: '',
  intro: '',
  tags: [],
  category: '',
  publishTime: new Date(), // 默认系统当前时间
  isHidden: false,
  isPinned: false,
  cover: ''
})

// 标签相关
const tagInput = ref('')
const handleAddTag = () => {
  if (tagInput.value.trim() && !article.tags.includes(tagInput.value.trim())) {
    article.tags.push(tagInput.value.trim())
  }
  tagInput.value = ''
}
const handleRemoveTag = (tag) => {
  article.tags = article.tags.filter(t => t !== tag)
}

// 分类选项（支持动态添加）
const categoryOptions = ref([
  { value: '前端开发', label: '前端开发' },
  { value: '生活日记', label: '生活日记' }
])

const showPreview = ref(false)
const renderedHtml = ref('')

// 按钮操作
const handleImport = () => {
  console.log('点击了导入')
  // 这里可以接入读取 .md 文件的逻辑
}
const handlePreview = () => {
  renderedHtml.value = md.render(article.content || '*(暂无内容)*')
  showPreview.value = true
}

const handlePublish = async () => {
  if (!article.title || !article.slug) {
    ElMessage.error('文章标题和Slug别名不能为空！')
    return
  }
  
  try {
    let response;
    
    // 如果是编辑模式，发送 PUT 请求给刚才后端写的更新接口
    if (isEditMode.value) {
      response = await axios.put(`http://127.0.0.1:8000/api/articles/${originalSlug.value}`, article)
    } else {
      // 如果是新建文章，发送 POST 请求
      response = await axios.post('http://127.0.0.1:8000/api/articles', article)
    }
    
    if (response.data.status === 'success') {
      ElMessage.success(isEditMode.value ? '🎉 文章更新成功！' : '🎉 文章发布成功！')
      
      // 如果你改了 slug，下次更新需要用新 slug，同步更新一下标记
      if (isEditMode.value) originalSlug.value = article.slug 

      setTimeout(() => {
        router.push('/')
      }, 1000)

    }
  } catch (error) {
    console.error('保存失败:', error)
    if (error.response && error.response.data && error.response.data.detail) {
      ElMessage.error(error.response.data.detail) // 报后端返回的具体错误（比如slug被占用）
    } else {
      ElMessage.error('网络请求失败，请检查后端是否启动。')
    }
  }
}

</script>

<template>
  <div class="write-container">
    <!-- 顶部操作按钮 -->
    <div class="action-bar">
      <el-button @click="handleImport">导入</el-button>
      <el-button @click="handlePreview">预览</el-button>
      <el-button type="primary" @click="handlePublish">发布</el-button>
    </div>

    <!-- 主体编辑区 -->
    <div class="editor-layout">
      <!-- 左侧：Markdown 编辑区 -->
      <div class="left-panel glass-box">
        <div class="title-row">
          <el-input v-model="article.title" placeholder="标题" size="large" class="title-input" />
          <el-input v-model="article.slug" placeholder="slug (URL别名)" size="large" class="slug-input" />
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
        <!-- 导入封面 -->
        <div class="glass-box panel-section cover-section">
          <el-upload
            class="cover-uploader"
            drag
            action="#"
            :auto-upload="false"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">导入封面</div>
          </el-upload>
        </div>

        <div class="glass-box panel-section settings-section">
          <!-- 简介 -->
          <div class="setting-item">
            <div class="label">简介</div>
            <el-input v-model="article.intro" type="textarea" :rows="3" placeholder="输入文章简介" />
          </div>

          <!-- 添加标签 -->
          <div class="setting-item">
            <div class="label">添加标签</div>
            <el-input 
              v-model="tagInput" 
              placeholder="输入标签后按回车" 
              @keyup.enter="handleAddTag"
            />
            <div class="tags-container" v-if="article.tags.length > 0">
              <el-tag
                v-for="tag in article.tags"
                :key="tag"
                closable
                @close="handleRemoveTag(tag)"
                class="article-tag"
              >
                {{ tag }}
              </el-tag>
            </div>
          </div>

          <!-- 分类 -->
          <div class="setting-item">
            <div class="label">分类</div>
            <el-select
              v-model="article.category"
              filterable
              allow-create
              default-first-option
              placeholder="选择或新建分类"
              style="width: 100%;"
            >
              <el-option
                v-for="item in categoryOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </div>

          <!-- 时间设置 -->
          <div class="setting-item">
            <div class="label">时间设置</div>
            <el-date-picker
              v-model="article.publishTime"
              type="datetime"
              placeholder="选择发布时间"
              style="width: 100%;"
            />
          </div>

          <!-- 隐藏与置顶 -->
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
  
  <!-- 👇 新增：预览用的抽屉组件 -->
    <el-drawer
      v-model="showPreview"
      title="文章预览"
      direction="rtl"
      size="50%"
    >
      <!-- 给渲染出的 HTML 套一个专门的类名 markdown-body 来美化它 -->
      <div class="markdown-body" v-html="renderedHtml"></div>
    </el-drawer>
  
  </div>
</template>

<style scoped>
.write-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 100px 20px 40px; /* 顶部留出导航栏的空间 */
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
  min-height: 80vh; /* 👈 新增：保证左侧面板有足够的最低高度 */
}

.title-row {
  display: flex;
  gap: 20px;
}
.title-input { flex: 2; }
.slug-input { flex: 1; }

/* 深度修改 Markdown 输入框样式使其铺满并隐去默认边框 */
:deep(.markdown-input) {
  flex: 1; /* 👈 新增：让输入框占满剩余的高度 */
}
:deep(.markdown-input .el-textarea__inner) {
  height: 100% !important; /* 👈 新增：让内部真正的输入区占满100%高度 */
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
  border-color: rgba(0,0,0,0.2);
}
html.dark .cover-section :deep(.el-upload-dragger) {
  border-color: rgba(255,255,255,0.2);
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

/* 👇 新增：美化渲染后的 Markdown 内容 */
.markdown-body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
  font-size: 16px;
  line-height: 1.6;
  color: #333;
}
html.dark .markdown-body {
  color: #ddd;
}
.markdown-body h1, .markdown-body h2, .markdown-body h3 {
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
  margin-top: 24px;
}
html.dark .markdown-body h1, html.dark .markdown-body h2, html.dark .markdown-body h3 {
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
  background-color: rgba(27,31,35,0.05);
  border-radius: 3px;
  padding: 0.2em 0.4em;
}
html.dark .markdown-body code {
  background-color: rgba(255,255,255,0.1);
}
.markdown-body pre code {
  background-color: transparent; /* 代码块里的 code 不加背景 */
  padding: 0;
}

</style>