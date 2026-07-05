// 公共 Markdown-it 实例：供 ArticleDetail 与 Write 共享同一份渲染/高亮配置
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'

// Note: github.css 仍由各使用方在 <style> 外手动 import
import 'highlight.js/styles/github.css'

export const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  highlight(str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, { language: lang }).value
      } catch (_) {
        /* ignore */
      }
    }
    return '' // 使用默认转义
  }
})

/**
 * 从一个渲染好的 Markdown DOM 容器里抽取标题，生成 TOC 列表
 * @param {HTMLElement} container
 * @returns {Array<{id:string,text:string,level:number}>}
 */
export function extractToc(container) {
  if (!container) return []
  const headers = container.querySelectorAll('h1, h2, h3, h4, h5, h6')
  const toc = []
  headers.forEach((header, index) => {
    const id = `heading-${index}`
    header.id = id
    const level = parseInt(header.tagName.replace('H', ''), 10)
    toc.push({ id, text: header.innerText, level })
  })
  return toc
}
