##### **V1.0.0（4f9b735）优化代码**

一、前端代码结构重组

1.1 目录划分

调整项	说明

新建 src/api/	接口层，统一管理所有后端调用

新建 src/stores/	Pinia 状态管理，替代 provide/inject

新建 src/composables/	可复用逻辑（打字机、Live2D）

新建 src/utils/	工具函数（markdown、format）

新建 src/views/	页面视图，从 components 拆出

components/ 精简	仅保留展示组件（AppHeader 等）

删除 HelloWorld.vue	模板遗留未使用文件

路由懒加载	4 个视图拆成独立 chunk

1.2 文件迁移

\- Home.vue → views/HomeView.vue

\- ArticleDetail.vue → views/ArticleView.vue

\- Write.vue → views/WriteView.vue

\- Visitors.vue → views/VisitorsView.vue

\- 导航栏逻辑从 App.vue（980 行）抽离为 components/AppHeader.vue

\- App.vue 精简为 \~80 行外壳

二、API 层统一封装

调整项	说明

新建 api/request.js	axios 实例，baseURL 来自环境变量

请求拦截器	自动注入 token（同时携带 token + Authorization 两种头）

响应拦截器	统一处理 401（自动登出）、403（权限提示）

setUnauthorizedHandler	避免 request 与 store 循环依赖

按模块拆分	auth.js / article.js / comment.js / category.js / settings.js / visitor.js / upload.js

api/index.js	统一出口，import { login } from '@/api'

消除硬编码 URL	所有 https://unihur.xyz/api/... 改为相对路径

三、状态管理（Pinia）

Store	职责

stores/user.js	token / username / avatar / isAdmin / 登录 / 退出 / 改昵称 / 上传头像 / refreshProfile

stores/site.js	siteConfig / isDark / bannerMode / glassType / themeColor / 主题应用 / 公开设置同步

移除 provide/inject	全局状态改用 store，组件解耦

四、Composables 抽离

文件	解决问题

useTypewriter.js	模块级单例，解决 startTypewriter() 被调用两次的双重触发

useLive2d.js	统一 oml2dInstance 引用，解决 let + window.\_\_oml2dInstance\_\_ 双套状态不同步

五、工具函数抽离

文件	内容

utils/markdown.js	共享 md 实例（ArticleView + WriteView 复用）+ extractToc()

utils/format.js	formatDate() / formatDuration()

六、Bug 修复清单（前端）

\#	Bug	位置	修复方式

1	storage 监听器在 setup 顶层注册、从不解绑（内存泄漏）	ArticleDetail	移入 onMounted，onUnmounted 中 removeEventListener

2	注册两个 onMounted、fetchArticles 调两次	Home	合并为单个 onMounted

3	startTypewriter() 调用两次导致双重触发	App	useTypewriter 改模块级单例

4	applyThemeStyle 未定义永远 false	App	删除死代码，改用 siteStore.applyUserConfig

5	replyContent 多回复框共用串内容	ArticleDetail	showReplyBox 统一重置

6	TOC 用 setTimeout(300) 等 DOM	ArticleDetail	改用 await nextTick()

7	admin\_token localStorage 根本不存在	Home	删除，统一用 token

8	Write 用相对路径、其他用绝对路径	Write	全部走 @/api

9	token 头部命名不统一（三种混用）	多处	拦截器统一注入 token + Authorization

10	管理员判定硬编码 'unihur'	App/Home/Article	改为后端 is\_admin 优先，环境变量回退

11	Remember Me 明文存密码	user store	仅存用户名，清除历史 saved\_password

12	vite.config.js rewrite 把 /api 去掉，代理 404	vite.config	删除 rewrite，保持 /api 原样转发

13	listArticles 不传 limit，只显示 10 篇	api/article	传 params: { limit: 1000 }

14	refreshProfile 不同步 username/avatar	user store	补充同步逻辑

七、路由守卫

调整项	说明

meta.requiresAdmin	/write、/visitors 标记

router.beforeEach	未登录拒绝；isAdmin 未知时先调 refreshProfile()

scrollBehavior	路由切换回到顶部

动态 import	守卫内 import('element-plus') 提示，避免循环引用

八、性能优化

调整项	说明

Element Plus 按需导入	unplugin-auto-import + unplugin-vue-components

路由懒加载	4 个视图拆成独立 chunk

@ 路径别名	vite.config.js 配置 resolve.alias

删除死代码	注释掉的 displayedTags、未用 import、HelloWorld.vue 等

九、环境变量与配置

文件	内容

.env	开发：VITE\_API\_BASE\_URL=/api、VITE\_API\_TARGET、VITE\_ADMIN\_USERNAME

.env.production	生产：VITE\_API\_BASE\_URL=https://unihur.xyz/api

vite.config.js	@ 别名 + 开发代理 /api → VITE\_API\_TARGET（无 rewrite）

.gitignore	新增忽略 \*.d.ts、dev-\*.log

十、代码质量工具

调整项	说明

eslint.config.js	Vue 3 flat config + Prettier 整合

.prettierrc.json	无分号、单引号、100 字宽

.prettierignore	排除 dist/node\_modules/public

package.json 脚本	lint / lint:check / format / format:check

首次修复	1072 个格式 warning → 0

规则定制	关闭 no-v-html（markdown 渲染必需）、caughtErrors: 'none'（空 catch）

十一、文档

调整项	说明

README.md 重写	功能特性、技术栈、项目结构、环境变量、开发/构建命令、安全说明、后端接口表

十二、后端适配（blog-backend/main.py）

\#	接口	修改内容

1	POST /api/login	返回值新增 is\_admin: boolean 字段

2	GET /api/user/me	返回值新增 is\_admin、username、avatar 字段

3	GET /api/user/me	裸 except: 改为 except jwt.InvalidTokenError，避免吞异常

4	POST /api/login	删除 return 之后的 29 行死代码（永远不执行的重复块）

十三、验证结果

检查项	结果

npm run lint:check	0 error / 0 warning

npm run build	编译通过（1.11s）

npm run dev	开发服务器正常启动（localhost:5173）

十四、后端部署提醒

后端改完后需要在服务器上重启：

cd /root/blog-backend

pkill -f uvicorn

source .venv/bin/activate

nohup uvicorn main:app --host 0.0.0.0 --port 8000 > backend.log 2>\&1 \&

本次后端改动未动数据库结构（没加新列），所以不需要 rm blog.db，现有数据不受影响。

十五、本次改动未涉及（未来可优化）

事项	说明

密码明文存储	后端 User.password 仍存明文，建议改 bcrypt 哈希

Token 持久化	仍用 localStorage，可考虑 httpOnly cookie + refresh token

文章列表分页	当前传 limit: 1000 一次性加载，文章多了应改真分页

评论 XSS	v-html 渲染 markdown，后端未做 sanitize，建议加 DOMPurify

后端密码错误返回 401	与"token 失效 401"混淆，建议密码错误改 400 或 403

