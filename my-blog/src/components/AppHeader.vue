<script setup>
// 顶部导航栏：
// - 路由导航项 + 管理员额外项
// - 设置 / 主题材质 / Banner / 日夜切换 图标
// - 头像下拉（登录态展示昵称 + 上传头像 + 改名 + 退出）
// - 登录弹窗（账号状态检测、记住账号密码）
// 内置 SettingDrawer 组件
import { reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  Setting,
  Brush,
  Picture,
  Sunny,
  Moon,
  HomeFilled,
  Edit,
  Box,
  VideoPlay,
  ChatDotSquare,
  Guide,
  InfoFilled,
  UserFilled,
  User,
  Check,
  Clock,
  Warning,
  ArrowRight
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

import SettingDrawer from './SettingDrawer.vue'
import { useSiteStore } from '@/stores/site'
import { useUserStore } from '@/stores/user'
import { checkUserStatus } from '@/api/auth'

const userStore = useUserStore()
const siteStore = useSiteStore()

const router = useRouter()

// ============ 登录弹窗状态 ============
const showLoginDialog = ref(false)
const loginForm = reactive({ username: '', password: '', remember: false })
const checkStatusResult = ref(null)

// 进入页面时恢复“记住的账号”（仅用户名，不再恢复密码）
restoreRememberedCredentials()
function restoreRememberedCredentials() {
  const savedUser = localStorage.getItem(userStore.LS.rememberUser)
  if (savedUser) {
    loginForm.username = savedUser
    loginForm.remember = true
  }
}

// 用户修改账号输入框时清空原检测结果
watch(
  () => loginForm.username,
  () => {
    checkStatusResult.value = null
  }
)

const handleCheckStatus = async () => {
  if (!loginForm.username) return ElMessage.warning('请先输入要检测的账号')
  try {
    const res = await checkUserStatus(loginForm.username)
    checkStatusResult.value = res.data
  } catch (e) {
    ElMessage.error('检测失败')
  }
}

const handleLoginClick = () => {
  if (!userStore.isLoggedIn) showLoginDialog.value = true
}

const handleLoginSubmit = async () => {
  try {
    const res = await userStore.login(loginForm)
    // 应用该用户绑定的主题 / Banner / 夜间模式
    siteStore.applyUserConfig(res.data?.config || {})
    ElMessage.success('登录成功！')
    showLoginDialog.value = false
  } catch (err) {
    const status = err.response?.status
    const errorMsg = err.response?.data?.detail || '账号或密码错误'
    if (status === 403) {
      // 需要管理员审核
      ElMessage.warning(errorMsg)
      showLoginDialog.value = false
    } else if (status === 422) {
      ElMessage.error(errorMsg)
    } else {
      ElMessage.error(errorMsg)
    }
  }
}

const logout = () => {
  userStore.logout()
  ElMessage.success('已安全退出登录')
}

// ============ 头像上传 / 昵称修改 ============
const newUsernameInput = ref('')

const handleAvatarUpload = async (options) => {
  try {
    await userStore.uploadAvatar(options.file)
    ElMessage.success('头像修改成功！')
  } catch (e) {
    ElMessage.error('上传失败')
  }
}

const updateUsername = async () => {
  if (!newUsernameInput.value) return ElMessage.warning('新用户名不能为空')
  try {
    await userStore.updateUser({ new_username: newUsernameInput.value })
    newUsernameInput.value = ''
    ElMessage.success('用户名修改成功！')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '修改失败')
  }
}

// ============ 主题/Banner 下拉指令 ============
const handleThemeCommand = (command) => {
  if (command.startsWith('glass_')) {
    siteStore.setTheme({ glass: command.substring(6) })
  } else if (command.startsWith('color_')) {
    siteStore.setTheme({ color: command.substring(6) })
  }
}
const changeBannerMode = (command) => {
  siteStore.changeBannerMode(command)
}
const toggleDarkMode = () => siteStore.toggleDarkMode()

// ============ 设置抽屉 ============
const showSettingDrawer = ref(false)
const openSetting = () => {
  if (!userStore.isAdmin) {
    ElMessage.warning('暂无权限：仅管理员可使用博客设置！')
    return
  }
  showSettingDrawer.value = true
}

const handleConfigUpdate = (newConfig) => {
  siteStore.updateSiteConfig(newConfig)
}

// ============ 路由跳转 ============
const handleWriteClick = () => {
  // 写作按钮：管理员或有写作权限的用户可点击，否则仅提示不登出
  if (!userStore.canWriteArticles) {
    ElMessage.warning('暂无权限：仅管理员或被授权用户可以发布或编辑文章！')
    return
  }
  router.push('/write')
}

const handleVisitorClick = () => {
  router.push('/visitors')
}
</script>

<template>
  <div class="nav-container">
    <nav class="glass-box navbar">
      <div class="nav-links">
        <router-link v-slot="{ navigate }" to="/" custom>
          <span @click="navigate"
            ><el-icon><HomeFilled /></el-icon>首页</span
          >
        </router-link>
        <span @click="handleWriteClick"
          ><el-icon><Edit /></el-icon>写作</span
        >
        <span
          ><el-icon><Box /></el-icon>项目</span
        >
        <span
          ><el-icon><VideoPlay /></el-icon>娱乐</span
        >
        <span
          ><el-icon><ChatDotSquare /></el-icon>留言</span
        >
        <span
          ><el-icon><Guide /></el-icon>导航</span
        >
        <span
          ><el-icon><InfoFilled /></el-icon>关于</span
        >
        <span v-if="userStore.isAdmin" style="color: #f56c6c" @click="handleVisitorClick">
          <el-icon><User /></el-icon>访客管理
        </span>
      </div>

      <div class="nav-icons">
        <!-- 登录头像（含设置/主题/Banner/日夜模式的二级悬浮子菜单） -->
        <el-dropdown
          :disabled="!userStore.isLoggedIn"
          trigger="hover"
          :hide-on-click="false"
          placement="bottom-end"
          popper-class="avatar-dropdown-popper"
        >
          <div
            class="avatar-wrapper"
            style="display: flex; align-items: center; cursor: pointer; outline: none"
            @click="handleLoginClick"
          >
            <el-tooltip
              :content="userStore.isLoggedIn ? '' : '点击登录'"
              placement="bottom"
              :disabled="userStore.isLoggedIn"
            >
              <el-avatar
                :size="36"
                :src="userStore.avatar || ''"
                :icon="userStore.avatar ? '' : UserFilled"
                class="login-avatar"
              />
            </el-tooltip>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <!-- 顶部头像 + 昵称 -->
              <div
                style="
                  display: flex;
                  flex-direction: column;
                  align-items: center;
                  margin-bottom: 15px;
                "
              >
                <el-upload
                  action=""
                  :http-request="handleAvatarUpload"
                  :show-file-list="false"
                  accept="image/png, image/jpeg, image/gif"
                >
                  <el-tooltip content="点击上传新头像" placement="right">
                    <el-avatar
                      :size="56"
                      :src="userStore.avatar || ''"
                      :icon="userStore.avatar ? '' : UserFilled"
                      style="margin-bottom: 10px; border: 2px solid #f4f4f5; cursor: pointer"
                    />
                  </el-tooltip>
                </el-upload>
                <h3 style="margin: 0; font-size: 1.1rem; color: #333">{{ userStore.username }}</h3>
              </div>

              <el-divider style="margin: 10px 0" />

              <!-- 修改昵称 -->
              <div style="margin: 10px 0">
                <div style="font-size: 0.8rem; color: #999; margin-bottom: 6px">修改昵称</div>
                <el-input v-model="newUsernameInput" placeholder="输入新名字" size="default">
                  <template #append>
                    <el-button style="color: #409eff" @click="updateUsername">保存</el-button>
                  </template>
                </el-input>
              </div>

              <el-divider style="margin: 10px 0" />

              <!-- ====== 功能菜单：设置/主题/Banner/日夜 ====== -->
              <div class="submenu-list">
                <!-- 设置 -->
                <div class="submenu-row" @click="openSetting">
                  <el-icon class="submenu-icon"><Setting /></el-icon>
                  <span class="submenu-label">设置</span>
                  <el-icon class="submenu-arrow"><ArrowRight /></el-icon>
                </div>

                <!-- 主题与材质：hover 行右侧弹出独立子面板（el-popover） -->
                <el-popover
                  placement="right-start"
                  trigger="hover"
                  :show-arrow="false"
                  :offset="0"
                  popper-class="submenu-popper"
                >
                  <template #reference>
                    <div class="submenu-row">
                      <el-icon class="submenu-icon"><Brush /></el-icon>
                      <span class="submenu-label">主题与材质设置</span>
                      <el-icon class="submenu-arrow"><ArrowRight /></el-icon>
                    </div>
                  </template>
                  <div class="submenu-panel-content">
                    <div class="submenu-section-title">材质</div>
                    <div
                      class="submenu-item"
                      :class="{ active: siteStore.glassType === 'default' }"
                      @click="handleThemeCommand('glass_default')"
                    >
                      <span>毛玻璃</span>
                      <el-icon v-if="siteStore.glassType === 'default'" color="#67C23A"
                        ><Check
                      /></el-icon>
                    </div>
                    <div
                      class="submenu-item"
                      :class="{ active: siteStore.glassType === 'liquid' }"
                      @click="handleThemeCommand('glass_liquid')"
                    >
                      <span>流光液态玻璃</span>
                      <el-icon v-if="siteStore.glassType === 'liquid'" color="#67C23A"
                        ><Check
                      /></el-icon>
                    </div>
                    <div
                      class="submenu-item"
                      :class="{ active: siteStore.glassType === 'liquid_clear' }"
                      @click="handleThemeCommand('glass_liquid_clear')"
                    >
                      <span>清透水晶</span>
                      <el-icon v-if="siteStore.glassType === 'liquid_clear'" color="#67C23A"
                        ><Check
                      /></el-icon>
                    </div>
                    <div class="submenu-section-divider"></div>
                    <div class="submenu-section-title">颜色</div>
                    <div
                      class="submenu-item"
                      :class="{ active: siteStore.themeColor === 'white' }"
                      @click="handleThemeCommand('color_white')"
                    >
                      <span
                        ><span
                          class="color-dot"
                          style="background: #fff; border: 1px solid #ddd"
                        ></span
                        >经典白</span
                      >
                      <el-icon v-if="siteStore.themeColor === 'white'" color="#67C23A"
                        ><Check
                      /></el-icon>
                    </div>
                    <div
                      class="submenu-item"
                      :class="{ active: siteStore.themeColor === 'blue' }"
                      @click="handleThemeCommand('color_blue')"
                    >
                      <span><span class="color-dot" style="background: #e6f7ff"></span>天空蓝</span>
                      <el-icon v-if="siteStore.themeColor === 'blue'" color="#67C23A"
                        ><Check
                      /></el-icon>
                    </div>
                    <div
                      class="submenu-item"
                      :class="{ active: siteStore.themeColor === 'pink' }"
                      @click="handleThemeCommand('color_pink')"
                    >
                      <span><span class="color-dot" style="background: #fff0f6"></span>樱花粉</span>
                      <el-icon v-if="siteStore.themeColor === 'pink'" color="#67C23A"
                        ><Check
                      /></el-icon>
                    </div>
                    <div
                      class="submenu-item"
                      :class="{ active: siteStore.themeColor === 'green' }"
                      @click="handleThemeCommand('color_green')"
                    >
                      <span><span class="color-dot" style="background: #f0f9eb"></span>薄荷绿</span>
                      <el-icon v-if="siteStore.themeColor === 'green'" color="#67C23A"
                        ><Check
                      /></el-icon>
                    </div>
                    <div
                      class="submenu-item"
                      :class="{ active: siteStore.themeColor === 'purple' }"
                      @click="handleThemeCommand('color_purple')"
                    >
                      <span
                        ><span
                          class="color-dot"
                          style="background: #f3e8ff; border: 1px solid #d9b8f1"
                        ></span
                        >薰衣紫</span
                      >
                      <el-icon v-if="siteStore.themeColor === 'purple'" color="#67C23A"
                        ><Check
                      /></el-icon>
                    </div>
                    <div
                      class="submenu-item"
                      :class="{ active: siteStore.themeColor === 'orange' }"
                      @click="handleThemeCommand('color_orange')"
                    >
                      <span
                        ><span
                          class="color-dot"
                          style="background: #fff3e6; border: 1px solid #f3d19e"
                        ></span
                        >暖阳橙</span
                      >
                      <el-icon v-if="siteStore.themeColor === 'orange'" color="#67C23A"
                        ><Check
                      /></el-icon>
                    </div>
                  </div>
                </el-popover>

                <!-- Banner 设置：hover 行右侧弹出独立子面板 -->
                <el-popover
                  placement="right-start"
                  trigger="hover"
                  :show-arrow="false"
                  :offset="0"
                  popper-class="submenu-popper"
                >
                  <template #reference>
                    <div class="submenu-row">
                      <el-icon class="submenu-icon"><Picture /></el-icon>
                      <span class="submenu-label">Banner 设置</span>
                      <el-icon class="submenu-arrow"><ArrowRight /></el-icon>
                    </div>
                  </template>
                  <div class="submenu-panel-content">
                    <div
                      class="submenu-item"
                      :class="{ active: siteStore.bannerMode === 'banner' }"
                      @click="changeBannerMode('banner')"
                    >
                      <span>横幅图模式</span>
                      <el-icon v-if="siteStore.bannerMode === 'banner'" color="#67C23A"
                        ><Check
                      /></el-icon>
                    </div>
                    <div
                      class="submenu-item"
                      :class="{ active: siteStore.bannerMode === 'fullscreen' }"
                      @click="changeBannerMode('fullscreen')"
                    >
                      <span>填充屏幕</span>
                      <el-icon v-if="siteStore.bannerMode === 'fullscreen'" color="#67C23A"
                        ><Check
                      /></el-icon>
                    </div>
                    <div
                      class="submenu-item"
                      :class="{ active: siteStore.bannerMode === 'background' }"
                      @click="changeBannerMode('background')"
                    >
                      <span>背景图片模式</span>
                      <el-icon v-if="siteStore.bannerMode === 'background'" color="#67C23A"
                        ><Check
                      /></el-icon>
                    </div>
                    <div
                      class="submenu-item"
                      :class="{ active: siteStore.bannerMode === 'hidden' }"
                      @click="changeBannerMode('hidden')"
                    >
                      <span>隐藏</span>
                      <el-icon v-if="siteStore.bannerMode === 'hidden'" color="#67C23A"
                        ><Check
                      /></el-icon>
                    </div>
                  </div>
                </el-popover>

                <!-- 日夜模式（点击直接切换） -->
                <div class="submenu-row" @click="toggleDarkMode">
                  <el-icon class="submenu-icon">
                    <component :is="siteStore.isDark ? Sunny : Moon" />
                  </el-icon>
                  <span class="submenu-label">{{
                    siteStore.isDark ? '日间模式' : '夜间模式'
                  }}</span>
                  <el-icon class="submenu-arrow"><ArrowRight /></el-icon>
                </div>
              </div>

              <el-divider style="margin: 10px 0" />

              <el-button
                type="danger"
                plain
                style="width: 100%; border-radius: 8px"
                @click="logout"
              >
                退出登录
              </el-button>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </nav>
  </div>

  <!-- 登录弹窗 -->
  <el-dialog v-model="showLoginDialog" title="账号登录" width="360px">
    <el-input v-model="loginForm.username" placeholder="请输入账号" style="margin-bottom: 15px">
      <template #append>
        <el-button @click="handleCheckStatus">检测状态</el-button>
      </template>
    </el-input>

    <div
      v-if="checkStatusResult"
      style="margin-top: -5px; margin-bottom: 15px; display: flex; align-items: center"
    >
      <el-tag v-if="checkStatusResult.status === 'approved'" type="success" effect="dark">
        <el-icon style="vertical-align: middle; margin-right: 4px"><Check /></el-icon>
        {{ checkStatusResult.message }}
      </el-tag>
      <el-tag v-else-if="checkStatusResult.status === 'pending'" type="warning" effect="dark">
        <el-icon style="vertical-align: middle; margin-right: 4px"><Clock /></el-icon>
        {{ checkStatusResult.message }}
      </el-tag>
      <el-tag v-else type="info">
        <el-icon style="vertical-align: middle; margin-right: 4px"><Warning /></el-icon>
        {{ checkStatusResult.message }}
      </el-tag>
    </div>

    <el-input
      v-model="loginForm.password"
      type="password"
      placeholder="请输入密码"
      show-password
      style="margin-bottom: 15px"
    />
    <el-checkbox v-model="loginForm.remember">记住账号</el-checkbox>

    <template #footer>
      <el-button @click="showLoginDialog = false">取消</el-button>
      <el-button type="primary" @click="handleLoginSubmit">确定登录</el-button>
    </template>
  </el-dialog>

  <SettingDrawer
    v-model:visible="showSettingDrawer"
    :config="siteStore.siteConfig"
    @update-config="handleConfigUpdate"
  />
</template>

<style scoped>
.nav-container {
  position: fixed;
  top: 15px;
  left: 0;
  width: 100%;
  display: flex;
  justify-content: center;
  z-index: 999;
  padding: 0 20px;
  box-sizing: border-box;
}

.navbar {
  width: 100%;
  max-width: 1160px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-radius: 50px;
  padding: 10px 30px;
  margin: 0;
  /* 不透明底色：滚动时内容不再从导航栏后透出。
     保留 backdrop-filter 让导航栏边缘与背景过渡仍然自然。 */
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
}
html.dark .navbar {
  background: rgba(30, 30, 30, 0.92);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
}

/* 液态玻璃/清透水晶模式下，导航栏也需要不透明底色，
   否则液态样式会把 background 改成近透明，内容又会透出来 */
html.liquid-glass .navbar,
html.liquid-glass-clear .navbar {
  background: rgba(255, 255, 255, 0.92);
}
html.dark.liquid-glass .navbar,
html.dark.liquid-glass-clear .navbar {
  background: rgba(20, 20, 20, 0.92);
}

/* 主题色模式下，让导航栏底色跟随主题色（不透明） */
html.theme-color-blue:not(.dark) .navbar {
  background: rgba(230, 247, 255, 0.95);
}
html.theme-color-pink:not(.dark) .navbar {
  background: rgba(255, 240, 246, 0.95);
}
html.theme-color-green:not(.dark) .navbar {
  background: rgba(240, 249, 235, 0.95);
}
html.theme-color-purple:not(.dark) .navbar {
  background: rgba(243, 232, 255, 0.95);
}
html.theme-color-orange:not(.dark) .navbar {
  background: rgba(255, 243, 230, 0.95);
}

.nav-links {
  display: flex;
  gap: 20px;
}
.nav-links span {
  font-weight: bold;
  cursor: pointer;
  transition: color 0.3s;
}
.nav-links span:hover {
  color: #409eff;
}

.nav-icons {
  display: flex;
  gap: 15px;
  align-items: center;
}

.icon-btn {
  font-size: 22px;
  cursor: pointer;
  outline: none;
  transition: all 0.3s;
  color: #333;
}
html.dark .icon-btn {
  color: #e5eaf3;
}
.el-dropdown-link {
  color: inherit;
  display: flex;
  align-items: center;
}
.icon-btn:hover {
  color: #409eff;
  transform: scale(1.1);
}

.divider {
  width: 1px;
  height: 20px;
  background-color: rgba(0, 0, 0, 0.2);
  margin: 0 5px;
}
html.dark .divider {
  background-color: rgba(255, 255, 255, 0.2);
}

.login-avatar {
  cursor: pointer;
  border: 2px solid transparent;
  transition:
    border-color 0.3s,
    transform 0.3s;
}
.login-avatar:hover {
  transform: scale(1.1);
  border-color: #409eff;
}

/* 手机端适配 */
@media screen and (max-width: 768px) {
  .nav-container {
    top: 5px !important;
    padding: 0 10px !important;
  }
  .navbar {
    padding: 10px !important;
    border-radius: 16px !important;
  }
  .nav-links {
    overflow-x: auto;
    white-space: nowrap;
    -webkit-overflow-scrolling: touch;
    padding-bottom: 2px;
  }
  .nav-links::-webkit-scrollbar {
    display: none;
  }
  .nav-links span {
    font-size: 0.9rem;
  }
}
</style>

<!-- 全局样式：头像下拉菜单（el-dropdown 弹层 teleport 到 body，scoped 不生效） -->
<style>
/* ===== 弹窗背景跟随主题色 ===== */
.avatar-dropdown-popper .el-dropdown-menu {
  width: 260px;
  padding: 15px;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  background: rgba(255, 255, 255, 0.95) !important;
  border: 1px solid rgba(0, 0, 0, 0.06);
}
html.dark .avatar-dropdown-popper .el-dropdown-menu {
  background: rgba(30, 30, 30, 0.95) !important;
  border-color: rgba(255, 255, 255, 0.08);
}
html.theme-color-blue:not(.dark) .avatar-dropdown-popper .el-dropdown-menu {
  background: rgba(230, 247, 255, 0.95) !important;
}
html.theme-color-pink:not(.dark) .avatar-dropdown-popper .el-dropdown-menu {
  background: rgba(255, 240, 246, 0.95) !important;
}
html.theme-color-green:not(.dark) .avatar-dropdown-popper .el-dropdown-menu {
  background: rgba(240, 249, 235, 0.95) !important;
}
html.theme-color-purple:not(.dark) .avatar-dropdown-popper .el-dropdown-menu {
  background: rgba(243, 232, 255, 0.95) !important;
}
html.theme-color-orange:not(.dark) .avatar-dropdown-popper .el-dropdown-menu {
  background: rgba(255, 243, 230, 0.95) !important;
}

/* ===== 菜单结构 ===== */
.avatar-dropdown-popper .submenu-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

/* 一级菜单行 */
.avatar-dropdown-popper .submenu-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}
.avatar-dropdown-popper .submenu-row:hover {
  background: rgba(64, 158, 255, 0.08);
}
.avatar-dropdown-popper .submenu-icon {
  font-size: 1.1rem;
  color: #666;
}
.avatar-dropdown-popper .submenu-label {
  flex: 1;
  font-size: 0.9rem;
  color: #333;
}
.avatar-dropdown-popper .submenu-arrow {
  font-size: 0.8rem;
  color: #ccc;
  transition:
    transform 0.3s,
    color 0.2s;
}
.avatar-dropdown-popper .submenu-arrow.rotated {
  transform: rotate(90deg);
  color: #409eff;
}
.avatar-dropdown-popper .submenu-row:hover .submenu-arrow {
  color: #409eff;
}
html.dark .avatar-dropdown-popper .submenu-icon {
  color: #ccc;
}
html.dark .avatar-dropdown-popper .submenu-label {
  color: #eee;
}

/* el-popover 子面板内容容器（右侧弹出的独立面板） */
.submenu-popper.el-popover.el-popper {
  padding: 8px !important;
  border-radius: 10px !important;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15) !important;
  background: rgba(255, 255, 255, 0.98) !important;
  border: 1px solid rgba(0, 0, 0, 0.06) !important;
  min-width: 180px;
}
html.dark .submenu-popper.el-popover.el-popper {
  background: rgba(30, 30, 30, 0.98) !important;
  border-color: rgba(255, 255, 255, 0.08) !important;
}
/* 主题色跟随 */
html.theme-color-blue:not(.dark) .submenu-popper.el-popover.el-popper {
  background: rgba(230, 247, 255, 0.98) !important;
}
html.theme-color-pink:not(.dark) .submenu-popper.el-popover.el-popper {
  background: rgba(255, 240, 246, 0.98) !important;
}
html.theme-color-green:not(.dark) .submenu-popper.el-popover.el-popper {
  background: rgba(240, 249, 235, 0.98) !important;
}
html.theme-color-purple:not(.dark) .submenu-popper.el-popover.el-popper {
  background: rgba(243, 232, 255, 0.98) !important;
}
html.theme-color-orange:not(.dark) .submenu-popper.el-popover.el-popper {
  background: rgba(255, 243, 230, 0.98) !important;
}

/* 子面板内容 */
.submenu-panel-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

/* 分组标题 */
.submenu-popper .submenu-section-title {
  font-size: 0.75rem;
  color: #999;
  padding: 4px 12px;
  font-weight: bold;
}
.submenu-popper .submenu-section-divider {
  height: 1px;
  background: rgba(0, 0, 0, 0.08);
  margin: 4px 0;
}
html.dark .submenu-popper .submenu-section-divider {
  background: rgba(255, 255, 255, 0.08);
}

/* 子选项 */
.submenu-popper .submenu-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  color: #333;
  transition: background 0.2s;
}
.submenu-popper .submenu-item:hover {
  background: rgba(64, 158, 255, 0.1);
}
.submenu-popper .submenu-item.active {
  color: #409eff;
  font-weight: bold;
}
html.dark .submenu-popper .submenu-item {
  color: #ddd;
}

/* 颜色小圆点 */
.submenu-popper .color-dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-right: 8px;
}
</style>
