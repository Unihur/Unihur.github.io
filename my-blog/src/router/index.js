import { createRouter, createWebHashHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

// 路由懒加载：把视图拆成独立 chunk，避免首屏一次性加载所有页面
const HomeView = () => import('@/views/HomeView.vue')
const WriteView = () => import('@/views/WriteView.vue')
const ArticleView = () => import('@/views/ArticleView.vue')
const VisitorsView = () => import('@/views/VisitorsView.vue')

const routes = [
  { path: '/', name: 'Home', component: HomeView },
  { path: '/write', name: 'Write', component: WriteView, meta: { requiresAdmin: true } },
  { path: '/post/:slug', name: 'Article', component: ArticleView },
  { path: '/visitors', name: 'Visitors', component: VisitorsView, meta: { requiresAdmin: true } }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

// 全局守卫：进入 admin 路由前确保已登录，且 isAdmin
// 注意：isAdmin 由后端 /user/me 同步注入；首次进入时如果没有缓存，会先重定向登录
router.beforeEach(async (to) => {
  if (!to.meta.requiresAdmin) return true

  const userStore = useUserStore()

  // 未登录直接拒绝
  if (!userStore.isLoggedIn) {
    ElMessageSafe('请先登录管理员账号')
    return { path: '/' }
  }

  // 如果 isAdmin 还没拿到（首次刷新），尝试拉一次 /user/me
  let isAdmin = userStore.isAdmin
  if (!isAdmin) {
    await userStore.refreshProfile()
    isAdmin = userStore.isAdmin
  }

  if (!isAdmin) {
    ElMessageSafe('权限不足：仅管理员可访问该页面')
    return { path: '/' }
  }
  return true
})

// 不在守卫内直接 import element-plus，避免循环引用；
// 这里包一层，组件未初始化前也能安全提示
function ElMessageSafe(text) {
  import('element-plus').then(({ ElMessage }) => ElMessage.warning(text))
}

export default router
