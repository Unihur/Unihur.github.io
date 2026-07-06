<script setup>
// 访客管理页（管理员）：
// - 右上角两个 tab 切换：访客管理 / 文章审核
// - 访客管理：审核新账号、删除用户、编辑称号、设置写作权限
// - 文章审核：预览待审核文章、通过/拒绝发布
import { ref, computed, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UserFilled, Edit, Document } from '@element-plus/icons-vue'

import {
  listVisitors,
  approveVisitor,
  deleteVisitor,
  setVisitorTitle,
  setVisitorCanWrite
} from '@/api/visitor'
import { listPendingArticles, publishArticle, rejectArticle } from '@/api/article'
import { md } from '@/utils/markdown'

const router = useRouter()
const ADMIN_USERNAME = import.meta.env.VITE_ADMIN_USERNAME || ''

// ===== 当前 tab =====
const activeTab = ref('visitors')

// ===== 访客管理数据 =====
const visitors = ref([])
const loading = ref(false)

const pendingUsers = computed(() => visitors.value.filter((u) => !u.is_approved))
const approvedUsers = computed(() => visitors.value.filter((u) => u.is_approved))

const fetchVisitors = async () => {
  loading.value = true
  try {
    const res = await listVisitors()
    visitors.value = res.data
  } catch (e) {
    ElMessage.error('权限不足或加载失败')
    router.push('/')
  } finally {
    loading.value = false
  }
}

const approveVisitorHandler = async (id) => {
  try {
    await approveVisitor(id)
    ElMessage.success('审核已通过')
    fetchVisitors()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const deleteVisitorHandler = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除该账号吗？该用户的头像文件也会被物理删除！', '警告', {
      type: 'warning'
    })
    await deleteVisitor(id)
    ElMessage.success('账号已彻底删除')
    fetchVisitors()
  } catch (_) {
    /* 用户取消 */
  }
}

// ===== 写作权限切换 =====
const toggleCanWrite = async (user) => {
  try {
    await setVisitorCanWrite(user.id, !user.can_write)
    ElMessage.success(user.can_write ? '已收回写作权限' : '已授予写作权限')
    fetchVisitors()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

// ===== 称号编辑弹窗 =====
const titleDialogVisible = ref(false)
const editingUser = reactive({ id: null, username: '', title: '', titleColor: '' })

const colorPresets = [
  { label: '红色', color: '#f56c6c' },
  { label: '蓝色', color: '#409eff' },
  { label: '绿色', color: '#67c23a' },
  { label: '紫色', color: '#8e44ad' },
  { label: '橙色', color: '#e6a23c' },
  { label: '粉色', color: '#ff79c6' },
  { label: '青色', color: '#00aeec' },
  { label: '金色', color: '#daa520' }
]

const openTitleDialog = (user) => {
  editingUser.id = user.id
  editingUser.username = user.username
  editingUser.title = user.title || ''
  editingUser.titleColor = user.title_color || '#f56c6c'
  titleDialogVisible.value = true
}

const saveTitle = async () => {
  try {
    await setVisitorTitle(editingUser.id, editingUser.title, editingUser.titleColor)
    ElMessage.success('称号设置成功')
    titleDialogVisible.value = false
    fetchVisitors()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '设置失败')
  }
}

// ===== 文章审核数据 =====
const pendingArticles = ref([])
const articleLoading = ref(false)
const previewVisible = ref(false)
const previewArticle = ref(null)
const previewHtml = ref('')

const fetchPendingArticles = async () => {
  articleLoading.value = true
  try {
    const res = await listPendingArticles()
    pendingArticles.value = res.data
  } catch (e) {
    ElMessage.error('加载待审核文章失败')
  } finally {
    articleLoading.value = false
  }
}

const openPreview = (article) => {
  previewArticle.value = article
  previewHtml.value = md.render(article.content || '*无内容*')
  previewVisible.value = true
}

const publishHandler = async (article) => {
  try {
    await ElMessageBox.confirm(`确定通过审核并发布文章「${article.title}」吗？`, '审核确认', {
      type: 'success'
    })
    await publishArticle(article.id)
    ElMessage.success('文章已审核通过并发布')
    fetchPendingArticles()
  } catch (_) {
    /* 用户取消 */
  }
}

const rejectHandler = async (article) => {
  try {
    await ElMessageBox.confirm(`确定拒绝文章「${article.title}」吗？文章将被删除。`, '拒绝确认', {
      type: 'warning'
    })
    await rejectArticle(article.id)
    ElMessage.success('文章已被拒绝并删除')
    fetchPendingArticles()
  } catch (_) {
    /* 用户取消 */
  }
}

// 预览弹窗内的通过/拒绝按钮：先关闭弹窗再执行审核
const previewPublish = async () => {
  if (!previewArticle.value) return
  const article = previewArticle.value
  previewVisible.value = false
  await publishHandler(article)
}
const previewReject = async () => {
  if (!previewArticle.value) return
  const article = previewArticle.value
  previewVisible.value = false
  await rejectHandler(article)
}

// ===== tab 切换时加载对应数据 =====
function switchTab(tab) {
  activeTab.value = tab
  if (tab === 'visitors' && visitors.value.length === 0) fetchVisitors()
  if (tab === 'articles' && pendingArticles.value.length === 0) fetchPendingArticles()
}

onMounted(() => {
  fetchVisitors()
})
</script>

<template>
  <div class="main-content-wrapper" style="padding-top: 100px; min-height: 100vh">
    <div class="glass-box">
      <!-- 右上角 tab 切换 -->
      <div class="tab-header">
        <div class="tab-buttons">
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'visitors' }"
            @click="switchTab('visitors')"
          >
            <el-icon><UserFilled /></el-icon> 访客管理
          </button>
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'articles' }"
            @click="switchTab('articles')"
          >
            <el-icon><Document /></el-icon> 文章审核
            <el-tag
              v-if="pendingArticles.length > 0"
              type="danger"
              size="small"
              style="margin-left: 6px"
            >
              {{ pendingArticles.length }}
            </el-tag>
          </button>
        </div>
      </div>

      <!-- ===== 访客管理 tab ===== -->
      <div v-show="activeTab === 'visitors'">
        <h2>
          新账号审核区
          <el-tag type="danger" size="small">{{ pendingUsers.length }} 待办</el-tag>
        </h2>
        <el-table v-loading="loading" :data="pendingUsers" style="width: 100%; margin-bottom: 40px">
          <el-table-column label="头像" width="100">
            <template #default="scope">
              <el-avatar :src="scope.row.avatar || ''" :icon="scope.row.avatar ? '' : UserFilled" />
            </template>
          </el-table-column>
          <el-table-column prop="username" label="昵称" />
          <el-table-column label="操作" width="200" align="center">
            <template #default="scope">
              <el-button type="success" size="small" @click="approveVisitorHandler(scope.row.id)">
                通过
              </el-button>
              <el-button type="danger" size="small" @click="deleteVisitorHandler(scope.row.id)">
                拒绝并删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <h2>已通过账号管理</h2>
        <el-table v-loading="loading" :data="approvedUsers" style="width: 100%">
          <el-table-column label="头像" width="100">
            <template #default="scope">
              <el-avatar :src="scope.row.avatar || ''" :icon="scope.row.avatar ? '' : UserFilled" />
            </template>
          </el-table-column>
          <el-table-column prop="username" label="昵称">
            <template #default="scope">
              <span>{{ scope.row.username }}</span>
              <el-tag
                v-if="scope.row.username === ADMIN_USERNAME"
                size="small"
                type="danger"
                effect="plain"
                style="margin-left: 6px"
              >
                管理员
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="称号" width="180">
            <template #default="scope">
              <span v-if="scope.row.username === ADMIN_USERNAME" class="admin-title-badge">
                管理员
              </span>
              <span
                v-else-if="scope.row.title"
                class="user-title-badge"
                :style="{
                  color: scope.row.title_color || '#f56c6c',
                  borderColor: scope.row.title_color || '#f56c6c'
                }"
              >
                {{ scope.row.title }}
              </span>
              <span v-else style="color: #ccc; font-size: 0.85rem">未设置</span>
            </template>
          </el-table-column>
          <el-table-column label="写作权限" width="120" align="center">
            <template #default="scope">
              <!-- 管理员恒为可写，不可修改 -->
              <el-tag v-if="scope.row.username === ADMIN_USERNAME" type="success" size="small">
                内置权限
              </el-tag>
              <el-switch
                v-else
                :model-value="scope.row.can_write"
                @change="toggleCanWrite(scope.row)"
              />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="220" align="center">
            <template #default="scope">
              <template v-if="scope.row.username !== ADMIN_USERNAME">
                <el-button size="small" @click="openTitleDialog(scope.row)">
                  <el-icon><Edit /></el-icon> 编辑称号
                </el-button>
                <el-button type="danger" size="small" @click="deleteVisitorHandler(scope.row.id)">
                  删除用户
                </el-button>
              </template>
              <span v-else style="color: #ccc; font-size: 0.85rem">—</span>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- ===== 文章审核 tab ===== -->
      <div v-show="activeTab === 'articles'">
        <h2>待审核文章</h2>
        <el-table v-loading="articleLoading" :data="pendingArticles" style="width: 100%">
          <el-table-column prop="title" label="标题" min-width="200" />
          <el-table-column prop="author_name" label="作者" width="150" />
          <el-table-column prop="category" label="分类" width="120" />
          <el-table-column label="提交时间" width="180">
            <template #default="scope">
              {{ new Date(scope.row.created_at).toLocaleString() }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" align="center">
            <template #default="scope">
              <el-button size="small" @click="openPreview(scope.row)">预览</el-button>
              <el-button type="success" size="small" @click="publishHandler(scope.row)">
                通过
              </el-button>
              <el-button type="danger" size="small" @click="rejectHandler(scope.row)">
                拒绝
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <div
          v-if="!articleLoading && pendingArticles.length === 0"
          style="text-align: center; padding: 40px; color: #999"
        >
          暂无待审核文章
        </div>
      </div>
    </div>

    <!-- 称号编辑弹窗 -->
    <el-dialog v-model="titleDialogVisible" title="编辑用户称号" width="420px">
      <div style="margin-bottom: 15px">
        <span style="color: #888; font-size: 0.9rem">用户：{{ editingUser.username }}</span>
      </div>

      <div class="title-form-item">
        <div class="title-label">称号文字</div>
        <el-input
          v-model="editingUser.title"
          placeholder="输入称号（如：老朋友、VIP、大佬）"
          maxlength="20"
          show-word-limit
          clearable
        />
      </div>

      <div class="title-form-item">
        <div class="title-label">称号颜色</div>
        <div class="color-preset-row">
          <div
            v-for="preset in colorPresets"
            :key="preset.color"
            class="color-preset-dot"
            :class="{ 'is-selected': editingUser.titleColor === preset.color }"
            :style="{ background: preset.color }"
            :title="preset.label"
            @click="editingUser.titleColor = preset.color"
          ></div>
        </div>
      </div>

      <div class="title-preview">
        <span style="color: #888; font-size: 0.85rem; margin-right: 8px">预览：</span>
        <span
          v-if="editingUser.title"
          class="user-title-badge"
          :style="{
            color: editingUser.titleColor,
            borderColor: editingUser.titleColor
          }"
        >
          {{ editingUser.title }}
        </span>
        <span v-else style="color: #ccc">（输入称号后可见预览）</span>
      </div>

      <template #footer>
        <el-button @click="titleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveTitle">保存</el-button>
      </template>
    </el-dialog>

    <!-- 文章预览弹窗 -->
    <el-dialog
      v-model="previewVisible"
      :title="previewArticle ? previewArticle.title : '预览'"
      width="70%"
      top="5vh"
    >
      <div v-if="previewArticle" style="margin-bottom: 15px; color: #888; font-size: 0.9rem">
        作者：{{ previewArticle.author_name }} ｜ 分类：{{ previewArticle.category || '无' }} ｜
        提交时间：{{ new Date(previewArticle.created_at).toLocaleString() }}
      </div>
      <div class="markdown-body preview-markdown" v-html="previewHtml"></div>
      <template #footer>
        <el-button @click="previewVisible = false">关闭</el-button>
        <el-button v-if="previewArticle" type="danger" @click="previewReject">
          拒绝并删除
        </el-button>
        <el-button v-if="previewArticle" type="success" @click="previewPublish">
          通过并发布
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
/* tab 切换 */
.tab-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 25px;
}
.tab-buttons {
  display: flex;
  gap: 10px;
}
.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: bold;
  color: #666;
  transition: all 0.3s;
}
.tab-btn:hover {
  border-color: #409eff;
  color: #409eff;
}
.tab-btn.active {
  background: #409eff;
  border-color: #409eff;
  color: #fff;
}
html.dark .tab-btn {
  border-color: rgba(255, 255, 255, 0.15);
  color: #ccc;
}
html.dark .tab-btn.active {
  background: #409eff;
  color: #fff;
}

.user-title-badge {
  display: inline-block;
  padding: 1px 8px;
  border: 1px solid;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}
.admin-title-badge {
  display: inline-block;
  padding: 1px 8px;
  border: 1px solid #f56c6c;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
  color: #f56c6c;
}

.title-form-item {
  margin-bottom: 20px;
}
.title-label {
  font-weight: bold;
  margin-bottom: 8px;
  font-size: 0.9rem;
}

.color-preset-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.color-preset-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  cursor: pointer;
  border: 3px solid transparent;
  transition: all 0.2s;
}
.color-preset-dot:hover {
  transform: scale(1.15);
}
.color-preset-dot.is-selected {
  border-color: #333;
  transform: scale(1.15);
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.8);
}
html.dark .color-preset-dot.is-selected {
  border-color: #fff;
  box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.5);
}

.title-preview {
  display: flex;
  align-items: center;
  padding: 12px;
  background: rgba(0, 0, 0, 0.03);
  border-radius: 8px;
}
html.dark .title-preview {
  background: rgba(255, 255, 255, 0.05);
}

/* 文章预览 */
.preview-markdown {
  max-height: 60vh;
  overflow-y: auto;
  padding: 20px;
  font-size: 15px;
  line-height: 1.8;
  color: #333;
}
html.dark .preview-markdown {
  color: #ddd;
}
.preview-markdown :deep(pre) {
  background: #f6f8fa;
  padding: 15px;
  border-radius: 8px;
  overflow: auto;
}
html.dark .preview-markdown :deep(pre) {
  background: #2d2d2d;
}
.preview-markdown :deep(img) {
  max-width: 100%;
  border-radius: 8px;
  margin: 10px 0;
}
.preview-markdown :deep(blockquote) {
  border-left: 4px solid #409eff;
  margin: 0;
  padding: 10px 15px;
  color: #666;
  background: rgba(64, 158, 255, 0.05);
  border-radius: 0 4px 4px 0;
}
</style>
