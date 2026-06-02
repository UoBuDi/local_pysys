<script setup lang="ts">
import type { EChartsOption } from 'echarts'
import { debounce } from 'lodash-es'
import { propTypes } from '@/utils/propTypes'
import { computed, PropType, ref, unref, watch, onMounted, onBeforeUnmount, onActivated } from 'vue'
import { useAppStore } from '@/store/modules/app'
import { isString } from '@/utils/is'
import { useDesign } from '@/hooks/web/useDesign'

const { getPrefixCls, variables } = useDesign()

const prefixCls = getPrefixCls('echart')

const appStore = useAppStore()

const props = defineProps({
  options: {
    type: Object as PropType<EChartsOption>,
    required: true
  },
  width: propTypes.oneOfType([Number, String]).def('100%'),
  height: propTypes.oneOfType([Number, String]).def('500px'),
  chartType: propTypes.string.def('') // 图表类型: 'bar', 'line', 'pie', 'radar', 'map'
})

const isDark = computed(() => appStore.getIsDark)

const theme = computed(() => {
  const echartTheme: boolean | string = unref(isDark) ? true : 'auto'

  return echartTheme
})

const options = computed(() => {
  return Object.assign(props.options, {
    darkMode: unref(theme)
  })
})

const elRef = ref<ElRef>()

let echartRef: Nullable<any> = null

const contentEl = ref<Element>()

const loading = ref(true)

const echartsInstance = ref<any>(null)

const styles = computed(() => {
  const width = isString(props.width) ? props.width : `${props.width}px`
  const height = isString(props.height) ? props.height : `${props.height}px`

  return {
    width,
    height
  }
})

// 动态加载ECharts模块
const loadEChartsModules = async () => {
  try {
    // 动态导入ECharts核心
    const echartsCore = await import('echarts/core')

    // 导入基础组件
    const [
      { TitleComponent },
      { TooltipComponent },
      { GridComponent },
      { LegendComponent },
      { CanvasRenderer }
    ] = await Promise.all([
      import('echarts/components'),
      import('echarts/components'),
      import('echarts/components'),
      import('echarts/components'),
      import('echarts/renderers')
    ])

    echartsCore.use([
      TitleComponent,
      TooltipComponent,
      GridComponent,
      LegendComponent,
      CanvasRenderer
    ])

    // 根据图表类型动态导入
    if (props.chartType) {
      const chartModules = await import('echarts/charts')
      const chartTypeMap: Record<string, string> = {
        bar: 'BarChart',
        line: 'LineChart',
        pie: 'PieChart',
        radar: 'RadarChart',
        map: 'MapChart',
        scatter: 'ScatterChart',
        effectScatter: 'EffectScatterChart',
        tree: 'TreeChart',
        treemap: 'TreemapChart',
        sunburst: 'SunburstChart',
        boxplot: 'BoxplotChart',
        candlestick: 'CandlestickChart',
        heatmap: 'HeatmapChart',
        parallel: 'ParallelChart',
        lines: 'LinesChart',
        graph: 'GraphChart',
        sankey: 'SankeyChart',
        funnel: 'FunnelChart',
        themeRiver: 'ThemeRiverChart',
        pictorialBar: 'PictorialBarChart'
      }

      const chartComponentName = chartTypeMap[props.chartType.toLowerCase()]
      if (chartComponentName) {
        const ChartComponent = chartModules[chartComponentName]
        if (ChartComponent) {
          echartsCore.use([ChartComponent])
        }
      }
    }

    // 动态导入词云插件
    if (props.chartType === 'wordcloud') {
      await import('echarts-wordcloud')
    }

    echartsInstance.value = echartsCore
    loading.value = false

    return echartsCore
  } catch (error) {
    console.error('[ECharts] 加载模块失败:', error)
    loading.value = false
    return null
  }
}

const initChart = () => {
  if (unref(elRef) && props.options && echartsInstance.value) {
    echartRef = echartsInstance.value.init(unref(elRef) as HTMLElement)
    echartRef?.setOption(unref(options))
  }
}

watch(
  () => options.value,
  (options) => {
    if (echartRef) {
      echartRef?.setOption(options)
    }
  },
  {
    deep: true
  }
)

const resizeHandler = debounce(() => {
  if (echartRef) {
    echartRef.resize()
  }
}, 100)

const contentResizeHandler = async (e: TransitionEvent) => {
  if (e.propertyName === 'width') {
    resizeHandler()
  }
}

onMounted(async () => {
  // 动态加载ECharts模块
  await loadEChartsModules()

  setTimeout(() => {
    initChart()
  }, 0)

  window.addEventListener('resize', resizeHandler)

  contentEl.value = document.getElementsByClassName(`${variables.namespace}-layout-content`)[0]
  unref(contentEl) &&
    (unref(contentEl) as Element).addEventListener('transitionend', contentResizeHandler)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeHandler)
  unref(contentEl) &&
    (unref(contentEl) as Element).removeEventListener('transitionend', contentResizeHandler)
})

onActivated(() => {
  if (echartRef) {
    echartRef.resize()
  }
})
</script>

<template>
  <div
    ref="elRef"
    :class="[$attrs.class, prefixCls]"
    :style="styles"
    v-loading="loading"
    element-loading-text="加载图表中..."
  ></div>
</template>
