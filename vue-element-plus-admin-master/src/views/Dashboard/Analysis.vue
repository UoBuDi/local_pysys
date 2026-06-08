<script setup lang="ts">
import PanelGroup from './components/PanelGroup.vue'
import {
  ElRow,
  ElCol,
  ElCard,
  ElSkeleton,
  ElEmpty,
  ElDatePicker,
  ElButton,
  ElIcon,
  ElSpace
} from 'element-plus'
import { CaretLeft, CaretRight } from '@element-plus/icons-vue'
import { Echart } from '@/components/Echart'
import { ref, computed, watch, onMounted } from 'vue'
import { EChartsOption } from 'echarts'
import { useI18n } from '@/hooks/web/useI18n'
import { useAppStore } from '@/store/modules/app'
import { getDashboardStatisticsApi } from '@/api/scheduled-tasks'
import type { DashboardStatistics } from '@/api/scheduled-tasks'

const { t } = useI18n()

const loading = ref(true)
const statistics = ref<DashboardStatistics | null>(null)
const selectedMonth = ref('')
const latestAvailableMonth = ref('')

const appStore = useAppStore()
const isDark = computed(() => appStore.getIsDark)

const emptyText = computed(() => t('analysis.noData'))

const pieOptionsData = ref<EChartsOption>({})
const barOptionsData = ref<EChartsOption>({})
const lineOptionsData = ref<EChartsOption>({})

const hasVehicleTypeData = computed(() => (statistics.value?.vehicle_types?.length || 0) > 0)
const hasMediaTypeData = computed(() => (statistics.value?.media_types?.length || 0) > 0)
const hasProvinceData = computed(() => (statistics.value?.province_data?.length || 0) > 0)

const infoItems = computed(() => {
  const data = statistics.value
  if (!data) return []
  return [
    { label: t('analysis.statMonth'), value: formatMonth(data.stat_month) || '-' },
    {
      label: t('analysis.statDate'),
      value: formatDateTime(data.updated_at || data.created_at) || '-'
    },
    { label: t('analysis.vehicleTypeCount'), value: String(data.vehicle_types?.length || 0) },
    { label: t('analysis.provinceCoverage'), value: String(data.province_data?.length || 0) }
  ]
})

const formatMonth = (value?: string) => {
  if (!value) return ''
  if (/^\d{6}$/.test(value)) {
    return `${value.slice(0, 4)}-${value.slice(4, 6)}`
  }
  return value
}

const compareMonth = (left?: string, right?: string) => {
  if (!left || !right) return 0
  return formatMonth(left).localeCompare(formatMonth(right))
}

const shiftMonth = (value: string, step: number) => {
  const normalizedValue = formatMonth(value)
  if (!/^\d{4}-\d{2}$/.test(normalizedValue)) return ''

  const [year, month] = normalizedValue.split('-').map(Number)
  const date = new Date(year, month - 1 + step, 1)
  const nextYear = date.getFullYear()
  const nextMonth = `${date.getMonth() + 1}`.padStart(2, '0')
  return `${nextYear}-${nextMonth}`
}

const formatDateTime = (value?: string) => {
  if (!value) return ''
  return String(value).replace('T', ' ').slice(0, 19)
}

const getAxisColor = () => (isDark.value ? '#cfd3dc' : '#606266')
const getSplitLineColor = () => (isDark.value ? '#303133' : '#ebeef5')
const getTitleColor = () => (isDark.value ? '#e5eaf3' : '#303133')
const getSubTextColor = () => (isDark.value ? '#a3a6ad' : '#909399')

const disableNextMonth = computed(() => {
  if (!selectedMonth.value || !latestAvailableMonth.value) return true
  return compareMonth(selectedMonth.value, latestAvailableMonth.value) >= 0
})

const updateChartOptions = () => {
  const data = statistics.value
  if (!data) {
    pieOptionsData.value = {}
    barOptionsData.value = {}
    lineOptionsData.value = {}
    return
  }

  const vehicleTypes = [...(data.vehicle_types || [])]
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)
    .map((item) => ({ name: item.type || t('analysis.unknown'), value: item.count }))
  const vehicleTotal = vehicleTypes.reduce((sum, item) => sum + item.value, 0)

  pieOptionsData.value = {
    title: {
      text: t('analysis.userAccessSource'),
      subtext: `${t('analysis.total')}: ${vehicleTotal}`,
      left: 'center',
      top: 10,
      textStyle: { color: getTitleColor(), fontSize: 16, fontWeight: 600 },
      subtextStyle: { color: getSubTextColor(), fontSize: 12 }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}<br/>' + `${t('analysis.activeQuantity')}: {c} ({d}%)`
    },
    legend: {
      type: 'scroll',
      bottom: 0,
      left: 'center',
      textStyle: { color: getAxisColor() }
    },
    series: [
      {
        name: t('analysis.userAccessSource'),
        type: 'pie',
        radius: ['42%', '68%'],
        center: ['50%', '45%'],
        avoidLabelOverlap: true,
        label: {
          formatter: '{b}\n{c}',
          color: getAxisColor()
        },
        itemStyle: {
          borderRadius: 6,
          borderColor: isDark.value ? '#141414' : '#fff',
          borderWidth: 2
        },
        data: vehicleTypes
      }
    ]
  }

  const mediaTypes = [...(data.media_types || [])]
    .map((item) => ({
      name: item.type || t('analysis.unknown'),
      value: item.count || 0
    }))
    .sort((a, b) => b.value - a.value)

  barOptionsData.value = {
    title: {
      text: t('analysis.weeklyUserActivity'),
      left: 'center',
      top: 10,
      textStyle: { color: getTitleColor(), fontSize: 16, fontWeight: 600 }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    grid: {
      left: 30,
      right: 30,
      top: 60,
      bottom: 25,
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: mediaTypes.map((item) => item.name),
      axisTick: { alignWithLabel: true },
      axisLabel: { color: getAxisColor(), interval: 0 },
      axisLine: { lineStyle: { color: getAxisColor() } }
    },
    yAxis: {
      type: 'value',
      name: t('analysis.activeQuantity'),
      nameTextStyle: { color: getAxisColor() },
      axisLabel: { color: getAxisColor() },
      splitLine: { lineStyle: { color: getSplitLineColor() } }
    },
    series: [
      {
        name: t('analysis.activeQuantity'),
        type: 'bar',
        barMaxWidth: 48,
        label: { show: true, position: 'top', color: getAxisColor() },
        itemStyle: { borderRadius: [6, 6, 0, 0] },
        data: mediaTypes.map((item) => item.value)
      }
    ]
  }

  const provinceData = [...(data.province_data || [])]
    .map((item) => ({ name: item.province || t('analysis.unknown'), value: item.count || 0 }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 10)
    .reverse()

  lineOptionsData.value = {
    title: {
      text: t('analysis.monthlySales'),
      subtext: t('analysis.top10'),
      left: 'center',
      top: 10,
      textStyle: { color: getTitleColor(), fontSize: 16, fontWeight: 600 },
      subtextStyle: { color: getSubTextColor(), fontSize: 12 }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    grid: {
      left: 90,
      right: 30,
      top: 65,
      bottom: 25,
      containLabel: true
    },
    xAxis: {
      type: 'value',
      axisLabel: { color: getAxisColor() },
      splitLine: { lineStyle: { color: getSplitLineColor() } }
    },
    yAxis: {
      type: 'category',
      data: provinceData.map((item) => item.name),
      axisLabel: { color: getAxisColor(), width: 120, overflow: 'truncate' },
      axisTick: { show: false },
      axisLine: { lineStyle: { color: getAxisColor() } }
    },
    series: [
      {
        name: t('analysis.activeQuantity'),
        type: 'bar',
        barMaxWidth: 22,
        label: { show: true, position: 'right', color: getAxisColor() },
        itemStyle: { borderRadius: [0, 6, 6, 0] },
        data: provinceData.map((item) => item.value)
      }
    ]
  }
}

const getAllApi = async (targetMonth?: string) => {
  loading.value = true
  const requestMonth = formatMonth(targetMonth || selectedMonth.value)

  const res = await getDashboardStatisticsApi(requestMonth || undefined).catch(() => undefined)
  if (res?.data) {
    statistics.value = res.data

    if (requestMonth) {
      selectedMonth.value = requestMonth
    }

    const responseMonth = formatMonth(res.data.stat_month)
    if (!requestMonth && responseMonth) {
      selectedMonth.value = responseMonth
      latestAvailableMonth.value = responseMonth
    } else if (responseMonth && compareMonth(responseMonth, latestAvailableMonth.value) > 0) {
      latestAvailableMonth.value = responseMonth
    }
  } else {
    statistics.value = null
  }

  updateChartOptions()
  loading.value = false
}

const handleMonthChange = (value?: string | null) => {
  const nextMonth = formatMonth(value || '')
  selectedMonth.value = nextMonth
  void getAllApi(nextMonth || undefined)
}

const handleSwitchMonth = (step: number) => {
  const baseMonth = selectedMonth.value || latestAvailableMonth.value
  const nextMonth = shiftMonth(baseMonth, step)
  if (!nextMonth) return
  selectedMonth.value = nextMonth
  void getAllApi(nextMonth)
}

void getAllApi()

watch(isDark, () => {
  updateChartOptions()
})
onMounted(() => {
  updateChartOptions()
})
</script>

<template>
  <PanelGroup :loading="loading" :statistics="statistics" />
  <ElCard shadow="never" class="mb-20px analysis-filter-card">
    <div class="analysis-filter">
      <span class="analysis-filter__label">{{ t('analysis.statMonth') }}</span>
      <ElSpace wrap>
        <ElButton circle :disabled="loading" @click="handleSwitchMonth(-1)">
          <ElIcon><CaretLeft /></ElIcon>
        </ElButton>
        <ElDatePicker
          v-model="selectedMonth"
          type="month"
          value-format="YYYY-MM"
          :placeholder="t('analysis.selectStatMonth')"
          @change="handleMonthChange"
        />
        <ElButton circle :disabled="loading || disableNextMonth" @click="handleSwitchMonth(1)">
          <ElIcon><CaretRight /></ElIcon>
        </ElButton>
      </ElSpace>
    </div>
  </ElCard>
  <ElCard shadow="never" class="mb-20px analysis-summary-card">
    <div class="analysis-summary">
      <div v-for="item in infoItems" :key="item.label" class="analysis-summary__item">
        <span class="analysis-summary__label">{{ item.label }}</span>
        <span class="analysis-summary__value">{{ item.value }}</span>
      </div>
    </div>
  </ElCard>
  <ElRow :gutter="20" justify="space-between">
    <ElCol :xl="10" :lg="10" :md="24" :sm="24" :xs="24">
      <ElCard shadow="hover" class="mb-20px">
        <ElSkeleton :loading="loading" animated>
          <Echart v-if="hasVehicleTypeData" :options="pieOptionsData" :height="340" />
          <ElEmpty v-else :description="emptyText" :image-size="88" />
        </ElSkeleton>
      </ElCard>
    </ElCol>
    <ElCol :xl="14" :lg="14" :md="24" :sm="24" :xs="24">
      <ElCard shadow="hover" class="mb-20px">
        <ElSkeleton :loading="loading" animated>
          <Echart v-if="hasMediaTypeData" :options="barOptionsData" :height="340" />
          <ElEmpty v-else :description="emptyText" :image-size="88" />
        </ElSkeleton>
      </ElCard>
    </ElCol>
    <ElCol :span="24">
      <ElCard shadow="hover" class="mb-20px">
        <ElSkeleton :loading="loading" animated :rows="4">
          <Echart v-if="hasProvinceData" :options="lineOptionsData" :height="420" />
          <ElEmpty v-else :description="emptyText" :image-size="88" />
        </ElSkeleton>
      </ElCard>
    </ElCol>
  </ElRow>
</template>

<style scoped lang="less">
.analysis-filter-card,
.analysis-summary-card {
  border: 1px solid var(--el-border-color-lighter);
}

.analysis-filter {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.analysis-filter__label {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.analysis-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.analysis-summary__item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px 16px;
  border-radius: 8px;
  background: var(--el-fill-color-light);
}

.analysis-summary__label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.analysis-summary__value {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

@media (max-width: 1200px) {
  .analysis-summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .analysis-filter {
    align-items: stretch;
  }

  .analysis-summary {
    grid-template-columns: 1fr;
  }
}
</style>
