import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import ExcelJS from 'exceljs'
import { saveAs } from 'file-saver'
import { getExportSplitMatchData } from '@/api/split-match'

const isImageData = (data: any): boolean => {
  if (typeof data !== 'string') return false
  return data.startsWith('=DISPIMG(') || data.startsWith('data:image/')
}

const processImageForExcel = (imageData: string) => {
  if (!imageData || typeof imageData !== 'string') {
    return { success: false }
  }

  if (imageData.startsWith('=DISPIMG(')) {
    return { success: true, isWPS: true, data: null, extension: null }
  }

  if (imageData.startsWith('data:image/')) {
    const matches = imageData.match(/^data:image\/(\w+);base64,(.+)$/)
    if (matches && matches.length >= 3) {
      let extension = matches[1].toLowerCase()
      if (extension === 'jpeg') extension = 'jpeg'
      return {
        success: true,
        isWPS: false,
        data: matches[2],
        extension: extension
      }
    }
  }

  if (/^[A-Za-z0-9+/=]+$/.test(imageData) && imageData.length > 100) {
    return {
      success: true,
      isWPS: false,
      data: imageData,
      extension: 'jpeg'
    }
  }

  return { success: false }
}

const createPlaceholderImage = (text: string, width: number, height: number): string | null => {
  try {
    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    const ctx = canvas.getContext('2d')
    if (!ctx) return null

    ctx.fillStyle = '#f5f5f5'
    ctx.fillRect(0, 0, width, height)
    ctx.strokeStyle = '#d9d9d9'
    ctx.strokeRect(0, 0, width, height)
    ctx.fillStyle = '#999999'
    ctx.font = '10px Arial'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(text, width / 2, height / 2)

    const dataUrl = canvas.toDataURL('image/png')
    return dataUrl.split(',')[1]
  } catch (error) {
    return null
  }
}

export const useSplitMatchExport = (getSelectedTable: () => string, getFilters: () => any) => {
  const exportLoading = ref(false)
  const exportProgress = ref(0)
  const exportProgressText = ref('')
  const exportProgressVisible = ref(false)
  const exportTotalCount = ref(0)
  const exportProcessedCount = ref(0)

  const handleExport = async () => {
    const tableName = getSelectedTable()
    if (!tableName) {
      ElMessage.warning('请先选择数据表')
      return
    }

    exportLoading.value = true
    exportProgress.value = 0
    exportProgressText.value = '正在获取数据...'
    exportProgressVisible.value = true
    exportTotalCount.value = 0
    exportProcessedCount.value = 0

    try {
      const response = await getExportSplitMatchData({
        table_name: tableName,
        filters: JSON.stringify(getFilters())
      })

      let exportData: any[] = []
      let headers: string[] = []
      let columnTypes: Record<string, string> = {}

      if (response && response.code === 200 && response.data) {
        const responseData = response.data
        exportData = Array.isArray(responseData.data) ? responseData.data : []
        headers = Array.isArray(responseData.columns) ? responseData.columns : []
        columnTypes = responseData.column_types || {}
      }

      if (exportData.length === 0) {
        ElMessage.warning('没有数据可导出')
        exportProgressVisible.value = false
        return
      }

      if (headers.length === 0 && exportData.length > 0) {
        headers = Object.keys(exportData[0] || {})
      }

      exportTotalCount.value = exportData.length
      exportProgressText.value = '正在创建工作簿...'
      exportProgress.value = 5

      const workbook = new ExcelJS.Workbook()
      workbook.creator = '拆分匹配系统'
      workbook.created = new Date()

      const worksheet = workbook.addWorksheet('数据', {
        views: [{ state: 'frozen', ySplit: 1 }]
      })

      const IMAGE_COLUMNS = ['查核资料1', '查核资料2']
      const IMAGE_COL_WIDTH = 13.23
      const IMAGE_ROW_HEIGHT = 37.42
      const NORMAL_COL_WIDTH = 15
      const IMAGE_WIDTH_PX = 93
      const IMAGE_HEIGHT_PX = 50

      worksheet.columns = headers.map((header) => ({
        header,
        key: header,
        width: IMAGE_COLUMNS.includes(header) ? IMAGE_COL_WIDTH : NORMAL_COL_WIDTH
      }))

      const headerRow = worksheet.getRow(1)
      headerRow.height = 25
      headerRow.eachCell((cell) => {
        cell.font = { bold: true, size: 11 }
        cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFE0E0E0' } }
        cell.alignment = { horizontal: 'center', vertical: 'middle' }
        cell.border = {
          top: { style: 'thin' },
          left: { style: 'thin' },
          bottom: { style: 'thin' },
          right: { style: 'thin' }
        }
      })

      exportProgressText.value = '正在写入数据...'
      exportProgress.value = 10

      for (let rowIndex = 0; rowIndex < exportData.length; rowIndex++) {
        const row = exportData[rowIndex]
        const dataRow = worksheet.addRow(
          headers.map((header) => {
            const value = row[header]
            if (IMAGE_COLUMNS.includes(header)) return ''
            return value ?? ''
          })
        )

        const hasImage = IMAGE_COLUMNS.some(
          (col) => row[col] && typeof row[col] === 'string' && isImageData(row[col])
        )
        dataRow.height = hasImage ? IMAGE_ROW_HEIGHT : 20

        dataRow.eachCell((cell, colNumber) => {
          const header = headers[colNumber - 1]
          const columnType = columnTypes[header]
          if (columnType && columnType.toLowerCase() === 'varchar') {
            cell.numFmt = '@'
          }
          cell.alignment = {
            horizontal: IMAGE_COLUMNS.includes(header) ? 'center' : 'left',
            vertical: 'middle',
            wrapText: true
          }
          cell.border = {
            top: { style: 'thin' },
            left: { style: 'thin' },
            bottom: { style: 'thin' },
            right: { style: 'thin' }
          }
        })

        if ((rowIndex + 1) % 50 === 0 || rowIndex === exportData.length - 1) {
          const progress = 10 + Math.round((rowIndex / exportData.length) * 40)
          exportProgress.value = progress
          exportProgressText.value = `正在写入数据 ${rowIndex + 1}/${exportData.length}`
          await new Promise((resolve) => setTimeout(resolve, 0))
        }
      }

      exportProgressText.value = '正在处理图片...'
      exportProgress.value = 50

      let processedImages = 0
      const totalImages = exportData.reduce((count, row) => {
        return (
          count +
          IMAGE_COLUMNS.filter(
            (col) => row[col] && typeof row[col] === 'string' && isImageData(row[col])
          ).length
        )
      }, 0)

      for (let rowIndex = 0; rowIndex < exportData.length; rowIndex++) {
        const row = exportData[rowIndex]

        for (const imageCol of IMAGE_COLUMNS) {
          const colIndex = headers.indexOf(imageCol)
          if (colIndex === -1) continue

          const imageData = row[imageCol]
          if (!imageData) continue

          try {
            const result = processImageForExcel(imageData)

            if (result.success && result.data && result.extension) {
              if (result.isWPS) {
                const placeholderBase64 = createPlaceholderImage(
                  'WPS图片',
                  IMAGE_WIDTH_PX,
                  IMAGE_HEIGHT_PX
                )
                if (placeholderBase64) {
                  const imageId = workbook.addImage({ base64: placeholderBase64, extension: 'png' })
                  worksheet.addImage(imageId, {
                    tl: { col: colIndex, row: rowIndex + 1 },
                    br: { col: colIndex + 1, row: rowIndex + 2 },
                    editAs: 'oneCell'
                  })
                }
              } else {
                const imageId = workbook.addImage({
                  base64: result.data,
                  extension: result.extension
                })
                worksheet.addImage(imageId, {
                  tl: { col: colIndex, row: rowIndex + 1 },
                  br: { col: colIndex + 1, row: rowIndex + 2 },
                  editAs: 'oneCell'
                })
              }
            }

            processedImages++
            if (processedImages % 10 === 0 || processedImages === totalImages) {
              const progress = 50 + Math.round((processedImages / Math.max(totalImages, 1)) * 45)
              exportProgress.value = progress
              exportProgressText.value = `正在处理图片 ${processedImages}/${totalImages || 1}`
              await new Promise((resolve) => setTimeout(resolve, 0))
            }
          } catch (error) {
            console.error(`处理图片失败 [行${rowIndex + 2}, 列${imageCol}]:`, error)
          }
        }
      }

      exportProgressText.value = '正在生成Excel文件...'
      exportProgress.value = 95

      const buffer = await workbook.xlsx.writeBuffer()
      const blob = new Blob([buffer], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      })

      const fileName = `${tableName}_${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.xlsx`
      saveAs(blob, fileName)

      exportProgress.value = 100
      exportProgressText.value = '导出完成'

      setTimeout(() => {
        exportProgressVisible.value = false
      }, 1000)

      ElMessage.success(`数据导出成功，共${exportData.length}条记录`)
    } catch (error) {
      console.error('导出失败:', error)
      ElMessage.error('数据导出失败')
      exportProgressVisible.value = false
    } finally {
      exportLoading.value = false
    }
  }

  return {
    exportLoading,
    exportProgress,
    exportProgressText,
    exportProgressVisible,
    exportTotalCount,
    exportProcessedCount,
    handleExport
  }
}
