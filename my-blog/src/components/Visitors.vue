<script setup>
import { ref, onMounted, inject, computed } from 'vue'
import { UserFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import { useRouter } from 'vue-router'

const visitors = ref([])
const loading = ref(false)
const router = useRouter()
const contentPaddingTop = inject('contentPaddingTop', '100px')

const pendingUsers = computed(() => visitors.value.filter(u => !u.is_approved))
const approvedUsers = computed(() => visitors.value.filter(u => u.is_approved))

const fetchVisitors = async () => {
  loading.value = true
  try {
    const res = await axios.get('http://116.62.218.51:8000/api/admin/visitors', {
      headers: { token: localStorage.getItem('token') }
    })
    visitors.value = res.data
  } catch (e) {
    ElMessage.error('权限不足或加载失败')
    router.push('/')
  }
  loading.value = false
}

// 👇 新增审核通过 API
const approveVisitor = async (id) => {
  try {
    await axios.put(`http://116.62.218.51:8000/api/admin/visitors/${id}/approve`, {}, {
      headers: { token: localStorage.getItem('token') }
    })
    ElMessage.success('审核已通过')
    fetchVisitors()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const deleteVisitor = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除该账号吗？该用户的头像文件也会被物理删除！', '警告', { type: 'warning' })
    await axios.delete(`http://116.62.218.51:8000/api/admin/visitors/${id}`, {
      headers: { token: localStorage.getItem('token') }
    })
    ElMessage.success('账号已彻底删除')
    fetchVisitors()
  } catch(e) {}
}

onMounted(() => {
  fetchVisitors()
})
</script>

<template>
  <div class="main-content-wrapper" style="padding-top: 100px; min-height: 100vh;">
    <div class="glass-box">
      <h2>新账号审核区 <el-tag type="danger" size="small">{{ pendingUsers.length }} 待办</el-tag></h2>
      <el-table :data="pendingUsers" style="width: 100%; margin-bottom: 40px;" v-loading="loading">
        <el-table-column label="头像" width="100">
          <template #default="scope">
            <el-avatar :src="scope.row.avatar || ''" :icon="scope.row.avatar ? '' : UserFilled" />
          </template>
        </el-table-column>
        <el-table-column prop="username" label="昵称" />
        <el-table-column label="操作" width="200" align="right">
          <template #default="scope">
            <el-button type="success" size="small" @click="approveVisitor(scope.row.id)">通过</el-button>
            <el-button type="danger" size="small" @click="deleteVisitor(scope.row.id)">拒绝并删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <h2>已通过账号管理</h2>
      <el-table :data="approvedUsers" style="width: 100%" v-loading="loading">
        <el-table-column label="头像" width="100">
          <template #default="scope">
            <el-avatar :src="scope.row.avatar || ''" :icon="scope.row.avatar ? '' : UserFilled" />
          </template>
        </el-table-column>
        <el-table-column prop="username" label="昵称" />
        <el-table-column label="操作" width="150" align="right">
          <template #default="scope">
            <el-button type="danger" size="small" @click="deleteVisitor(scope.row.id)">删除用户</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

