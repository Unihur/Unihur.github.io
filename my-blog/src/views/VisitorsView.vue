<script setup>
// 访客管理页（管理员）：列出待审核与已通过账号，支持审核与删除
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UserFilled } from '@element-plus/icons-vue'

import { listVisitors, approveVisitor, deleteVisitor } from '@/api/visitor'

const router = useRouter()
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

onMounted(fetchVisitors)
</script>

<template>
  <div class="main-content-wrapper" style="padding-top: 100px; min-height: 100vh">
    <div class="glass-box">
      <h2>
        新账号审核区 <el-tag type="danger" size="small">{{ pendingUsers.length }} 待办</el-tag>
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
            <el-button type="success" size="small" @click="approveVisitorHandler(scope.row.id)"
              >通过</el-button
            >
            <el-button type="danger" size="small" @click="deleteVisitorHandler(scope.row.id)"
              >拒绝并删除</el-button
            >
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
        <el-table-column prop="username" label="昵称" />
        <el-table-column label="操作" width="150" align="right">
          <template #default="scope">
            <el-button type="danger" size="small" @click="deleteVisitorHandler(scope.row.id)"
              >删除用户</el-button
            >
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>
