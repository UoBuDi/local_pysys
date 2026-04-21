export type ExcelImageExtension = 'png' | 'jpeg' | 'gif'

export interface ImageProcessResult {
  success: boolean
  data?: string
  extension?: ExcelImageExtension
  error?: string
  isWPS?: boolean
  wpsId?: string
}

export const processImageForExcel = (imageData: unknown): ImageProcessResult => {
  if (!imageData || typeof imageData !== 'string') {
    return { success: false, error: '无效的图片数据' }
  }

  const data = imageData.trim()

  if (data.startsWith('=DISPIMG(')) {
    const matches = data.match(/^=DISPIMG\("([^"]+)"\s*,\s*\d+\)$/)
    if (matches && matches[1]) {
      return {
        success: true,
        isWPS: true,
        wpsId: matches[1],
        data: '',
        extension: 'png'
      }
    }
    return {
      success: true,
      isWPS: true,
      wpsId: 'unknown',
      data: '',
      extension: 'png'
    }
  }

  if (data.startsWith('data:image/')) {
    const matches = data.match(/^data:image\/(\w+);base64,(.+)$/)
    if (matches && matches.length === 3) {
      let extension = matches[1].toLowerCase()
      if (extension === 'jpg') {
        extension = 'jpeg'
      }
      if (extension === 'bmp') {
        return {
          success: true,
          data: matches[2],
          extension: 'png',
          error: 'BMP格式需要转换'
        }
      }
      if (extension === 'png' || extension === 'jpeg' || extension === 'gif') {
        return {
          success: true,
          data: matches[2],
          extension: extension as ExcelImageExtension
        }
      }
      return {
        success: true,
        data: matches[2],
        extension: 'png'
      }
    }
  }

  if (/^[A-Za-z0-9+/=]+$/.test(data) && data.length > 100) {
    return {
      success: true,
      data: data,
      extension: 'png'
    }
  }

  return { success: false, error: '无法识别的图片格式' }
}

export const createPlaceholderImage = (
  text: string,
  width: number = 200,
  height: number = 100
): string => {
  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const ctx = canvas.getContext('2d')

  if (!ctx) {
    return ''
  }

  ctx.fillStyle = '#f5f5f5'
  ctx.fillRect(0, 0, width, height)

  ctx.strokeStyle = '#d9d9d9'
  ctx.lineWidth = 2
  ctx.strokeRect(0, 0, width, height)

  ctx.fillStyle = '#8c8c8c'
  ctx.font = '14px Arial'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(text, width / 2, height / 2)

  const dataUrl = canvas.toDataURL('image/png')
  const matches = dataUrl.match(/^data:image\/png;base64,(.+)$/)
  return matches ? matches[1] : ''
}

export const extractWPSImagesFromXlsx = async (file: File): Promise<Map<string, string>> => {
  const imageMap = new Map<string, string>()

  try {
    const JSZip = (await import('jszip')).default
    const zip = new JSZip()
    const zipContent = await zip.loadAsync(file)

    const mediaFiles: string[] = []
    zipContent.forEach((relativePath) => {
      if (relativePath.startsWith('xl/media/')) {
        mediaFiles.push(relativePath)
      }
    })

    const drawingRelsPath = 'xl/drawings/_rels/drawing1.xml.rels'
    if (zipContent.files[drawingRelsPath]) {
      const relsContent = await zipContent.files[drawingRelsPath].async('text')
      const parser = new DOMParser()
      const relsDoc = parser.parseFromString(relsContent, 'text/xml')
      const relationships = relsDoc.getElementsByTagName('Relationship')

      for (let i = 0; i < relationships.length; i++) {
        const rel = relationships[i]
        const target = rel.getAttribute('Target')
        const id = rel.getAttribute('Id')
        if (target && id) {
          const mediaPath = target.replace('../', 'xl/')
          if (zipContent.files[mediaPath]) {
            const mediaData = await zipContent.files[mediaPath].async('base64')
            imageMap.set(id, mediaData)
          }
        }
      }
    }

    const drawingsPath = 'xl/drawings/drawing1.xml'
    if (zipContent.files[drawingsPath]) {
      const drawingsContent = await zipContent.files[drawingsPath].async('text')
      const parser = new DOMParser()
      const drawingsDoc = parser.parseFromString(drawingsContent, 'text/xml')
      const pics = drawingsDoc.getElementsByTagName('xdr:pic')

      for (let i = 0; i < pics.length; i++) {
        const pic = pics[i]
        const nvPicPr = pic.getElementsByTagName('xdr:nvPicPr')[0]
        if (nvPicPr) {
          const cNvPr = nvPicPr.getElementsByTagName('xdr:cNvPr')[0]
          if (cNvPr) {
            const name = cNvPr.getAttribute('name')
            const blipFill = pic.getElementsByTagName('xdr:blipFill')[0]
            if (blipFill) {
              const blip = blipFill.getElementsByTagName('a:blip')[0]
              if (blip) {
                const embedId = blip.getAttribute('xmlns:r')
                  ? blip.getAttribute('r:embed')
                  : blip.getAttribute('embed')
                if (embedId && name) {
                  const imageData = imageMap.get(embedId)
                  if (imageData) {
                    imageMap.set(name, imageData)
                  }
                }
              }
            }
          }
        }
      }
    }
  } catch (error) {
    console.error('提取WPS图片失败:', error)
  }

  return imageMap
}

export const isImageData = (data: any): boolean => {
  if (typeof data !== 'string') {
    return false
  }
  if (data.startsWith('=DISPIMG(')) {
    return true
  }
  return data.startsWith('data:image/') || (/^[A-Za-z0-9+/=]+$/.test(data) && data.length > 100)
}
