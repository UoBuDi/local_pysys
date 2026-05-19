import { ref } from 'vue'
import { ElMessage } from 'element-plus'

export const useImageHandler = () => {
  const imagePreviewList = ref<Record<string, string[]>>({})
  const imageBinaryData = ref<Record<string, Blob>>({})
  const activeImageField = ref<string>('查核资料1')
  const tableImagePreviewVisible = ref(false)
  const tableImagePreviewList = ref<string[]>([])

  const convertToWebP = (source: File | string): Promise<Blob> => {
    return new Promise((resolve, reject) => {
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      const img = new Image()

      img.onload = () => {
        canvas.width = img.width
        canvas.height = img.height
        ctx?.drawImage(img, 0, 0)
        canvas.toBlob(
          (blob) => {
            if (blob) {
              resolve(blob)
            } else {
              reject(new Error('无法转换图片为WebP格式'))
            }
          },
          'image/webp',
          0.8
        )
      }

      img.onerror = () => {
        reject(new Error('图片加载失败'))
      }

      img.src = source instanceof File ? URL.createObjectURL(source) : source
    })
  }

  const handleImageUpload = async (file: any, field: string) => {
    if (!file.raw) return

    try {
      const webpBlob = await convertToWebP(file.raw)

      const arrayBuffer = await webpBlob.arrayBuffer()
      const base64String = btoa(
        new Uint8Array(arrayBuffer).reduce((data, byte) => data + String.fromCharCode(byte), '')
      )

      const dataUrl = 'data:image/webp;base64,' + base64String

      imageBinaryData.value[field] = webpBlob

      if (!imagePreviewList.value[field]) {
        imagePreviewList.value[field] = []
      }
      imagePreviewList.value[field] = [dataUrl]

      return dataUrl
    } catch (error) {
      console.error('图片转换失败:', error)
      ElMessage.error('图片转换失败')
      return null
    }
  }

  const handlePaste = (event: ClipboardEvent) => {
    const items = event.clipboardData?.items
    if (!items) return

    for (let i = 0; i < items.length; i++) {
      if (items[i].type.indexOf('image') !== -1) {
        const file = items[i].getAsFile()
        if (file) {
          handleImageUpload({ raw: file }, activeImageField.value)
        }
        break
      }
    }
  }

  const handleRemoveImage = (field: string) => {
    imagePreviewList.value[field] = []
    delete imageBinaryData.value[field]
  }

  const showTableImagePreview = (imageUrl: string) => {
    tableImagePreviewList.value = [imageUrl]
    tableImagePreviewVisible.value = true
  }

  const resetImageData = () => {
    imageBinaryData.value = {}
  }

  return {
    imagePreviewList,
    imageBinaryData,
    activeImageField,
    tableImagePreviewVisible,
    tableImagePreviewList,
    convertToWebP,
    handleImageUpload,
    handlePaste,
    handleRemoveImage,
    showTableImagePreview,
    resetImageData
  }
}
