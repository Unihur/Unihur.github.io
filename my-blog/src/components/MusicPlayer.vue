<template>
  <div class="glass-box modern-player">
    
    <!-- 左侧：旋转的唱片封面 -->
    <div class="cover-wrapper" :class="{ 'is-playing': isPlaying }">
      <img :src="currentSong.cover" alt="cover" class="cover-img" />
      <div class="cover-hole"></div> <!-- 唱片中间的小圆孔 -->
    </div>

    <!-- 中间：歌曲信息与���度条 -->
    <div class="info-wrapper">
      <div class="song-title">{{ currentSong.title }}</div>
      <div class="song-artist">{{ currentSong.artist }}</div>
      
      <!-- 进度条 -->
      <div class="progress-container" @click="seekAudio">
        <div class="progress-bar" :style="{ width: progressPercent + '%' }"></div>
      </div>
      <div class="time-display">
        <span>{{ formatTime(currentTime) }}</span>
        <span>{{ formatTime(duration) }}</span>
      </div>
    </div>

    <!-- 右侧：控制按钮 -->
    <div class="controls">
      <el-icon class="play-btn" @click="togglePlay">
        <!-- 动态切换播放/暂停图标 -->
        <component :is="isPlaying ? VideoPause : VideoPlay" />
      </el-icon>
    </div>

    <!-- 隐藏的原生 audio 标签 -->
    <audio 
      ref="audioRef" 
      :src="currentSong.url" 
      @timeupdate="onTimeUpdate" 
      @loadedmetadata="onLoadedMetadata"
      @ended="onEnded"
    ></audio>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { VideoPlay, VideoPause } from '@element-plus/icons-vue'

// 音乐播放器的数据 (换成你 public 文件夹里的文件名)
const currentSong = reactive({
  title: '打上花火',
  artist: '米津玄师',
  // 临时用一个绝对不会 403 的测试音频，建议换成你自己的 '/music.mp3'
  url: '/musics/firework.mp3', 
  // 封面图，可以换成 '/cover.jpg'
  cover: '/musics/firework.jpg'
})

const audioRef = ref(null)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const progressPercent = ref(0)

// 播放/暂停切换
const togglePlay = () => {
  if (!audioRef.value) return
  if (isPlaying.value) {
    audioRef.value.pause()
  } else {
    audioRef.value.play()
  }
  isPlaying.value = !isPlaying.value
}

// 音频加载完成，获取总时长
const onLoadedMetadata = () => {
  duration.value = audioRef.value.duration
}

// 播放时更新进度条
const onTimeUpdate = () => {
  if (!audioRef.value) return
  currentTime.value = audioRef.value.currentTime
  progressPercent.value = (currentTime.value / duration.value) * 100
}

// 点击进度条跳转
const seekAudio = (event) => {
  if (!audioRef.value) return
  const rect = event.currentTarget.getBoundingClientRect()
  const clickX = event.clientX - rect.left
  const percent = clickX / rect.width
  audioRef.value.currentTime = percent * duration.value
}

// 播放结束自动重置
const onEnded = () => {
  isPlaying.value = false
  currentTime.value = 0
  progressPercent.value = 0
}

// ���式化时间 (例如 65秒 -> 01:05)
const formatTime = (time) => {
  if (!time || isNaN(time)) return '00:00'
  const m = Math.floor(time / 60).toString().padStart(2, '0')
  const s = Math.floor(time % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}
</script>

<style scoped>
.modern-player {
  display: flex;
  align-items: center;
  padding: 15px 20px;
  gap: 15px;
  background: rgba(255, 255, 255, 0.7);
}
html.dark .modern-player {
  background: rgba(40, 42, 54, 0.8);
}

/* 旋转唱片样式 */
.cover-wrapper {
  position: relative;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  overflow: hidden;
  border: 3px solid #333;
  box-shadow: 0 4px 10px rgba(0,0,0,0.2);
  flex-shrink: 0;
  /* 动画默认暂停 */
  animation: spin 10s linear infinite;
  animation-play-state: paused; 
}
html.dark .cover-wrapper { border-color: #1a1525; }

/* 播放时开启旋转动画 */
.cover-wrapper.is-playing {
  animation-play-state: running;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-hole {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 12px;
  height: 12px;
  background-color: #f4f4f5;
  border-radius: 50%;
  border: 1px solid rgba(0,0,0,0.2);
}
html.dark .cover-hole { background-color: #1a1525; }

/* 歌曲信息 */
.info-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.song-title {
  font-size: 1rem;
  font-weight: bold;
  color: #333;
  margin-bottom: 2px;
}
html.dark .song-title { color: #eee; }

.song-artist {
  font-size: 0.8rem;
  color: #888;
  margin-bottom: 8px;
}
html.dark .song-artist { color: #aaa; }

/* 进度条 */
.progress-container {
  width: 100%;
  height: 6px;
  background-color: rgba(0,0,0,0.1);
  border-radius: 3px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}
html.dark .progress-container { background-color: rgba(255,255,255,0.1); }

.progress-bar {
  height: 100%;
  background-color: #ff79c6; /* 粉色进度条 */
  border-radius: 3px;
  transition: width 0.1s linear;
}

.time-display {
  display: flex;
  justify-content: space-between;
  font-size: 0.7rem;
  color: #999;
  margin-top: 4px;
}

/* 播放按钮 */
.controls {
  display: flex;
  align-items: center;
  justify-content: center;
  padding-left: 10px;
}
.play-btn {
  font-size: 2.5rem;
  color: #ff79c6;
  cursor: pointer;
  transition: transform 0.2s, color 0.2s;
}
.play-btn:hover {
  transform: scale(1.1);
  color: #ff92d0;
}
</style>