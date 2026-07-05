// 打字机特效（模块级单例）
// - 在 App.vue 中调用 useTypewriter().start() 一次即可
// - 任何组件再次调用 useTypewriter() 都拿到同一个 typewriterText
// - 解决原代码 startTypewriter 被调用两次导致的“双重触发” bug
import { ref, watch } from 'vue'

let instance = null

/**
 * @param {() => string} getText  返回当前打字机要显示的完整文本（响应式来源）
 */
export function useTypewriter(getText) {
  if (instance) return instance

  const typewriterText = ref('')
  let timer = null

  function clearTimer() {
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
  }

  function tick() {
    const fullText = getText() || ''
    if (!fullText) {
      typewriterText.value = ''
      return
    }
    let i = typewriterText.value.length
    let isDeleting = false

    const step = () => {
      const current = getText() || ''
      if (!current) {
        typewriterText.value = ''
        return
      }
      if (!isDeleting) {
        typewriterText.value = current.substring(0, i + 1)
        i++
        if (i === current.length) {
          isDeleting = true
          timer = setTimeout(step, 2000)
          return
        }
        timer = setTimeout(step, Math.random() * 100 + 100)
      } else {
        typewriterText.value = current.substring(0, i - 1)
        i--
        if (i === 0) {
          isDeleting = false
          timer = setTimeout(step, 500)
          return
        }
        timer = setTimeout(step, 50)
      }
    }
    step()
  }

  function start() {
    clearTimer()
    tick()
  }

  function stop() {
    clearTimer()
    typewriterText.value = ''
  }

  if (getText) {
    watch(getText, () => start())
  }

  instance = { typewriterText, start, stop }
  return instance
}
