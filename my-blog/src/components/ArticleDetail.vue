<script setup>
import { ref, onMounted, onUnmounted, inject, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage, ElMessageBox} from 'element-plus'
import { Calendar, Folder, PriceTag, Share, Edit, View, UserFilled, Delete, ChatRound, CaretTop, CaretBottom, PictureRounded } from '@element-plus/icons-vue'

import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

import ProfileCard from './ProfileCard.vue'

const route = useRoute()
const router = useRouter()
const isAdmin = inject('isAdmin')

// 注入全局 UI 配置，保持和首页一样的横幅效果
const siteConfig = inject('siteConfig')
const bannerMode = inject('bannerMode')
const bannerImages = inject('bannerImages')
const bannerWrapperHeight = inject('bannerWrapperHeight')
const carouselHeight = inject('carouselHeight')
const contentPaddingTop = inject('contentPaddingTop')
const contentMarginTop = inject('contentMarginTop')
const typewriterText = inject('typewriterText')
const isLoggedIn = inject('isLoggedIn', ref(false))

// Markdown 配置
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try { return hljs.highlight(str, { language: lang }).value } catch (__) {}
    }
    return ''
  }
})

// 点击编辑按钮跳转到写作页（并���上当前文章的 slug，方便写作页读取数据）
const editArticle = () => {
  router.push(`/write?slug=${article.value.slug}`)
}

// 数据状态
const article = ref(null) // 初始值必须是 null
const renderedHtml = ref('')
const prevPost = ref(null)
const nextPost = ref(null)
const isLoading = ref(true)
const likes = ref(0) 
const shares = ref(0)
const floatingHearts = ref([]) 
const allArticles = ref([])

let heartIdCounter = 0

// 全新的点赞函数 (合并了特效 + 后端请求)
const handleLike = async () => {
  // 1. 前端先立刻让点赞数 +1，让用户感觉反应很快（乐观更新）
  likes.value++
  
  // 2. 播放爱心特效
  const newHeart = {
    id: heartIdCounter++,
    size: Math.random() * 10 + 15,
    color: ['#ff79c6', '#ff4d4f', '#f56c6c', '#e0b0ff', '#ff6b81'][Math.floor(Math.random() * 5)],
    leftOffset: (Math.random() - 0.5) * 40
  }
  floatingHearts.value.push(newHeart)
  setTimeout(() => {
    floatingHearts.value = floatingHearts.value.filter(h => h.id !== newHeart.id)
  }, 1500)

  // 3. 异步发送请求给后端保存点赞数
  try {
    // 假设文章的 slug 存在，告诉后端这篇文章被点赞了
    if (article.value && article.value.slug) {
      await axios.post(`https://unihur.xyz/api/articles/${article.value.slug}/like`)
    }
  } catch (error) {
    console.error('点赞保存到后端失败:', error)
    // 如果想要严谨点，失败了可以把 likes.value 减回来，这里简单处理仅打印错误
  }
}

// ================= 新增：动态目录功能 =================
const tocList = ref([]) // 用于存放提取出来的目录

const generateTOC = () => {
  const container = document.querySelector('.markdown-body')
  if (!container) {
    console.log("没找到 .markdown-body 容器") // 用于排错
    return
  }
  
  // 👇 修改这里：增加 h4, h5, h6，以防你文章里用的是四级或五级标题
  const headers = container.querySelectorAll('h1, h2, h3, h4, h5, h6')
  const toc = []
  
  headers.forEach((header, index) => {
    const id = `heading-${index}`
    header.id = id 
    
    // 取出标题级别
    const level = parseInt(header.tagName.replace('H', ''))
    
    toc.push({
      id: id,
      text: header.innerText,
      level: level
    })
  })
  
  tocList.value = toc 
  console.log("成功提取目录：", tocList.value) // 用于看控制台是否成功抓到了
}

// 点击目录跳转的方法
const scrollToAnchor = (id) => {
  const element = document.getElementById(id)
  if (element) {
    // 减去80是为了给顶部的导航栏留点空间，不会被挡住
    const top = element.offsetTop - 80 
    window.scrollTo({ top, behavior: 'smooth' })
  }
}

// 修改后的 handleShare：兼容 HTTP 和 HTTPS
const handleShare = async () => {
  const url = window.location.href
  
  // 1. 复制链接到剪贴板 (兼容处理)
  if (navigator.clipboard && window.isSecureContext) {
    // 如果是 HTTPS 或者 localhost，使用现代 API
    await navigator.clipboard.writeText(url)
  } else {
    // 如果是 HTTP 环境，使用传统 DOM 降级方案
    const textArea = document.createElement("textarea")
    textArea.value = url
    // 把输入框藏在屏幕外面
    textArea.style.position = "absolute"
    textArea.style.left = "-999999px"
    document.body.prepend(textArea)
    textArea.select()
    try {
      document.execCommand('copy')
    } catch (err) {
      console.error('复制失败', err)
    } finally {
      textArea.remove() // 用完删掉
    }
  }

  ElMessage.success('🔗 链接已复制！感谢你的分享~')
  
  // 2. 页面立刻展示转发数 +1
  shares.value++
  
  // 3. 告诉后端记录这条转发
  try {
    if (article.value && article.value.slug) {
      await axios.post(`https://unihur.xyz/api/articles/${article.value.slug}/share`)
    }
  } catch (error) {
    console.error('转发保存到后端失败:', error)
  }
}

// ================= 真实的评论功能 =================
const comments = ref([])
const currentUsername = ref(localStorage.getItem('username') || '')
const newComment = ref('')
const articleList = ref([])
const rawComments = ref([]) // 后端原始数据
const rootComments = ref([]) // 经过组装的树形数据

// 常见表情包库
const emojis = ['😀','😂','🤣','😍','😒','😘','😁','😉','😎','😊','🤔','🙄','🤨','😑','🤐','😪','😫','🥱','😴','😛','😜','😝','🤤','😒','😓','😔','😕','🙃','🤑','😲','☹️','🙁','😖','😞','😟','😤','😢','😭','😦','😧','😨','😩','🤯','😬','😰','😱','🥵','🥶','😳','🤪','😵','😡','😠','🤬','😷','🤒','🤕','🤢','🤮','🤧','😇','🥳','🥺','🥺','🤠','🤡','🤥','🤫','🤭','🧐','🤓','😈','👿','👹','👺','💀','👻','👽','🤖','💩','😺','😸','😹','😻','😼','😽','🙀','😿','😾','🙏','👍','🔥','❤️','✨','🎉','🤔','😅','👀']
// 排序与回复状态
const sortBy = ref('time') // 'time' 或 'hot'
const activeReplyId = ref(null) // 记录当前正在回复哪条评论
const replyContent = ref('') // 回复框内容
const showEmojiPicker = ref(false) // 是否显示主评论表情包
const showReplyEmojiPicker = ref(false) // 是否显示回复框表情包

// 每当浏览器 token 变化（可能跨标签页登录）时同步
window.addEventListener('storage', () => {
  currentUsername.value = localStorage.getItem('username') || ''
})

// 读取评论并组装成 B站两级树形结构
const loadComments = async (slug) => {
  try {
    // 携带 token 以便后端判定当前账号点赞状态
    const res = await axios.get(`https://unihur.xyz/api/comments/${slug}`, {
      headers: { token: localStorage.getItem('token') || '' }
    })
    const flatList = res.data
    const map = {}
    const roots = []

    flatList.forEach(c => {
      c.children = []
      c.isLiked = c.userAction === 'like'
      c.isDisliked = c.userAction === 'dislike'
      
      // 改成空字符串，让模板自动去触发默认头像的 fallback
      c.avatar = c.avatar || '' 
      
      map[c.id] = c
    })

    flatList.forEach(c => {
      if (c.parent_id) {
        let rootId = c.parent_id
        while (map[rootId] && map[rootId].parent_id) {
          rootId = map[rootId].parent_id
        }
        c.replyToAuthor = map[c.parent_id] ? map[c.parent_id].author : '未知'
        if (map[rootId]) map[rootId].children.push(c)
      } else {
        roots.push(c)
      }
    })

    // 依然保留折叠与分页初始化
    roots.forEach(root => {
      root.isExpanded = false
      root.currentPage = 1
      root.pageSize = 5
    })

    rootComments.value = roots
    sortCommentsTree()
  } catch (error) {
    console.error('获取评论失败:', error)
  }
}

// 展开/收起回复列表
const toggleReplies = (root) => {
  root.isExpanded = !root.isExpanded
  if (!root.isExpanded) {
    root.currentPage = 1 // 收起时重置页码
  }
}

// 获取某评论当前页的子回复
const getPagedChildren = (root) => {
  const start = (root.currentPage - 1) * root.pageSize
  const end = start + root.pageSize
  return root.children.slice(start, end)
}

const changePage = (root, delta) => {
  const maxPage = Math.ceil(root.children.length / root.pageSize)
  root.currentPage += delta
  if (root.currentPage < 1) root.currentPage = 1
  if (root.currentPage > maxPage) root.currentPage = maxPage
}

// 针对指定的页码跳转
const goToPage = (root, page) => {
  root.currentPage = page
}

// 展开回复框
const showReplyBox = (commentId) => {
  activeReplyId.value = activeReplyId.value === commentId ? null : commentId
  replyContent.value = ''
  showReplyEmojiPicker.value = false
}

// 获取文章数据
const fetchArticle = async (slug) => {
  try {
    isLoading.value = true
    const res = await axios.get(`https://unihur.xyz/api/articles/${slug}`)
    
    // 👇【关键修改点】不管后端返回的是嵌套的，还是没嵌套的，我们都能拿到！
    const data = res.data
    const articleData = data.article || data // 兼容新旧两版 API
    
    if (articleData && articleData.title) {
      article.value = articleData
      
      likes.value = articleData.likes || 0
      shares.value = articleData.shares || 0
      
      // 提取上一篇和下一篇（如果是旧格式，这里取不到就是 null，很安全）
      prevPost.value = data.prev || null
      nextPost.value = data.next || null
      
      // 渲染 Markdown
      renderedHtml.value = md.render(article.value.content || '*无内容*')
      document.title = `${article.value.title} - UniHur's Blog`
      
      // 👇 清空旧目录，确保产生数据变动
      tocList.value = []
      
      // 👇 把 generateTOC 的触发放在数据确实赋完值、DOM刷新后
      setTimeout(() => {
        generateTOC()
      }, 300) // 把延迟稍微调长一点到 300ms，确保文章主体已经彻底显示出来
      
      // 💥【新增这一步】此时后端已经给当前文章的浏览量+1了，我们现在去拉取全站总数据，绝对是最新的！
      fetchAllArticlesForStats() 

    } else {
      ElMessage.error('文章数据格式错误: 找不到标题')
    }
  } catch (error) {
    console.error('获取文章失败:', error)
    ElMessage.error('获取文章失败或文章不存在')
  } finally {
    isLoading.value = false
  }
}

// 新增：获取所有文章为了算总浏览量
const fetchAllArticlesForStats = async () => {
   try {
    const res = await axios.get('https://unihur.xyz/api/articles')
    // 取决于你后端的格式，可能是 res.data，也可能是 res.data.articles
    // 如果你在主页用的 res.data，那就统一用 res.data
    allArticles.value = res.data 
  } catch (error) {
    console.error('获取所有文章列表失败:', error)
  }
}

// 监听路由参数变化（用于点击“上一篇/下一篇”时刷新内容和评论）
watch(() => route.params.slug, (newSlug) => {
  if (newSlug) {
    // 切换文章时，也把原目录清空
    tocList.value = []
    fetchArticle(newSlug)
    loadComments(newSlug) 
  }
})

// ====== 新增：点击空白处自动关闭表情包 ======
const handleOutsideClick = (e) => {
  // 如果点击的区域不在 emoji-wrapper 内部，就把表情包关掉
  if (!e.target.closest('.emoji-wrapper')) {
    showEmojiPicker.value = false
    showReplyEmojiPicker.value = false
  }
}

onMounted(() => {

  document.addEventListener('click', handleOutsideClick)

  fetchArticle(route.params.slug)
  //fetchAllArticlesForStats()
  loadComments(route.params.slug) // 👉 新增：第一次进页面时，拉取评论
})

onUnmounted(() => {
  // 页面销毁时移除事件，防止内存泄漏
  document.removeEventListener('click', handleOutsideClick)
})

// 发送评论 (整合主评论与回复)
const submitComment = async (parentId = null) => {
  let content = parentId ? replyContent.value : newComment.value
  
  // 核心2：如果回复内容包含了生成的蓝字前缀，发送给后端前将其去掉，保持数据库纯净
  // 因为展示时前端会自动加上，不需要存入数据库
  const replyPrefixRegex = /^回复\s*@[^\s：]+：/
  content = content.replace(replyPrefixRegex, '').trim()

  if (!content) return ElMessage.warning('内容不能为空')
  
  const authorName = currentUsername.value || '游客'
  try {
    await axios.post('https://unihur.xyz/api/comments', {
      article_slug: route.params.slug,
      author: authorName,
      content: content,
      parent_id: parentId
    }, { headers: { token: localStorage.getItem('token') || '' } })
    
    ElMessage.success('发布成功')
    if (parentId) {
      replyContent.value = ''
      activeReplyId.value = null
      
      // 找到对应的根节点并强行展开它，跳到最后一页看新评论
      const targetRoot = rootComments.value.find(r => r.id === parentId || r.children.some(c => c.id === parentId))
      if (targetRoot) {
        targetRoot.isExpanded = true
        targetRoot.currentPage = Math.ceil((targetRoot.children.length + 1) / targetRoot.pageSize)
      }

    } else {
      newComment.value = ''
    }
    await loadComments(route.params.slug) // 重新拉取
  } catch (e) {
    ElMessage.error('评论失败')
  }
}

// 检查是否可以删除评论
const canDelete = (commentAuthor) => {
  return currentUsername.value === 'unihur' || currentUsername.value === commentAuthor
}

// 回复发表
const submitReply = async (targetComment) => {
  if (!replyContent.value.trim()) return ElMessage.warning('回复内容不能为空')
  const username = localStorage.getItem('username') || '游客'
  try {
    await axios.post('https://unihur.xyz/api/comments', {
      article_slug: route.params.slug,
      author: username,
      content: replyContent.value,
      reply_to: targetComment.author // 记录回复给了谁
    }, { headers: { token: localStorage.getItem('token') || '' } })
    ElMessage.success('回复成功')
    replyContent.value = ''
    activeReplyId.value = null // 收起回复框
    showReplyEmojiPicker.value = false
    loadComments(route.params.slug)
  } catch (e) {
    ElMessage.error('回复失败')
  }
}

// 删除评论
const handleDeleteComment = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这条评论吗？', '删除确认', { type: 'warning' })
    await axios.delete(`https://unihur.xyz/api/comments/${id}`, {
      headers: { token: localStorage.getItem('token') }
    })
    ElMessage.success('删除成功')
    loadComments(route.params.slug) 
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('权限不足或网络错误')
  }
}

// ====== 新增：管理员置顶/取消置顶评论 ======
const handlePinComment = async (id) => {
  try {
    await axios.post(`https://unihur.xyz/api/comments/${id}/pin`, {}, {
      headers: { token: localStorage.getItem('token') }
    })
    ElMessage.success('操作成功')
    loadComments(route.params.slug) // 刷新列表
  } catch (e) {
    ElMessage.error('权限不足或网络错误')
  }
}

// 互斥点赞与点踩逻辑
const handleCommentAction = async (comment, action) => {
  if (!currentUsername.value) {
    return ElMessage.warning('请先登录再操作')
  }

  try {
    // 请求后端处理状态反转
    const res = await axios.post(`https://unihur.xyz/api/comments/${comment.id}/action`, {
      action: action
    }, {
      headers: { token: localStorage.getItem('token') }
    })
    
    // 更新为后端计算好的真实数据
    comment.likes = res.data.likes
    comment.dislikes = res.data.dislikes
    comment.isLiked = res.data.userAction === 'like'
    comment.isDisliked = res.data.userAction === 'dislike'
  } catch(e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

// 插入表情
const insertEmoji = (emoji, isReply = false) => {
  if (isReply) {
    replyContent.value += emoji
    showReplyEmojiPicker.value = false
  } else {
    newComment.value += emoji
    showEmojiPicker.value = false
  }
}

// 切换排序方式
const changeSort = (mode) => {
  sortBy.value = mode
  sortCommentsTree()
}

// 对评论树进行排序
const sortCommentsTree = () => {
  if (sortBy.value === 'hot') {
    rootComments.value.sort((a, b) => {
      if (a.is_pinned !== b.is_pinned) return a.is_pinned ? -1 : 1;
      return b.likes - a.likes;
    })
  } else {
    rootComments.value.sort((a, b) => {
      if (a.is_pinned !== b.is_pinned) return a.is_pinned ? -1 : 1;
      return new Date(b.time) - new Date(a.time);
    })
  }
  // 子评论固定按时间正序
  rootComments.value.forEach(root => {
    root.children.sort((a, b) => new Date(a.time) - new Date(b.time))
  })
}

const navigateTo = (slug) => {
  router.push(`/post/${slug}`)
}
</script>

<template>
  <div class="article-detail-container">
    <!-- 1. 博客大标题 Banner (完全复用主页的逻辑，显示全局的 Blog 标题) -->
    <header v-if="bannerMode !== 'hidden'" :class="['banner', bannerMode]" :style="{ height: bannerWrapperHeight }">
      <el-carousel :interval="4000" arrow="always" class="banner-carousel" :height="carouselHeight">
        <el-carousel-item v-for="(img, index) in bannerImages" :key="index">
          <img :src="img" class="carousel-img" alt="banner">
        </el-carousel-item>
      </el-carousel>
      
      <div v-if="bannerMode === 'background'" class="banner-overlay"></div>
      
      <!-- 这里显示全局的 Blog 标题和打字机，不是文章标题 -->
      <h1 v-if="bannerMode !== 'background'" class="blog-title">
        {{ siteConfig.name }}'s Blog
        <p class="blog-subtitle">
          {{ typewriterText }}<span class="cursor">|</span>
        </p>
      </h1>

      <div class="waves-container" v-if="bannerMode === 'banner' || bannerMode === 'fullscreen'">
        <svg class="waves" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 24 150 28" preserveAspectRatio="none">
          <defs><path id="gentle-wave" d="M-160 44c30 0 58-18 88-18s 58 18 88 18 58-18 88-18 58 18 88 18 v44h-352z" /></defs>
          <g class="parallax">
            <use xlink:href="#gentle-wave" x="48" y="0" class="wave wave1" />
            <use xlink:href="#gentle-wave" x="48" y="3" class="wave wave2" />
            <use xlink:href="#gentle-wave" x="48" y="5" class="wave wave3" />
            <use xlink:href="#gentle-wave" x="48" y="7" class="wave wave4" />
          </g>
        </svg>
      </div>
    </header>

    <!-- 2. 主体内容区 -->
    <div class="main-content-wrapper" :style="{ paddingTop: contentPaddingTop, marginTop: contentMarginTop }">
      
      <!-- 加载中提示 -->
      <div v-if="isLoading" class="glass-box" style="padding: 50px; text-align: center; margin-top: 20px;">
        <h2>拼命加载文章中...</h2>
      </div>

      <el-row :gutter="20" v-else-if="article">
        <!-- ================= 左侧栏 (包含个人信息、分类标签、目录) ================= -->
        <el-col :xs="24" :md="6">
          <ProfileCard :config="siteConfig" :articles="allArticles" />

          <!-- 修改后的：文章目录 -->
          <div class="glass-box toc-box" v-if="tocList && tocList.length > 0">
            <h3>📖 文章目录</h3>
            <ul class="toc-list">
              <!-- 用 v-for 循环我们提取出来的目录 -->
              <li 
                v-for="item in tocList" 
                :key="item.id"
                :style="{ paddingLeft: (item.level - 1) * 15 + 'px' }"
              >
                <!-- 点击时阻止默认跳转，使用我们自己写的滚动函数 -->
                <a href="#" @click.prevent="scrollToAnchor(item.id)">
                  {{ item.text }}
                </a>
              </li>
            </ul>
          </div>
        </el-col>

        <!-- ================= 右侧：文章展示区 ================= -->
        <el-col :xs="24" :md="18">
          
          <!-- 核心文章卡片 -->
          <div class="glass-box article-main-card">
            
            <!-- 顶部：文章封面图，标题悬浮在左下角 -->
            <div class="article-hero">
              <!-- 如果没有传封面，用一张默认的高清图代替 -->
              <img :src="article.cover || '/banner/1.png'" class="hero-img">
              <div class="hero-title-box">
                <h1 class="hero-title">{{ article.title }}</h1>
              </div>
            </div>

            <!-- 元信息：时间、分类、标签 (带图标) -->
            <div class="article-meta">
              <!-- 第一行：时间 和 浏览量 -->
              <div class="meta-row" style="gap: 20px;">
                <!-- 时间 -->
                <div class="meta-item time">
                  <el-icon><Calendar /></el-icon>
                  <span>发布于: {{ new Date(article.publishTime).toLocaleDateString() }}</span>
                </div>
                <!-- 浏览量 (新增) -->
                <div class="meta-item views">
                  <el-icon><View /></el-icon>
                  <span>浏览: {{ article.views || 0 }}</span>
                </div>
              </div>
              
              <div class="meta-row tags-row" v-if="article.category || (article.tags && article.tags.length > 0)">
                <!-- 分类框 (黄色) -->
                <div class="meta-box category-box" v-if="article.category">
                  <el-icon><Folder /></el-icon>
                  <span>{{ article.category }}</span>
                </div>

                <!-- 标签框 (绿色，循环生成) -->
                <template v-if="article.tags && article.tags.length > 0">
                  <div class="meta-box tag-box" v-for="tag in article.tags" :key="tag">
                    <el-icon><PriceTag /></el-icon>
                    <span>{{ tag }}</span>
                  </div>
                </template>

                <!-- 👇 新增：编辑按钮 (只在管理员登录时显示) -->
                <div class="edit-btn-wrapper" v-if="isAdmin">
                  <el-button round size="small" class="pink-edit-btn" @click="editArticle">
                    <el-icon><Edit /></el-icon> 编辑文章
                  </el-button>
                </div>

              </div>
            </div>

            <el-divider border-style="dashed" />

            <!-- 正文渲染区 -->
            <div class="markdown-body" v-html="renderedHtml"></div>
            
            <!-- 点赞按钮 -->
            <div class="action-center">
              
              <!-- 点赞模块（包含按钮和漂浮爱心的容器） -->
              <div class="like-wrapper">
                <!-- 漂浮爱心渲染区 -->
                <transition-group name="heart-float" tag="div" class="hearts-container">
                  <div 
                    v-for="heart in floatingHearts" 
                    :key="heart.id" 
                    class="floating-heart"
                    :style="{ 
                      fontSize: heart.size + 'px', 
                      color: heart.color,
                      left: `calc(50% + ${heart.leftOffset}px)`
                    }"
                  >
                    ❤️
                  </div>
                </transition-group>
                
                <el-button type="danger" plain round size="large" @click="handleLike" class="action-btn">
                  ❤️ 点赞 ({{ likes }})
                </el-button>
              </div>

              <!-- 分享/转发按钮 -->
              <el-button type="primary" plain round size="large" @click="handleShare" class="action-btn">
                <el-icon style="margin-right: 5px;"><Share /></el-icon> 分享文章 ({{ shares }})
              </el-button>
              
            </div>
          </div>

          <!-- 下方：上一篇 / 下一篇 -->
          <div class="prev-next-nav">
            <div class="nav-item prev glass-box" @click="prevPost ? navigateTo(prevPost.slug) : null" :class="{ disabled: !prevPost }">
              <div class="nav-label">上一篇</div>
              <div class="nav-title">{{ prevPost ? prevPost.title : '没有了' }}</div>
            </div>
            <div class="nav-item next glass-box" @click="nextPost ? navigateTo(nextPost.slug) : null" :class="{ disabled: !nextPost }">
              <div class="nav-label" style="text-align: right;">下一篇</div>
              <div class="nav-title" style="text-align: right;">{{ nextPost ? nextPost.title : '没有了' }}</div>
            </div>
          </div>

          <!-- 下方：评论区 -->
          <div class="glass-box comments-section">
            <div class="comments-header-row">
              <h3>💬 评论区</h3>
              <div class="sort-tabs">
                <span :class="{active: sortBy === 'hot'}" @click="changeSort('hot')">最热</span>
                <span class="divider">|</span>
                <span :class="{active: sortBy === 'time'}" @click="changeSort('time')">最新</span>
              </div>
            </div>

            <!-- 主输入区 -->
            <div class="comment-input">
              <el-input v-model="newComment" type="textarea" :rows="3" placeholder="写下你的评论..." />
              <div class="comment-input-footer">
                <div class="emoji-wrapper">
                  <el-icon class="emoji-btn" @click="showEmojiPicker = !showEmojiPicker"><PictureRounded /></el-icon>
                  <div class="emoji-picker glass-box" v-if="showEmojiPicker">
                    <span v-for="e in emojis" :key="e" @click="insertEmoji(e, false)">{{ e }}</span>
                  </div>
                </div>
                <el-button type="primary" @click="submitComment(null)">发表评论</el-button>
              </div>
            </div>
            
            <div class="comment-list">
              <!-- 遍历根评论 -->
              <div class="comment-item" v-for="comment in rootComments" :key="comment.id">
                <el-avatar :src="comment.avatar || ''" :icon="comment.avatar ? '' : UserFilled" :size="48" class="comment-avatar" />
                
                <div class="comment-content-box">
                  <div class="comment-header">
                    <div class="author-area">
                      <span class="comment-author" :class="{ 'admin-name': comment.author === 'unihur' }">{{ comment.author }}</span>
                      <!-- 管理员专属标识 -->
                      <span class="admin-badge" v-if="comment.author === 'unihur'">管理员</span>
                    </div>
                    
                    <div class="admin-tools" v-if="currentUsername === 'unihur'">
                      <!-- 置顶按钮 (图钉) -->
                      <el-tooltip :content="comment.is_pinned ? '取消置顶' : '置顶评论'" placement="top">
                        <span class="pin-btn" :class="{ 'is-pinned-icon': comment.is_pinned }" @click="handlePinComment(comment.id)">📌</span>
                      </el-tooltip>
                      <el-tooltip content="删除该评论" placement="top">
                        <el-icon class="delete-comment-btn" @click="handleDeleteComment(comment.id)"><Delete /></el-icon>
                      </el-tooltip>
                    </div>
                    <!-- 普通用户只能删自己的 -->
                    <el-icon class="delete-comment-btn" @click="handleDeleteComment(comment.id)" v-else-if="canDelete(comment.author)"><Delete /></el-icon>
                  </div>
                  
                  <div class="comment-text">
                    <span class="pinned-badge" v-if="comment.is_pinned">置顶</span>
                    {{ comment.content }}
                  </div>
                  
                  <!-- ======= 底部操作栏（间距缩小） ======= -->
                  <div class="comment-footer">
                    <span class="comment-time">{{ comment.time }}</span>
                    <div class="comment-actions">
                      <!-- 赞 (SVG大拇指) -->
                      <span class="action-btn" :class="{ 'active-blue': comment.isLiked }" @click="handleCommentAction(comment, 'like')">
                        <svg viewBox="0 0 1024 1024" width="14" height="14" :fill="comment.isLiked ? '#00aeec' : '#9499a0'">
                          <path d="M853.333333 469.333333h-190.293333l40.96-193.28c4.693333-22.186667-2.133333-45.653333-17.92-62.293333-14.506667-15.36-35.413333-23.466667-56.746667-22.186667l-35.84 2.56-258.133333 300.373334V853.333333h384c24.746667 0 46.933333-16.64 53.333333-40.533333l71.68-256c5.546667-19.626667-0.426667-40.533333-14.933333-55.04-14.933333-14.933333-35.413333-23.466667-56.746667-23.466666zM256 853.333333H128c-23.466667 0-42.666667-19.2-42.666667-42.666666V512c0-23.466667 19.2-42.666667 42.666667-42.666667h128c23.466667 0 42.666667 19.2 42.666667 42.666667v298.666667c0 23.466667-19.2 42.666667-42.666667 42.666666z"></path>
                        </svg>
                        <span class="num">{{ comment.likes || '' }}</span>
                      </span>
                      <!-- 踩 (SVG反转) -->
                      <span class="action-btn flip-icon" :class="{ 'active-blue': comment.isDisliked }" @click="handleCommentAction(comment, 'dislike')">
                        <svg viewBox="0 0 1024 1024" width="14" height="14" :fill="comment.isDisliked ? '#00aeec' : '#9499a0'">
                          <path d="M853.333333 469.333333h-190.293333l40.96-193.28c4.693333-22.186667-2.133333-45.653333-17.92-62.293333-14.506667-15.36-35.413333-23.466667-56.746667-22.186667l-35.84 2.56-258.133333 300.373334V853.333333h384c24.746667 0 46.933333-16.64 53.333333-40.533333l71.68-256c5.546667-19.626667-0.426667-40.533333-14.933333-55.04-14.933333-14.933333-35.413333-23.466667-56.746667-23.466666zM256 853.333333H128c-23.466667 0-42.666667-19.2-42.666667-42.666666V512c0-23.466667 19.2-42.666667 42.666667-42.666667h128c23.466667 0 42.666667 19.2 42.666667 42.666667v298.666667c0 23.466667-19.2 42.666667-42.666667 42.666666z"></path>
                        </svg>
                      </span>
                      <span class="action-btn reply-text-btn" @click="() => { showReplyBox(comment.id); replyContent = `回复 @${comment.author}： ` }">回复</span>
                    </div>
                  </div>

                  <!-- 回复输入框 -->
                  <div class="reply-input-area" v-if="activeReplyId === comment.id">
                    <el-input v-model="replyContent" type="textarea" :rows="2" class="custom-reply-input" />
                    <div class="comment-input-footer">
                      <div class="emoji-wrapper">
                        <el-icon class="emoji-btn" @click="showReplyEmojiPicker = !showReplyEmojiPicker"><PictureRounded /></el-icon>
                        <div class="emoji-picker glass-box" v-if="showReplyEmojiPicker">
                          <span v-for="e in emojis" :key="e" @click="insertEmoji(e, true)">{{ e }}</span>
                        </div>
                      </div>
                      <div>
                        <el-button size="small" @click="activeReplyId = null">取消</el-button>
                        <el-button type="primary" size="small" @click="submitComment(comment.id)">发送</el-button>
                      </div>
                    </div>
                  </div>

                  <!-- 核心3：子评论列表及折叠逻辑 -->
                  <div class="sub-comments-list" v-if="comment.children && comment.children.length > 0">
                    
                    <!-- 收起状态，仅显示提示 -->
                    <div class="toggle-reply-btn" v-if="!comment.isExpanded" @click="toggleReplies(comment)">
                      共 {{ comment.children.length }} 条回复，点击查看
                    </div>

                    <!-- 展开状态 -->
                    <div v-else>
                      <!-- 这里一定要用 getPagedChildren(comment) 来截取当前页 -->
                      <div class="sub-comment-item" v-for="child in getPagedChildren(comment)" :key="child.id">
                        <el-avatar :src="child.avatar || ''" :icon="child.avatar ? '' : UserFilled" :size="32" class="comment-avatar" />
                        <div class="sub-content-box">
                          
                          <div class="comment-header">
                            <div class="author-area">
                              <span class="comment-author" :class="{ 'admin-name': child.author === 'unihur' }">{{ child.author }}</span>
                              <span class="admin-badge" v-if="child.author === 'unihur'">管理员</span>
                            </div>
                            <el-icon class="delete-comment-btn" @click="handleDeleteComment(child.id)" v-if="canDelete(child.author)"><Delete /></el-icon>
                          </div>
                          
                          <div class="comment-text">
                            <span class="reply-target" v-if="child.replyToAuthor && child.replyToAuthor !== comment.author">
                              回复 <span class="blue-text">@{{ child.replyToAuthor }}</span>：
                            </span>
                            {{ child.content }}
                          </div>
                          
                          <!-- 子评论的底部操作栏... (保留你原有的 action-btn 结构) -->
                          <div class="comment-footer">
                            <span class="comment-time">{{ child.time }}</span>
                            <div class="comment-actions">
                              <span class="action-btn" :class="{ 'active-blue': child.isLiked }" @click="handleCommentAction(child, 'like')">
                                <svg viewBox="0 0 1024 1024" width="14" height="14" :fill="child.isLiked ? '#00aeec' : '#9499a0'">
                                  <path d="M853.333333 469.333333h-190.293333l40.96-193.28c4.693333-22.186667-2.133333-45.653333-17.92-62.293333-14.506667-15.36-35.413333-23.466667-56.746667-22.186667l-35.84 2.56-258.133333 300.373334V853.333333h384c24.746667 0 46.933333-16.64 53.333333-40.533333l71.68-256c5.546667-19.626667-0.426667-40.533333-14.933333-55.04-14.933333-14.933333-35.413333-23.466667-56.746667-23.466666zM256 853.333333H128c-23.466667 0-42.666667-19.2-42.666667-42.666666V512c0-23.466667 19.2-42.666667 42.666667-42.666667h128c23.466667 0 42.666667 19.2 42.666667 42.666667v298.666667c0 23.466667-19.2 42.666667-42.666667 42.666666z"></path>
                                </svg>
                                <span class="num">{{ child.likes || '' }}</span>
                              </span>
                              <span class="action-btn flip-icon" :class="{ 'active-blue': child.isDisliked }" @click="handleCommentAction(child, 'dislike')">
                                <svg viewBox="0 0 1024 1024" width="14" height="14" :fill="child.isDisliked ? '#00aeec' : '#9499a0'">
                                  <path d="M853.333333 469.333333h-190.293333l40.96-193.28c4.693333-22.186667-2.133333-45.653333-17.92-62.293333-14.506667-15.36-35.413333-23.466667-56.746667-22.186667l-35.84 2.56-258.133333 300.373334V853.333333h384c24.746667 0 46.933333-16.64 53.333333-40.533333l71.68-256c5.546667-19.626667-0.426667-40.533333-14.933333-55.04-14.933333-14.933333-35.413333-23.466667-56.746667-23.466666zM256 853.333333H128c-23.466667 0-42.666667-19.2-42.666667-42.666666V512c0-23.466667 19.2-42.666667 42.666667-42.666667h128c23.466667 0 42.666667 19.2 42.666667 42.666667v298.666667c0 23.466667-19.2 42.666667-42.666667 42.666666z"></path>
                                </svg>
                              </span>
                              <span class="action-btn reply-text-btn" @click="() => { showReplyBox(child.id); replyContent = `回复 @${child.author}： ` }">回复</span>
                            </div>
                          </div>

                          <div class="reply-input-area" v-if="activeReplyId === child.id">
                            <el-input v-model="replyContent" type="textarea" :rows="2" class="custom-reply-input" />
                            <div class="comment-input-footer">
                              <div class="emoji-wrapper">
                                <el-icon class="emoji-btn" @click="showReplyEmojiPicker = !showReplyEmojiPicker"><PictureRounded /></el-icon>
                                <div class="emoji-picker glass-box" v-if="showReplyEmojiPicker">
                                  <span v-for="e in emojis" :key="e" @click="insertEmoji(e, true)">{{ e }}</span>
                                </div>
                              </div>
                              <div>
                                <el-button size="small" @click="activeReplyId = null">取消</el-button>
                                <el-button type="primary" size="small" @click="submitComment(comment.id)">发送</el-button>
                              </div>
                            </div>
                          </div>

                        </div>
                      </div>

                      <!-- 分页器与蓝色的收起按钮 -->
                      <div class="pagination-row">
                        <span class="page-info">共 {{ Math.ceil(comment.children.length / comment.pageSize) }} 页</span>
                        <span class="page-btn" :class="{disabled: comment.currentPage === 1}" @click="changePage(comment, -1)">上一页</span>
                        
                        <span class="page-num" 
                              v-for="p in Math.ceil(comment.children.length / comment.pageSize)" :key="p"
                              :class="{active: comment.currentPage === p}"
                              @click="goToPage(comment, p)">
                          {{ p }}
                        </span>

                        <span class="page-btn" :class="{disabled: comment.currentPage === Math.ceil(comment.children.length / comment.pageSize)}" @click="changePage(comment, 1)">下一页</span>
                        
                        <!-- 核心：蓝色收起按钮 -->
                        <span class="fold-btn" @click="toggleReplies(comment)">收起</span>
                      </div>

                    </div>
                  </div>

                </div>
              </div>
            </div>
          </div>

        </el-col>
      </el-row>
    </div>
  </div>
</template>

<style scoped>
.main-content-wrapper { max-width: 1200px; margin: 0 auto; padding: 0 20px 40px 20px; position: relative; z-index: 10; }
.banner { position: relative; width: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; overflow: hidden; }
.banner-carousel { position: absolute; top: 0; left: 0; width: 100%; z-index: 1; }
.carousel-img { width: 100%; height: 100%; object-fit: cover; }
.blog-title { position: relative; z-index: 3; font-size: 4rem; font-weight: 900; color: #fff; text-shadow: 2px 2px 8px rgba(0,0,0,0.5); text-align: center; margin-top: -60px; }
.blog-subtitle { font-size: 2rem; font-weight: normal; margin-top: 10px; text-shadow: 1px 1px 5px rgba(0,0,0,0.8); }

.waves-container { position: absolute; bottom: 0; left: 0; width: 100%; height: 6vw; min-height: 100px; z-index: 10; line-height: 0; }
.waves { width: 100%; height: 100%; display: block; }
.wave1 { fill: rgba(244, 244, 245, 0.3); } .wave2 { fill: rgba(244, 244, 245, 0.5); } .wave3 { fill: rgba(244, 244, 245, 0.7); } .wave4 { fill: #f4f4f5; } 
html.dark .wave1 { fill: rgba(43, 34, 61, 0.3); } html.dark .wave2 { fill: rgba(43, 34, 61, 0.5); } html.dark .wave3 { fill: rgba(43, 34, 61, 0.7); } html.dark .wave4 { fill: #1a1525; } 

/* ================= 修复波浪动画 ================= */
.parallax > use { 
  animation: move-forever 25s cubic-bezier(.55,.5,.45,.5) infinite; 
}
.parallax > use:nth-child(1) { animation-delay: -2s; animation-duration: 7s; }
.parallax > use:nth-child(2) { animation-delay: -3s; animation-duration: 10s; }
.parallax > use:nth-child(3) { animation-delay: -4s; animation-duration: 13s; }
.parallax > use:nth-child(4) { animation-delay: -5s; animation-duration: 20s; }

@keyframes move-forever {
  0% { transform: translate3d(-90px, 0, 0); }
  100% { transform: translate3d(85px, 0, 0); }
}

/* 左侧分���和标签列表样式 */
.category-list { list-style: none; padding: 0; }
.category-list li { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px dashed rgba(0,0,0,0.1); }
html.dark .category-list li { border-bottom-color: rgba(255,255,255,0.1); }
.tag-list .custom-tag { margin: 5px; }

/* 目录样式 */
.toc-box { padding: 20px; margin-top: 20px; position: sticky; top: 80px; }
.toc-box h3 { margin-top: 0; border-bottom: 1px dashed rgba(0,0,0,0.1); padding-bottom: 10px; }
html.dark .toc-box h3 { border-bottom-color: rgba(255,255,255,0.1); color: #fff; } /* 夜间模式标题变白 */

.toc-list { list-style: none; padding-left: 0; }
.toc-list li { margin: 10px 0; }

.toc-list a { text-decoration: none; color: #555; transition: color 0.3s; }
html.dark .toc-list a { color: #ccc; } /* 夜间模式默认浅灰白 */

.toc-list a:hover { color: #409eff; }
html.dark .toc-list a:hover { color: #66b1ff; } /* 夜间模式悬浮时用更亮的蓝色 */

/* ================= 右侧核心文章区域 (已去重并修复对齐) ================= */
.article-main-card {
  /* 必须加 !important 来强制覆盖全局 glass-box 的 padding，这是对齐的关键！ */
  padding: 0 !important; 
  margin-top: 0 !important; 
  overflow: hidden; 
  min-height: calc(100vh - 200px); 
  display: flex;
  flex-direction: column;
}

/* 顶部封面图与悬浮标题 */
.article-hero {
  position: relative;
  width: 100%;
  height: 300px;
}
.hero-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: brightness(0.8);
  /* 保证顶格后不会因为直角把外框的圆角覆盖住 */
  border-radius: 8px 8px 0 0; 
}
.hero-title-box {
  position: absolute;
  bottom: 20px;
  left: 30px;
  right: 30px;
  background: rgba(0, 0, 0, 0.5); 
  padding: 10px 20px;
  border-radius: 8px;
  backdrop-filter: blur(4px);
}
.hero-title {
  color: white;
  margin: 0;
  font-size: 2rem;
  font-weight: bold;
}

/* 元信息和框框样式 */
.article-meta {
  padding: 20px 30px 0;
  color: #666;
}
html.dark .article-meta { color: #aaa; }

/* 新增：让编辑按钮靠最右边显示 */
.tags-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  position: relative;
  width: 100%;
}
.edit-btn-wrapper {
  margin-left: auto; /* 核心魔法：把按钮推到最右边 */
}

.meta-row {
  display: flex;
  align-items: center;
  margin-bottom: 15px; 
}

.tags-row {
  flex-wrap: wrap;
  gap: 12px; 
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.95rem;
}
/* 给它下面的图标增加防糊 buff */
.meta-item .el-icon {
  font-size: 1.15rem;
  -webkit-font-smoothing: antialiased;
  transform: translateZ(0);
}

/* 分类和标签的统一框框基础样式 */
.meta-box {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 8px; 
  font-size: 0.85rem;
  font-weight: bold;
  transition: transform 0.3s;
  cursor: pointer;
}
.meta-box:hover {
  transform: translateY(-2px); 
}

/* 分类框专属样式 (黄色) */
.category-box {
  background: rgba(230, 162, 60, 0.1);
  color: #e6a23c;
  border: 1px solid rgba(230, 162, 60, 0.3);
}

/* 标签框专属样式 (绿色) */
.tag-box {
  background: rgba(103, 194, 58, 0.1);
  color: #67c23a;
  border: 1px solid rgba(103, 194, 58, 0.3);
}

/* 正文渲染区 */
.markdown-body {
  padding: 0 30px 30px;
  font-family: sans-serif; 
  font-size: 16px; 
  line-height: 1.8; 
  color: #333; 
  flex: 1; /* 让内容太少时，把点赞按钮自动推到最底部 */
}
html.dark .markdown-body { color: #ddd; }
.markdown-body :deep(pre) { background: #f6f8fa; padding: 15px; border-radius: 8px; overflow: auto; }
html.dark .markdown-body :deep(pre) { background: #2d2d2d; }
.markdown-body :deep(img) { max-width: 100%; border-radius: 8px; margin: 10px 0;}
.markdown-body :deep(blockquote) { border-left: 4px solid #409eff; margin: 0; padding-left: 15px; color: #666; background: rgba(64,158,255,0.05); padding: 10px 15px; border-radius: 0 4px 4px 0; }

.action-center { 
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px; /* 两个按钮的间距 */
  padding-bottom: 40px; 
}

.action-btn {
  font-weight: bold;
  font-size: 1.1rem;
  padding: 12px 30px;
  height: auto;
  transition: transform 0.2s, box-shadow 0.2s;
}
.action-btn:hover {
  transform: translateY(-2px) scale(1.05); /* 鼠标悬浮微微放大 */
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

/* 点赞外层包裹，用来做相对定位 */
.like-wrapper {
  position: relative;
}

/* 漂浮爱心的容器，定位���点赞按钮正上方 */
.hearts-container {
  position: absolute;
  bottom: 100%; /* 在按钮顶部 */
  left: 0;
  width: 100%;
  height: 100px;
  pointer-events: none; /* 让鼠标穿透，防止挡住按钮点击 */
  z-index: 10;
}

/* 每颗漂浮的爱心基础样式 */
.floating-heart {
  position: absolute;
  bottom: 0;
  transform: translateX(-50%); /* 因为我们在内联样式用了 left: 50%，这里拉回中心对齐 */
  opacity: 1;
}

/* Vue 的 transition-group 动画类名 (入场和离开过程) */
.heart-float-enter-active {
  animation: floatUp 1.5s ease-out forwards;
}
.heart-float-leave-active {
  opacity: 0;
  transition: opacity 0.3s;
}

/* 定义“向上飘散并渐渐消失”的关键帧动画 */
@keyframes floatUp {
  0% {
    bottom: 0;
    opacity: 1;
    transform: translateX(-50%) scale(0.5); /* 刚出现时有点小 */
  }
  50% {
    opacity: 1;
    transform: translateX(-50%) scale(1.2); /* 飘到一半放大 */
  }
  100% {
    bottom: 80px; /* 向上飘的高度 */
    opacity: 0;   /* 最终完全透明 */
    transform: translateX(-50%) scale(1);
  }
}

/* 上下篇导航 */
.prev-next-nav { display: flex; justify-content: space-between; gap: 20px; margin-top: 20px; }
.nav-item { flex: 1; padding: 20px; cursor: pointer; transition: transform 0.3s, box-shadow 0.3s; }
.nav-item:hover:not(.disabled) { transform: translateY(-3px); color: #409eff; }
.nav-item.disabled { cursor: not-allowed; opacity: 0.5; }
.nav-label { font-size: 0.85rem; color: #888; margin-bottom: 5px; }
.nav-title { font-size: 1.1rem; font-weight: bold; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* ================= 评论区风格样式 ================= */

/* 管理员姓名变红，管理员专属徽章 */
.author-area { display: flex; align-items: center; gap: 6px; }
.admin-name { color: #f56c6c !important; font-weight: bold; }
.admin-badge {
  color: #f56c6c; border: 1px solid #f56c6c; padding: 0 4px; 
  border-radius: 4px; font-size: 11px; transform: scale(0.9); transform-origin: left;
}

/* 置顶徽章 (橙色小框) */
.pinned-badge {
  color: #ff9800;          /* 字体改为橙色 */
  border: 1px solid #ff9800; /* 边框改为橙色 */
  padding: 0 4px;
  border-radius: 4px; 
  font-size: 11px; 
  margin-right: 6px; 
  vertical-align: middle; 
  display: inline-block;
}

/* 管理员工具栏：置顶图钉 */
.admin-tools { display: flex; align-items: center; gap: 10px; }
.pin-btn { cursor: pointer; font-size: 14px; filter: grayscale(100%); transition: all 0.3s; }
.is-pinned-icon { filter: grayscale(0%); transform: rotate(45deg); }

/* @用户 蓝色高亮 */
.blue-text { color: #00aeec; cursor: pointer; }
.reply-target { color: #666; margin-right: 5px; }

.comments-header-row {
  display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(0,0,0,0.1); padding-bottom: 10px; margin-bottom: 20px;
}
html.dark .comments-header-row { border-bottom-color: rgba(255,255,255,0.1); }
.sort-tabs span { cursor: pointer; color: #999; font-size: 14px; transition: color 0.3s; }
.sort-tabs span:hover, .sort-tabs span.active { color: #409eff; font-weight: bold; }
.sort-tabs .divider { margin: 0 10px; color: #ccc; cursor: default; }

.comment-input-footer {
  display: flex; justify-content: space-between; align-items: center; margin-top: 10px; position: relative;
}
.emoji-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}
.emoji-btn { font-size: 24px; color: #999; cursor: pointer; transition: color 0.3s; }
.emoji-btn:hover { color: #f56c6c; }
.emoji-picker {
  position: absolute;
  top: 35px;  /* 👈 核心修改：改为 top，在按钮的下方弹出 */
  left: 0;
  width: 260px; 
  height: 160px; 
  overflow-y: auto; 
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  padding: 10px;
  z-index: 1000; /* 调大层级，防止被下面的评论挡住 */
  border-radius: 8px;
  /* 加一点阴影，看起来更有立体悬浮感 */
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2); 
  background: var(--bg-color, rgba(255, 255, 255, 0.9)); /* 确保有背景色，不会透明混在一起 */
}
html.dark .emoji-picker {
  background: rgba(30, 30, 30, 0.95);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.5);
}

/* 隐藏系统默认的丑陋滚动条（变成类似手机的隐藏式，更好看） */
.emoji-picker::-webkit-scrollbar { width: 4px; }
.emoji-picker::-webkit-scrollbar-thumb { background-color: rgba(0, 0, 0, 0.2); border-radius: 4px; }
html.dark .emoji-picker::-webkit-scrollbar-thumb { background-color: rgba(255, 255, 255, 0.2); }

.emoji-picker span {
  font-size: 1.2rem;
  cursor: pointer;
  padding: 2px;
  transition: transform 0.2s;
}
.emoji-picker span:hover {
  transform: scale(1.3);
}

.comments-title { margin-bottom: 20px; font-size: 1.2rem; }

.comment-input-area { margin-bottom: 30px; }
.comment-toolbar { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  margin-top: 10px; 
}
.emoji-btn {
  font-size: 20px;
  color: #9499a0;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: color 0.3s;
}
.emoji-btn:hover {
  color: #409eff; /* 变成主色调蓝色 */
  transform: scale(1.1);
}
html.dark .emoji-btn:hover {
  color: #66b1ff;
}

.emoji-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
}
.emoji-item {
  font-size: 20px;
  cursor: pointer;
  text-align: center;
  transition: transform 0.2s;
}
.emoji-item:hover { transform: scale(1.3); }

.comments-section { padding: 30px; margin-top: 20px; }
.comment-btn-row { display: flex; justify-content: flex-end; }
.comment-list { margin-top: 30px; }

/* 主评论 */
.comment-item { display: flex; gap: 16px; margin-bottom: 20px; padding-bottom: 20px; border-bottom: 1px solid rgba(0,0,0,0.05); }
html.dark .comment-item { border-bottom-color: rgba(255,255,255,0.05); }

/* 子评论 (嵌套回复缩进) */
.sub-comments-list {
  background: rgba(0,0,0,0.02); border-radius: 8px; padding: 15px; margin-top: 10px;
}
html.dark .sub-comments-list { background: rgba(255,255,255,0.02); }
.sub-comment-item { display: flex; gap: 12px; margin-bottom: 15px; }
.sub-comment-item:last-child { margin-bottom: 0; }
.sub-content-box { flex: 1; display: flex; flex-direction: column; }

/* 蓝色的回复用户ID */
.reply-target { 
  color: #00aeec; 
  font-weight: 500; 
  margin-right: 5px; 
  font-size: 14px;
}

/* 展开收起按钮样式 */
.toggle-reply-btn {
  font-size: 13px; color: #00aeec; cursor: pointer; user-select: none;
  display: inline-block; margin-top: 5px; font-weight: 500;
}
.toggle-reply-btn:hover { text-decoration: underline; }

/* 修改置顶徽章的颜色（由原本的红色改为 B站同款低调橙或者主题蓝） */
.pin-badge {
  font-size: 12px;
  color: #ff7f24; /* 橙色 */
  border: 1px solid #ff7f24;
  border-radius: 4px;
  padding: 0 4px;
  margin-left: 8px;
  user-select: none;
}

/* 分页器样式 */
/* 分页器相关，重点恢复蓝色收起按钮 */
.pagination-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px dashed rgba(0,0,0,0.05);
  font-size: 13px;
  color: #9499a0;
}
html.dark .pagination-row { border-top-color: rgba(255,255,255,0.05); }
.page-info { margin-right: 5px; }
/* 顺便修复一下收起按钮为蓝色 */
.fold-btn { 
  margin-left: auto; /* 推到最右边 */
  color: #00aeec;    /* 强制设为蓝色 */
  cursor: pointer; 
  font-size: 13px; 
}
.fold-btn:hover { 
  text-decoration: underline; 
}

.page-btn { cursor: pointer; transition: color 0.2s; user-select: none; }
.page-btn:hover { color: #00aeec; }
.page-btn.disabled { color: #ccc; cursor: not-allowed; }
.page-num { cursor: pointer; padding: 2px 6px; border-radius: 4px; }
.page-num:hover { color: #00aeec; }
.page-num.active { color: #fff; background: #00aeec; }

/* 必须存在这个类，控制收起按钮居右且为蓝色 */
.collapse-btn {
  margin-left: auto;
  color: #00aeec;
  cursor: pointer;
  user-select: none;
  font-weight: 500;
}
.collapse-btn:hover { text-decoration: underline; }

/* 缩进背景调整 */
.sub-comments-list { margin-top: 10px; background: rgba(0,0,0,0.02); border-radius: 6px; padding: 12px; }
html.dark .sub-comments-list { background: rgba(255,255,255,0.02); }

.sub-comment-item { display: flex; gap: 10px; margin-bottom: 12px; }
.sub-comment-item:last-child { margin-bottom: 0; }
.sub-content-box { flex: 1; display: flex; flex-direction: column; }
.comment-avatar { cursor: pointer; flex-shrink: 0; }
.comment-content-box { flex: 1; display: flex; flex-direction: column; }

/* 头部昵称和删除 */
.comment-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.comment-author { font-weight: 500; font-size: 13px; color: #61666d; }
html.dark .comment-author { color: #999; }
.delete-comment-btn { color: #f56c6c; cursor: pointer; font-size: 16px; transition: transform 0.2s; }
.delete-comment-btn:hover { transform: scale(1.2); }

/* 正文与时间 */
.comment-text { font-size: 15px; line-height: 1.6; color: #18191c; margin-bottom: 10px; }
html.dark .comment-text { color: #e3e5e7; }

/* ======== 修改间距：极小间距和较小字体 ======== */
.comment-footer { display: flex; align-items: center; font-size: 12px; color: #9499a0; }
.comment-time { margin-right: 15px; }

/* ======== 修改间距：18px 缩小为 1px ======== */
.comment-actions { 
  display: flex; 
  align-items: center; 
  gap: 12px; /* 进一步缩小间距 */
}

/* 2. 重置按钮自身的隐藏宽度 */
.action-btn { 
  display: inline-flex; 
  align-items: center; 
  cursor: pointer; 
  transition: color 0.2s; 
  color: #9499a0; 
  
  /* 强制清空可能继承的 padding 和 margin，防止被撑大 */
  margin: 0 !important; 
  padding: 0 !important; 
  background: transparent;
  border: none;
}

.action-btn:hover { color: #00aeec; }
.action-btn:hover svg { fill: #00aeec !important; }

.action-btn svg {
  margin-right: 4px; /* 让图标和旁边的数字/文字保持一点点距离 */
}

.action-btn .num { 
  font-size: 13px; 
  font-weight: 500; 
  user-select: none; 
  margin: 0 !important; /* 清空可能存在的旧 margin */
}

/* 专门把“回复”两个字的字号调小 */
.reply-text-btn { 
  font-size: 13px; 
  margin: 0 !important; /* 清空边距 */
}
.active-blue { color: #00aeec !important; }

.active-like { color: #00aeec !important; }

/* 大拇指图标稍微比时间字体大一点 (15px) */
.thumb-icon { font-size: 15px; margin-right: 3px; }
.action-num { font-size: 13px; font-weight: 500; }
.active-blue { color: #00aeec !important; }

/* 回复输入框容器 */
.reply-input-area { margin-top: 10px; }
.custom-reply-input :deep(textarea) { font-size: 14px; }

.reply-input-box {
  margin-top: 15px;
  background: rgba(0,0,0,0.02);
  padding: 15px;
  border-radius: 8px;
}
html.dark .reply-input-box { background: rgba(255,255,255,0.05); }

/* 激活状态的点赞/踩颜色 */
.active-like { color: #00aeec !important; }

.action-text { margin-left: 4px; }
.reply-btn:hover { color: #00aeec; }

/* 自定义粉色编辑按钮 */
.pink-edit-btn {
  background: linear-gradient(135deg, #ff79c6, #ff9a9e);
  border: none;
  color: #fff;
  font-weight: bold;
  box-shadow: 0 4px 15px rgba(255, 121, 198, 0.4);
  transition: all 0.3s;
}
.pink-edit-btn:hover {
  background: linear-gradient(135deg, #ff9a9e, #ff79c6);
  box-shadow: 0 6px 20px rgba(255, 121, 198, 0.6);
  transform: translateY(-2px);
  color: #fff;
}

/* ================= 手机端阅读页适配 ================= */
@media screen and (max-width: 768px) {
  /* 缩小正文外框的留白 */
  .markdown-body {
    padding: 0 15px 15px !important;
    font-size: 15px !important; /* 字体稍微缩小提升阅读性 */
  }
  .article-meta {
    padding: 15px 15px 0 !important;
  }
  /* 缩小顶部图片上悬浮的标题 */
  .hero-title-box {
    left: 15px !important;
    right: 15px !important;
    bottom: 15px !important;
    padding: 8px 15px !important;
  }
  .hero-title {
    font-size: 1.4rem !important;
  }
  /* 底部按钮稍微放小 */
  .action-btn {
    padding: 10px 20px !important;
    font-size: 1rem !important;
  }
}

/* 踩大拇指翻转 */
.flip-icon svg { transform: rotate(180deg); }

/* 图标整体变大一点，数字变大一点，对齐文本 */
.action-btn {
  display: flex;
  align-items: center;
  cursor: pointer;
  transition: color 0.2s;
  color: #9499a0;
}
.action-btn svg {
  margin-top: 2px; /* 微调图标对齐 */
  transition: fill 0.3s;
}
.action-btn:hover svg {
  fill: #00aeec !important; /* 悬浮时 SVG 变蓝 */
}
.action-btn:hover .action-text {
  color: #00aeec;
}

.action-text {
  margin-left: 6px;
  font-size: 14px; /* 比时间的 13px 稍微大一点点 */
  font-weight: 500;
  user-select: none;
}



</style>