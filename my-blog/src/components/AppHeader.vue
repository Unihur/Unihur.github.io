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
  Warning
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
  // 写作按钮：只有管理员可以点击，非管理员仅提示不登出
  if (!userStore.isAdmin) {
    ElMessage.warning('暂无权限：仅管理员可以发布或编辑文章！')
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
        <el-tooltip content="设置" placement="bottom">
          <el-icon class="icon-btn" @click="openSetting"><Setting /></el-icon>
        </el-tooltip>

        <el-dropdown trigger="click" @command="handleThemeCommand">
          <span class="el-dropdown-link">
            <el-tooltip content="主题与材质设置" placement="bottom">
              <el-icon class="icon-btn"><Brush /></el-icon>
            </el-tooltip>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item
                command="glass_default"
                style="display: flex; justify-content: space-between; align-items: center"
              >
                <span>毛玻璃</span>
                <el-icon v-if="siteStore.glassType === 'default'" color="#67C23A"
                  ><Check
                /></el-icon>
              </el-dropdown-item>
              <el-dropdown-item
                command="glass_liquid"
                style="display: flex; justify-content: space-between; align-items: center"
              >
                <span>流光液态玻璃</span>
                <el-icon v-if="siteStore.glassType === 'liquid'" color="#67C23A"><Check /></el-icon>
              </el-dropdown-item>
              <el-dropdown-item
                command="glass_liquid_clear"
                style="display: flex; justify-content: space-between; align-items: center"
              >
                <span>清透水晶</span>
                <el-icon v-if="siteStore.glassType === 'liquid_clear'" color="#67C23A"
                  ><Check
                /></el-icon>
              </el-dropdown-item>

              <el-divider style="margin: 4px 0" />

              <el-dropdown-item
                command="color_white"
                style="display: flex; justify-content: space-between; align-items: center"
              >
                <span
                  ><span
                    style="
                      display: inline-block;
                      width: 12px;
                      height: 12px;
                      border-radius: 50%;
                      background: #ffffff;
                      border: 1px solid #ddd;
                      margin-right: 8px;
                    "
                  ></span
                  >经典白</span
                >
                <el-icon v-if="siteStore.themeColor === 'white'" color="#67C23A"><Check /></el-icon>
              </el-dropdown-item>
              <el-dropdown-item
                command="color_blue"
                style="display: flex; justify-content: space-between; align-items: center"
              >
                <span
                  ><span
                    style="
                      display: inline-block;
                      width: 12px;
                      height: 12px;
                      border-radius: 50%;
                      background: #e6f7ff;
                      margin-right: 8px;
                    "
                  ></span
                  >天空蓝</span
                >
                <el-icon v-if="siteStore.themeColor === 'blue'" color="#67C23A"><Check /></el-icon>
              </el-dropdown-item>
              <el-dropdown-item
                command="color_pink"
                style="display: flex; justify-content: space-between; align-items: center"
              >
                <span
                  ><span
                    style="
                      display: inline-block;
                      width: 12px;
                      height: 12px;
                      border-radius: 50%;
                      background: #fff0f6;
                      margin-right: 8px;
                    "
                  ></span
                  >樱花粉</span
                >
                <el-icon v-if="siteStore.themeColor === 'pink'" color="#67C23A"><Check /></el-icon>
              </el-dropdown-item>
              <el-dropdown-item
                command="color_green"
                style="display: flex; justify-content: space-between; align-items: center"
              >
                <span
                  ><span
                    style="
                      display: inline-block;
                      width: 12px;
                      height: 12px;
                      border-radius: 50%;
                      background: #f0f9eb;
                      margin-right: 8px;
                    "
                  ></span
                  >薄荷绿</span
                >
                <el-icon v-if="siteStore.themeColor === 'green'" color="#67C23A"><Check /></el-icon>
              </el-dropdown-item>
              <el-dropdown-item
                command="color_purple"
                style="display: flex; justify-content: space-between; align-items: center"
              >
                <span
                  ><span
                    style="
                      display: inline-block;
                      width: 12px;
                      height: 12px;
                      border-radius: 50%;
                      background: #f3e8ff;
                      border: 1px solid #d9b8f1;
                      margin-right: 8px;
                    "
                  ></span
                  >薰衣紫</span
                >
                <el-icon v-if="siteStore.themeColor === 'purple'" color="#67C23A"
                  ><Check
                /></el-icon>
              </el-dropdown-item>
              <el-dropdown-item
                command="color_orange"
                style="display: flex; justify-content: space-between; align-items: center"
              >
                <span
                  ><span
                    style="
                      display: inline-block;
                      width: 12px;
                      height: 12px;
                      border-radius: 50%;
                      background: #fff3e6;
                      border: 1px solid #f3d19e;
                      margin-right: 8px;
                    "
                  ></span
                  >暖阳橙</span
                >
                <el-icon v-if="siteStore.themeColor === 'orange'" color="#67C23A"
                  ><Check
                /></el-icon>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <el-dropdown trigger="click" @command="changeBannerMode">
          <span class="el-dropdown-link">
            <el-tooltip content="Banner设置" placement="bottom">
              <el-icon class="icon-btn"><Picture /></el-icon>
            </el-tooltip>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item
                command="banner"
                style="display: flex; justify-content: space-between; align-items: center"
              >
                <span>横幅图模式</span>
                <el-icon v-if="siteStore.bannerMode === 'banner'" color="#67C23A"
                  ><Check
                /></el-icon>
              </el-dropdown-item>
              <el-dropdown-item
                command="fullscreen"
                style="display: flex; justify-content: space-between; align-items: center"
              >
                <span>填充屏幕</span>
                <el-icon v-if="siteStore.bannerMode === 'fullscreen'" color="#67C23A"
                  ><Check
                /></el-icon>
              </el-dropdown-item>
              <el-dropdown-item
                command="background"
                style="display: flex; justify-content: space-between; align-items: center"
              >
                <span>背景图片模式</span>
                <el-icon v-if="siteStore.bannerMode === 'background'" color="#67C23A"
                  ><Check
                /></el-icon>
              </el-dropdown-item>
              <el-dropdown-item
                command="hidden"
                style="display: flex; justify-content: space-between; align-items: center"
              >
                <span>隐藏</span>
                <el-icon v-if="siteStore.bannerMode === 'hidden'" color="#67C23A"
                  ><Check
                /></el-icon>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <el-tooltip :content="siteStore.isDark ? '日间模式' : '夜间模式'" placement="bottom">
          <el-icon class="icon-btn" @click="toggleDarkMode">
            <component :is="siteStore.isDark ? Sunny : Moon" />
          </el-icon>
        </el-tooltip>

        <!-- 登录头像 -->
        <div class="divider"></div>
        <el-dropdown
          :disabled="!userStore.isLoggedIn"
          trigger="hover"
          :hide-on-click="false"
          placement="bottom-end"
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
            <el-dropdown-menu
              style="
                width: 260px;
                padding: 15px;
                border-radius: 12px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
              "
            >
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

              <div style="margin: 10px 0">
                <div style="font-size: 0.8rem; color: #999; margin-bottom: 6px">修改昵称</div>
                <el-input v-model="newUsernameInput" placeholder="输入新名字" size="default">
                  <template #append>
                    <el-button style="color: #409eff" @click="updateUsername">保存</el-button>
                  </template>
                </el-input>
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
