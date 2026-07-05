<script setup>
// 访客管理页（管理员）：列出待审核与已通过账号，支持审核、删除、设置自定义称号
import { ref, computed, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UserFilled, Edit } from '@element-plus/icons-vue'

import { listVisitors, approveVisitor, deleteVisitor, setVisitorTitle } from '@/api/visitor'

const router = useRouter()
const visitors = ref([])
const loading = ref(false)

// 管理员用户名（用于在列表中标注管理员行）
const ADMIN_USERNAME = import.meta.env.VITE_ADMIN_USERNAME || ''

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

// ===== 称号编辑弹窗 =====
const titleDialogVisible = ref(false)
const editingUser = reactive({ id: null, username: '', title: '', titleColor: '' })

// 颜色预设方案
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

onMounted(fetchVisitors)
</script>

<template>
  <div class="main-content-wrapper" style="padding-top: 100px; min-height: 100vh">
    <div class="glass-box">
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
        <el-table-column label="操作" width="200" align="right">
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
            <span
              v-if="scope.row.title"
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
        <el-table-column label="操作" width="220" align="right">
          <template #default="scope">
            <el-button size="small" @click="openTitleDialog(scope.row)">
              <el-icon><Edit /></el-icon> 编辑称号
            </el-button>
            <el-button type="danger" size="small" @click="deleteVisitorHandler(scope.row.id)">
              删除用户
            </el-button>
          </template>
        </el-table-column>
      </el-table>
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

      <!-- 预览 -->
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
  </div>
</template>

<style scoped>
.user-title-badge {
  display: inline-block;
  padding: 1px 8px;
  border: 1px solid;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
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
</style>
