import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getSplitMatchTables,
  getSplitMatchData,
  getTableImages,
  executeSplitMatch,
  previewSplitMatch,
  getExportSplitMatchData,
  getSplitStatistics,
  type MatchResult
} from '@/api/split-match'

export const useSplitMatchTable = () => {
  const selectedTable = ref('')
  const tableList = ref<Array<{ label: string; value: string }>>([])
  const tableData = ref<Record<string, unknown>[]>([])
  const displayColumns = ref<string[]>([])
  const tableLoading = ref(false)
  const matchLoading = ref(false)
  const matchResult = ref<MatchResult | null>(null)
  const currentPage = ref(1)
  const pageSize = ref(20)
  const total = ref(0)
  const filters = ref({
    通行标识ID: '',
    车牌号码: '',
    核查通行标识: '',
    复核情况: [] as string[],
    备注: '',
    收费车型: '',
    特情: '',
    核查拆分: ''
  })
  const checkSplitOptions = ref<string[]>([])
  const imageLoading = ref(false)
  const imageLoadingProgress = ref(0)
  const imageLoadingTotal = ref(0)
  const imageAbortController = ref<AbortController | null>(null)
  const splitStatistics = ref({ split_count: 0, total_split_amount: 0 })
  const statisticsLoading = ref(false)
  const statisticsVisible = ref(false)
  const splitDetailVisible = ref(false)
  const splitDetailRow = ref<Record<string, unknown> | null>(null)

  const tableMaxHeight = computed(() => {
    const rowHeight = 48
    const headerHeight = 40
    return headerHeight + pageSize.value * rowHeight
  })

  const loadTableList = async () => {
    try {
      const response = await getSplitMatchTables()
      if (response && response.code === 200 && response.data) {
        tableList.value = response.data.map((tableName: string) => ({
          label: tableName.replace('_yc', ''),
          value: tableName
        }))
      } else {
        tableList.value = []
      }
    } catch (error) {
      console.error('获取表列表失败:', error)
      ElMessage.error('获取表列表失败')
    }
  }

  const loadImagesAsync = async (dataRows: any[]) => {
    const passIds = dataRows
      .map((row) => row['通行标识ID'])
      .filter((id): id is string => !!id && typeof id === 'string')

    if (passIds.length === 0) return

    const controller = new AbortController()
    imageAbortController.value = controller

    imageLoading.value = true
    imageLoadingProgress.value = 0
    imageLoadingTotal.value = passIds.length

    try {
      const batchSize = 10
      const totalBatches = Math.ceil(passIds.length / batchSize)
      let loadedCount = 0

      for (let i = 0; i < totalBatches; i++) {
        if (controller.signal.aborted) break

        const batchIds = passIds.slice(i * batchSize, (i + 1) * batchSize)
        const passIdsStr = batchIds.join(',')

        const imageResponse = await getTableImages({
          table_name: selectedTable.value,
          pass_ids: passIdsStr
        })

        if (controller.signal.aborted) break

        if (imageResponse && imageResponse.code === 200 && imageResponse.data) {
          const imagesMap = imageResponse.data
          tableData.value = tableData.value.map((row: any) => {
            const passId = row['通行标识ID']
            if (passId && imagesMap[passId]) {
              const images = imagesMap[passId]
              return {
                ...row,
                查核资料1: images['查核资料1'] || null,
                查核资料2: images['查核资料2'] || null
              }
            }
            return row
          })
        }

        loadedCount += batchIds.length
        imageLoadingProgress.value = loadedCount
      }
    } catch (error) {
      if (controller.signal.aborted) return
      console.error('加载图片失败:', error)
    } finally {
      imageLoading.value = false
      imageLoadingProgress.value = 0
      imageLoadingTotal.value = 0
      if (imageAbortController.value === controller) {
        imageAbortController.value = null
      }
    }
  }

  const loadTableData = async () => {
    if (!selectedTable.value) {
      tableData.value = []
      displayColumns.value = []
      total.value = 0
      return
    }

    if (imageAbortController.value) {
      imageAbortController.value.abort()
      imageAbortController.value = null
    }

    tableLoading.value = true
    try {
      const params = {
        table_name: selectedTable.value,
        filters: JSON.stringify(filters.value),
        page: currentPage.value,
        page_size: pageSize.value
      }

      const response = await getSplitMatchData(params)

      let tableDataArray: any[] = []
      let columnsArray: string[] = []
      let totalCount = 0

      if (response && response.code === 200 && response.data) {
        const responseData = response.data
        tableDataArray = Array.isArray(responseData.data) ? responseData.data : []
        columnsArray = Array.isArray(responseData.columns) ? responseData.columns : []
        totalCount = typeof responseData.total === 'number' ? responseData.total : 0
      }

      const imageFields = ['查核资料1', '查核资料2']
      for (const imgField of imageFields) {
        if (!columnsArray.includes(imgField)) {
          columnsArray.push(imgField)
        }
      }

      const processedData = tableDataArray.map((row: any) => ({
        ...row,
        查核资料1: null,
        查核资料2: null
      }))

      tableData.value = processedData
      displayColumns.value = columnsArray
      total.value = totalCount

      const splitValues = new Set<string>()
      splitValues.add('已拆')
      splitValues.add('未拆')
      processedData.forEach((row) => {
        const value = row['核查拆分']
        if (value && typeof value === 'string') {
          splitValues.add(value)
        }
      })
      checkSplitOptions.value = Array.from(splitValues)

      await loadImagesAsync(tableDataArray)
    } catch (error) {
      console.error('获取表数据失败:', error)
      ElMessage.error('获取表数据失败，请检查后端服务')
      tableData.value = []
      displayColumns.value = []
      total.value = 0
    } finally {
      tableLoading.value = false
    }
  }

  const handleTableChange = () => {
    currentPage.value = 1
    matchResult.value = null
    loadTableData()
  }

  const handleExecuteMatch = async () => {
    if (!selectedTable.value) {
      ElMessage.warning('请先选择数据表')
      return
    }

    matchLoading.value = true
    try {
      const exportParams = {
        table_name: selectedTable.value,
        filters: JSON.stringify(filters.value)
      }
      const exportResponse = await getExportSplitMatchData(exportParams)

      if (!exportResponse || !exportResponse.data || !exportResponse.data.data) {
        ElMessage.error('获取记录失败')
        return
      }

      const allRecords = exportResponse.data.data
      const recordsToMatch = allRecords.map((record: any) => ({
        id: record.id,
        通行标识ID: record['通行标识ID'],
        核查通行标识: record['核查通行标识']
      }))

      const params = {
        table_name: selectedTable.value,
        records: recordsToMatch
      }

      await previewSplitMatch(params)

      const response = await executeSplitMatch(params)

      let responseData = null
      if (response && response.code === 200) {
        responseData = response.data
      }

      if (responseData) {
        if (responseData && typeof responseData === 'object') {
          matchResult.value = responseData as unknown as MatchResult
          ElMessage.success('匹配完成')
          loadTableData()
        } else {
          ElMessage.error('执行匹配失败')
        }
      }
    } catch (error) {
      console.error('执行匹配失败:', error)
      ElMessage.error('执行匹配失败')
    } finally {
      matchLoading.value = false
    }
  }

  const handleSizeChange = (size: number) => {
    pageSize.value = size
    currentPage.value = 1
    loadTableData()
  }

  const handleCurrentChange = (page: number) => {
    currentPage.value = page
    loadTableData()
  }

  const cancelImageLoading = () => {
    if (imageAbortController.value) {
      imageAbortController.value.abort()
      imageAbortController.value = null
    }
  }

  const loadSplitStatistics = async () => {
    if (!selectedTable.value) return
    statisticsLoading.value = true
    try {
      const response = await getSplitStatistics({ table_name: selectedTable.value })
      if (response && response.code === 200 && response.data) {
        splitStatistics.value = response.data
      }
    } catch (error) {
      console.error('获取拆分统计失败:', error)
      ElMessage.error('获取拆分统计失败')
    } finally {
      statisticsLoading.value = false
    }
  }

  const handleSplitStatistics = () => {
    loadSplitStatistics().then(() => {
      statisticsVisible.value = true
    })
  }

  const handleSplitDetailClick = (row: Record<string, unknown>) => {
    splitDetailRow.value = row
    splitDetailVisible.value = true
  }

  return {
    selectedTable,
    tableList,
    tableData,
    displayColumns,
    tableLoading,
    matchLoading,
    matchResult,
    currentPage,
    pageSize,
    total,
    filters,
    checkSplitOptions,
    imageLoading,
    imageLoadingProgress,
    imageLoadingTotal,
    tableMaxHeight,
    splitStatistics,
    statisticsLoading,
    statisticsVisible,
    splitDetailVisible,
    splitDetailRow,
    loadTableList,
    loadTableData,
    handleTableChange,
    handleExecuteMatch,
    handleSizeChange,
    handleCurrentChange,
    cancelImageLoading,
    handleSplitStatistics,
    handleSplitDetailClick
  }
}
