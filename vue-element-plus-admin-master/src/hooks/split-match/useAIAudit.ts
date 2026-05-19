import { ref, computed, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { domToPng } from 'modern-screenshot'
import {
  aiAuditBatchQuery,
  aiAuditVehicleImages,
  aiAuditOriginalImage,
  aiAuditGantryImages,
  aiAuditSaveImages,
  type AIAuditVehicleImage,
  type AIAuditGantryImage,
  type AIAuditGantryTrade,
  type AIAuditBatchQueryResult
} from '@/api/split-match'

const ORIGINAL_IMAGE_CACHE_MAX_SIZE = 100
const originalImageCache = new Map<string, string>()

const SCREENSHOT_CACHE_MAX_SIZE = 10
const screenshotCache = new Map<string, { dataUrl: string; timestamp: number }>()
const SCREENSHOT_CACHE_TTL = 5 * 60 * 1000

const setOriginalImageCache = (key: string, value: string) => {
  if (originalImageCache.size >= ORIGINAL_IMAGE_CACHE_MAX_SIZE) {
    const firstKey = originalImageCache.keys().next().value
    if (firstKey !== undefined) {
      originalImageCache.delete(firstKey)
    }
  }
  originalImageCache.set(key, value)
}

const clearOriginalImageCache = () => {
  originalImageCache.clear()
}

const clearScreenshotCache = () => {
  screenshotCache.clear()
}

const computeTableHash = async (el: HTMLElement): Promise<string> => {
  const textContent = el.innerText || ''
  const styleContent = Array.from(el.attributes)
    .map((attr) => `${attr.name}=${attr.value}`)
    .join('&')
  
  const rawString = `${textContent}|${styleContent}|${el.children.length}`
  
  const encoder = new TextEncoder()
  const data = encoder.encode(rawString)
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('')
}

const getCachedScreenshot = (cacheKey: string): string | null => {
  const cached = screenshotCache.get(cacheKey)
  if (!cached) return null
  
  const now = Date.now()
  if (now - cached.timestamp > SCREENSHOT_CACHE_TTL) {
    screenshotCache.delete(cacheKey)
    return null
  }
  
  return cached.dataUrl
}

const setCachedScreenshot = (cacheKey: string, dataUrl: string) => {
  if (screenshotCache.size >= SCREENSHOT_CACHE_MAX_SIZE) {
    let oldestKey: string | null = null
    let oldestTime = Infinity
    
    screenshotCache.forEach((value, key) => {
      if (value.timestamp < oldestTime) {
        oldestTime = value.timestamp
        oldestKey = key
      }
    })
    
    if (oldestKey) {
      screenshotCache.delete(oldestKey)
    }
  }
  
  screenshotCache.set(cacheKey, { dataUrl, timestamp: Date.now() })
}

export const useAIAudit = (isLoggedIn: () => boolean) => {
  const aiAuditLoading = ref(false)
  const aiAuditResult = ref<AIAuditBatchQueryResult | null>(null)
  const aiAuditReviewStatus = ref('')
  const aiAuditCheckPassId = ref('')
  const aiAuditSpecialSituation = ref('')
  const aiAuditCheckSplit = ref('')
  const aiAuditRemark = ref('')
  const aiAuditSelectedImage1 = ref('')
  const aiAuditSelectedImage2 = ref('')
  const aiAuditSavingImages = ref(false)
  const originalImageLoading = ref('')
  const previewLoading = ref('')
  const previewLoadingText = ref('')
  const previewImageList = ref<string[]>([])

  const vehicleImagesPage = ref(0)
  const vehicleImagesPageSize = ref(20)
  const vehicleImagesTotal = ref(0)
  const vehicleImagesLoading = ref(false)
  const vehicleImagesSort = ref('desc')
  const maxPage = computed(() => Math.max(0, Math.ceil(vehicleImagesTotal.value / vehicleImagesPageSize.value) - 1))

  const gantryImagesResult = ref<any>(null)
  const gantryImagesPreviewList = ref<string[]>([])
  const gantryImagesDialogVisible = ref(false)
  const gantryImageLoading = ref('')

  const vehicleDetailResult = ref<AIAuditBatchQueryResult | null>(null)
  const vehicleDetailLoading = ref(false)
  const vehicleDetailDialogVisible = ref(false)
  const vehicleDetailActiveTab = ref('gantry_trade')
  const vehicleDetailPlate = ref('')

  const getImageSrc = (base64Data: string | undefined): string => {
    if (!base64Data) return ''
    if (base64Data.startsWith('data:image')) return base64Data
    return 'data:image/jpeg;base64,' + base64Data
  }

  const formatDateTimeForQuery = (date: Date): string => {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    const seconds = String(date.getSeconds()).padStart(2, '0')
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
  }

  const formatPicTime = (picTime: string): string => {
    if (!picTime) return '-'
    if (picTime.length >= 19) return picTime.substring(11, 19)
    return picTime
  }

  const formatFee = (fee: number) => {
    if (fee === null || fee === undefined) return '-'
    return (fee / 100).toFixed(2) + '元'
  }

  const formatMatchRate = (rate: number): string => {
    if (rate === null || rate === undefined) return '-'
    if (rate > 1) return rate.toFixed(1) + '%'
    return (rate * 100).toFixed(1) + '%'
  }

  const getRateType = (rate: number): string => {
    if (rate === null || rate === undefined) return 'info'
    const actualRate = rate > 1 ? rate : rate * 100
    if (actualRate >= 80) return 'success'
    if (actualRate >= 50) return 'warning'
    return 'info'
  }

  const getOrderStatusType = (status: number): string => {
    if (status === null || status === undefined) return 'info'
    switch (status) {
      case 1: case 2: return 'warning'
      case 3: case 4: return 'primary'
      case 5: case 6: return 'info'
      case 7: case 8: return 'success'
      default: return 'info'
    }
  }

  const executeAIAuditBatchQuery = async (params: {
    plateNumber: string
    entryTime: string
    gateTime: string
    passId?: string
    hours?: number
    rows?: number
  }) => {
    if (!isLoggedIn()) {
      ElMessage.warning('请先登录云门户')
      return
    }

    aiAuditLoading.value = true
    aiAuditResult.value = null

    try {
      const response = await aiAuditBatchQuery({
        plate_number: params.plateNumber,
        entry_time: params.entryTime,
        gate_time: params.gateTime,
        pass_id: params.passId || undefined,
        hours: params.hours,
        rows: params.rows
      })

      if (response && response.code === 200) {
        aiAuditResult.value = response.data as any
        if ((response.data as any)?.time_range) {
          vehicleImagesTotal.value = (response.data as any).vehicle_images?.total || 0
        }
        if ((response.data as any)?.errors && (response.data as any).errors.length > 0) {
          ElMessage.warning(`部分查询失败: ${(response.data as any).errors.join('; ')}`)
        } else {
          ElMessage.success('AI稽核查询完成')
        }
      } else {
        ElMessage.error(response?.message || 'AI稽核查询失败')
      }
    } catch (error: any) {
      ElMessage.error(error?.message || 'AI稽核查询失败')
    } finally {
      aiAuditLoading.value = false
    }
  }

  const fetchOriginalImageWithRetry = async (
    picturePath: string,
    maxRetries: number = 2
  ): Promise<string | null> => {
    if (!isLoggedIn()) return null

    let lastError: string = ''
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const response = await aiAuditOriginalImage({
          picture_path: picturePath
        })

        if (response && response.code === 200 && response.data?.image) {
          return response.data.image
        } else {
          lastError = response?.message || '获取原图失败'
        }
      } catch (error: any) {
        lastError = error?.message || '网络错误'
      }

      if (attempt < maxRetries) {
        await new Promise((resolve) => setTimeout(resolve, 500))
      }
    }

    console.error(`获取原图失败(重试${maxRetries}次):`, lastError)
    return null
  }

  const selectImageForCheck = async (image: AIAuditVehicleImage, target: 'image1' | 'image2') => {
    if (!image.picturePath) {
      if (target === 'image1') {
        aiAuditSelectedImage1.value = image.bigPositivePic
      } else {
        aiAuditSelectedImage2.value = image.bigPositivePic
      }
      ElMessage.success(`已选择压缩图片作为查核资料${target === 'image1' ? '1' : '2'}`)
      return
    }

    const loadingKey = `${target}-${image.picturePath}`
    if (originalImageLoading.value === loadingKey) return

    originalImageLoading.value = loadingKey
    try {
      const cachedImage = originalImageCache.get(image.picturePath)
      let originalImage: string

      if (cachedImage) {
        originalImage = cachedImage
      } else {
        if (!isLoggedIn()) {
          ElMessage.warning('请先登录云门户')
          return
        }

        originalImage = (await fetchOriginalImageWithRetry(image.picturePath, 2)) || ''

        if (!originalImage) {
          ElMessage.warning('获取原图失败，使用压缩图片')
          if (target === 'image1') {
            aiAuditSelectedImage1.value = image.bigPositivePic
          } else {
            aiAuditSelectedImage2.value = image.bigPositivePic
          }
          return
        }

        setOriginalImageCache(image.picturePath, originalImage)
      }

      if (target === 'image1') {
        aiAuditSelectedImage1.value = originalImage
      } else {
        aiAuditSelectedImage2.value = originalImage
      }
      ElMessage.success(`已选择高清原图作为查核资料${target === 'image1' ? '1' : '2'}`)
    } catch (error: any) {
      ElMessage.warning('获取原图失败，使用压缩图片')
      if (target === 'image1') {
        aiAuditSelectedImage1.value = image.bigPositivePic
      } else {
        aiAuditSelectedImage2.value = image.bigPositivePic
      }
    } finally {
      originalImageLoading.value = ''
    }
  }

  const getPreviewImages = async (image: AIAuditVehicleImage): Promise<string[]> => {
    if (!image.picturePath) return [getImageSrc(image.bigPositivePic)]

    const cachedImage = originalImageCache.get(image.picturePath)
    if (cachedImage) return [getImageSrc(cachedImage)]

    const originalImage = await fetchOriginalImageWithRetry(image.picturePath, 2)
    if (originalImage) {
      setOriginalImageCache(image.picturePath, originalImage)
      return [getImageSrc(originalImage)]
    }

    return [getImageSrc(image.bigPositivePic)]
  }

  const handleImagePreview = async (image: AIAuditVehicleImage) => {
    previewImageList.value = [getImageSrc(image.bigPositivePic)]
    if (!image.picturePath) return

    const cachedImage = originalImageCache.get(image.picturePath)
    if (cachedImage) {
      previewImageList.value = [getImageSrc(cachedImage)]
      return
    }

    previewLoading.value = image.picturePath
    previewLoadingText.value = '正在加载高清原图...'

    try {
      const images = await getPreviewImages(image)
      previewImageList.value = images
    } catch (error: any) {
      console.error('预览原图失败:', error)
    } finally {
      previewLoading.value = ''
      previewLoadingText.value = ''
    }
  }

  const loadVehicleImagesPage = async (plateNumber: string) => {
    if (!isLoggedIn() || !plateNumber || !aiAuditResult.value?.time_range) return

    vehicleImagesLoading.value = true
    try {
      const response = await aiAuditVehicleImages({
        plate_number: plateNumber.split('_')[0],
        start_time: aiAuditResult.value.time_range.start_time,
        end_time: aiAuditResult.value.time_range.end_time,
        page: vehicleImagesPage.value,
        page_size: vehicleImagesPageSize.value,
        sort: vehicleImagesSort.value
      })

      if (response && response.code === 200 && response.data?.success) {
        if (aiAuditResult.value) {
          aiAuditResult.value.vehicle_images = response.data
          vehicleImagesTotal.value = response.data.total || 0
        }
      } else {
        ElMessage.error(response?.message || '加载车辆图库失败')
      }
    } catch (error: any) {
      ElMessage.error(error?.message || '加载车辆图库失败')
    } finally {
      vehicleImagesLoading.value = false
    }
  }

  const queryGantryImagesForRow = async (row: AIAuditGantryTrade) => {
    if (!isLoggedIn()) {
      ElMessage.warning('请先登录云门户')
      return
    }
    if (!row.gantryId) {
      ElMessage.warning('该记录缺少门架编号')
      return
    }

    const transDate = new Date(row.transTime)
    const startDate = new Date(transDate.getTime() - 5000)
    const endDate = new Date(transDate.getTime() + 5000)
    const startTime = formatDateTimeForQuery(startDate)
    const endTime = formatDateTimeForQuery(endDate)

    gantryImageLoading.value = row.gantryId

    try {
      const response = await aiAuditGantryImages({
      station_id: row.gantryId,
        start_time: startTime,
        end_time: endTime,
        rows: 50
      })

      if (response && response.code === 200 && response.data?.success) {
        const images = response.data.images || []
        gantryImagesResult.value = {
          gantryName: row.gantryName,
          gantryId: row.gantryId,
          transTime: row.transTime,
          timeRange: { startTime, endTime },
          images,
          total: response.data.total || 0
        }
        gantryImagesPreviewList.value = images.map((img: AIAuditGantryImage) =>
          getImageSrc(img.bigPositivePic)
        )
        gantryImagesDialogVisible.value = true
      } else {
        ElMessage.error(response?.message || '查询门架图库失败')
      }
    } catch (error: any) {
      ElMessage.error(error?.message || '查询门架图库失败')
    } finally {
      gantryImageLoading.value = ''
    }
  }

  const selectGantryImageAsCheck = async (img: AIAuditGantryImage, target: 'image1' | 'image2') => {
    if (img.picturePath) {
      const originalImage = await fetchOriginalImageWithRetry(img.picturePath, 2)
      if (originalImage) {
        if (target === 'image1') aiAuditSelectedImage1.value = originalImage
        else aiAuditSelectedImage2.value = originalImage
        ElMessage.success(`已选择高清原图作为查核资料${target === 'image1' ? '1' : '2'}`)
      } else {
        if (target === 'image1') aiAuditSelectedImage1.value = img.bigPositivePic
        else aiAuditSelectedImage2.value = img.bigPositivePic
        ElMessage.success(`已选择压缩图片作为查核资料${target === 'image1' ? '1' : '2'}`)
      }
    } else {
      if (target === 'image1') aiAuditSelectedImage1.value = img.bigPositivePic
      else aiAuditSelectedImage2.value = img.bigPositivePic
      ElMessage.success(`已选择图片作为查核资料${target === 'image1' ? '1' : '2'}`)
    }
    gantryImagesDialogVisible.value = false
  }

  const queryVehicleDetail = async (plateNumber: string, picTime: string) => {
    if (!isLoggedIn()) {
      ElMessage.warning('请先登录云门户')
      return
    }

    vehicleDetailPlate.value = plateNumber
    vehicleDetailLoading.value = true
    vehicleDetailDialogVisible.value = true
    vehicleDetailActiveTab.value = 'gantry_trade'

    const picDate = new Date(picTime)
    const startDate = new Date(picDate.getTime() - 24 * 60 * 60 * 1000)
    const endDate = new Date(picDate.getTime() + 24 * 60 * 60 * 1000)

    try {
      const response = await aiAuditBatchQuery({
      plate_number: plateNumber,
        entry_time: formatDateTimeForQuery(startDate),
        gate_time: formatDateTimeForQuery(endDate),
        hours: 48,
        rows: 100
      })

      if (response && response.code === 200) {
        vehicleDetailResult.value = response.data
      } else {
        ElMessage.error(response?.message || '查询车辆信息失败')
      }
    } catch (error: any) {
      ElMessage.error(error?.message || '查询车辆信息失败')
    } finally {
      vehicleDetailLoading.value = false
    }
  }

  const captureTable = async (tableEl: HTMLElement, tableLabel: string, targetImage: 'image1' | 'image2') => {
    if (!tableEl) {
      ElMessage.warning('无法获取表格元素')
      return
    }

    const startTime = performance.now()
    ElMessage.info(`正在截取${tableLabel}表格...`)
    
    await nextTick()

    try {
      const cacheKey = `${tableLabel}-${targetImage}`
      
      const cachedDataUrl = getCachedScreenshot(cacheKey)
      if (cachedDataUrl) {
        const cacheHitTime = performance.now() - startTime
        
        if (targetImage === 'image1') {
          aiAuditSelectedImage1.value = cachedDataUrl
        } else {
          aiAuditSelectedImage2.value = cachedDataUrl
        }
        
        console.log(`[Screenshot] ${tableLabel} 缓存命中 (${cacheHitTime.toFixed(0)}ms)`)
        ElMessage.success(`${tableLabel}表格已截图到查核资料${targetImage === 'image1' ? '1' : '2'} (缓存)`)
        return
      }
      
      const tableHash = await computeTableHash(tableEl)
      const fullCacheKey = `${cacheKey}-${tableHash}`
      
      const hashCachedDataUrl = getCachedScreenshot(fullCacheKey)
      if (hashCachedDataUrl) {
        const cacheHitTime = performance.now() - startTime
        
        if (targetImage === 'image1') {
          aiAuditSelectedImage1.value = hashCachedDataUrl
        } else {
          aiAuditSelectedImage2.value = hashCachedDataUrl
        }
        
        setCachedScreenshot(cacheKey, hashCachedDataUrl)
        
        console.log(`[Screenshot] ${tableLabel} Hash缓存命中 (${cacheHitTime.toFixed(0)}ms)`)
        ElMessage.success(`${tableLabel}表格已截图到查核资料${targetImage === 'image1' ? '1' : '2'} (缓存)`)
        return
      }

      console.log(`[Screenshot] 开始截取 ${tableLabel}...`)

      const dataUrl = await domToPng(tableEl, {
        scale: 1.2,
        quality: 0.9,
        backgroundColor: '#ffffff',
        width: tableEl.scrollWidth,
        height: tableEl.scrollHeight,
        style: {
          overflow: 'visible !important'
        },
        filter: (node) => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            const el = node as Element
            if (el.classList?.contains('is-loading')) return false
            if (el.tagName === 'BUTTON') return false
            if (el.classList?.contains('el-loading-mask')) return false
          }
          return true
        },
        /** 
         * 内置性能优化:
         * - 自动并行加载图片
         * - 使用 requestAnimationFrame 优化渲染
         * - 智能跳过不可见元素
         */
      })

      const endTime = performance.now()
      const duration = endTime - startTime
      
      console.log(
        `[Screenshot] ${tableLabel} 截图完成 (${duration.toFixed(0)}ms)` +
        `\n  - 元素尺寸: ${tableEl.scrollWidth}x${tableEl.scrollHeight}` +
        `\n  - 数据大小: ${(dataUrl.length / 1024).toFixed(1)}KB`
      )

      if (targetImage === 'image1') {
        aiAuditSelectedImage1.value = dataUrl
      } else {
        aiAuditSelectedImage2.value = dataUrl
      }
      
      setCachedScreenshot(cacheKey, dataUrl)
      setCachedScreenshot(fullCacheKey, dataUrl)
      
      ElMessage.success(`${tableLabel}表格已截图到查核资料${targetImage === 'image1' ? '1' : '2'} (${duration.toFixed(0)}ms)`)
    } catch (error: any) {
      const errorTime = performance.now() - startTime
      console.error(`[Screenshot] ${tableLabel} 截图失败 (${errorTime.toFixed(0)}ms):`, error)
      ElMessage.error(`截图失败: ${error.message || '未知错误'}`)
    }
  }

  const saveImagesToDatabase = async (params: {
    tableName: string
    recordId: string
  }) => {
    const hasData =
      aiAuditSelectedImage1.value ||
      aiAuditSelectedImage2.value ||
      aiAuditReviewStatus.value ||
      aiAuditCheckPassId.value ||
      aiAuditSpecialSituation.value ||
      aiAuditCheckSplit.value ||
      aiAuditRemark.value

    if (!hasData) {
      ElMessage.warning('请先填写信息或选择图片')
      return
    }

    if (!params.tableName || !params.recordId) {
      ElMessage.warning('缺少表名或记录ID')
      return
    }

    aiAuditSavingImages.value = true
    try {
      const image1Base64 = aiAuditSelectedImage1.value
      const image2Base64 = aiAuditSelectedImage2.value

      const base64ToSave1 = image1Base64.startsWith('data:image') ? image1Base64.split(',')[1] : image1Base64
      const base64ToSave2 = image2Base64.startsWith('data:image') ? image2Base64.split(',')[1] : image2Base64

      const response = await aiAuditSaveImages({
        table_name: params.tableName,
        record_id: params.recordId,
        image1_base64: base64ToSave1 || undefined,
        image2_base64: base64ToSave2 || undefined,
        review_status: aiAuditReviewStatus.value || undefined,
        check_pass_id: aiAuditCheckPassId.value || undefined,
        special_situation: aiAuditSpecialSituation.value || undefined,
        check_split: aiAuditCheckSplit.value || undefined,
        remark: aiAuditRemark.value || undefined,
        clear_empty: true
      })

      if (response && response.code === 200) {
        ElMessage.success(`成功保存 ${(response.data as any)?.affected_rows || 0} 条记录`)
        return true
      } else {
        ElMessage.error(response?.message || '保存图片失败')
        return false
      }
    } catch (error: any) {
      ElMessage.error(error?.message || '保存图片失败')
      return false
    } finally {
      aiAuditSavingImages.value = false
    }
  }

  return {
    aiAuditLoading,
    aiAuditResult,
    aiAuditReviewStatus,
    aiAuditCheckPassId,
    aiAuditSpecialSituation,
    aiAuditCheckSplit,
    aiAuditRemark,
    aiAuditSelectedImage1,
    aiAuditSelectedImage2,
    aiAuditSavingImages,
    originalImageLoading,
    previewLoading,
    previewLoadingText,
    previewImageList,
    vehicleImagesPage,
    vehicleImagesPageSize,
    vehicleImagesTotal,
    vehicleImagesLoading,
    vehicleImagesSort,
    maxPage,
    gantryImagesResult,
    gantryImagesPreviewList,
    gantryImagesDialogVisible,
    gantryImageLoading,
    vehicleDetailResult,
    vehicleDetailLoading,
    vehicleDetailDialogVisible,
    vehicleDetailActiveTab,
    vehicleDetailPlate,
    getImageSrc,
    formatDateTimeForQuery,
    formatPicTime,
    formatFee,
    formatMatchRate,
    getRateType,
    getOrderStatusType,
    executeAIAuditBatchQuery,
    fetchOriginalImageWithRetry,
    selectImageForCheck,
    getPreviewImages,
    handleImagePreview,
    loadVehicleImagesPage,
    queryGantryImagesForRow,
    selectGantryImageAsCheck,
    queryVehicleDetail,
    captureTable,
    saveImagesToDatabase,
    clearOriginalImageCache,
    clearScreenshotCache
  }
}
