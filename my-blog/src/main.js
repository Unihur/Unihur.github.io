import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './style.css'
import App from './App.vue'

// Element Plus 全局样式（按需导入仅影响组件 JS，主题 CSS 仍需手动引入，
// 此处保留 dark / 主样式；如果未来需要进一步裁剪可以仅引入对应主题文件）
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'

import router from './router'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.mount('#app')
