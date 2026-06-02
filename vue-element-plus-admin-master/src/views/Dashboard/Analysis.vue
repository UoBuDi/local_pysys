<script setup lang="ts">
import PanelGroup from './components/PanelGroup.vue'
import { ElRow, ElCol, ElCard, ElSkeleton } from 'element-plus'
import { Echart } from '@/components/Echart'
import { pieOptions, barOptions, lineOptions } from './echarts-data'
import { ref, reactive, computed, watch, onMounted } from 'vue'
import {
  getUserAccessSourceApi,
  getWeeklyUserActivityApi,
  getMonthlySalesApi
} from '@/api/dashboard/analysis/index'
import { set } from 'lodash-es'
import { EChartsOption } from 'echarts'
import { useI18n } from '@/hooks/web/useI18n'
import { useAppStore } from '@/store/modules/app'

const { t } = useI18n()

const loading = ref(true)

const appStore = useAppStore()
const isDark = computed(() => appStore.getIsDark)

const pieOptionsData = reactive<EChartsOption>(pieOptions) as EChartsOption

const getUserAccessSource = async () => {
  const res = await getUserAccessSourceApi().catch(() => {})
  if (res) {
    set(
      pieOptionsData,
      'legend.data',
      res.data.map((v) => v.name)
    )
    pieOptionsData!.series![0].data = res.data.map((v) => {
      return {
        name: v.name,
        value: v.value
      }
    })
  }
}

const barOptionsData = reactive<EChartsOption>(barOptions) as EChartsOption

const getWeeklyUserActivity = async () => {
  const res = await getWeeklyUserActivityApi().catch(() => {})
  if (res) {
    set(
      barOptionsData,
      'xAxis.data',
      res.data.map((v) => v.name)
    )
    set(barOptionsData, 'series', [
      {
        name: t('analysis.activeQuantity'),
        data: res.data.map((v) => v.value),
        type: 'bar'
      }
    ])
  }
}

const lineOptionsData = reactive<EChartsOption>(lineOptions) as EChartsOption

const getMonthlySales = async () => {
  const res = await getMonthlySalesApi().catch(() => {})
  if (res) {
    set(
      lineOptionsData,
      'xAxis.data',
      res.data.map((v) => v.name)
    )
    set(lineOptionsData, 'series', [
      {
        name: t('analysis.estimate'),
        smooth: true,
        type: 'line',
        data: res.data.map((v) => v.estimate),
        animationDuration: 2800,
        animationEasing: 'cubicInOut'
      },
      {
        name: t('analysis.actual'),
        smooth: true,
        type: 'line',
        itemStyle: {},
        data: res.data.map((v) => v.actual),
        animationDuration: 2800,
        animationEasing: 'quadraticOut'
      }
    ])
  }
}

const updateLegendTextStyle = (options) => {
  const newTextStyle = {
    color: isDark.value ? '#ccc' : 'var(--el-text-color-primary)'
  }
  const axisColor = isDark.value ? '#ccc' : 'var(--el-text-color-secondary)'
  const inactiveColor = isDark.value ? '#abacac' : '#ccc'
  set(options, 'title.textStyle', newTextStyle)
  set(options, 'xAxis.axisLabel.color', axisColor)
  set(options, 'yAxis.axisLabel.color', axisColor)
  set(options, 'xAxis.axisLine.lineStyle.color', axisColor)
  set(options, 'yAxis.axisLine.lineStyle.color', axisColor)
  set(options, 'xAxis.splitLine.lineStyle.color', isDark.value ? '#333' : '#eee')
  set(options, 'yAxis.splitLine.lineStyle.color', isDark.value ? '#333' : '#eee')
  if (options !== barOptionsData) {
    set(options, 'legend.textStyle', newTextStyle)
    set(options, 'legend.inactiveColor', inactiveColor)
  }
  options === pieOptionsData && set(options, 'series[0].emptyCircleStyle.color', inactiveColor)
}

const getAllApi = async () => {
  await Promise.all([getUserAccessSource(), getWeeklyUserActivity(), getMonthlySales()])
  loading.value = false
}

getAllApi()

watch(isDark, () => {
  updateLegendTextStyle(pieOptionsData)
  updateLegendTextStyle(barOptionsData)
  updateLegendTextStyle(lineOptionsData)
})
onMounted(() => {
  updateLegendTextStyle(pieOptionsData)
  updateLegendTextStyle(barOptionsData)
  updateLegendTextStyle(lineOptionsData)
})
</script>

<template>
  <PanelGroup />
  <ElRow :gutter="20" justify="space-between">
    <ElCol :xl="10" :lg="10" :md="24" :sm="24" :xs="24">
      <ElCard shadow="hover" class="mb-20px">
        <ElSkeleton :loading="loading" animated>
          <Echart :options="pieOptionsData" :height="300" />
        </ElSkeleton>
      </ElCard>
    </ElCol>
    <ElCol :xl="14" :lg="14" :md="24" :sm="24" :xs="24">
      <ElCard shadow="hover" class="mb-20px">
        <ElSkeleton :loading="loading" animated>
          <Echart :options="barOptionsData" :height="300" />
        </ElSkeleton>
      </ElCard>
    </ElCol>
    <ElCol :span="24">
      <ElCard shadow="hover" class="mb-20px">
        <ElSkeleton :loading="loading" animated :rows="4">
          <Echart :options="lineOptionsData" :height="350" />
        </ElSkeleton>
      </ElCard>
    </ElCol>
  </ElRow>
</template>
