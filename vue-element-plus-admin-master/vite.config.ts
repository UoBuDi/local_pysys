import { resolve } from 'path'
import { loadEnv } from 'vite'
import type { UserConfig, ConfigEnv } from 'vite'
import Vue from '@vitejs/plugin-vue'
import VueJsx from '@vitejs/plugin-vue-jsx'
import progress from 'vite-plugin-progress'
import EslintPlugin from 'vite-plugin-eslint'
import { ViteEjsPlugin } from 'vite-plugin-ejs'
import { viteMockServe } from 'vite-plugin-mock'
import PurgeIcons from 'vite-plugin-purge-icons'
import ServerUrlCopy from 'vite-plugin-url-copy'
import VueI18nPlugin from '@intlify/unplugin-vue-i18n/vite'
import { createSvgIconsPlugin } from 'vite-plugin-svg-icons'
import { createStyleImportPlugin, ElementPlusResolve } from 'vite-plugin-style-import'
import UnoCSS from 'unocss/vite'
import { visualizer } from 'rollup-plugin-visualizer'

// https://vitejs.dev/config/
const root = process.cwd()

function pathResolve(dir: string) {
  return resolve(root, '.', dir)
}

export default ({ command, mode }: ConfigEnv): UserConfig => {
  let env = {} as any
  const isBuild = command === 'build'
  if (!isBuild) {
    env = loadEnv(process.argv[3] === '--mode' ? process.argv[4] : process.argv[3], root)
  } else {
    env = loadEnv(mode, root)
  }
  return {
    base: env.VITE_BASE_PATH,
    plugins: [
      Vue({
        script: {
          // 开启defineModel
          defineModel: true
        }
      }),
      VueJsx(),
      ServerUrlCopy(),
      progress(),
      createStyleImportPlugin({
        resolves: [ElementPlusResolve()],
        libs: [
          {
            libraryName: 'element-plus',
            esModule: true,
            resolveStyle: (name) => {
              const styleMap: Record<string, string> = {
                'el-button': 'button',
                'el-form': 'form',
                'el-form-item': 'form-item',
                'el-input': 'input',
                'el-input-number': 'input-number',
                'el-autocomplete': 'autocomplete',
                'el-select': 'select',
                'el-option': 'select',
                'el-option-group': 'select',
                'el-table': 'table',
                'el-table-column': 'table',
                'el-pagination': 'pagination',
                'el-dialog': 'dialog',
                'el-card': 'card',
                'el-row': 'row',
                'el-col': 'col',
                'el-tag': 'tag',
                'el-icon': 'icon',
                'el-upload': 'upload',
                'el-dropdown': 'dropdown',
                'el-dropdown-menu': 'dropdown',
                'el-dropdown-item': 'dropdown',
                'el-menu': 'menu',
                'el-menu-item': 'menu',
                'el-sub-menu': 'menu',
                'el-tabs': 'tabs',
                'el-tab-pane': 'tabs',
                'el-badge': 'badge',
                'el-avatar': 'avatar',
                'el-skeleton': 'skeleton',
                'el-divider': 'divider',
                'el-link': 'link',
                'el-checkbox': 'checkbox',
                'el-checkbox-group': 'checkbox',
                'el-radio': 'radio',
                'el-radio-group': 'radio',
                'el-radio-button': 'radio',
                'el-switch': 'switch',
                'el-date-picker': 'date-picker',
                'el-time-picker': 'time-picker',
                'el-time-select': 'time-select',
                'el-tooltip': 'tooltip',
                'el-popover': 'popover',
                'el-alert': 'alert',
                'el-image': 'image',
                'el-descriptions': 'descriptions',
                'el-descriptions-item': 'descriptions',
                'el-empty': 'empty',
                'el-progress': 'progress',
                'el-tree': 'tree',
                'el-tree-select': 'tree-select',
                'el-cascader': 'cascader',
                'el-color-picker': 'color-picker',
                'el-transfer': 'transfer',
                'el-slider': 'slider',
                'el-rate': 'rate',
                'el-carousel': 'carousel',
                'el-carousel-item': 'carousel',
                'el-collapse': 'collapse',
                'el-collapse-item': 'collapse',
                'el-timeline': 'timeline',
                'el-timeline-item': 'timeline',
                'el-result': 'result',
                'el-statistic': 'statistic',
                'el-countdown': 'countdown',
                'el-config-provider': 'config-provider',
                'el-container': 'container',
                'el-header': 'container',
                'el-aside': 'container',
                'el-main': 'container',
                'el-footer': 'container',
                'el-backtop': 'backtop',
                'el-affix': 'affix',
                'el-breadcrumb': 'breadcrumb',
                'el-breadcrumb-item': 'breadcrumb',
                'el-page-header': 'page-header',
                'el-steps': 'steps',
                'el-step': 'steps',
                'el-drawer': 'drawer',
                'el-popconfirm': 'popconfirm',
                'el-skeleton-item': 'skeleton',
                'el-space': 'space'
              }
              
              if (name === 'click-outside') {
                return ''
              }
              
              const component = styleMap[name]
              if (component) {
                return `element-plus/es/components/${component}/style/css`
              }
              
              return `element-plus/es/components/${name.replace(/^el-/, '')}/style/css`
            }
          }
        ]
      }),
      EslintPlugin({
        cache: false,
        failOnWarning: false,
        failOnError: false,
        include: ['src/**/*.vue', 'src/**/*.ts', 'src/**/*.tsx'] // 检查的文件
      }),
      VueI18nPlugin({
        runtimeOnly: true,
        compositionOnly: true,
        include: [resolve(__dirname, 'src/locales/**')]
      }),
      createSvgIconsPlugin({
        iconDirs: [pathResolve('src/assets/svgs')],
        symbolId: 'icon-[dir]-[name]',
        svgoOptions: true
      }),
      // PurgeIcons({
      //   content: [
      //     './src/**/*.vue',
      //     './src/**/*.ts',
      //     './src/**/*.tsx',
      //     './src/**/*.js',
      //     './src/**/*.jsx'
      //   ],
      //   extractors: [
      //     {
      //       extractor: (content: string) => {
      //         const regex = /vi-([a-z0-9-]+):[\w\d-]+/g
      //         const matches = content.match(regex) || []
      //         return matches.map((icon) => icon.replace('vi-', ''))
      //       },
      //       extensions: ['vue', 'ts', 'js', 'tsx', 'jsx']
      //     }
      //   ]
      // }),
      env.VITE_USE_MOCK === 'true'
        ? viteMockServe({
            ignore: /^\_/,
            mockPath: 'mock',
            localEnabled: !isBuild,
            prodEnabled: isBuild,
            injectCode: `
          import { setupProdMockServer } from '../mock/_createProductionServer'

          setupProdMockServer()
          `
          })
        : undefined,
      ViteEjsPlugin({
        title: env.VITE_APP_TITLE
      }),
      UnoCSS()
    ],

    css: {
      preprocessorOptions: {
        less: {
          additionalData: '@import "./src/styles/variables.module.less";',
          javascriptEnabled: true
        }
      }
    },
    resolve: {
      extensions: ['.mjs', '.js', '.ts', '.jsx', '.tsx', '.json', '.less', '.css'],
      alias: [
        {
          find: 'vue-i18n',
          replacement: 'vue-i18n/dist/vue-i18n.cjs.js'
        },
        {
          find: /\@\//,
          replacement: `${pathResolve('src')}/`
        }
      ]
    },
    esbuild: {
      pure: env.VITE_DROP_CONSOLE === 'true' ? ['console.log'] : undefined,
      drop: env.VITE_DROP_DEBUGGER === 'true' ? ['debugger'] : undefined
    },
    build: {
      target: 'es2015',
      outDir: env.VITE_OUT_DIR || 'dist',
      sourcemap: env.VITE_SOURCEMAP === 'true',
      // brotliSize: false,
      minify: 'terser',
      terserOptions: {
        compress: {
          drop_console: env.VITE_DROP_CONSOLE === 'true',
          drop_debugger: env.VITE_DROP_DEBUGGER === 'true',
          pure_funcs: env.VITE_DROP_CONSOLE === 'true' ? ['console.log'] : []
        }
      },
      rollupOptions: {
        plugins: env.VITE_USE_BUNDLE_ANALYZER === 'true' ? [visualizer()] : undefined,
        output: {
          manualChunks: (id) => {
            // Vue核心库
            if (id.includes('node_modules/vue/') || 
                id.includes('node_modules/@vue/') ||
                id.includes('node_modules/vue-router/') ||
                id.includes('node_modules/pinia/') ||
                id.includes('node_modules/vue-i18n/')) {
              return 'vue-vendor'
            }
            
            // Element Plus
            if (id.includes('node_modules/element-plus/')) {
              return 'element-plus'
            }
            
            // ECharts
            if (id.includes('node_modules/echarts/') || 
                id.includes('node_modules/echarts-wordcloud/') ||
                id.includes('node_modules/zrender/')) {
              return 'echarts'
            }
            
            // 富文本编辑器
            if (id.includes('node_modules/@wangeditor/')) {
              return 'wang-editor'
            }
            
            // 图标库
            if (id.includes('node_modules/@element-plus/icons-vue/')) {
              return 'element-icons'
            }
            
            // 工具库
            if (id.includes('node_modules/lodash-es/') || 
                id.includes('node_modules/lodash/')) {
              return 'lodash'
            }
            
            // 工具库
            if (id.includes('node_modules/axios/') || 
                id.includes('node_modules/dayjs/') ||
                id.includes('node_modules/crypto-js/')) {
              return 'utils'
            }
            
            // 其他第三方库
            if (id.includes('node_modules/')) {
              return 'vendor'
            }
          },
          chunkFileNames: 'assets/js/[name]-[hash].js',
          entryFileNames: 'assets/js/[name]-[hash].js',
          assetFileNames: (assetInfo) => {
            const info = assetInfo.name?.split('.') || []
            let extType = info[info.length - 1]
            
            if (/\.(png|jpe?g|gif|svg|webp|ico)$/i.test(assetInfo.name || '')) {
              return `assets/images/[name]-[hash].[ext]`
            } else if (/\.(woff2?|eot|ttf|otf)$/i.test(assetInfo.name || '')) {
              return `assets/fonts/[name]-[hash].[ext]`
            } else if (/\.css$/i.test(assetInfo.name || '')) {
              return `assets/css/[name]-[hash].[ext]`
            }
            
            return `assets/[ext]/[name]-[hash].[ext]`
          }
        }
      },
      cssCodeSplit: !(env.VITE_USE_CSS_SPLIT === 'false'),
      cssTarget: ['chrome31'],
      chunkSizeWarningLimit: 2000,
      reportCompressedSize: true
    },
    server: {
      port: 4000,
      host: '0.0.0.0',
      hmr: {
        overlay: false
      },
      proxy: {
        '/api': {
          target: 'http://172.32.48.254:8000',
          changeOrigin: true
        },
        '/ws': {
          target: 'http://172.32.48.254:8000',
          changeOrigin: true,
          ws: true
        }
      }
    },
    optimizeDeps: {
      include: [
        'vue',
        'vue-router',
        'vue-types',
        'element-plus/es/locale/lang/zh-cn',
        'element-plus/es/locale/lang/en',
        '@iconify/iconify',
        '@vueuse/core',
        'axios',
        'qs',
        'echarts',
        'echarts-wordcloud',
        'qrcode',
        '@wangeditor/editor',
        '@wangeditor/editor-for-vue',
        'vue-json-pretty',
        '@zxcvbn-ts/core',
        'dayjs',
        'cropperjs'
      ]
    }
  }
}
