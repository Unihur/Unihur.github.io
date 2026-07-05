<script setup>
// 文章详情页：Markdown 渲染 / TOC 目录 / 点赞分享 / B站式两级评论
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Calendar,
  Folder,
  PriceTag,
  Share,
  Edit,
  View,
  UserFilled,
  Delete,
  PictureRounded,
  ArrowDownBold
} from '@element-plus/icons-vue'

import { md, extractToc } from '@/utils/markdown'

import ProfileCard from '@/components/ProfileCard.vue'

import { useSiteStore } from '@/stores/site'
import { useUserStore } from '@/stores/user'
import { useTypewriter } from '@/composables/useTypewriter'

import { getArticle, likeArticle, shareArticle, listArticles } from '@/api/article'
import {
  listComments,
  createComment,
  deleteComment,
  pinComment,
  commentAction
} from '@/api/comment'

const route = useRoute()
const router = useRouter()
const siteStore = useSiteStore()
const userStore = useUserStore()
const { typewriterText } = useTypewriter(() => siteStore.siteConfig.signature)

// 管理员用户名（用于在评论区高亮管理员评论）；通过环境变量配置，避免硬编码
const ADMIN_USERNAME = import.meta.env.VITE_ADMIN_USERNAME || ''

// ===== 文章数据 =====
const article = ref(null)
const renderedHtml = ref('')
const prevPost = ref(null)
const nextPost = ref(null)
const isLoading = ref(true)
const likes = ref(0)
const shares = ref(0)
const floatingHearts = ref([])
let heartIdCounter = 0

const allArticles = ref([]) // 用于侧栏总浏览量统计

// ===== TOC =====
const tocList = ref([])

// ===== 评论相关 =====
const newComment = ref('')
const replyContent = ref('')
const activeReplyId = ref(null)
const rootComments = ref([])
const sortBy = ref('time')
const showEmojiPicker = ref(false)
const showReplyEmojiPicker = ref(false)

// 表情包库
const emojis = [
  '😀',
  '😂',
  '🤣',
  '😍',
  '😒',
  '😘',
  '😁',
  '😉',
  '😎',
  '😊',
  '🤔',
  '🙄',
  '🤨',
  '😑',
  '🤐',
  '😪',
  '😫',
  '🥱',
  '😴',
  '😛',
  '😜',
  '😝',
  '🤤',
  '😓',
  '😔',
  '😕',
  '🙃',
  '🤑',
  '😲',
  '☹️',
  '🙁',
  '😖',
  '😞',
  '😟',
  '😤',
  '😢',
  '😭',
  '😦',
  '😧',
  '😨',
  '😩',
  '🤯',
  '😬',
  '😰',
  '😱',
  '🥵',
  '🥶',
  '😳',
  '🤪',
  '😵',
  '😡',
  '😠',
  '🤬',
  '😷',
  '🤒',
  '🤕',
  '🤢',
  '🤮',
  '🤧',
  '😇',
  '🥳',
  '🥺',
  '🤠',
  '🤡',
  '🤥',
  '🤫',
  '🤭',
  '🧐',
  '🤓',
  '😈',
  '👿',
  '👹',
  '👺',
  '💀',
  '👻',
  '👽',
  '🤖',
  '💩',
  '😺',
  '😸',
  '😹',
  '😻',
  '😼',
  '😽',
  '🙀',
  '😿',
  '😾',
  '🙏',
  '👍',
  '🔥',
  '❤️',
  '✨',
  '🎉',
  '😅',
  '👀'
]

// ===== 点赞（合并特效 + 后端请求）=====
const handleLike = async () => {
  // 乐观更新
  likes.value++

  // 爱心特效
  const newHeart = {
    id: heartIdCounter++,
    size: Math.random() * 10 + 15,
    color: ['#ff79c6', '#ff4d4f', '#f56c6c', '#e0b0ff', '#ff6b81'][Math.floor(Math.random() * 5)],
    leftOffset: (Math.random() - 0.5) * 40
  }
  floatingHearts.value.push(newHeart)
  setTimeout(() => {
    floatingHearts.value = floatingHearts.value.filter((h) => h.id !== newHeart.id)
  }, 1500)

  // 后端记录
  try {
    if (article.value?.slug) await likeArticle(article.value.slug)
  } catch (error) {
    console.error('点赞保存到后端失败:', error)
  }
}

// ===== TOC 生成：等 DOM 更新完再读取标题 =====
async function generateTOC() {
  // 第一次 nextTick：等 renderedHtml 赋值后的 DOM 刷新
  await nextTick()
  let container = document.querySelector('.markdown-body')
  // 兜底：若容器仍未渲染（例如 isLoading 刚切换的边缘情况），再等一帧
  if (!container) {
    await nextTick()
    container = document.querySelector('.markdown-body')
  }
  tocList.value = extractToc(container)
}

const scrollToAnchor = (id) => {
  const element = document.getElementById(id)
  if (element) {
    const top = element.offsetTop - 80
    window.scrollTo({ top, behavior: 'smooth' })
  }
}

// 跳转到评论区
const scrollToComments = () => {
  const target = document.querySelector('.comments-section')
  if (target) {
    const top = target.offsetTop - 80
    window.scrollTo({ top, behavior: 'smooth' })
  }
}

// ===== 分享（兼容 HTTP / HTTPS）=====
const handleShare = async () => {
  const url = window.location.href
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(url)
  } else {
    // HTTP 降级
    const textArea = document.createElement('textarea')
    textArea.value = url
    textArea.style.position = 'absolute'
    textArea.style.left = '-999999px'
    document.body.prepend(textArea)
    textArea.select()
    try {
      document.execCommand('copy')
    } catch (err) {
      console.error('复制失败', err)
    } finally {
      textArea.remove()
    }
  }
  ElMessage.success('🔗 链接已复制！感谢你的分享~')
  shares.value++
  try {
    if (article.value?.slug) await shareArticle(article.value.slug)
  } catch (error) {
    console.error('转发保存到后端失败:', error)
  }
}

// ===== 评论：拉取并组装 B站两级树形结构 =====
const loadComments = async (slug) => {
  try {
    const res = await listComments(slug)
    const flatList = res.data
    const map = {}
    const roots = []

    flatList.forEach((c) => {
      c.children = []
      c.isLiked = c.userAction === 'like'
      c.isDisliked = c.userAction === 'dislike'
      c.avatar = c.avatar || ''
      map[c.id] = c
    })

    flatList.forEach((c) => {
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

    roots.forEach((root) => {
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

const toggleReplies = (root) => {
  root.isExpanded = !root.isExpanded
  if (!root.isExpanded) root.currentPage = 1
}

const getPagedChildren = (root) => {
  const start = (root.currentPage - 1) * root.pageSize
  return root.children.slice(start, start + root.pageSize)
}

const changePage = (root, delta) => {
  const maxPage = Math.ceil(root.children.length / root.pageSize)
  root.currentPage += delta
  if (root.currentPage < 1) root.currentPage = 1
  if (root.currentPage > maxPage) root.currentPage = maxPage
}

const goToPage = (root, page) => {
  root.currentPage = page
}

const showReplyBox = (commentId) => {
  activeReplyId.value = activeReplyId.value === commentId ? null : commentId
  replyContent.value = ''
  showReplyEmojiPicker.value = false
}

// ===== 拉取文章详情 =====
const fetchArticle = async (slug) => {
  isLoading.value = true
  try {
    const res = await getArticle(slug)

    // 兼容新旧两版 API：{ article, prev, next } 或直接数据
    const data = res.data
    const articleData = data.article || data

    if (articleData && articleData.title) {
      article.value = articleData
      likes.value = articleData.likes || 0
      shares.value = articleData.shares || 0
      prevPost.value = data.prev || null
      nextPost.value = data.next || null

      renderedHtml.value = md.render(article.value.content || '*无内容*')
      document.title = `${article.value.title} - UniHur's Blog`

      // 清空旧目录
      tocList.value = []

      // 关键：先把 isLoading 置 false，让 v-else-if="article" 分支渲染出 .markdown-body，
      // 再调 generateTOC（内部 await nextTick 等 DOM 刷新后读取标题）
      isLoading.value = false
      await generateTOC()

      // 后端访问该文章时浏览量已自增；这里同步拉取全站列表用于侧栏总浏览量
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

const fetchAllArticlesForStats = async () => {
  try {
    const res = await listArticles()
    allArticles.value = res.data
  } catch (error) {
    console.error('获取所有文章列表失败:', error)
  }
}

// 监听路由参数变化（上一篇 / 下一篇切换）
watch(
  () => route.params.slug,
  (newSlug) => {
    if (newSlug) {
      tocList.value = []
      fetchArticle(newSlug)
      loadComments(newSlug)
    }
  }
)

// ===== 点击空白处关闭表情包 =====
const handleOutsideClick = (e) => {
  if (!e.target.closest('.emoji-wrapper')) {
    showEmojiPicker.value = false
    showReplyEmojiPicker.value = false
  }
}

// ===== 跨标签页同步用户名（修复原代码在 setup 顶层注册、从不解绑的内存泄漏）=====
const handleStorage = (e) => {
  if (e.key === 'username' || e.key === null) {
    // userStore 已经读取 localStorage；这里仅在退出/切换时让组件感知
  }
}

onMounted(() => {
  document.addEventListener('click', handleOutsideClick)
  window.addEventListener('storage', handleStorage)

  fetchArticle(route.params.slug)
  loadComments(route.params.slug)
})

onUnmounted(() => {
  document.removeEventListener('click', handleOutsideClick)
  window.removeEventListener('storage', handleStorage)
})

// ===== 发布评论 / 回复（统一接口）=====
const submitComment = async (parentId = null) => {
  let content = parentId ? replyContent.value : newComment.value

  // 去掉自动生成的“回复 @xxx：”前缀，保持数据库纯净
  const replyPrefixRegex = /^回复\s*@[^\s：]+：/
  content = content.replace(replyPrefixRegex, '').trim()

  if (!content) return ElMessage.warning('内容不能为空')

  const authorName = userStore.username || '游客'
  try {
    await createComment({
      article_slug: route.params.slug,
      author: authorName,
      content,
      parent_id: parentId
    })
    ElMessage.success('发布成功')

    if (parentId) {
      replyContent.value = ''
      activeReplyId.value = null
      // 找到对应根节点并展开到最后一页
      const targetRoot = rootComments.value.find(
        (r) => r.id === parentId || r.children.some((c) => c.id === parentId)
      )
      if (targetRoot) {
        targetRoot.isExpanded = true
        targetRoot.currentPage = Math.ceil((targetRoot.children.length + 1) / targetRoot.pageSize)
      }
    } else {
      newComment.value = ''
    }

    await loadComments(route.params.slug)
  } catch (e) {
    ElMessage.error('评论失败')
  }
}

const canDelete = (commentAuthor) => {
  return userStore.isAdmin || userStore.username === commentAuthor
}

const handleDeleteComment = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这条评论吗？', '删除确认', { type: 'warning' })
    await deleteComment(id)
    ElMessage.success('删除成功')
    loadComments(route.params.slug)
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('权限不足或网络错误')
  }
}

const handlePinComment = async (id) => {
  try {
    await pinComment(id)
    ElMessage.success('操作成功')
    loadComments(route.params.slug)
  } catch (e) {
    ElMessage.error('权限不足或网络错误')
  }
}

// 互斥点赞 / 点踩
const handleCommentAction = async (comment, action) => {
  if (!userStore.isLoggedIn) return ElMessage.warning('请先登录再操作')
  try {
    const res = await commentAction(comment.id, action)
    comment.likes = res.data.likes
    comment.dislikes = res.data.dislikes
    comment.isLiked = res.data.userAction === 'like'
    comment.isDisliked = res.data.userAction === 'dislike'
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

const insertEmoji = (emoji, isReply = false) => {
  if (isReply) {
    replyContent.value += emoji
    showReplyEmojiPicker.value = false
  } else {
    newComment.value += emoji
    showEmojiPicker.value = false
  }
}

const changeSort = (mode) => {
  sortBy.value = mode
  sortCommentsTree()
}

const sortCommentsTree = () => {
  if (sortBy.value === 'hot') {
    rootComments.value.sort((a, b) => {
      if (a.is_pinned !== b.is_pinned) return a.is_pinned ? -1 : 1
      return b.likes - a.likes
    })
  } else {
    rootComments.value.sort((a, b) => {
      if (a.is_pinned !== b.is_pinned) return a.is_pinned ? -1 : 1
      return new Date(b.time) - new Date(a.time)
    })
  }
  rootComments.value.forEach((root) => {
    root.children.sort((a, b) => new Date(a.time) - new Date(b.time))
  })
}

const editArticle = () => {
  router.push(`/write?slug=${article.value.slug}`)
}

const navigateTo = (slug) => {
  router.push(`/post/${slug}`)
}
</script>

<template>
  <div class="article-detail-container">
    <!-- Banner（与首页一致） -->
    <header
      v-if="siteStore.bannerMode !== 'hidden'"
      :class="['banner', siteStore.bannerMode]"
      :style="{ height: siteStore.bannerWrapperHeight }"
    >
      <el-carousel
        :interval="4000"
        arrow="always"
        class="banner-carousel"
        :height="siteStore.carouselHeight"
      >
        <el-carousel-item v-for="(img, index) in siteStore.bannerImages" :key="index">
          <img :src="img" class="carousel-img" alt="banner" />
        </el-carousel-item>
      </el-carousel>

      <div v-if="siteStore.bannerMode === 'background'" class="banner-overlay"></div>

      <h1 v-if="siteStore.bannerMode !== 'background'" class="blog-title">
        {{ siteStore.siteConfig.name }}'s Blog
        <p class="blog-subtitle">{{ typewriterText }}<span class="cursor">|</span></p>
      </h1>

      <div
        v-if="siteStore.bannerMode === 'banner' || siteStore.bannerMode === 'fullscreen'"
        class="waves-container"
      >
        <svg
          class="waves"
          xmlns="http://www.w3.org/2000/svg"
          xmlns:xlink="http://www.w3.org/1999/xlink"
          viewBox="0 24 150 28"
          preserveAspectRatio="none"
        >
          <defs>
            <path
              id="gentle-wave"
              d="M-160 44c30 0 58-18 88-18s 58 18 88 18 58-18 88-18 58 18 88 18 v44h-352z"
            />
          </defs>
          <g class="parallax">
            <use xlink:href="#gentle-wave" x="48" y="0" class="wave wave1" />
            <use xlink:href="#gentle-wave" x="48" y="3" class="wave wave2" />
            <use xlink:href="#gentle-wave" x="48" y="5" class="wave wave3" />
            <use xlink:href="#gentle-wave" x="48" y="7" class="wave wave4" />
          </g>
        </svg>
      </div>
    </header>

    <!-- 主体内容 -->
    <div
      class="main-content-wrapper"
      :style="{ paddingTop: siteStore.contentPaddingTop, marginTop: siteStore.contentMarginTop }"
    >
      <div
        v-if="isLoading"
        class="glass-box"
        style="padding: 50px; text-align: center; margin-top: 20px"
      >
        <h2>拼命加载文章中...</h2>
      </div>

      <el-row v-else-if="article" :gutter="20">
        <!-- 左侧栏 -->
        <el-col :xs="24" :md="6">
          <ProfileCard :articles="allArticles" />

          <div v-if="tocList.length > 0" class="glass-box toc-box">
            <h3>📖 文章目录</h3>
            <ul class="toc-list">
              <li
                v-for="item in tocList"
                :key="item.id"
                :style="{ paddingLeft: (item.level - 1) * 15 + 'px' }"
              >
                <a href="#" @click.prevent="scrollToAnchor(item.id)">{{ item.text }}</a>
              </li>
            </ul>
            <!-- 跳转到评论区箭头：在目录矩形内部底部，随 .toc-box 一起 sticky 吸顶 -->
            <div class="toc-comment-btn-wrapper">
              <el-tooltip content="前往评论区" placement="bottom">
                <el-icon class="toc-comment-arrow" @click="scrollToComments">
                  <ArrowDownBold />
                </el-icon>
              </el-tooltip>
            </div>
          </div>
        </el-col>

        <!-- 右侧：文章 -->
        <el-col :xs="24" :md="18">
          <div class="glass-box article-main-card">
            <!-- 顶部封面图 + 标题 -->
            <div class="article-hero">
              <img :src="article.cover || '/banner/1.png'" class="hero-img" />
              <div class="hero-title-box">
                <h1 class="hero-title">{{ article.title }}</h1>
              </div>
            </div>

            <!-- 元信息 -->
            <div class="article-meta">
              <div class="meta-row" style="gap: 20px">
                <div class="meta-item time">
                  <el-icon><Calendar /></el-icon>
                  <span>发布于: {{ new Date(article.publishTime).toLocaleDateString() }}</span>
                </div>
                <div class="meta-item views">
                  <el-icon><View /></el-icon>
                  <span>浏览: {{ article.views || 0 }}</span>
                </div>
              </div>

              <div
                v-if="
                  article.category || (article.tags && article.tags.length > 0) || userStore.isAdmin
                "
                class="meta-row tags-row"
              >
                <div v-if="article.category" class="meta-box category-box">
                  <el-icon><Folder /></el-icon>
                  <span>{{ article.category }}</span>
                </div>
                <template v-if="article.tags && article.tags.length > 0">
                  <div v-for="tag in article.tags" :key="tag" class="meta-box tag-box">
                    <el-icon><PriceTag /></el-icon>
                    <span>{{ tag }}</span>
                  </div>
                </template>
                <div v-if="userStore.isAdmin" class="edit-btn-wrapper">
                  <el-button round size="small" class="pink-edit-btn" @click="editArticle">
                    <el-icon><Edit /></el-icon> 编辑文章
                  </el-button>
                </div>
              </div>
            </div>

            <el-divider border-style="dashed" />

            <!-- 正文 -->
            <div class="markdown-body" v-html="renderedHtml"></div>

            <!-- 点赞 / 分享 -->
            <div class="action-center">
              <div class="like-wrapper">
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

                <el-button
                  type="danger"
                  plain
                  round
                  size="large"
                  class="action-btn"
                  @click="handleLike"
                >
                  ❤️ 点赞 ({{ likes }})
                </el-button>
              </div>

              <el-button
                type="primary"
                plain
                round
                size="large"
                class="action-btn"
                @click="handleShare"
              >
                <el-icon style="margin-right: 5px"><Share /></el-icon> 分享文章 ({{ shares }})
              </el-button>
            </div>
          </div>

          <!-- 上一篇 / 下一篇 -->
          <div class="prev-next-nav">
            <div
              class="nav-item prev glass-box"
              :class="{ disabled: !prevPost }"
              @click="prevPost ? navigateTo(prevPost.slug) : null"
            >
              <div class="nav-label">上一篇</div>
              <div class="nav-title">{{ prevPost ? prevPost.title : '没有了' }}</div>
            </div>
            <div
              class="nav-item next glass-box"
              :class="{ disabled: !nextPost }"
              @click="nextPost ? navigateTo(nextPost.slug) : null"
            >
              <div class="nav-label" style="text-align: right">下一篇</div>
              <div class="nav-title" style="text-align: right">
                {{ nextPost ? nextPost.title : '没有了' }}
              </div>
            </div>
          </div>

          <!-- 评论区 -->
          <div class="glass-box comments-section">
            <div class="comments-header-row">
              <h3>💬 评论区</h3>
              <div class="sort-tabs">
                <span :class="{ active: sortBy === 'hot' }" @click="changeSort('hot')">最热</span>
                <span class="divider">|</span>
                <span :class="{ active: sortBy === 'time' }" @click="changeSort('time')">最新</span>
              </div>
            </div>

            <!-- 主输入区 -->
            <div class="comment-input">
              <el-input
                v-model="newComment"
                type="textarea"
                :rows="3"
                placeholder="写下你的评论..."
              />
              <div class="comment-input-footer">
                <div class="emoji-wrapper">
                  <el-icon class="emoji-btn" @click="showEmojiPicker = !showEmojiPicker"
                    ><PictureRounded
                  /></el-icon>
                  <div v-if="showEmojiPicker" class="emoji-picker glass-box">
                    <span v-for="e in emojis" :key="e" @click="insertEmoji(e, false)">{{ e }}</span>
                  </div>
                </div>
                <el-button type="primary" @click="submitComment(null)">发表评论</el-button>
              </div>
            </div>

            <div class="comment-list">
              <div v-for="comment in rootComments" :key="comment.id" class="comment-item">
                <el-avatar
                  :src="comment.avatar || ''"
                  :icon="comment.avatar ? '' : UserFilled"
                  :size="48"
                  class="comment-avatar"
                />

                <div class="comment-content-box">
                  <div class="comment-header">
                    <div class="author-area">
                      <span
                        class="comment-author"
                        :class="{ 'admin-name': comment.author === ADMIN_USERNAME }"
                        >{{ comment.author }}</span
                      >
                      <!-- 自定义称号：优先显示后端返回的 author_title；
                           没有称号但作者是管理员时，回退显示默认"管理员" -->
                      <span
                        v-if="comment.author_title"
                        class="user-title-badge"
                        :style="{
                          color: comment.author_title_color || '#f56c6c',
                          borderColor: comment.author_title_color || '#f56c6c'
                        }"
                        >{{ comment.author_title }}</span
                      >
                      <span v-else-if="comment.author === ADMIN_USERNAME" class="admin-badge"
                        >管理员</span
                      >
                    </div>

                    <div v-if="userStore.isAdmin" class="admin-tools">
                      <el-tooltip
                        :content="comment.is_pinned ? '取消置顶' : '置顶评论'"
                        placement="top"
                      >
                        <span
                          class="pin-btn"
                          :class="{ 'is-pinned-icon': comment.is_pinned }"
                          @click="handlePinComment(comment.id)"
                          >📌</span
                        >
                      </el-tooltip>
                      <el-tooltip content="删除该评论" placement="top">
                        <el-icon class="delete-comment-btn" @click="handleDeleteComment(comment.id)"
                          ><Delete
                        /></el-icon>
                      </el-tooltip>
                    </div>
                    <el-icon
                      v-else-if="canDelete(comment.author)"
                      class="delete-comment-btn"
                      @click="handleDeleteComment(comment.id)"
                      ><Delete
                    /></el-icon>
                  </div>

                  <div class="comment-text">
                    <span v-if="comment.is_pinned" class="pinned-badge">置顶</span>
                    {{ comment.content }}
                  </div>

                  <div class="comment-footer">
                    <span class="comment-time">{{ comment.time }}</span>
                    <div class="comment-actions">
                      <span
                        class="action-btn"
                        :class="{ 'active-blue': comment.isLiked }"
                        @click="handleCommentAction(comment, 'like')"
                      >
                        <svg
                          viewBox="0 0 1024 1024"
                          width="14"
                          height="14"
                          :fill="comment.isLiked ? '#00aeec' : '#9499a0'"
                        >
                          <path
                            d="M853.333333 469.333333h-190.293333l40.96-193.28c4.693333-22.186667-2.133333-45.653333-17.92-62.293333-14.506667-15.36-35.413333-23.466667-56.746667-22.186667l-35.84 2.56-258.133333 300.373334V853.333333h384c24.746667 0 46.933333-16.64 53.333333-40.533333l71.68-256c5.546667-19.626667-0.426667-40.533333-14.933333-55.04-14.933333-14.933333-35.413333-23.466667-56.746667-23.466666zM256 853.333333H128c-23.466667 0-42.666667-19.2-42.666667-42.666666V512c0-23.466667 19.2-42.666667 42.666667-42.666667h128c23.466667 0 42.666667 19.2 42.666667 42.666667v298.666667c0 23.466667-19.2 42.666667-42.666667 42.666666z"
                          ></path>
                        </svg>
                        <span class="num">{{ comment.likes || '' }}</span>
                      </span>
                      <span
                        class="action-btn flip-icon"
                        :class="{ 'active-blue': comment.isDisliked }"
                        @click="handleCommentAction(comment, 'dislike')"
                      >
                        <svg
                          viewBox="0 0 1024 1024"
                          width="14"
                          height="14"
                          :fill="comment.isDisliked ? '#00aeec' : '#9499a0'"
                        >
                          <path
                            d="M853.333333 469.333333h-190.293333l40.96-193.28c4.693333-22.186667-2.133333-45.653333-17.92-62.293333-14.506667-15.36-35.413333-23.466667-56.746667-22.186667l-35.84 2.56-258.133333 300.373334V853.333333h384c24.746667 0 46.933333-16.64 53.333333-40.533333l71.68-256c5.546667-19.626667-0.426667-40.533333-14.933333-55.04-14.933333-14.933333-35.413333-23.466667-56.746667-23.466666zM256 853.333333H128c-23.466667 0-42.666667-19.2-42.666667-42.666666V512c0-23.466667 19.2-42.666667 42.666667-42.666667h128c23.466667 0 42.666667 19.2 42.666667 42.666667v298.666667c0 23.466667-19.2 42.666667-42.666667 42.666666z"
                          ></path>
                        </svg>
                      </span>
                      <span
                        class="action-btn reply-text-btn"
                        @click="
                          () => {
                            showReplyBox(comment.id)
                            replyContent = `回复 @${comment.author}： `
                          }
                        "
                        >回复</span
                      >
                    </div>
                  </div>

                  <!-- 回复输入框 -->
                  <div v-if="activeReplyId === comment.id" class="reply-input-area">
                    <el-input
                      v-model="replyContent"
                      type="textarea"
                      :rows="2"
                      class="custom-reply-input"
                    />
                    <div class="comment-input-footer">
                      <div class="emoji-wrapper">
                        <el-icon
                          class="emoji-btn"
                          @click="showReplyEmojiPicker = !showReplyEmojiPicker"
                          ><PictureRounded
                        /></el-icon>
                        <div v-if="showReplyEmojiPicker" class="emoji-picker glass-box">
                          <span v-for="e in emojis" :key="e" @click="insertEmoji(e, true)">{{
                            e
                          }}</span>
                        </div>
                      </div>
                      <div>
                        <el-button size="small" @click="activeReplyId = null">取消</el-button>
                        <el-button type="primary" size="small" @click="submitComment(comment.id)"
                          >发送</el-button
                        >
                      </div>
                    </div>
                  </div>

                  <!-- 子评论 -->
                  <div
                    v-if="comment.children && comment.children.length > 0"
                    class="sub-comments-list"
                  >
                    <div
                      v-if="!comment.isExpanded"
                      class="toggle-reply-btn"
                      @click="toggleReplies(comment)"
                    >
                      共 {{ comment.children.length }} 条回复，点击查看
                    </div>

                    <div v-else>
                      <div
                        v-for="child in getPagedChildren(comment)"
                        :key="child.id"
                        class="sub-comment-item"
                      >
                        <el-avatar
                          :src="child.avatar || ''"
                          :icon="child.avatar ? '' : UserFilled"
                          :size="32"
                          class="comment-avatar"
                        />
                        <div class="sub-content-box">
                          <div class="comment-header">
                            <div class="author-area">
                              <span
                                class="comment-author"
                                :class="{ 'admin-name': child.author === ADMIN_USERNAME }"
                                >{{ child.author }}</span
                              >
                              <span
                                v-if="child.author_title"
                                class="user-title-badge"
                                :style="{
                                  color: child.author_title_color || '#f56c6c',
                                  borderColor: child.author_title_color || '#f56c6c'
                                }"
                                >{{ child.author_title }}</span
                              >
                              <span v-else-if="child.author === ADMIN_USERNAME" class="admin-badge"
                                >管理员</span
                              >
                            </div>
                            <el-icon
                              v-if="canDelete(child.author)"
                              class="delete-comment-btn"
                              @click="handleDeleteComment(child.id)"
                              ><Delete
                            /></el-icon>
                          </div>

                          <div class="comment-text">
                            <span
                              v-if="child.replyToAuthor && child.replyToAuthor !== comment.author"
                              class="reply-target"
                            >
                              回复 <span class="blue-text">@{{ child.replyToAuthor }}</span
                              >：
                            </span>
                            {{ child.content }}
                          </div>

                          <div class="comment-footer">
                            <span class="comment-time">{{ child.time }}</span>
                            <div class="comment-actions">
                              <span
                                class="action-btn"
                                :class="{ 'active-blue': child.isLiked }"
                                @click="handleCommentAction(child, 'like')"
                              >
                                <svg
                                  viewBox="0 0 1024 1024"
                                  width="14"
                                  height="14"
                                  :fill="child.isLiked ? '#00aeec' : '#9499a0'"
                                >
                                  <path
                                    d="M853.333333 469.333333h-190.293333l40.96-193.28c4.693333-22.186667-2.133333-45.653333-17.92-62.293333-14.506667-15.36-35.413333-23.466667-56.746667-22.186667l-35.84 2.56-258.133333 300.373334V853.333333h384c24.746667 0 46.933333-16.64 53.333333-40.533333l71.68-256c5.546667-19.626667-0.426667-40.533333-14.933333-55.04-14.933333-14.933333-35.413333-23.466667-56.746667-23.466666zM256 853.333333H128c-23.466667 0-42.666667-19.2-42.666667-42.666666V512c0-23.466667 19.2-42.666667 42.666667-42.666667h128c23.466667 0 42.666667 19.2 42.666667 42.666667v298.666667c0 23.466667-19.2 42.666667-42.666667 42.666666z"
                                  ></path>
                                </svg>
                                <span class="num">{{ child.likes || '' }}</span>
                              </span>
                              <span
                                class="action-btn flip-icon"
                                :class="{ 'active-blue': child.isDisliked }"
                                @click="handleCommentAction(child, 'dislike')"
                              >
                                <svg
                                  viewBox="0 0 1024 1024"
                                  width="14"
                                  height="14"
                                  :fill="child.isDisliked ? '#00aeec' : '#9499a0'"
                                >
                                  <path
                                    d="M853.333333 469.333333h-190.293333l40.96-193.28c4.693333-22.186667-2.133333-45.653333-17.92-62.293333-14.506667-15.36-35.413333-23.466667-56.746667-22.186667l-35.84 2.56-258.133333 300.373334V853.333333h384c24.746667 0 46.933333-16.64 53.333333-40.533333l71.68-256c5.546667-19.626667-0.426667-40.533333-14.933333-55.04-14.933333-14.933333-35.413333-23.466667-56.746667-23.466666zM256 853.333333H128c-23.466667 0-42.666667-19.2-42.666667-42.666666V512c0-23.466667 19.2-42.666667 42.666667-42.666667h128c23.466667 0 42.666667 19.2 42.666667 42.666667v298.666667c0 23.466667-19.2 42.666667-42.666667 42.666666z"
                                  ></path>
                                </svg>
                              </span>
                              <span
                                class="action-btn reply-text-btn"
                                @click="
                                  () => {
                                    showReplyBox(child.id)
                                    replyContent = `回复 @${child.author}： `
                                  }
                                "
                                >回复</span
                              >
                            </div>
                          </div>

                          <div v-if="activeReplyId === child.id" class="reply-input-area">
                            <el-input
                              v-model="replyContent"
                              type="textarea"
                              :rows="2"
                              class="custom-reply-input"
                            />
                            <div class="comment-input-footer">
                              <div class="emoji-wrapper">
                                <el-icon
                                  class="emoji-btn"
                                  @click="showReplyEmojiPicker = !showReplyEmojiPicker"
                                  ><PictureRounded
                                /></el-icon>
                                <div v-if="showReplyEmojiPicker" class="emoji-picker glass-box">
                                  <span
                                    v-for="e in emojis"
                                    :key="e"
                                    @click="insertEmoji(e, true)"
                                    >{{ e }}</span
                                  >
                                </div>
                              </div>
                              <div>
                                <el-button size="small" @click="activeReplyId = null"
                                  >取消</el-button
                                >
                                <el-button
                                  type="primary"
                                  size="small"
                                  @click="submitComment(comment.id)"
                                  >发送</el-button
                                >
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>

                      <!-- 分页 -->
                      <div class="pagination-row">
                        <span class="page-info"
                          >共 {{ Math.ceil(comment.children.length / comment.pageSize) }} 页</span
                        >
                        <span
                          class="page-btn"
                          :class="{ disabled: comment.currentPage === 1 }"
                          @click="changePage(comment, -1)"
                          >上一页</span
                        >
                        <span
                          v-for="p in Math.ceil(comment.children.length / comment.pageSize)"
                          :key="p"
                          class="page-num"
                          :class="{ active: comment.currentPage === p }"
                          @click="goToPage(comment, p)"
                        >
                          {{ p }}
                        </span>
                        <span
                          class="page-btn"
                          :class="{
                            disabled:
                              comment.currentPage ===
                              Math.ceil(comment.children.length / comment.pageSize)
                          }"
                          @click="changePage(comment, 1)"
                          >下一页</span
                        >
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
.main-content-wrapper {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px 40px 20px;
  position: relative;
  z-index: 10;
}
.banner {
  position: relative;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.banner-carousel {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  z-index: 1;
}
.carousel-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.blog-title {
  position: relative;
  z-index: 3;
  font-size: 4rem;
  font-weight: 900;
  color: #fff;
  text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.5);
  text-align: center;
  margin-top: -60px;
}
.blog-subtitle {
  font-size: 2rem;
  font-weight: normal;
  margin-top: 10px;
  text-shadow: 1px 1px 5px rgba(0, 0, 0, 0.8);
  min-height: 2.2rem;
}
.cursor {
  display: inline-block;
  width: 3px;
  background-color: transparent;
  animation: blink 1s infinite;
  margin-left: 2px;
  color: #fff;
}
@keyframes blink {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0;
  }
}

.waves-container {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 6vw;
  min-height: 100px;
  z-index: 10;
  line-height: 0;
}
.waves {
  width: 100%;
  height: 100%;
  display: block;
}
.wave1 {
  fill: rgba(244, 244, 245, 0.3);
}
.wave2 {
  fill: rgba(244, 244, 245, 0.5);
}
.wave3 {
  fill: rgba(244, 244, 245, 0.7);
}
.wave4 {
  fill: #f4f4f5;
}
html.dark .wave1 {
  fill: rgba(43, 34, 61, 0.3);
}
html.dark .wave2 {
  fill: rgba(43, 34, 61, 0.5);
}
html.dark .wave3 {
  fill: rgba(43, 34, 61, 0.7);
}
html.dark .wave4 {
  fill: #1a1525;
}

.parallax > use {
  animation: move-forever 25s cubic-bezier(0.55, 0.5, 0.45, 0.5) infinite;
}
.parallax > use:nth-child(1) {
  animation-delay: -2s;
  animation-duration: 7s;
}
.parallax > use:nth-child(2) {
  animation-delay: -3s;
  animation-duration: 10s;
}
.parallax > use:nth-child(3) {
  animation-delay: -4s;
  animation-duration: 13s;
}
.parallax > use:nth-child(4) {
  animation-delay: -5s;
  animation-duration: 20s;
}
@keyframes move-forever {
  0% {
    transform: translate3d(-90px, 0, 0);
  }
  100% {
    transform: translate3d(85px, 0, 0);
  }
}

.toc-box {
  padding: 20px;
  margin-top: 20px;
  position: sticky;
  top: 80px;
}
/* 修复：液态玻璃/清透水晶模式下 .glass-box 被加了 position: relative，
   选择器特异性高于 .toc-box，会覆盖 sticky。这里用同等特异性夺回 sticky */
html.liquid-glass .toc-box,
html.liquid-glass-clear .toc-box {
  position: sticky;
}
.toc-box h3 {
  margin-top: 0;
  border-bottom: 1px dashed rgba(0, 0, 0, 0.1);
  padding-bottom: 10px;
}
html.dark .toc-box h3 {
  border-bottom-color: rgba(255, 255, 255, 0.1);
  color: #fff;
}
.toc-list {
  list-style: none;
  padding-left: 0;
}
.toc-list li {
  margin: 10px 0;
}
.toc-list a {
  text-decoration: none;
  color: #555;
  transition: color 0.3s;
}
html.dark .toc-list a {
  color: #ccc;
}
.toc-list a:hover {
  color: #409eff;
}
html.dark .toc-list a:hover {
  color: #66b1ff;
}

/* 跳转评论区箭头（在 .toc-box 内部底部，随目录一起吸顶） */
.toc-comment-btn-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 15px;
  padding-top: 12px;
  border-top: 1px dashed rgba(0, 0, 0, 0.1);
}
html.dark .toc-comment-btn-wrapper {
  border-top-color: rgba(255, 255, 255, 0.1);
}
.toc-comment-arrow {
  font-size: 1.4rem;
  color: #999;
  cursor: pointer;
  transition: all 0.3s;
  padding: 4px;
  border-radius: 50%;
}
.toc-comment-arrow:hover {
  color: #ff79c6;
  transform: translateY(3px);
  background: rgba(255, 121, 198, 0.1);
}

.article-main-card {
  padding: 0 !important;
  margin-top: 0 !important;
  overflow: hidden;
  min-height: calc(100vh - 200px);
  display: flex;
  flex-direction: column;
}
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

.article-meta {
  padding: 20px 30px 0;
  color: #666;
}
html.dark .article-meta {
  color: #aaa;
}
.tags-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  position: relative;
  width: 100%;
  gap: 12px;
}
.edit-btn-wrapper {
  margin-left: auto;
}
.meta-row {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}
.meta-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.95rem;
}
.meta-item .el-icon {
  font-size: 1.15rem;
  -webkit-font-smoothing: antialiased;
  transform: translateZ(0);
}

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
.category-box {
  background: rgba(230, 162, 60, 0.1);
  color: #e6a23c;
  border: 1px solid rgba(230, 162, 60, 0.3);
}
.tag-box {
  background: rgba(103, 194, 58, 0.1);
  color: #67c23a;
  border: 1px solid rgba(103, 194, 58, 0.3);
}

.markdown-body {
  padding: 0 30px 30px;
  font-family: sans-serif;
  font-size: 16px;
  line-height: 1.8;
  color: #333;
  flex: 1;
}
html.dark .markdown-body {
  color: #ddd;
}
.markdown-body :deep(pre) {
  background: #f6f8fa;
  padding: 15px;
  border-radius: 8px;
  overflow: auto;
}
html.dark .markdown-body :deep(pre) {
  background: #2d2d2d;
}
.markdown-body :deep(img) {
  max-width: 100%;
  border-radius: 8px;
  margin: 10px 0;
}
.markdown-body :deep(blockquote) {
  border-left: 4px solid #409eff;
  margin: 0;
  padding: 10px 15px;
  color: #666;
  background: rgba(64, 158, 255, 0.05);
  border-radius: 0 4px 4px 0;
}

.action-center {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  padding-bottom: 40px;
}
.action-btn {
  font-weight: bold;
  font-size: 1.1rem;
  padding: 12px 30px;
  height: auto;
  transition:
    transform 0.2s,
    box-shadow 0.2s;
}
.action-btn:hover {
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.like-wrapper {
  position: relative;
}
.hearts-container {
  position: absolute;
  bottom: 100%;
  left: 0;
  width: 100%;
  height: 100px;
  pointer-events: none;
  z-index: 10;
}
.floating-heart {
  position: absolute;
  bottom: 0;
  transform: translateX(-50%);
  opacity: 1;
}
.heart-float-enter-active {
  animation: floatUp 1.5s ease-out forwards;
}
.heart-float-leave-active {
  opacity: 0;
  transition: opacity 0.3s;
}
@keyframes floatUp {
  0% {
    bottom: 0;
    opacity: 1;
    transform: translateX(-50%) scale(0.5);
  }
  50% {
    opacity: 1;
    transform: translateX(-50%) scale(1.2);
  }
  100% {
    bottom: 80px;
    opacity: 0;
    transform: translateX(-50%) scale(1);
  }
}

.prev-next-nav {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  margin-top: 20px;
}
.nav-item {
  flex: 1;
  padding: 20px;
  cursor: pointer;
  transition:
    transform 0.3s,
    box-shadow 0.3s;
}
.nav-item:hover:not(.disabled) {
  transform: translateY(-3px);
  color: #409eff;
}
.nav-item.disabled {
  cursor: not-allowed;
  opacity: 0.5;
}
.nav-label {
  font-size: 0.85rem;
  color: #888;
  margin-bottom: 5px;
}
.nav-title {
  font-size: 1.1rem;
  font-weight: bold;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 评论区 */
.author-area {
  display: flex;
  align-items: center;
  gap: 6px;
}
.admin-name {
  color: #f56c6c !important;
  font-weight: bold;
}
.admin-badge {
  color: #f56c6c;
  border: 1px solid #f56c6c;
  padding: 0 4px;
  border-radius: 4px;
  font-size: 11px;
  transform: scale(0.9);
  transform-origin: left;
}
/* 自定义用户称号徽章（颜色由内联 style 控制） */
.user-title-badge {
  padding: 0 4px;
  border: 1px solid;
  border-radius: 4px;
  font-size: 11px;
  font-weight: bold;
  transform: scale(0.9);
  transform-origin: left;
}
.pinned-badge {
  color: #ff9800;
  border: 1px solid #ff9800;
  padding: 0 4px;
  border-radius: 4px;
  font-size: 11px;
  margin-right: 6px;
  vertical-align: middle;
  display: inline-block;
}
.admin-tools {
  display: flex;
  align-items: center;
  gap: 10px;
}
.pin-btn {
  cursor: pointer;
  font-size: 14px;
  filter: grayscale(100%);
  transition: all 0.3s;
}
.is-pinned-icon {
  filter: grayscale(0%);
  transform: rotate(45deg);
}
.blue-text {
  color: #00aeec;
  cursor: pointer;
}
.reply-target {
  color: #666;
  margin-right: 5px;
}

.comments-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  padding-bottom: 10px;
  margin-bottom: 20px;
}
html.dark .comments-header-row {
  border-bottom-color: rgba(255, 255, 255, 0.1);
}
.sort-tabs span {
  cursor: pointer;
  color: #999;
  font-size: 14px;
  transition: color 0.3s;
}
.sort-tabs span:hover,
.sort-tabs span.active {
  color: #409eff;
  font-weight: bold;
}
.sort-tabs .divider {
  margin: 0 10px;
  color: #ccc;
  cursor: default;
}

.comment-input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
  position: relative;
}
.emoji-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}
.emoji-btn {
  font-size: 24px;
  color: #999;
  cursor: pointer;
  transition: color 0.3s;
}
.emoji-btn:hover {
  color: #f56c6c;
}
.emoji-picker {
  position: absolute;
  top: 35px;
  left: 0;
  width: 260px;
  height: 160px;
  overflow-y: auto;
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  padding: 10px;
  z-index: 1000;
  border-radius: 8px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
  background: var(--bg-color, rgba(255, 255, 255, 0.9));
}
html.dark .emoji-picker {
  background: rgba(30, 30, 30, 0.95);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.5);
}
.emoji-picker::-webkit-scrollbar {
  width: 4px;
}
.emoji-picker::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}
html.dark .emoji-picker::-webkit-scrollbar-thumb {
  background-color: rgba(255, 255, 255, 0.2);
}
.emoji-picker span {
  font-size: 1.2rem;
  cursor: pointer;
  padding: 2px;
  transition: transform 0.2s;
}
.emoji-picker span:hover {
  transform: scale(1.3);
}

.comments-section {
  padding: 30px;
  margin-top: 20px;
}
.comment-list {
  margin-top: 30px;
}
.comment-item {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}
html.dark .comment-item {
  border-bottom-color: rgba(255, 255, 255, 0.05);
}

.sub-comments-list {
  background: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
  padding: 15px;
  margin-top: 10px;
}
html.dark .sub-comments-list {
  background: rgba(255, 255, 255, 0.02);
}
.sub-comment-item {
  display: flex;
  gap: 12px;
  margin-bottom: 15px;
}
.sub-comment-item:last-child {
  margin-bottom: 0;
}
.sub-content-box {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.toggle-reply-btn {
  font-size: 13px;
  color: #00aeec;
  cursor: pointer;
  user-select: none;
  display: inline-block;
  margin-top: 5px;
  font-weight: 500;
}
.toggle-reply-btn:hover {
  text-decoration: underline;
}

.pagination-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px dashed rgba(0, 0, 0, 0.05);
  font-size: 13px;
  color: #9499a0;
}
html.dark .pagination-row {
  border-top-color: rgba(255, 255, 255, 0.05);
}
.page-info {
  margin-right: 5px;
}
.fold-btn {
  margin-left: auto;
  color: #00aeec;
  cursor: pointer;
  font-size: 13px;
}
.fold-btn:hover {
  text-decoration: underline;
}
.page-btn {
  cursor: pointer;
  transition: color 0.2s;
  user-select: none;
}
.page-btn:hover {
  color: #00aeec;
}
.page-btn.disabled {
  color: #ccc;
  cursor: not-allowed;
}
.page-num {
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
}
.page-num:hover {
  color: #00aeec;
}
.page-num.active {
  color: #fff;
  background: #00aeec;
}

.comment-avatar {
  cursor: pointer;
  flex-shrink: 0;
}
.comment-content-box {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.comment-author {
  font-weight: 500;
  font-size: 13px;
  color: #61666d;
}
html.dark .comment-author {
  color: #999;
}
.delete-comment-btn {
  color: #f56c6c;
  cursor: pointer;
  font-size: 16px;
  transition: transform 0.2s;
}
.delete-comment-btn:hover {
  transform: scale(1.2);
}

.comment-text {
  font-size: 15px;
  line-height: 1.6;
  color: #18191c;
  margin-bottom: 10px;
}
html.dark .comment-text {
  color: #e3e5e7;
}
.comment-footer {
  display: flex;
  align-items: center;
  font-size: 12px;
  color: #9499a0;
}
.comment-time {
  margin-right: 15px;
}
.comment-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 评论区里的小图标按钮（注意：与 .action-center 的点赞按钮同名，这里在子作用域内不冲突） */
.comment-actions .action-btn {
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  transition: color 0.2s;
  color: #9499a0;
  margin: 0 !important;
  padding: 0 !important;
  background: transparent;
  border: none;
}
.comment-actions .action-btn:hover {
  color: #00aeec;
}
.comment-actions .action-btn svg {
  margin-right: 4px;
  transition: fill 0.3s;
}
.comment-actions .action-btn:hover svg {
  fill: #00aeec !important;
}
.comment-actions .action-btn .num {
  font-size: 13px;
  font-weight: 500;
  user-select: none;
}
.comment-actions .reply-text-btn {
  font-size: 13px;
}
.active-blue {
  color: #00aeec !important;
}
.flip-icon svg {
  transform: rotate(180deg);
}

.reply-input-area {
  margin-top: 10px;
}
.custom-reply-input :deep(textarea) {
  font-size: 14px;
}

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

@media screen and (max-width: 768px) {
  .markdown-body {
    padding: 0 15px 15px !important;
    font-size: 15px !important;
  }
  .article-meta {
    padding: 15px 15px 0 !important;
  }
  .hero-title-box {
    left: 15px !important;
    right: 15px !important;
    bottom: 15px !important;
    padding: 8px 15px !important;
  }
  .hero-title {
    font-size: 1.4rem !important;
  }
  .action-center .action-btn {
    padding: 10px 20px !important;
    font-size: 1rem !important;
  }
}
</style>
