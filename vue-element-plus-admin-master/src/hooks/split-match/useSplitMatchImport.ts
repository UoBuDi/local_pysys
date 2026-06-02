import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getSplitMatchData, updateSplitMatchData } from '@/api/split-match'

export interface ImportMatchResult {
  通行标识ID: string
  匹配状态: string
  导入数据: any
}

export const useSplitMatchImport = (getSelectedTable: () => string, getFilters: () => any) => {
  const importPreviewVisible = ref(false)
  const importData = ref<any[]>([])
  const importResult = ref<ImportMatchResult[]>([])
  const importError = ref('')
  const importLoading = ref(false)
  const importProgress = ref(0)
  const importProgressText = ref('')
  const importStep = ref<'preview' | 'matching' | 'importing'>('preview')
  const importTotalCount = ref(0)
  const uploadLoading = ref(false)
  const uploadProgress = ref(0)
  const uploadProgressText = ref('')
  const extractedImagesCount = ref(0)

  const getAllTableData = async (): Promise<any[]> => {
    const tableName = getSelectedTable()
    if (!tableName) return []

    try {
      const response = await getSplitMatchData({
        table_name: tableName,
        filters: JSON.stringify(getFilters()),
        page: 1,
        page_size: 10000
      })

      if (response && response.code === 200 && response.data) {
        return Array.isArray(response.data.data) ? response.data.data : []
      }
      return []
    } catch (error) {
      console.error('获取所有表格数据失败:', error)
      ElMessage.error('获取所有表格数据失败')
      return []
    }
  }

  const matchImportData = async (allTableData: any[]) => {
    if (allTableData.length === 0) {
      ElMessage.warning('没有数据可匹配')
      return
    }

    const matchResult: ImportMatchResult[] = []
    const total = importData.value.length

    const tableDataMap = new Map<string, any>()
    for (const tableRow of allTableData) {
      const tableId = String(tableRow['通行标识ID'])
        .trim()
        .replace(/[^a-zA-Z0-9]/g, '')
        .toLowerCase()
      if (tableId) {
        tableDataMap.set(tableId, tableRow)
      }
    }

    for (let i = 0; i < total; i++) {
      const importRow = importData.value[i]
      const 通行标识ID = importRow['通行标识ID']

      if (!通行标识ID) {
        matchResult.push({
          通行标识ID: '',
          匹配状态: '缺少通行标识ID',
          导入数据: importRow
        })
        continue
      }

      const importId = String(通行标识ID)
        .trim()
        .replace(/[^a-zA-Z0-9]/g, '')
        .toLowerCase()
      const matchedRow = tableDataMap.get(importId)

      if (matchedRow) {
        matchResult.push({
          通行标识ID: String(matchedRow['通行标识ID']),
          匹配状态: '已匹配',
          导入数据: importRow
        })
      } else {
        matchResult.push({
          通行标识ID: String(通行标识ID),
          匹配状态: '未匹配',
          导入数据: importRow
        })
      }

      importProgress.value = Math.round(((i + 1) / total) * 100)
      importProgressText.value = `正在匹配 ${i + 1}/${total}...`

      if (i % 50 === 0) {
        await new Promise((resolve) => setTimeout(resolve, 0))
      }
    }

    importResult.value = matchResult
  }

  const processImportedImages = async (importRow: any) => {
    const processedRow: any = { ...importRow }

    for (const field of ['查核资料1', '查核资料2']) {
      if (processedRow[field]) {
        try {
          if (
            typeof processedRow[field] === 'string' &&
            processedRow[field].startsWith('=DISPIMG(')
          ) {
            continue
          }
          if (typeof processedRow[field] === 'string' && processedRow[field].includes(',')) {
            const { convertToWebP } = await import('./useImageHandler').then((m) => ({
              convertToWebP: m.useImageHandler
            }))
          }
        } catch (error) {
          console.error(`处理${field}图片失败:`, error)
        }
      }
    }

    return processedRow
  }

  const executeImport = async (onReloadData: () => Promise<void>) => {
    const tableName = getSelectedTable()
    if (!tableName || importResult.value.length === 0) {
      ElMessage.warning('没有数据可导入')
      return
    }

    importLoading.value = true
    let successCount = 0
    let errorCount = 0
    const total = importResult.value.length

    try {
      for (let i = 0; i < total; i++) {
        const item = importResult.value[i]
        try {
          importProgress.value = Math.round(((i + 1) / total) * 100)
          importProgressText.value = `正在导入 ${i + 1}/${total}...`

          const processedImportData = await processImportedImages(item.导入数据)

          const updateData: any = {
            核查通行标识: processedImportData['核查通行标识'],
            复核情况: processedImportData['复核情况'],
            备注: processedImportData['备注'],
            查核资料1: processedImportData['查核资料1'],
            查核资料2: processedImportData['查核资料2'],
            特情: processedImportData['特情']
          }

          Object.keys(updateData).forEach((key) => {
            if (updateData[key] === undefined) delete updateData[key]
          })

          await updateSplitMatchData({
            table_name: tableName,
            row_id: String(item.通行标识ID),
            data: updateData
          })

          successCount++
        } catch (error) {
          console.error(`更新数据失败，通行标识ID: ${item.通行标识ID}`, error)
          errorCount++
        }

        await new Promise((resolve) => setTimeout(resolve, 50))
      }

      importProgress.value = 100
      importProgressText.value = '导入完成'
      ElMessage.success(`导入完成，成功: ${successCount} 条，失败: ${errorCount} 条`)

      await onReloadData()
    } catch (error) {
      console.error('导入数据失败:', error)
      ElMessage.error('导入数据失败')
    } finally {
      importLoading.value = false
    }
  }

  const startImport = async (onReloadData: () => Promise<void>) => {
    const tableName = getSelectedTable()
    if (!tableName || importData.value.length === 0) {
      ElMessage.warning('没有数据可导入')
      return
    }

    importStep.value = 'matching'
    importProgress.value = 0
    importProgressText.value = '正在匹配数据...'
    importTotalCount.value = importData.value.length
    importResult.value = []

    try {
      importProgress.value = 10
      importProgressText.value = '正在获取所有表格数据...'

      const allTableData = await getAllTableData()

      if (allTableData.length === 0) {
        ElMessage.warning('没有数据可匹配')
        importLoading.value = false
        return
      }

      await matchImportData(allTableData)

      importStep.value = 'importing'
      importProgress.value = 0
      importProgressText.value = '正在导入数据...'
      await executeImport(onReloadData)
    } catch (error) {
      console.error('导入过程失败:', error)
      importError.value = '导入过程失败'
      ElMessage.error('导入过程失败')
      importStep.value = 'preview'
    } finally {
      importLoading.value = false
    }
  }

  const handleImportCancel = () => {
    importData.value = []
    importResult.value = []
    importError.value = ''
    importProgress.value = 0
    importProgressText.value = ''
    importStep.value = 'preview'
    importTotalCount.value = 0
    importPreviewVisible.value = false
  }

  const getImportDialogTitle = () => {
    switch (importStep.value) {
      case 'preview':
        return '导入数据预览'
      case 'matching':
        return '正在匹配数据'
      case 'importing':
        return '正在导入数据'
      default:
        return '导入数据预览'
    }
  }

  const getUploadStatusText = () => {
    if (uploadProgress.value < 30) return '正在初始化文件读取...'
    if (uploadProgress.value < 70) return '正在解析Excel文件内容...'
    if (uploadProgress.value < 100) return '正在处理数据...'
    return '文件读取完成，准备导入...'
  }

  const getStatusColor = () => {
    if (uploadProgress.value < 30) return '#409eff'
    if (uploadProgress.value < 70) return '#67c23a'
    if (uploadProgress.value < 100) return '#e6a23c'
    return '#67c23a'
  }

  const isIdMatched = (id: any): boolean => {
    if (!id) return false
    const importId = String(id)
      .trim()
      .replace(/[^a-zA-Z0-9]/g, '')
      .toLowerCase()
    return importResult.value.some((item) => {
      const matchedId = String(item.通行标识ID)
        .trim()
        .replace(/[^a-zA-Z0-9]/g, '')
        .toLowerCase()
      return matchedId === importId
    })
  }

  const isImageData = (data: any): boolean => {
    if (typeof data !== 'string') return false
    return data.startsWith('=DISPIMG(') || data.startsWith('data:image/')
  }

  const getImportColumns = () => {
    const userDefinedOrder = [
      '通行标识ID',
      '车牌号码',
      '核查通行标识',
      '复核情况',
      '备注',
      '查核资料1',
      '查核资料2',
      '特情',
      '门架通行时间',
      '入口时间',
      '收费车型',
      '车种',
      '通行介质',
      '门架应收金额',
      '门架交易金额',
      '收费入口名称',
      '通行门架组合',
      '通行门架名称组合',
      '通行日期'
    ]

    const allColumns = new Set<string>()
    importData.value.forEach((row) => {
      Object.keys(row).forEach((key) => {
        if (key !== '_excelRowNumber') allColumns.add(key)
      })
    })

    const sortedColumns: string[] = []
    userDefinedOrder.forEach((column) => {
      if (allColumns.has(column)) {
        sortedColumns.push(column)
        allColumns.delete(column)
      }
    })
    allColumns.forEach((column) => sortedColumns.push(column))

    return sortedColumns
  }

  const getColumnWidth = (column: string) => {
    const widthMap: Record<string, number> = {
      通行标识ID: 200,
      核查通行标识: 200,
      查核资料1: 100,
      查核资料2: 100
    }
    return widthMap[column] || 120
  }

  return {
    importPreviewVisible,
    importData,
    importResult,
    importError,
    importLoading,
    importProgress,
    importProgressText,
    importStep,
    importTotalCount,
    uploadLoading,
    uploadProgress,
    uploadProgressText,
    extractedImagesCount,
    getAllTableData,
    matchImportData,
    executeImport,
    startImport,
    handleImportCancel,
    getImportDialogTitle,
    getUploadStatusText,
    getStatusColor,
    isIdMatched,
    isImageData,
    getImportColumns,
    getColumnWidth
  }
}
