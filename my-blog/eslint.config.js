// ESLint 配置：Vue 3 + Prettier
// 使用 eslint-plugin-vue 推荐规则 + prettier 自动格式化
import js from '@eslint/js'
import vue from 'eslint-plugin-vue'
import prettier from 'eslint-plugin-prettier/recommended'
import globals from 'globals'

export default [
  // 忽略构建产物与依赖
  {
    ignores: ['dist/**', 'node_modules/**', '*.d.ts', 'dev-*.log']
  },
  // JS 基础规则
  js.configs.recommended,
  // Vue 推荐规则
  ...vue.configs['flat/recommended'],
  // Prettier 整合（关闭与 prettier 冲突的规则，并把格式问题报为 warning）
  prettier,
  {
    // 全局变量与浏览器环境
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node
      },
      ecmaVersion: 'latest',
      sourceType: 'module'
    },
    rules: {
      // === 项目级宽松规则 ===
      // 函数/变量命名风格不强制（项目里现用 camelCase + 个别 PascalCase 组件）
      'vue/multi-word-component-names': 'off',
      // 允许 console.warn / console.error，仅警告 console.log
      'no-console': ['warn', { allow: ['warn', 'error'] }],
      // 允许未使用的函数参数；catch 子句不检查（空 catch 在本项目常见）
      'no-unused-vars': [
        'warn',
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_',
          caughtErrors: 'none'
        }
      ],
      // Vue template 中允许自闭合组件
      'vue/html-self-closing': 'off',
      // 不强制每行最大属性数
      'vue/max-attributes-per-line': 'off',
      // 允许 template 中使用复杂表达式
      'vue/no-template-syntax': 'off',
      // 允许 v-html：本项目用 markdown-it 渲染文章正文，源头可控
      'vue/no-v-html': 'off',
      // Vue 3 + defineProps 不强制要求 default
      'vue/require-default-prop': 'off',
      // prettier 问题统一为 warning，不阻断 build
      'prettier/prettier': 'warn'
    }
  }
]
