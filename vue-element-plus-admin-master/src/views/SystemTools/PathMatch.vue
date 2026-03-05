<template>
  <div class="path-match">
    <el-card class="search-card">
      <template #header>
        <div class="card-header">
          <span>收费路径匹配与金额计算系统</span>
        </div>
      </template>

      <el-form :inline="false" class="search-form">
        <el-row :gutter="20">
          <el-col :xs="24" :sm="12">
            <el-form-item label="清分日范围">
              <el-date-picker
                v-model="transactionTimeRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始时间"
                end-placeholder="结束时间"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="门架经过时间">
              <div class="time-range-wrapper">
                <el-date-picker
                  v-model="timeRange"
                  type="datetimerange"
                  range-separator="至"
                  start-placeholder="开始时间"
                  end-placeholder="结束时间"
                  format="YYYY-MM-DD HH:mm:ss"
                  value-format="YYYY-MM-DD HH:mm:ss"
                  style="flex: 1"
                  :default-time="[new Date(2000, 1, 1, 0, 0, 0), new Date(2000, 1, 1, 23, 59, 59)]"
                />
                <el-checkbox v-model="excludeGreenChannel" class="exclude-checkbox"
                  >排除绿通</el-checkbox
                >
              </div>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :xs="24" :sm="12">
            <el-form-item label="包含的拆分收费单元名称">
              <el-input
                v-model="startUnit"
                placeholder="例如：安邵_邵永交界-邵阳西站49"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="终点位置包含的拆分收费单元名称">
              <el-input v-model="endUnit" placeholder="例如：邵阳西（出口）" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :xs="24" :sm="12">
            <el-form-item label="收费车型">
              <el-select-v2
                v-model="selectedVehicleTypes"
                :options="vehicleTypeOptions"
                multiple
                filterable
                collapse-tags
                collapse-tags-tooltip
                placeholder="请选择收费车型"
                style="width: 100%"
                :max-collapse-tags="2"
              >
                <template #header>
                  <el-checkbox
                    v-model="isAllVehicleTypesSelected"
                    :indeterminate="isVehicleTypesIndeterminate"
                    @change="handleSelectAllVehicleTypes"
                    style="padding: 8px 16px"
                  >
                    全选
                  </el-checkbox>
                </template>
              </el-select-v2>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="排除的收费出口名称">
              <el-select
                v-model="excludeExits"
                multiple
                allow-create
                filterable
                default-first-option
                placeholder="请选择或输入要排除的收费出口名称"
                style="width: 100%"
              >
                <el-option
                  v-for="item in excludeExitOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :xs="24" :sm="12">
            <el-form-item label="排除的拆分收费单元名称">
              <el-input
                v-model="excludeUnits"
                placeholder="例如：出口,入口（多个用逗号分隔）"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item class="button-group">
              <el-button type="primary" @click="searchData" :loading="loading">
                开始搜索
              </el-button>
              <el-button type="success" @click="exportExcel" :disabled="!hasResults">
                导出Excel
              </el-button>
              <el-button type="warning" @click="showVisualization" :disabled="!hasResults">
                可视化分析
              </el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <el-card class="result-card">
      <template #header>
        <div class="card-header">
          <span>匹配结果</span>
          <el-badge v-if="hasResults" :value="results.length" type="primary" />
        </div>
      </template>

      <div v-if="loading" class="loading-container">
        <el-icon class="loading"><Loading /></el-icon>
        <span>正在搜索数据，请稍候...</span>
      </div>

      <div v-else-if="!hasResults && searched" class="empty-container">
        <el-empty description="未找到匹配的数据" />
      </div>

      <div v-else-if="!searched" class="empty-container">
        <el-empty description="请设置搜索条件并点击搜索按钮" />
      </div>

      <div v-else class="virtual-table-container">
        <el-table-v2
          :columns="virtualColumns"
          :data="results"
          :width="tableWidth"
          :height="500"
          :row-height="50"
          :row-props="getRowProps"
        />
      </div>
    </el-card>

    <el-dialog v-model="detailDialogVisible" title="数据详情" width="60%" destroy-on-close>
      <div v-if="detailLoading" class="loading-container">
        <el-icon class="loading"><Loading /></el-icon>
        <span>正在加载详情数据...</span>
      </div>
      <div v-else class="detail-scroll-container">
        <el-descriptions :column="1" border>
          <el-descriptions-item
            v-for="(value, key) in selectedRow"
            :key="key"
            :label="key"
            label-class-name="detail-label"
          >
            <div class="detail-value">{{ value }}</div>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>

    <el-dialog
      v-model="visualizationVisible"
      title="可视化分析"
      width="80%"
      top="2vh"
      destroy-on-close
      class="visualization-dialog"
    >
      <div class="visualization-container">
        <el-row :gutter="15">
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-value">{{ statistics.totalCount }}</div>
              <div class="stat-label">总记录数</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-value">{{ statistics.avgAmount }}</div>
              <div class="stat-label">平均金额（元）</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-value">{{ statistics.totalAmount }}</div>
              <div class="stat-label">总金额（元）</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-row">
                <span class="stat-label-inline">客车：</span>
                <span class="stat-value-inline">{{ passengerCargoRatio.passenger }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-label-inline">货车：</span>
                <span class="stat-value-inline">{{ passengerCargoRatio.cargo }}</span>
              </div>
            </el-card>
          </el-col>
        </el-row>
        <el-row :gutter="15" style="margin-top: 15px">
          <el-col :span="12">
            <el-card class="chart-card">
              <template #header>
                <span>车型占比（按记录数）</span>
              </template>
              <div class="chart-wrapper">
                <div class="pie-chart">
                  <div
                    v-for="(item, index) in vehicleTypeDistribution"
                    :key="index"
                    class="pie-item"
                  >
                    <div class="pie-color" :style="{ backgroundColor: getChartColor(index) }"></div>
                    <div class="pie-label">{{ item.name }}</div>
                    <div class="pie-value">{{ item.count }}条 ({{ item.percentage }}%)</div>
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card class="chart-card">
              <template #header>
                <span>拆分金额占比（按车型）</span>
              </template>
              <div class="chart-wrapper">
                <div class="pie-chart">
                  <div
                    v-for="(item, index) in vehicleTypeAmountDistribution"
                    :key="index"
                    class="pie-item"
                  >
                    <div class="pie-color" :style="{ backgroundColor: getChartColor(index) }"></div>
                    <div class="pie-label">{{ item.name }}</div>
                    <div class="pie-value">{{ item.amount }}元 ({{ item.percentage }}%)</div>
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
        <el-row :gutter="15" style="margin-top: 15px">
          <el-col :span="12">
            <el-card class="chart-card">
              <template #header>
                <span>收费出口分布</span>
              </template>
              <div class="chart-wrapper">
                <div class="pie-chart">
                  <div v-for="(item, index) in exitDistribution" :key="index" class="pie-item">
                    <div class="pie-color" :style="{ backgroundColor: getChartColor(index) }"></div>
                    <div class="pie-label">{{ item.name }}</div>
                    <div class="pie-value">{{ item.count }}条 ({{ item.percentage }}%)</div>
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card class="chart-card">
              <template #header>
                <span>入口省份分布</span>
              </template>
              <div class="chart-wrapper">
                <div class="pie-chart">
                  <div
                    v-for="(item, index) in entryProvinceDistribution"
                    :key="index"
                    class="pie-item"
                  >
                    <div class="pie-color" :style="{ backgroundColor: getChartColor(index) }"></div>
                    <div class="pie-label">{{ item.name }}</div>
                    <div class="pie-value">{{ item.count }}条 ({{ item.percentage }}%)</div>
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
        <el-row :gutter="15" style="margin-top: 15px">
          <el-col :span="12">
            <el-card class="chart-card">
              <template #header>
                <span>出口省份分布</span>
              </template>
              <div class="chart-wrapper">
                <div class="pie-chart">
                  <div
                    v-for="(item, index) in exitProvinceDistribution"
                    :key="index"
                    class="pie-item"
                  >
                    <div class="pie-color" :style="{ backgroundColor: getChartColor(index) }"></div>
                    <div class="pie-label">{{ item.name }}</div>
                    <div class="pie-value">{{ item.count }}条 ({{ item.percentage }}%)</div>
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-dialog>

    <el-card class="debug-panel" v-if="canShowDebug">
      <template #header>
        <div class="card-header">
          <span>调试信息</span>
          <el-button type="primary" link size="small" @click="showDebug = !showDebug">
            {{ showDebug ? '收起' : '展开' }}
          </el-button>
        </div>
      </template>

      <div v-show="showDebug" class="debug-content">
        <div v-if="requestParams" class="debug-section">
          <h4>请求参数</h4>
          <el-input :model-value="requestParams" type="textarea" :rows="6" readonly />
          <el-button type="primary" link size="small" @click="copySql(requestParams)">
            复制
          </el-button>
        </div>

        <div v-if="previewSql" class="debug-section">
          <h4>预览 SQL（提交时生成）</h4>
          <el-input :model-value="previewSql" type="textarea" :rows="8" readonly />
          <el-button type="primary" link size="small" @click="copySql(previewSql)">
            复制
          </el-button>
        </div>

        <div v-if="debugInfo" class="debug-statistics">
          <el-tag type="info">总耗时: {{ debugInfo.total_time.toFixed(3) }}s</el-tag>
          <el-tag type="warning" style="margin-left: 10px"
            >查询耗时: {{ debugInfo.count_duration.toFixed(3) }}s</el-tag
          >
        </div>

        <div v-if="debugInfo?.select_sql" class="debug-section">
          <h4>实际执行 SQL（查询完成后显示）</h4>
          <el-input :model-value="debugInfo.select_sql" type="textarea" :rows="8" readonly />
          <el-button type="primary" link size="small" @click="copySql(debugInfo.select_sql)">
            复制
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, h, nextTick } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { ElMessage, ElTableV2 } from 'element-plus'
import { searchPathMatch, getProvincesByCodes, getPathMatchDetail } from '@/api/path-match'
import { useUserStore } from '@/store/modules/user'
import type { Column } from 'element-plus'

const userStore = useUserStore()

const hasPermission = (): boolean => {
  const userInfo = userStore.getUserInfo
  const roleList = userInfo?.roleList || []

  if (roleList.includes('超级管理员') || roleList.includes('管理员')) {
    return true
  }

  return false
}

const canShowDebug = computed(() => hasPermission())

const timeRange = ref(['2025-01-02 00:00:00', '2025-01-03 23:59:59'])
const transactionTimeRange = ref(['2025-01-02', '2025-01-03'])
const excludeGreenChannel = ref(true)

const vehicleTypeOptions = [
  { label: '客一', value: '1' },
  { label: '客二', value: '2' },
  { label: '客三', value: '3' },
  { label: '客四', value: '4' },
  { label: '货一', value: '11' },
  { label: '货二', value: '12' },
  { label: '货三', value: '13' },
  { label: '货四', value: '14' },
  { label: '货五', value: '15' },
  { label: '货六', value: '16' },
  { label: '专一', value: '21' },
  { label: '专二', value: '22' },
  { label: '专三', value: '23' },
  { label: '专四', value: '24' },
  { label: '专五', value: '25' },
  { label: '专六', value: '26' }
]
const allVehicleTypeValues = vehicleTypeOptions.map((item) => item.value)
const selectedVehicleTypes = ref<string[]>([...allVehicleTypeValues])

const isAllVehicleTypesSelected = computed({
  get: () => selectedVehicleTypes.value.length === allVehicleTypeValues.length,
  set: () => {}
})

const isVehicleTypesIndeterminate = computed(() => {
  const len = selectedVehicleTypes.value.length
  return len > 0 && len < allVehicleTypeValues.length
})

const handleSelectAllVehicleTypes = (val: boolean) => {
  if (val) {
    selectedVehicleTypes.value = [...allVehicleTypeValues]
  } else {
    selectedVehicleTypes.value = []
  }
}

const excludeExits = ref<string[]>([])
const excludeExitOptions = ref([
  { label: '湖南清塘铺站', value: '湖南清塘铺站' },
  { label: '湖南伏口站', value: '湖南伏口站' },
  { label: '湖南龙塘站', value: '湖南龙塘站' },
  { label: '湖南涟源东站', value: '湖南涟源东站' },
  { label: '湖南白马站', value: '湖南白马站' },
  { label: '湖南新邵西站', value: '湖南新邵西站' },
  { label: '湖南邵阳西站', value: '湖南邵阳西站' }
])
const excludeUnits = ref('')
const startUnit = ref('安邵_邵永交界-邵阳西站49')
const endUnit = ref('清塘铺站-常安_安邵交界31')
const loading = ref(false)
const detailLoading = ref(false)
const searched = ref(false)
const results = ref<any[]>([])
const debugInfo = ref<any>(null)
const requestParams = ref<string>('')
const previewSql = ref<string>('')
const showDebug = ref(true)
const detailDialogVisible = ref(false)
const selectedRow = ref<any>(null)
const visualizationVisible = ref(false)
const statistics = ref({
  totalCount: 0,
  avgAmount: '0.00',
  totalAmount: '0.00'
})
const amountDistribution = ref<any[]>([])
const exitDistribution = ref<any[]>([])
const pathLengthDistribution = ref<any[]>([])
const vehicleTypeDistribution = ref<any[]>([])
const vehicleTypeAmountDistribution = ref<any[]>([])
const passengerCargoRatio = ref({ passenger: '0.0%', cargo: '0.0%' })
const entryProvinceDistribution = ref<any[]>([])
const exitProvinceDistribution = ref<any[]>([])
const tableColumns = ref([
  { prop: '通行标识ID', label: '通行标识ID', width: '300' },
  { prop: '收费入口名称', label: '收费入口名称', width: '150' },
  { prop: '收费出口名称', label: '收费出口名称', width: '150' },
  { prop: '计费交易起点时间', label: '计费交易起点时间', width: '160' },
  { prop: '计费交易终点时间', label: '计费交易终点时间', width: '160' },
  { prop: '实际车辆车牌号码+颜色', label: '车牌号码', width: '150' },
  { prop: '收费车型', label: '收费车型', width: '100' },
  { prop: '清分日', label: '清分日', width: '160' },
  { prop: '拆分路段拆分金额', label: '拆分金额(分)', width: '120' },
  { prop: '拆分收费单元名称组合', label: '拆分收费单元名称组合', minWidth: '400' }
])
const tableWidth = ref(1700)

const hasResults = computed(() => results.value.length > 0)

const virtualColumns = computed(() => {
  const fixedWidthColumns = [
    { prop: '序号', width: 70 },
    { prop: '通行标识ID', width: 300 },
    { prop: '收费入口名称', width: 150 },
    { prop: '收费出口名称', width: 150 },
    { prop: '计费交易起点时间', width: 160 },
    { prop: '计费交易终点时间', width: 160 },
    { prop: '实际车辆车牌号码+颜色', width: 150 },
    { prop: '收费车型', width: 100 },
    { prop: '清分日', width: 160 },
    { prop: '拆分路段拆分金额', width: 120 }
  ]

  const totalFixedWidth = fixedWidthColumns.reduce((sum, col) => sum + col.width, 0)
  const autoWidth = Math.max(400, tableWidth.value - totalFixedWidth)

  const columns = [
    {
      key: 'rowIndex',
      title: '序号',
      dataKey: 'rowIndex',
      width: 70,
      align: 'center',
      headerCellRenderer: () =>
        h(
          'span',
          { class: 'copyable-header', onClick: (e: MouseEvent) => copyHeaderText('序号') },
          '序号'
        ),
      cellRenderer: ({ rowIndex }: { rowIndex: number }) => {
        return h('span', {}, rowIndex + 1)
      }
    }
  ]

  const dataColumns = tableColumns.value.map((col, index) => {
    const isLastColumn = index === tableColumns.value.length - 1
    let colWidth: number

    if (isLastColumn) {
      colWidth = autoWidth
    } else {
      colWidth = col.width ? parseInt(col.width) : 150
    }

    return {
      key: col.prop,
      title: col.label,
      dataKey: col.prop,
      width: colWidth,
      align: 'center',
      headerCellRenderer: () =>
        h(
          'span',
          {
            class: 'copyable-header',
            onClick: (e: MouseEvent) => copyHeaderText(col.label)
          },
          col.label
        ),
      cellRenderer: ({ cellData }: { cellData: any }) => {
        if (cellData === null || cellData === undefined) return h('span', {}, '-')
        const str = String(cellData)
        if (str.length > 50) {
          return h('span', { title: str }, str.substring(0, 50) + '...')
        }
        return h('span', {}, str)
      }
    }
  })

  return [...columns, ...dataColumns]
})

const copyHeaderText = (text: string) => {
  navigator.clipboard
    .writeText(text)
    .then(() => {
      ElMessage.success(`已复制: ${text}`)
    })
    .catch(() => {
      ElMessage.error('复制失败')
    })
}

const handleRowClick = ({ rowData }: { rowData: any }) => {
  showRowDetail(rowData)
}

const getRowProps = ({ rowData }: { rowData: any }) => {
  return {
    onClick: () => handleRowClick({ rowData }),
    style: 'cursor: pointer;'
  }
}

const updateTableWidth = () => {
  const container = document.querySelector('.virtual-table-container')
  if (container) {
    tableWidth.value = container.clientWidth
  }
}

onMounted(() => {
  updateTableWidth()
  window.addEventListener('resize', updateTableWidth)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateTableWidth)
})

const showRowDetail = async (row: any) => {
  const passageId = row['通行标识ID']
  if (!passageId) {
    ElMessage.warning('缺少通行标识ID，无法获取详情')
    return
  }

  detailLoading.value = true
  detailDialogVisible.value = true
  selectedRow.value = { loading: true }

  try {
    const res = await getPathMatchDetail(passageId)
    if (res.code === 200 && res.data) {
      selectedRow.value = res.data
    } else {
      ElMessage.error(res.message || '获取详情失败')
      selectedRow.value = row
    }
  } catch (err) {
    console.error('获取详情失败:', err)
    ElMessage.error('获取详情失败')
    selectedRow.value = row
  } finally {
    detailLoading.value = false
  }
}

const getChartColor = (index: number) => {
  const colors = [
    '#409EFF',
    '#67C23A',
    '#E6A23C',
    '#F56C6C',
    '#909399',
    '#9B59B6',
    '#1ABC9C',
    '#3498DB'
  ]
  return colors[index % colors.length]
}

const showVisualization = async () => {
  if (!hasResults.value) return

  const data = results.value

  statistics.value.totalCount = data.length

  const amounts = data.map((item) => {
    const val = item['拆分路段拆分金额']
    if (val === null || val === undefined || val === '') return 0
    return parseFloat(String(val)) / 100 || 0
  })
  const total = amounts.reduce((sum, val) => sum + val, 0)
  statistics.value.totalAmount = total.toFixed(2)
  statistics.value.avgAmount = data.length > 0 ? (total / data.length).toFixed(2) : '0.00'

  const vehicleTypeMap = new Map<string, number>()
  const vehicleTypeAmountMap = new Map<string, number>()
  data.forEach((item, index) => {
    const type = item['收费车型'] || '未知'
    vehicleTypeMap.set(type, (vehicleTypeMap.get(type) || 0) + 1)
    vehicleTypeAmountMap.set(type, (vehicleTypeAmountMap.get(type) || 0) + amounts[index])
  })

  const vehicleTypeOrder = [
    '1',
    '2',
    '3',
    '4',
    '11',
    '12',
    '13',
    '14',
    '15',
    '16',
    '21',
    '22',
    '23',
    '24',
    '25',
    '26'
  ]

  const vehicleTypeData = Array.from(vehicleTypeMap.entries())
    .map(([name, count]) => ({
      name,
      count,
      percentage: parseFloat(((count / data.length) * 100).toFixed(1))
    }))
    .sort((a, b) => {
      const indexA = vehicleTypeOrder.indexOf(a.name)
      const indexB = vehicleTypeOrder.indexOf(b.name)
      if (indexA === -1 && indexB === -1) return a.name.localeCompare(b.name)
      if (indexA === -1) return 1
      if (indexB === -1) return -1
      return indexA - indexB
    })
  vehicleTypeDistribution.value = vehicleTypeData

  const vehicleTypeAmountData = Array.from(vehicleTypeAmountMap.entries())
    .map(([name, amount]) => ({
      name,
      amount: amount.toFixed(2),
      percentage: total > 0 ? parseFloat(((amount / total) * 100).toFixed(1)) : 0
    }))
    .sort((a, b) => {
      const indexA = vehicleTypeOrder.indexOf(a.name)
      const indexB = vehicleTypeOrder.indexOf(b.name)
      if (indexA === -1 && indexB === -1) return a.name.localeCompare(b.name)
      if (indexA === -1) return 1
      if (indexB === -1) return -1
      return indexA - indexB
    })
  vehicleTypeAmountDistribution.value = vehicleTypeAmountData

  let passengerCount = 0
  let cargoCount = 0
  data.forEach((item) => {
    const type = item['收费车型'] || ''
    const typeNum = parseInt(type)
    if (typeNum >= 1 && typeNum <= 4) {
      passengerCount++
    } else if (typeNum >= 11 && typeNum <= 26) {
      cargoCount++
    }
  })
  passengerCargoRatio.value = {
    passenger: data.length > 0 ? ((passengerCount / data.length) * 100).toFixed(1) + '%' : '0.0%',
    cargo: data.length > 0 ? ((cargoCount / data.length) * 100).toFixed(1) + '%' : '0.0%'
  }

  const amountRanges = [
    { min: 0, max: 50, label: '0-50元' },
    { min: 50, max: 100, label: '50-100元' },
    { min: 100, max: 200, label: '100-200元' },
    { min: 200, max: 500, label: '200-500元' },
    { min: 500, max: Infinity, label: '500元以上' }
  ]

  const amountCounts = amountRanges.map((range) => ({
    range: range.label,
    count: amounts.filter((a) => a >= range.min && a < range.max).length,
    percentage: 0
  }))

  amountCounts.forEach((item) => {
    item.percentage =
      data.length > 0 ? parseFloat(((item.count / data.length) * 100).toFixed(1)) : 0
  })
  amountDistribution.value = amountCounts.filter((item) => item.count > 0)

  const exitMap = new Map<string, number>()
  data.forEach((item) => {
    const exit = item['收费出口名称'] || '未知'
    exitMap.set(exit, (exitMap.get(exit) || 0) + 1)
  })

  const exitData = Array.from(exitMap.entries())
    .map(([name, count]) => ({
      name,
      count,
      percentage: parseFloat(((count / data.length) * 100).toFixed(1))
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)
  exitDistribution.value = exitData

  const entryCodes: string[] = []
  const exitCodes: string[] = []

  data.forEach((item) => {
    const entryCode = item['收费入口编码'] || ''
    const exitCode = item['收费出口编码'] || ''
    if (entryCode && entryCode.length >= 14) {
      entryCodes.push(entryCode)
    }
    if (exitCode && exitCode.length >= 14) {
      exitCodes.push(exitCode)
    }
  })

  try {
    const allCodes = [...new Set([...entryCodes, ...exitCodes])]
    let codeProvinceMap: Record<string, string> = {}

    if (allCodes.length > 0) {
      const provinceRes = await getProvincesByCodes(allCodes)
      if (provinceRes.code === 200 && provinceRes.data) {
        codeProvinceMap = provinceRes.data
      }
    }

    const entryProvinceMap = new Map<string, number>()
    entryCodes.forEach((code) => {
      const code14 = code.substring(0, 14)
      const province = codeProvinceMap[code14] || '未知'
      entryProvinceMap.set(province, (entryProvinceMap.get(province) || 0) + 1)
    })

    const entryProvinceData = Array.from(entryProvinceMap.entries())
      .map(([name, count]) => ({
        name,
        count,
        percentage:
          entryCodes.length > 0 ? parseFloat(((count / entryCodes.length) * 100).toFixed(1)) : 0
      }))
      .sort((a, b) => b.count - a.count)
    entryProvinceDistribution.value = entryProvinceData

    const exitProvinceMap = new Map<string, number>()
    exitCodes.forEach((code) => {
      const code14 = code.substring(0, 14)
      const province = codeProvinceMap[code14] || '未知'
      exitProvinceMap.set(province, (exitProvinceMap.get(province) || 0) + 1)
    })

    const exitProvinceData = Array.from(exitProvinceMap.entries())
      .map(([name, count]) => ({
        name,
        count,
        percentage:
          exitCodes.length > 0 ? parseFloat(((count / exitCodes.length) * 100).toFixed(1)) : 0
      }))
      .sort((a, b) => b.count - a.count)
    exitProvinceDistribution.value = exitProvinceData
  } catch (err) {
    console.error('获取省份信息失败:', err)
    entryProvinceDistribution.value = []
    exitProvinceDistribution.value = []
  }

  const pathLengths = data.map((item) => {
    const path = item['拆分收费单元名称组合'] || ''
    return (path.match(/\|/g) || []).length + 1
  })

  const lengthRanges = [
    { min: 1, max: 5, label: '1-5段' },
    { min: 5, max: 10, label: '5-10段' },
    { min: 10, max: 20, label: '10-20段' },
    { min: 20, max: Infinity, label: '20段以上' }
  ]

  const lengthCounts = lengthRanges.map((range) => ({
    range: range.label,
    count: pathLengths.filter((l) => l >= range.min && l < range.max).length,
    percentage: 0
  }))

  lengthCounts.forEach((item) => {
    item.percentage =
      data.length > 0 ? parseFloat(((item.count / data.length) * 100).toFixed(1)) : 0
  })
  pathLengthDistribution.value = lengthCounts.filter((item) => item.count > 0)

  visualizationVisible.value = true
}

const copySql = (sql: string) => {
  navigator.clipboard
    .writeText(sql)
    .then(() => {
      ElMessage.success('SQL 已复制到剪贴板')
    })
    .catch(() => {
      ElMessage.error('复制失败')
    })
}

const buildPreviewSql = (params: any, tableName: string) => {
  const {
    timeRange,
    transactionTimeRange,
    includeUnits,
    endUnit,
    excludeExits,
    excludeUnits,
    excludeGreenChannel,
    vehicleTypes
  } = params

  const selectFields =
    '`通行标识ID`, `收费入口编码`, `收费出口编码`, `收费入口名称`, `收费出口名称`, `计费交易起点时间`, `计费交易终点时间`, `实际车辆车牌号码+颜色`, `收费车型`, `清分日`, `拆分路段拆分金额`, `拆分收费单元名称组合`'
  let sql = `SELECT ${selectFields} FROM \`${tableName}\` WHERE 1=1`

  if (timeRange && timeRange.length === 2) {
    if (transactionTimeRange && transactionTimeRange.length === 2) {
      const startDate = transactionTimeRange[0]
      const endDate = transactionTimeRange[1]
      sql += `\n  AND \`清分日\` >= '${startDate}'`
      sql += `\n  AND \`清分日\` <= '${endDate} 23:59:59'`
    } else {
      const startDate = timeRange[0].split(' ')[0]
      const endDate = timeRange[1].split(' ')[0]
      sql += `\n  AND \`计费交易起点时间\` >= '${startDate}'`
      sql += `\n  AND \`计费交易终点时间\` <= '${endDate}'`
    }

    if (excludeGreenChannel) {
      sql += `\n  AND \`拆分类型/数据类型\` != 36`
    }

    if (vehicleTypes) {
      const typesArray = vehicleTypes.split(',').filter((item: string) => item)
      if (typesArray.length > 0 && typesArray.length < allVehicleTypeValues.length) {
        sql += `\n  AND \`收费车型\` IN (${typesArray.map((t: string) => `'${t}'`).join(', ')})`
      }
    }

    if (includeUnits && endUnit) {
      sql += `\n  AND \`拆分收费单元名称组合\` LIKE '%${includeUnits.trim()}%${endUnit.trim()}%'`
    } else if (includeUnits) {
      sql += `\n  AND \`拆分收费单元名称组合\` LIKE '%${includeUnits.trim()}%'`
    } else if (endUnit) {
      sql += `\n  AND \`拆分收费单元名称组合\` LIKE '%${endUnit.trim()}%'`
    }

    if (excludeUnits) {
      const excludeUnitsArray = excludeUnits
        .split(',')
        .map((item: string) => item.trim())
        .filter((item: string) => item)
      excludeUnitsArray.forEach((unit: string) => {
        sql += `\n  AND \`拆分收费单元名称组合\` NOT LIKE '%${unit}%'`
      })
    }

    if (excludeExits) {
      const excludeExitsArray = excludeExits
        .split(',')
        .map((item: string) => item.trim())
        .filter((item: string) => item)
      excludeExitsArray.forEach((exit: string) => {
        sql += `\n  AND \`收费出口名称\` NOT LIKE '${exit}%'`
      })
    }
  } else {
    if (excludeGreenChannel) {
      sql += `\n  AND \`拆分类型/数据类型\` != 36`
    }

    if (vehicleTypes) {
      const typesArray = vehicleTypes.split(',').filter((item: string) => item)
      if (typesArray.length > 0 && typesArray.length < allVehicleTypeValues.length) {
        sql += `\n  AND \`收费车型\` IN (${typesArray.map((t: string) => `'${t}'`).join(', ')})`
      }
    }

    if (includeUnits && endUnit) {
      sql += `\n  AND \`拆分收费单元名称组合\` LIKE '%${includeUnits.trim()}%${endUnit.trim()}%'`
    } else if (includeUnits) {
      sql += `\n  AND \`拆分收费单元名称组合\` LIKE '%${includeUnits.trim()}%'`
    } else if (endUnit) {
      sql += `\n  AND \`拆分收费单元名称组合\` LIKE '%${endUnit.trim()}%'`
    }

    if (excludeExits) {
      const excludeExitsArray = excludeExits
        .split(',')
        .map((item: string) => item.trim())
        .filter((item: string) => item)
      excludeExitsArray.forEach((exit: string) => {
        sql += `\n  AND \`收费出口名称\` NOT LIKE '${exit}%'`
      })
    }

    if (excludeUnits) {
      const excludeUnitsArray = excludeUnits
        .split(',')
        .map((item: string) => item.trim())
        .filter((item: string) => item)
      excludeUnitsArray.forEach((unit: string) => {
        sql += `\n  AND \`拆分收费单元名称组合\` NOT LIKE '%${unit}%'`
      })
    }
  }

  return sql
}

const searchData = async () => {
  loading.value = true
  searched.value = true
  debugInfo.value = null

  const params = {
    timeRange: timeRange.value,
    transactionTimeRange: transactionTimeRange.value,
    includeUnits: startUnit.value,
    endUnit: endUnit.value,
    excludeExits: excludeExits.value.join(','),
    excludeUnits: excludeUnits.value,
    excludeGreenChannel: excludeGreenChannel.value,
    vehicleTypes: selectedVehicleTypes.value.join(',')
  }

  requestParams.value = JSON.stringify(params, null, 2)

  previewSql.value = buildPreviewSql(params, 'path_match_table')

  try {
    const res: any = await searchPathMatch(params)

    if (res.code === 200 && res.data) {
      results.value = res.data

      nextTick(() => {
        updateTableWidth()
      })

      if (res.debug) {
        debugInfo.value = res.debug
      }
    } else {
      ElMessage.error(res.message || '搜索失败')
      results.value = []
    }
  } catch (err) {
    console.error('请求失败:', err)
    ElMessage.error('请求失败，请检查后端服务器是否运行')
    results.value = []
  } finally {
    loading.value = false
  }
}

const exportExcel = () => {
  if (!hasResults.value) {
    ElMessage.warning('没有数据可导出')
    return
  }

  const headers = [
    '通行标识ID',
    '收费入口名称',
    '收费出口名称',
    '车牌号码',
    '收费车型',
    '清分日',
    '拆分金额(分)',
    '拆分收费单元名称组合'
  ]
  const csvContent = [
    headers.join(','),
    ...results.value.map((item, index) =>
      [
        `"${(item['通行标识ID'] || '').replace(/"/g, '""')}"`,
        `"${(item['收费入口名称'] || '').replace(/"/g, '""')}"`,
        `"${(item['收费出口名称'] || '').replace(/"/g, '""')}"`,
        `"${(item['实际车辆车牌号码+颜色'] || '').replace(/"/g, '""')}"`,
        `"${(item['收费车型'] || '').replace(/"/g, '""')}"`,
        `"${(item['清分日'] || '').replace(/"/g, '""')}"`,
        item['拆分路段拆分金额'] || '0',
        `"${(item['拆分收费单元名称组合'] || '').replace(/"/g, '""')}"`
      ].join(',')
    )
  ].join('\n')

  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.setAttribute('href', url)
  link.setAttribute(
    'download',
    `收费路径匹配结果_${new Date().toISOString().slice(0, 19).replace(/[-:]/g, '').replace('T', '')}.csv`
  )
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
</script>

<style scoped lang="scss">
.path-match {
  max-width: 98%;
  margin: 20px auto;
  padding: 0 20px;

  @media (max-width: 768px) {
    max-width: 100%;
    margin: 10px auto;
    padding: 0 10px;
  }
}

.search-card {
  margin-bottom: 20px;

  @media (max-width: 768px) {
    margin-bottom: 10px;
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  @media (max-width: 768px) {
    font-size: 14px;
  }
}

.search-form {
  margin-top: 20px;

  @media (max-width: 768px) {
    margin-top: 10px;
  }
}

.search-form .el-form-item {
  margin-bottom: 15px;

  @media (max-width: 768px) {
    margin-bottom: 12px;
  }
}

.time-range-wrapper {
  display: flex;
  align-items: center;
  gap: 15px;

  @media (max-width: 768px) {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;

    .el-date-editor {
      width: 100% !important;
    }
  }
}

.exclude-checkbox {
  @media (max-width: 768px) {
    margin-top: 5px;
  }
}

.button-group {
  @media (max-width: 768px) {
    .el-button {
      margin-bottom: 8px;
      margin-right: 8px;

      &:last-child {
        margin-right: 0;
      }
    }
  }

  @media (min-width: 769px) {
    .el-button {
      margin-right: 10px;

      &:last-child {
        margin-right: 0;
      }
    }
  }
}

.result-card {
  margin-bottom: 20px;
  min-height: 400px;

  @media (max-width: 768px) {
    min-height: 300px;
    margin-bottom: 10px;
  }
}

.detail-scroll-container {
  max-height: 60vh;
  overflow-y: auto;

  @media (max-width: 768px) {
    max-height: 50vh;
  }
}

.detail-value {
  word-break: break-all;
  white-space: pre-wrap;
  max-height: 300px;
  overflow-y: auto;

  @media (max-width: 768px) {
    max-height: 200px;
    font-size: 13px;
  }
}

:deep(.detail-label) {
  width: 180px;
  font-weight: bold;

  @media (max-width: 768px) {
    width: 120px;
    font-size: 13px;
  }
}

.el-table {
  cursor: pointer;

  @media (max-width: 768px) {
    font-size: 12px;
  }
}

.virtual-table-container {
  width: 100%;
  height: 500px;

  @media (max-width: 768px) {
    height: 350px;
  }
}

.copyable-header {
  cursor: pointer;
  user-select: all;
}

.copyable-header:hover {
  color: #409eff;
}

.loading-container {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 50px 0;
  color: #409eff;

  @media (max-width: 768px) {
    padding: 30px 0;
    font-size: 14px;
  }
}

.loading-container .loading {
  font-size: 24px;
  margin-right: 10px;
  animation: rotate 1s linear infinite;

  @media (max-width: 768px) {
    font-size: 18px;
  }
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.empty-container {
  padding: 50px 0;

  @media (max-width: 768px) {
    padding: 30px 0;
  }
}

.path-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

@media (max-width: 768px) {
  :deep(.el-form-item__label) {
    font-size: 13px;
    padding-bottom: 5px;
  }

  :deep(.el-input__inner) {
    font-size: 14px;
  }

  :deep(.el-select-v2__wrapper) {
    font-size: 14px;
  }

  :deep(.el-date-editor) {
    font-size: 13px;
  }

  :deep(.el-checkbox__label) {
    font-size: 13px;
  }

  :deep(.el-dialog) {
    width: 95% !important;
    margin-top: 5vh !important;
  }

  :deep(.el-dialog__body) {
    padding: 15px;
  }
}

@media (max-width: 480px) {
  :deep(.el-button) {
    padding: 8px 12px;
    font-size: 12px;
  }

  :deep(.el-form-item__label) {
    font-size: 12px;
  }

  :deep(.el-input__inner) {
    font-size: 13px;
  }
}

.debug-panel {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 16px;
    font-weight: bold;
  }

  .debug-content {
    .debug-statistics {
      margin-bottom: 20px;
    }

    .debug-section {
      margin-bottom: 20px;

      h4 {
        margin: 0 0 10px 0;
        font-size: 14px;
        color: #606266;
      }

      .el-textarea {
        :deep(.el-textarea__inner) {
          font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
          font-size: 13px;
          color: #303133;
          background-color: #f5f7fa;
        }
      }
    }
  }
}

.visualization-dialog {
  :deep(.el-dialog__body) {
    max-height: 65vh;
    overflow-y: auto;
    padding: 10px 15px;
  }
}

.visualization-container {
  padding: 0;
  max-height: 65vh;
  overflow-y: auto;
}

.chart-card {
  height: 100%;
}

.chart-wrapper {
  min-height: 80px;
}

.bar-chart {
  .bar-item {
    display: flex;
    align-items: center;
    margin-bottom: 8px;

    .bar-label {
      width: 70px;
      font-size: 12px;
      color: #606266;
    }

    .bar-container {
      flex: 1;
      height: 16px;
      background-color: #f0f0f0;
      border-radius: 3px;
      overflow: hidden;
      margin: 0 8px;

      .bar-fill {
        height: 100%;
        background: linear-gradient(90deg, #409eff, #67c23a);
        border-radius: 3px;
        transition: width 0.3s ease;

        &.bar-fill-blue {
          background: linear-gradient(90deg, #409eff, #9b59b6);
        }
      }
    }

    .bar-value {
      width: 90px;
      font-size: 11px;
      color: #909399;
      text-align: right;
    }
  }
}

.pie-chart {
  .pie-item {
    display: flex;
    align-items: center;
    margin-bottom: 6px;

    .pie-color {
      width: 12px;
      height: 12px;
      border-radius: 2px;
      margin-right: 8px;
    }

    .pie-label {
      flex: 1;
      font-size: 12px;
      color: #606266;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .pie-value {
      width: 85px;
      font-size: 11px;
      color: #909399;
      text-align: right;
    }
  }
}

.stat-card {
  text-align: center;
  padding: 10px 0;

  .stat-value {
    font-size: 20px;
    font-weight: bold;
    color: #409eff;
    margin-bottom: 3px;
  }

  .stat-label {
    font-size: 12px;
    color: #909399;
  }

  .stat-row {
    display: flex;
    justify-content: center;
    align-items: center;
    margin: 5px 0;
  }

  .stat-label-inline {
    font-size: 12px;
    color: #909399;
    margin-right: 5px;
  }

  .stat-value-inline {
    font-size: 14px;
    font-weight: bold;
    color: #409eff;
  }
}
</style>
