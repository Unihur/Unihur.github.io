// Live2D 看板娘封装
// - 解决原 App.vue 用 let oml2dInstance + window.__oml2dInstance__ 两套状态不同步的问题
// - 统一实例引用、提供 load / changeModel / close / reload
import { loadOml2d } from 'oh-my-live2d'

let oml2dInstance = null

/**
 * @param {object} siteConfig 必须包含 live2dPath / live2dScale 字段
 */
export function useLive2d(siteConfig) {
  function load() {
    if (oml2dInstance) return

    // 响应式：按屏幕宽度自适应大小和横向偏移
    const screenWidth = window.innerWidth
    let adaptiveScale = siteConfig.live2dScale
    let offsetX = 0
    if (screenWidth < 1400 && screenWidth >= 1000) {
      adaptiveScale = siteConfig.live2dScale * 0.7
      offsetX = -50
    } else if (screenWidth < 1000) {
      adaptiveScale = siteConfig.live2dScale * 0.5
      offsetX = -100
    }

    oml2dInstance = loadOml2d({
      models: [
        {
          path: siteConfig.live2dPath,
          scale: adaptiveScale,
          position: [offsetX, 0]
        }
      ],
      primaryColor: '#ff79c6',
      menus: {
        disable: false,
        items: (defaultItems) => [
          defaultItems[0],
          defaultItems[1],
          {
            id: 'Hide',
            name: '隐藏看板娘',
            icon: 'icon-close',
            onClick: () => {
              oml2dInstance?.stage.slideOut()
            }
          }
        ]
      }
    })
  }

  function changeModel(newPath) {
    oml2dInstance?.loadNextModel({ path: newPath })
  }

  function getInstance() {
    return oml2dInstance
  }

  return { load, changeModel, getInstance }
}
