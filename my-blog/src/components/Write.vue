<script setup>
import { ref, reactive } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'

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

// 按钮操作
const handleImport = () => {
  console.log('点击了导入')
  // 这里可以接入读取 .md 文件的逻辑
}
const handlePreview = () => {
  console.log('点击了预览')
}
const handlePublish = () => {
  console.log('点击了发布', article)
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
</style>