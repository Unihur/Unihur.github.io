<template>
  <div class="main-content-wrapper" :style="{ paddingTop: contentPaddingTop || '100px' }">
    <div class="glass-box">
      <h2>访客账号管理</h2>
      <el-table :data="visitors" style="width: 100%" v-loading="loading">
        <el-table-column label="头像" width="100">
          <template #default="scope">
            <el-avatar :src="scope.row.avatar || ''" :icon="UserFilled" />
          </template>
        </el-table-column>
        <el-table-column prop="username" label="昵称" />
        <el-table-column label="操作" width="150" align="right">
          <template #default="scope">
            <el-button type="danger" size="small" @click="deleteVisitor(scope.row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue'
import { UserFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import { useRouter } from 'vue-router'

const visitors = ref([])
const loading = ref(false)
const router = useRouter()
const contentPaddingTop = inject('contentPaddingTop', '100px')

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

const deleteVisitor = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除该访客账号吗？删除后该用户的评论将变回游客状态。', '警告', { type: 'warning' })
    await axios.delete(`http://116.62.218.51:8000/api/admin/visitors/${id}`, {
      headers: { token: localStorage.getItem('token') }
    })
    ElMessage.success('删除成功')
    fetchVisitors()
  } catch(e) {}
}

onMounted(() => {
  fetchVisitors()
})
</script>