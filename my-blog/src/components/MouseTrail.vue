<template>
  <!-- 这是一个全屏透明、鼠标可穿透的画布 -->
  <canvas ref="canvasRef" class="mouse-trail-canvas"></canvas>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const canvasRef = ref(null)

onMounted(() => {
  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d')
  let particles = []
  let ripples = [] // 新增：用来存水波纹的数据
  
  let lastTime = 0
  const generateInterval = 30 
  
  const resize = () => {
    canvas.width = window.innerWidth
    canvas.height = window.innerHeight
  }
  window.addEventListener('resize', resize)
  resize()

  const addParticle = (e) => {
    const now = Date.now()
    if (now - lastTime < generateInterval) return 
    lastTime = now

    particles.push({
      x: e.clientX,
      y: e.clientY,
      size: Math.random() * 8 + 6, 
      color: `hsl(${Math.random() * 60 + 300}, 100%, 70%)`,
      life: 1 
    })
  }
  window.addEventListener('mousemove', addParticle)

  // 新增：鼠标点击时产生水波纹
  const addRipple = (e) => {
    ripples.push({
      x: e.clientX,
      y: e.clientY,
      radius: 0,      // 初始半径
      alpha: 1,       // 初始透明度
      maxRadius: 50 + Math.random() * 20 // 扩散的最大半径
    })
  }
  window.addEventListener('click', addRipple)

  const animate = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    
    // 1. 画心形拖尾
    for (let i = 0; i < particles.length; i++) {
      let p = particles[i]
      ctx.beginPath()
      const x = p.x, y = p.y, size = p.size 
      ctx.moveTo(x, y - size / 4)
      ctx.bezierCurveTo(x, y - size, x - size, y - size, x - size, y - size / 4)
      ctx.bezierCurveTo(x - size, y + size / 2, x, y + size, x, y + size)
      ctx.bezierCurveTo(x, y + size, x + size, y + size / 2, x + size, y - size / 4)
      ctx.bezierCurveTo(x + size, y - size, x, y - size, x, y - size / 4)
      ctx.fillStyle = p.color
      ctx.globalAlpha = p.life
      ctx.fill()
      
      p.life -= 0.01   
      p.size -= 0.05   
      p.y += 0.5       
      
      if (p.life <= 0 || p.size <= 0) {
        particles.splice(i, 1)
        i--
      }
    }

    // 2. 画点击的水波纹
    for (let i = 0; i < ripples.length; i++) {
      let r = ripples[i]
      ctx.beginPath()
      ctx.arc(r.x, r.y, r.radius, 0, Math.PI * 2)
      // 使用粉色边框画圆环
      ctx.strokeStyle = `rgba(255, 121, 198, ${r.alpha})`
      ctx.lineWidth = 2
      ctx.stroke()

      // 半径扩大，透明度降低
      r.radius += 1
      r.alpha -= 0.01

      if (r.alpha <= 0) {
        ripples.splice(i, 1)
        i--
      }
    }

    ctx.globalAlpha = 1
    requestAnimationFrame(animate)
  }
  animate()

  onUnmounted(() => {
    window.removeEventListener('resize', resize)
    window.removeEventListener('mousemove', addParticle)
    window.removeEventListener('click', addRipple) // 记得解绑点击事件
  })
})
</script>

<style scoped>
.mouse-trail-canvas {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  pointer-events: none; /* 核心：让鼠标穿透画布去点击下方的按钮 */
  z-index: 9999; /* 永远在最顶层 */
}
</style>