import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { aiAuditOrderDetail } from '@/api/split-match'

interface OrderDetailData {
  labelVo: any
  enData: any
  exData: any
  [key: string]: any
}

export const useOrderDetail = (isLoggedIn: () => boolean) => {
  const showOrderDetailDialog = ref(false)
  const orderDetailLoading = ref(false)
  const currentOrderDetail = ref<OrderDetailData | null>(null)
  const orderDetailActiveTab = ref('basic')
  const selectedPicture = ref<any>(null)

  const copyRawJsonData = async () => {
    try {
      const jsonString = JSON.stringify(currentOrderDetail.value, null, 2)
      await navigator.clipboard.writeText(jsonString)
      ElMessage.success('JSON数据已复制到剪贴板')
    } catch (error) {
      const textArea = document.createElement('textarea')
      textArea.value = JSON.stringify(currentOrderDetail.value, null, 2)
      textArea.style.position = 'fixed'
      textArea.style.left = '-9999px'
      document.body.appendChild(textArea)
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
      ElMessage.success('JSON数据已复制到剪贴板')
    }
  }

  const handleViewOrderDetail = async (orderId: string) => {
    if (!orderId) {
      ElMessage.warning('工单编号不能为空')
      return
    }

    showOrderDetailDialog.value = true
    orderDetailLoading.value = true
    currentOrderDetail.value = null
    selectedPicture.value = null

    try {
      const response = await aiAuditOrderDetail({
        order_id: orderId
      })

      if (response && response.code === 200) {
        currentOrderDetail.value = response.data as OrderDetailData
        if (currentOrderDetail.value?.picBeanVo?.picBeanList?.length > 0) {
          selectedPicture.value = currentOrderDetail.value.picBeanVo.picBeanList[0]
        }
        ElMessage.success('获取工单详情成功')
      } else {
        ElMessage.error(response?.message || '获取工单详情失败')
      }
    } catch (error: any) {
      let errorMessage = '获取工单详情失败'

      if (error?.code === 'ERR_NETWORK' || error?.code === 'ECONNREFUSED') {
        errorMessage = '无法连接到后端服务，请检查网络连接'
      } else if (error?.code === 'ETIMEDOUT' || error?.code === 'ECONNABORTED') {
        errorMessage = '请求超时，请稍后重试'
      } else if (error?.response) {
        errorMessage = `服务器错误 (${error.response.status}): ${error.response.data?.message || '未知错误'}`
      } else if (error?.message) {
        errorMessage += `: ${error.message}`
      }

      ElMessage.error(errorMessage)
    } finally {
      orderDetailLoading.value = false
    }
  }

  return {
    showOrderDetailDialog,
    orderDetailLoading,
    currentOrderDetail,
    orderDetailActiveTab,
    selectedPicture,
    copyRawJsonData,
    handleViewOrderDetail
  }
}
