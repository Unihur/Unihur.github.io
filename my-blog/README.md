# UniHur's Blog

基于 Vue 3 + Vite + Element Plus 构建的个人博客前端，配合自研 Python 后端（`https://unihur.xyz/api`）使用。

## 功能特性

- **文章系统**：Markdown 渲染、代码高亮、TOC 目录、上一篇/下一篇导航
- **互动**：点赞（爱心特效）、分享（剪贴板兼容 HTTP/HTTPS）、B 站式两级评论（表情包、点赞点踩、置顶、分页）
- **写作**：管理员专属，支持 .md 导入、实时预览、封面上传、历史图库管理
- **用户系统**：登录、注册审核、改昵称、换头像、个人配置云端同步
- **访客管理**：管理员审核新账号、删除用户
- **个性化**：
  - 夜间 / 日间模式
  - 6 种主题色（白/蓝/粉/绿/紫/橙）
  - 3 种玻璃材质（毛玻璃/流光液态/清透水晶）
  - Live2D 看板娘（可调位置/缩放/模型）
  - 鼠标拖尾 + 点击水波纹特效
  - 打字机签名
  - Banner 轮播 + 波浪动画（4 种模式）
  - 音乐播放器

## 技术栈

| 类别 | 技术 |
|------|------|
| 框架 | Vue 3（`<script setup>`） |
| 构建 | Vite 8 |
| 路由 | Vue Router 4（Hash 模式） |
| 状态 | Pinia |
| UI | Element Plus（按需自动导入） |
| HTTP | axios（统一封装 + 拦截器） |
| Markdown | markdown-it + highlight.js |
| 看板娘 | oh-my-live2d |

## 项目结构

```
src/
├── api/              # 接口层（统一 axios 实例 + 按模块拆分）
├── stores/           # Pinia 状态（user / site）
├── composables/      # 可复用逻辑（useTypewriter / useLive2d）
├── utils/            # 工具函数（markdown / format）
├── views/            # 页面视图（Home / Article / Write / Visitors）
├── components/       # 展示组件（AppHeader / ProfileCard 等）
├── router/           # 路由 + 守卫
├── App.vue           # 应用外壳
└── main.js           # 入口
```

## 环境变量

在项目根目录创建 `.env`（开发）和 `.env.production`（生产）：

| 变量 | 说明 | 开发默认值 |
|------|------|-----------|
| `VITE_API_BASE_URL` | 后端 API 基础路径 | `/api`（走 vite 代理） |
| `VITE_API_TARGET` | 开发代理转发的真实后端 | `https://unihur.xyz` |
| `VITE_ADMIN_USERNAME` | 前端回退用的管理员用户名 | `unihur` |

> 管理员权限优先由后端 `/user/me` 返回的 `is_admin` 字段判定，仅在未提供时回退到环境变量。

## 开发

```bash
npm install        # 安装依赖
npm run dev        # 启动开发服务器（localhost:5173）
```

开发环境下，所有 `/api/*` 请求会被 vite 代理转发到 `VITE_API_TARGET`，避免跨域。

## 构建

```bash
npm run build      # 生产构建到 dist/
npm run preview    # 本地预览生产包
```

## 代码质量

```bash
npm run lint       # ESLint 自动修复
npm run lint:check # 仅检查不修改
npm run format     # Prettier 格式化
npm run format:check
```

## 安全说明

- Token 存储在 localStorage（前端单页应用的常见做法）
- "记住账号"仅保存用户名，**不存储密码明文**
- 管理员判定以后端 `is_admin` 为准，前端环境变量仅作回退
- 路由守卫拦截 `/write`、`/visitors` 等管理员页面

## 后端依赖

本项目需要配合后端 API 使用，主要接口：

| 接口 | 说明 |
|------|------|
| `POST /login` | 登录 |
| `GET /user/me` | 获取当前用户信息（含 `is_admin`、`config`） |
| `GET/POST /articles` | 文章列表 / 新建 |
| `GET/PUT/DELETE /articles/:slug` | 文章 CRUD |
| `POST /articles/:slug/like` / `/share` | 点赞 / 分享 |
| `GET/POST /comments/:slug` | 评论 |
| `GET/POST /categories` | 分类 |
| `GET/POST /settings` | 全站公开设置 |
| `GET /admin/visitors` | 访客管理（管理员） |