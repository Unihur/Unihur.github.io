# AGENTS.md — UniHur's Blog 开发指南

> 本文档供 AI 助手（及人类开发者）快速理解项目结构、约定与开发流程。修改代码前请先通读本文档。

## 项目概述

UniHur's Blog 是一个个人博客系统的前端，基于 Vue 3 + Vite + Element Plus 构建，配合自研 Python FastAPI 后端（`blog-backend/`，部署在 `https://unihur.xyz`）使用。

## 技术栈

| 类别 | 技术 | 版本约束 |
|------|------|---------|
| 框架 | Vue 3（`<script setup>`） | ^3.5 |
| 构建 | Vite | ^8.0 |
| 路由 | Vue Router 4（Hash 模式） | ^4.6 |
| 状态 | Pinia | ^3.0 |
| UI | Element Plus（按需自动导入） | ^2.13 |
| HTTP | axios（统一封装） | ^1.13 |
| Markdown | markdown-it + highlight.js | - |
| 看板娘 | oh-my-live2d | ^0.19 |
| Lint | ESLint + Prettier | - |
| 后端 | FastAPI + SQLAlchemy + SQLite | 见 `blog-backend/` |

## 常用命令

```bash
# 开发
npm run dev              # 启动开发服务器（localhost:5173，自动代理 /api → 后端）

# 构建
npm run build            # 生产构建到 dist/
npm run preview          # 本地预览生产包

# 代码质量（修改代码后必须运行）
npm run lint             # ESLint 自动修复
npm run lint:check       # 仅检查不修改（应保持 0 warning）
npm run format           # Prettier 格式化
npm run format:check     # 仅检查
```

**重要：完成任何代码修改后，务必运行 `npm run lint:check` 和 `npm run build` 验证无报错。**

## 目录结构

```
my-blog/
├── src/
│   ├── api/              # 接口层（统一 axios 实例 + 按模块拆分）
│   │   ├── request.js    #   axios 实例 + 拦截器（token 注入、401 处理）
│   │   ├── auth.js       #   登录/用户信息/头像/改昵称
│   │   ├── article.js    #   文章 CRUD + 点赞/分享
│   │   ├── comment.js    #   评论 CRUD + 点赞点踩/置顶
│   │   ├── category.js   #   分类 CRUD
│   │   ├── settings.js   #   全站公开设置 + 访客统计
│   │   ├── visitor.js    #   管理员访客管理
│   │   ├── upload.js     #   图片上传/图库
│   │   └── index.js      #   统一出口
│   ├── stores/           # Pinia 状态
│   │   ├── user.js       #   登录/用户/管理员判定
│   │   └── site.js       #   站点配置/主题/Banner
│   ├── composables/      # 可复用逻辑
│   │   ├── useTypewriter.js  # 打字机（模块级单例）
│   │   └── useLive2d.js      # Live2D 看板娘
│   ├── utils/            # 工具函数
│   │   ├── markdown.js   #   共享 md 实例 + extractToc
│   │   └── format.js     #   formatDate / formatDuration
│   ├── views/            # 页面视图（路由懒加载）
│   │   ├── HomeView.vue
│   │   ├── ArticleView.vue
│   │   ├── WriteView.vue
│   │   └── VisitorsView.vue
│   ├── components/       # 展示组件
│   │   ├── AppHeader.vue     # 顶部导航栏 + 登录弹窗 + 设置抽屉
│   │   ├── ProfileCard.vue   # 个人资料卡片
│   │   ├── MusicPlayer.vue   # 音乐播放器
│   │   ├── MouseTrail.vue    # 鼠标拖尾特效
│   │   └── SettingDrawer.vue # 博客高级设置抽屉
│   ├── router/
│   │   └── index.js      # 路由 + 守卫（requiresAdmin）
│   ├── assets/           # 静态资源（会被 Vite 处理）
│   ├── App.vue           # 应用外壳（挂载 Header + 路由出口 + 鼠标特效）
│   ├── main.js           # 入口（注册 Pinia + Router）
│   └── style.css         # 全局样式（玻璃材质/主题色/夜间模式）
├── public/               # 静态资源（原样拷贝，不经过 Vite）
│   ├── avatar.png / favicon.svg / *.cur
│   ├── banner/           # 横幅图片
│   ├── musics/           # 音乐文件
│   ├── ulk/              # Live2D 模型
│   └── markdown_image/   # markdown 图片
├── .env                  # 开发环境变量
├── .env.production       # 生产环境变量
├── vite.config.js        # Vite 配置（@ 别名 + 代理 + Element Plus 自动导入）
├── eslint.config.js      # ESLint 配置
├── .prettierrc.json      # Prettier 配置
└── package.json
```

## 架构约定

### 1. API 调用规则（重要）

**永远不要在组件里直接 `import axios`**。所有后端调用必须走 `src/api/` 模块：

```js
// ✅ 正确
import { listArticles, login } from '@/api'

// ❌ 错误
import axios from 'axios'
axios.get('https://unihur.xyz/api/articles')
```

`api/request.js` 已统一处理：
- baseURL（来自 `VITE_API_BASE_URL`）
- 请求拦截器：自动注入 `token` 和 `Authorization: Bearer xxx` 两种头
- 响应拦截器：401 自动登出，403 权限提示

新增接口时，加到对应模块文件，并在 `api/index.js` 中通过 `export *` 暴露。

### 2. 状态管理规则

**永远不要用 provide/inject 传全局状态**。用 Pinia store：

```js
import { useUserStore } from '@/stores/user'
import { useSiteStore } from '@/stores/site'

const userStore = useUserStore()
const siteStore = useSiteStore()
```

- `useUserStore`：登录态、用户信息、`isAdmin`（优先后端 `is_admin`，回退 `VITE_ADMIN_USERNAME`）
- `useSiteStore`：站点配置、主题、Banner、夜间模式

### 3. 路由守卫

管理员页面在路由 meta 标记 `requiresAdmin: true`，由 `router.beforeEach` 统一拦截。**不要在组件内自行判断 `isAdmin` 来决定是否渲染**（会导致刷新闪烁）。

### 4. Composables

跨组件复用的逻辑抽到 `composables/`：
- `useTypewriter()`：模块级单例，全应用只需 `start()` 一次
- `useLive2d(siteConfig)`：Live2D 实例管理

### 5. 工具函数

- Markdown 渲染：`import { md, extractToc } from '@/utils/markdown'`
- 时间格式化：`import { formatDate } from '@/utils/format'`

**不要在多个组件里重复 new MarkdownIt()**，统一用 `utils/markdown.js` 的共享实例。

## 环境变量

| 变量 | 说明 | 开发默认 |
|------|------|---------|
| `VITE_API_BASE_URL` | 后端 API 基础路径 | `/api`（走 vite 代理） |
| `VITE_API_TARGET` | 开发代理转发的真实后端 | `https://unihur.xyz` |
| `VITE_ADMIN_USERNAME` | 前端回退用的管理员用户名 | `unihur` |
| `VITE_SITE_NAME` | 站点默认名称 | `UniHur` |

> 开发代理**不做 rewrite**：前端请求 `/api/articles`，代理转发到 `https://unihur.xyz/api/articles`（后端路由都带 `/api` 前缀）。

## 代码风格约定

- **无分号**、**单引号**、**100 字宽**（Prettier 强制）
- Vue 组件用 `<script setup>` + Composition API
- 路径用 `@/` 别名，不用相对路径（`../` 容易出错）
- 空的 `catch` 块用 `catch (_)` 或 `catch (_) {}`，加注释说明为什么忽略
- `console.log` 会触发 lint warning，用 `console.warn` / `console.error` 代替
- `v-html` 仅用于 markdown 渲染（已全局关闭 `vue/no-v-html` 规则）

## 前后端接口对应

| 前端 api 模块 | 后端路由 | 说明 |
|--------------|---------|------|
| `auth.login` | `POST /api/login` | 返回 token/username/avatar/is_admin/config |
| `auth.getMe` | `GET /api/user/me` | 返回 username/avatar/is_admin/config |
| `auth.checkUserStatus` | `GET /api/user/status` | 检测账号审核状态 |
| `auth.uploadAvatar` | `POST /api/user/avatar` | multipart 上传 |
| `auth.updateUser` | `POST /api/user/update` | 改昵称/同步配置 |
| `article.listArticles` | `GET /api/articles` | 列表（带 limit 参数） |
| `article.getArticle` | `GET /api/articles/:slug` | 详情（含 prev/next，浏览量自增） |
| `article.createArticle` | `POST /api/articles` | 管理员 |
| `article.updateArticle` | `PUT /api/articles/:slug` | 管理员 |
| `article.deleteArticle` | `DELETE /api/articles/:slug` | 管理员 |
| `article.likeArticle` | `POST /api/articles/:slug/like` | - |
| `article.shareArticle` | `POST /api/articles/:slug/share` | - |
| `comment.listComments` | `GET /api/comments/:slug` | 带 token 返回 userAction |
| `comment.createComment` | `POST /api/comments` | - |
| `comment.deleteComment` | `DELETE /api/comments/:id` | 管理员或作者 |
| `comment.pinComment` | `POST /api/comments/:id/pin` | 管理员 |
| `comment.commentAction` | `POST /api/comments/:id/action` | 点赞/点踩互斥 |
| `category.*` | `GET/POST/PUT/DELETE /api/categories` | 管理员可写 |
| `settings.getPublicSettings` | `GET /api/settings` | 无需登录 |
| `settings.savePublicSettings` | `POST /api/settings` | - |
| `visitor.*` | `/api/admin/visitors/*` | 管理员 |
| `upload.*` | `/api/upload/image`、`/api/images` | 管理员 |

## 已知技术债（未来优化方向）

| 事项 | 说明 | 优先级 |
|------|------|--------|
| 密码明文存储 | 后端 `User.password` 存明文，应改 bcrypt | 高 |
| Token 存 localStorage | 可考虑 httpOnly cookie + refresh token | 中 |
| 文章列表无真分页 | 当前 `limit: 1000` 一次性加载 | 中 |
| markdown XSS | `v-html` 渲染未 sanitize，建议加 DOMPurify | 中 |
| 后端密码错误返回 401 | 与 token 失效 401 混淆，建议改 400 | 低 |

## 后端开发

后端代码在 `../blog-backend/`（同级目录），技术栈：FastAPI + SQLAlchemy + SQLite。

- 入口：`main.py`
- 数据模型：`models.py`
- 数据库：`database.py`（SQLite，文件 `blog.db`）

**重启后端**（服务器上）：
```bash
cd /root/blog-backend
pkill -f uvicorn
source .venv/bin/activate
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
```

**改了数据库字段**才需要 `rm blog.db` 重建，否则不要删（会丢数据）。

## 开发流程检查清单

修改代码后，依次运行：

1. `npm run lint` — 自动修复格式问题
2. `npm run lint:check` — 确认 0 warning
3. `npm run build` — 确认编译通过
4. （可选）`npm run dev` — 本地启动验证页面正常

**永远不要在未验证的情况下提交代码。**
