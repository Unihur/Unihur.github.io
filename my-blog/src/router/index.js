import { createRouter, createWebHashHistory } from 'vue-router'

import Home from '../components/Home.vue'
import Write from '../components/Write.vue'
import ArticleDetail from '../components/ArticleDetail.vue'
import Visitors from '../components/Visitors.vue' 

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/write',
    name: 'Write',
    component: Write
  },
  // 👇 2. 新增动态路由，:slug 代表文章的唯一别名
  {
    path: '/post/:slug',
    name: 'ArticleDetail',
    component: ArticleDetail
  },
  { 
    path: '/visitors', 
    name: 'Visitors', 
    component: Visitors 
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router