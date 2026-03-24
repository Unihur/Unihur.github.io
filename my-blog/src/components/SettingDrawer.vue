<template>
  <el-drawer v-model="drawerVisible" title="博客高级设置" direction="rtl" size="400px">
    <div class="setting-container">
      
      <div class="setting-tip">
        <el-icon><InfoFilled /></el-icon> 设置内容已开启【实时热更新】！
      </div>

      <el-form label-position="top">
        <el-form-item label="用户名称">
          <el-input v-model="localConfig.name" placeholder="请输入你的博客名字" />
        </el-form-item>

        <el-form-item label="个人描述">
          <el-input v-model="localConfig.signature" type="textarea" :rows="3" />
        </el-form-item>

        <!-- 隐藏的本地文件选择器 -->
        <input type="file" ref="fileInput" accept="image/*" style="display: none" @change="handleFileUpload" />

        <div style="display: flex; gap: 20px;">
          <el-form-item label="用户头像 (点击修改)">
            <div class="img-preview" @click="triggerUpload('avatar')">
              <img :src="localConfig.avatar" alt="avatar">
              <div class="hover-mask">更换</div>
            </div>
          </el-form-item>

          <el-form-item label="网站图标 (点击修改)">
            <div class="img-preview" @click="triggerUpload('favicon')">
              <img :src="localConfig.favicon" alt="favicon" style="border-radius: 8px;">
              <div class="hover-mask">更换</div>
            </div>
          </el-form-item>
        </div>
        
        <el-divider>Live2D 看板娘设置</el-divider>

        <el-form-item label="看板娘状态">
          <el-switch v-model="localConfig.live2dEnabled" active-text="开启" inactive-text="关闭" />
        </el-form-item>

        <template v-if="localConfig.live2dEnabled">
          <el-form-item label="模型路径">
            <el-input v-model="localConfig.live2dPath" placeholder="支持在线URL或 /xxx.model3.json" />
          </el-form-item>

          <el-form-item label="模型大小 (缩放比例)">
            <el-slider v-model="localConfig.live2dScale" :min="0.5" :max="3" :step="0.1" show-input />
          </el-form-item>

          <el-form-item label="模型位置">
            <el-radio-group v-model="localConfig.live2dPosition">
              <el-radio label="left" border>左下角</el-radio>
              <el-radio label="right" border>右下角</el-radio>
            </el-radio-group>
          </el-form-item>
        </template>

      </el-form>
    </div>
  </el-drawer>
</template>

<script setup>
import { ref, watch, defineProps, defineEmits } from 'vue'
import { InfoFilled } from '@element-plus/icons-vue'

const props = defineProps({ visible: Boolean, config: Object })
const emit = defineEmits(['update:visible', 'updateConfig'])
const drawerVisible = ref(props.visible)

// 深度克隆一份本地数据
const localConfig = ref(JSON.parse(JSON.stringify(props.config)))

// 监听外部可见性
watch(() => props.visible, (newVal) => {
  drawerVisible.value = newVal
  if (newVal) localConfig.value = JSON.parse(JSON.stringify(props.config))
})
watch(drawerVisible, (newVal) => emit('update:visible', newVal))

// ！！！核心修改：深度监听 localConfig 的任何细微变化，瞬间发送给 App.vue ！！！
watch(() => localConfig.value, (newVal) => {
  emit('updateConfig', newVal)
}, { deep: true }) // deep: true 代表对象里面的属性变了也能监听到

// ================= 本地图片 1:1 裁切上传逻辑 =================
const fileInput = ref(null)
const currentUploadType = ref('')

const triggerUpload = (type) => {
  currentUploadType.value = type
  fileInput.value.click()
}

const cropImageToSquare = (file) => {
  return new Promise((resolve) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const img = new Image()
      img.onload = () => {
        const canvas = document.createElement('canvas')
        const size = Math.min(img.width, img.height)
        canvas.width = size
        canvas.height = size
        const ctx = canvas.getContext('2d')
        const startX = (img.width - size) / 2
        const startY = (img.height - size) / 2
        ctx.drawImage(img, startX, startY, size, size, 0, 0, size, size)
        resolve(canvas.toDataURL(file.type))
      }
      img.src = e.target.result
    }
    reader.readAsDataURL(file)
  })
}

const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  const base64Img = await cropImageToSquare(file)
  if (currentUploadType.value === 'avatar') localConfig.value.avatar = base64Img
  else if (currentUploadType.value === 'favicon') localConfig.value.favicon = base64Img
  event.target.value = '' 
}
</script>

<style scoped>
.setting-container { padding: 0 10px; padding-bottom: 50px; }
.setting-tip { display: flex; align-items: center; gap: 8px; background-color: rgba(103, 194, 58, 0.1); color: #67C23A; padding: 10px; border-radius: 8px; margin-bottom: 20px; font-size: 0.9rem; font-weight: bold; }
.img-preview { position: relative; width: 80px; height: 80px; border-radius: 50%; border: 2px dashed #dcdfe6; overflow: hidden; cursor: pointer; transition: all 0.3s; }
.img-preview:hover { border-color: #409EFF; }
.img-preview img { width: 100%; height: 100%; object-fit: cover; }
.hover-mask { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); color: #fff; display: flex; align-items: center; justify-content: center; opacity: 0; transition: opacity 0.3s; font-size: 14px; }
.img-preview:hover .hover-mask { opacity: 1; }
</style>