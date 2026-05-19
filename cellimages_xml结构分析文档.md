# cellimages.xml 文件结构分析文档

## 一、文件概述

分析目录：`G:\日常工作\数据分析\异常数据\42.2025年06月通行数据处理（完整）`

涉及文件：
1. `xl\cellimages.xml` - 图片定义文件
2. `xl\_rels\cellimages.xml.rels` - 图片关系映射文件
3. `xl\worksheets\sheet1.xml` - 工作表数据文件

---

## 二、cellimages.xml 文件结构分析

### 2.1 根节点结构
```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<etc:cellImages 
    xmlns:xdr="http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing" 
    xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" 
    xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" 
    xmlns:etc="http://www.wps.cn/officeDocument/2017/etCustomData">
```

**命名空间说明：**
- `etc:` - WPS自定义命名空间（关键！）
- `xdr:` - 绘图ML命名空间
- `r:` - 关系命名空间
- `a:` - 绘图ML主命名空间

### 2.2 cellImage节点结构
```xml
<etc:cellImage>
    <xdr:pic>
        <xdr:nvPicPr>
            <xdr:cNvPr id="3" name="ID_2BE52F9E1B5746B6AB9B1D6BB67F68C5"/>
            <xdr:cNvPicPr>
                <a:picLocks noChangeAspect="1"/>
            </xdr:cNvPicPr>
        </xdr:nvPicPr>
        <xdr:blipFill>
            <a:blip r:embed="rId1"/>
            <a:stretch>
                <a:fillRect/>
            </a:stretch>
        </xdr:blipFill>
        <xdr:spPr>
            <a:xfrm>
                <a:off x="6202045" y="190500"/>
                <a:ext cx="23412450" cy="11144250"/>
            </a:xfrm>
            <a:prstGeom prst="rect">
                <a:avLst/>
            </a:prstGeom>
            <a:noFill/>
            <a:ln w="9525">
                <a:noFill/>
            </a:ln>
        </xdr:spPr>
    </xdr:pic>
</etc:cellImage>
```

### 2.3 关键节点属性说明

#### xdr:cNvPr 节点（连接非可视属性）
- **id属性**：图片唯一标识符
  - 示例值：`"3"`, `"4"`, `"2"`, `"5"`
  - 用途：唯一标识图片
  - **注意**：这是图片ID，不是关系ID！

- **name属性**：图片名称
  - 示例值：`"ID_2BE52F9E1B5746B6AB9B1D6BB67F68C5"`
  - 用途：图片的显示名称
  - 格式：`ID_` + 16进制字符串

#### a:blip 节点（位图）
- **r:embed属性**：关系ID（关键！）
  - 示例值：`"rId1"`, `"rId2"`, `"rId3"`, `"rId4"`
  - 用途：引用cellimages.xml.rels中的关系
  - **注意**：这才是与rels文件关联的关键！

#### a:xfrm 节点（变换信息）
- **a:off节点**：偏移坐标
  - x属性：X偏移（EMU单位）
  - y属性：Y偏移（EMU单位）
  
- **a:ext节点**：扩展尺寸
  - cx属性：宽度（EMU单位）
  - cy属性：高度（EMU单位）

### 2.4 重要发现

**问题1：缺少ref属性**
- 标准cellimages格式应该有`ref`属性（单元格引用）
- 当前文件中**没有**`ref`属性
- 这导致无法直接关联到工作表中的单元格

**问题2：命名空间差异**
- 使用WPS自定义命名空间`etc:`
- 与标准Excel格式不同
- 需要特殊处理

**问题3：节点名称差异**
- 使用`xdr:cNvPr`而不是`xdr:cNvPicPr`
- 需要调整解析逻辑

---

## 三、cellimages.xml.rels 文件结构分析

### 3.1 根节点结构
```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
```

### 3.2 Relationship节点结构
```xml
<Relationship 
    Id="rId99" 
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" 
    Target="media/image99.png"/>
```

### 3.3 关键属性说明

- **Id属性**：关系ID
  - 示例：`"rId1"`, `"rId2"`, ..., `"rId99"`
  - 用途：唯一标识关系
  - 格式：`rId` + 数字

- **Type属性**：关系类型
  - 值：`http://schemas.openxmlformats.org/officeDocument/2006/relationships/image`
  - 用途：标识这是图片关系

- **Target属性**：图片文件路径
  - 示例：`"media/image99.png"`
  - 用途：指向xl/media/目录下的图片文件
  - 格式：`media/image` + 数字 + `.png`

### 3.4 关联关系

**cellimages.xml → cellimages.xml.rels 关联：**
```
cellimages.xml中的a:blip r:embed="rId1" 
    ↓ 关联
cellimages.xml.rels中的Relationship Id="rId1" 
    ↓ 关联
media/image1.png（实际图片文件）
```

---

## 四、sheet1.xml 文件结构分析

### 4.1 根节点结构
```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet 
    xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" 
    xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" 
    xmlns:xdr="http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing" 
    xmlns:x14="http://schemas.microsoft.com/office/spreadsheetml/2009/9/main" 
    xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" 
    xmlns:etc="http://www.wps.cn/officeDocument/2017/etCustomData">
```

### 4.2 关键节点

- **dimension节点**：工作表尺寸
  - ref属性：`"A1:T525"`
  - 含义：从A1到T525单元格

- **sheetViews节点**：工作表视图
  - 包含冻结窗格、选择等信息

- **cols节点**：列定义
  - 定义每列的宽度

- **sheetData节点**：工作表数据
  - 包含所有单元格数据

### 4.3 单元格数据结构
```xml
<row r="1" spans="1:20">
    <c r="A1" t="s">
        <v>0</v>
    </c>
    <c r="B1" t="s">
        <v>1</v>
    </c>
    ...
</row>
```

- **row节点**：行
  - r属性：行号（从1开始）
- **c节点**：单元格
  - r属性：单元格引用（如"A1"）
  - t属性：类型（"s"=字符串）

### 4.4 重要发现：DISPIMG函数关联

**关键发现：图片通过DISPIMG函数关联到单元格**

```xml
<!-- cellimages.xml中的图片名称 -->
<xdr:cNvPr name="ID_C11C9072428C4CC6A2968AD1CC39E0DC"/>

<!-- sheet1.xml中的单元格数据 -->
<c r="H3" t="str">
    <f>_xlfn.DISPIMG(&quot;ID_C11C9072428C4CC6A2968AD1CC39E0DC&quot;,1)</f>
    <v>=DISPIMG(&quot;ID_C11C9072428C4CC6A2968AD1CC39E0DC&quot;,1)</v>
</c>
```

**关联机制：**
1. cellimages.xml中的`xdr:cNvPr.name`属性包含图片名称
2. sheet1.xml中的单元格包含`DISPIMG`函数调用
3. DISPIMG函数的第一个参数与图片名称匹配
4. 单元格的`r`属性（如"H3"）是单元格坐标

**DISPIMG函数格式：**
```
_xlfn.DISPIMG("图片名称",索引号)
=DISPIMG("图片名称",索引号)
```

- 第一个参数：图片名称（与cellimages.xml中的name属性匹配）
- 第二个参数：索引号（通常为1）
- `_xlfn.`前缀：表示这是Excel函数

**关联示例：**
```
cellimages.xml: name="ID_C11C9072428C4CC6A2968AD1CC39E0DC"
    ↓ 匹配
sheet1.xml: DISPIMG("ID_C11C9072428C4CC6A2968AD1CC39E0DC",1)
    ↓ 所在单元格
sheet1.xml: <c r="H3" t="str">
```

### 4.5 图片定位策略

**策略1：解析DISPIMG函数**
```javascript
// 从单元格值中提取DISPIMG函数参数
const extractImageNameFromCell = (cellValue) => {
  if (!cellValue || typeof cellValue !== 'string') {
    return null
  }
  
  // 匹配DISPIMG函数
  const dispimgMatch = cellValue.match(/DISPIMG\s*\(\s*"([^"]+)"\s*,\s*\d+\s*\)/i)
  
  if (dispimgMatch && dispimgMatch[1]) {
    return dispimgMatch[1]  // 返回图片名称
  }
  
  return null
}

// 示例
const cellValue = '=DISPIMG("ID_C11C9072428C4CC6A2968AD1CC39E0DC",1)'
const imageName = extractImageNameFromCell(cellValue)
// 结果: "ID_C11C9072428C4CC6A2968AD1CC39E0DC"
```

**策略2：建立图片名称到单元格的映射**
```javascript
// 遍历工作表数据，建立图片名称到单元格的映射
const buildImageCellMap = (processedData) => {
  const imageCellMap = {}  // { 图片名称: 单元格引用 }
  
  for (const row of processedData) {
    for (const [columnName, cellValue] of Object.entries(row)) {
      // 跳过非字符串类型的单元格
      if (typeof cellValue !== 'string') {
        continue
      }
      
      // 提取图片名称
      const imageName = extractImageNameFromCell(cellValue)
      
      if (imageName) {
        // 获取单元格引用（如"H3"）
        // 注意：需要从原始XML中获取单元格坐标
        // 这里假设columnName就是单元格引用
        imageCellMap[imageName] = columnName
        console.log(`图片 "${imageName}" 关联到单元格 ${columnName}`)
      }
    }
  }
  
  return imageCellMap
}
```

**策略3：关联图片到数据行**
```javascript
const associateImagesByDispimg = (processedData, cellImageMap, mediaFiles) => {
  // 步骤1：建立图片名称到单元格的映射
  const imageCellMap = buildImageCellMap(processedData)
  
  // 步骤2：遍历cellimages.xml中的图片
  for (const [relationshipId, imageInfo] of Object.entries(cellImageMap)) {
    const imageName = imageInfo.imageName  // 从xdr:cNvPr.name获取
    
    // 步骤3：查找对应的单元格
    const cellRef = imageCellMap[imageName]
    
    if (!cellRef) {
      console.warn(`图片 "${imageName}" 未找到对应的单元格`)
      continue
    }
    
    // 步骤4：解析单元格引用，获取行号
    const rowNumber = parseCellRef(cellRef).row
    
    if (!rowNumber) {
      console.warn(`无法解析单元格引用: ${cellRef}`)
      continue
    }
    
    // 步骤5：关联图片到数据行
    const dataRowIndex = rowNumber - 2  // Excel行号转数据索引（跳过表头）
    
    if (dataRowIndex >= 0 && dataRowIndex < processedData.length) {
      const targetRow = processedData[dataRowIndex]
      
      // 分配图片到查核资料字段
      if (!targetRow['查核资料1']) {
        targetRow['查核资料1'] = mediaFiles[imageInfo.filePath]
        console.log(`✓ 图片 "${imageName}" 关联到行 ${dataRowIndex} 的查核资料1`)
      } else if (!targetRow['查核资料2']) {
        targetRow['查核资料2'] = mediaFiles[imageInfo.filePath]
        console.log(`✓ 图片 "${imageName}" 关联到行 ${dataRowIndex} 的查核资料2`)
      }
    }
  }
}

// 解析单元格引用（如"H3" -> {row: 3, col: 8}）
const parseCellRef = (cellRef) => {
  const match = cellRef.match(/^([A-Z]+)(\d+)$/)
  if (!match) {
    return null
  }
  
  const colStr = match[1]
  const rowStr = match[2]
  
  // 列字母转数字（A=1, B=2, ..., H=8）
  let col = 0
  for (let i = 0; i < colStr.length; i++) {
    col = col * 26 + (colStr.charCodeAt(i) - 64)
  }
  
  return {
    row: parseInt(rowStr),
    col: col
  }
}
```

### 4.6 完整关联流程

```
步骤1：解析cellimages.xml
    ↓ 提取xdr:cNvPr.name（图片名称）
    ↓ 提取a:blip r:embed（关系ID）
    
步骤2：解析cellimages.xml.rels
    ↓ 根据关系ID查找图片文件路径
    ↓ 建立关系ID到文件路径的映射
    
步骤3：解析sheet1.xml
    ↓ 提取所有单元格数据
    ↓ 查找包含DISPIMG函数的单元格
    ↓ 提取DISPIMG函数的第一个参数（图片名称）
    ↓ 建立图片名称到单元格引用的映射
    
步骤4：关联图片到数据行
    ↓ 根据图片名称查找单元格引用
    ↓ 解析单元格引用获取行号
    ↓ 根据行号关联图片到数据行
    ↓ 分配图片到查核资料字段
    
步骤5：提取图片文件
    ↓ 从xl/media/目录读取图片
    ↓ 转换为Base64编码
```

### 4.7 关键优势

1. **精确关联**：通过DISPIMG函数直接关联，无需ref属性
2. **兼容性强**：支持WPS自定义格式
3. **准确性高**：图片名称唯一，不会混淆
4. **可追溯**：完整的关联链路清晰可见

---

## 五、三文件关联关系总结

### 5.1 完整关联链

```
cellimages.xml (图片定义)
    ↓ a:blip r:embed="rId1"
cellimages.xml.rels (关系映射)
    ↓ Relationship Id="rId1"
xl/media/image1.png (实际图片文件)
```

### 5.2 数据提取流程

```
步骤1：解析cellimages.xml
    ↓ 提取xdr:cNvPr的id属性（图片ID）
    ↓ 提取a:blip的r:embed属性（关系ID）
    
步骤2：解析cellimages.xml.rels
    ↓ 根据关系ID查找Relationship节点
    ↓ 提取Target属性（图片文件路径）
    
步骤3：解析sheet1.xml（可选）
    ↓ 查找单元格数据
    ↓ 关联图片到单元格（如果有ref属性）
    
步骤4：提取图片文件
    ↓ 从xl/media/目录读取图片
    ↓ 转换为Base64编码
```

### 5.3 关键问题

**问题1：缺少单元格引用**
- cellimages.xml中没有`ref`属性
- 无法直接关联到sheet1.xml中的单元格
- 需要通过其他方式确定图片位置

**问题2：WPS自定义格式**
- 使用`etc:`命名空间
- 节点结构略有不同
- 需要适配WPS格式

**问题3：图片ID与关系ID混淆**
- `xdr:cNvPr id`是图片内部ID
- `a:blip r:embed`是关系ID
- 两者不同，需要正确区分

---

## 六、解析策略建议

### 6.1 XML解析器配置

```javascript
const cellImagesXmlParser = new XMLParser({
  ignoreAttributes: false,
  attributeNamePrefix: '',
  textNodeName: '#text',
  parseAttributeValue: true,
  trimValues: true,
  removeNSPrefix: false,  // 保留命名空间前缀
  isArray: (name) => {
    // 强制将cellImage解析为数组
    return name === 'cellImage' || name === 'Relationship'
  }
})
```

### 6.2 节点提取逻辑

```javascript
// 步骤1：从cellimages.xml提取图片信息
const cellImages = cellImagesXml['etc:cellImages']?.cellImage

for (const cellImage of cellImages) {
  const pic = cellImage['xdr:pic']
  const nvPicPr = pic['xdr:nvPicPr']
  const cNvPr = nvPicPr['xdr:cNvPr']
  
  const imageId = cNvPr.id  // 图片内部ID
  const imageName = cNvPr.name  // 图片名称
  
  const blipFill = pic['xdr:blipFill']
  const blip = blipFill['a:blip']
  const relationshipId = blip['r:embed']  // 关系ID（关键！）
  
  console.log(`图片ID: ${imageId}, 关系ID: ${relationshipId}, 名称: ${imageName}`)
}

// 步骤2：从cellimages.xml.rels提取文件路径
const relationships = relsXml.Relationships?.Relationship

for (const rel of relationships) {
  const id = rel.Id  // 关系ID
  const target = rel.Target  // 图片文件路径
  
  console.log(`关系ID: ${id} -> ${target}`)
}

// 步骤3：建立映射
const imageMap = {
  [relationshipId]: {
    imageId: imageId,
    imageName: imageName,
    filePath: target
  }
}
```

### 6.3 错误处理建议

```javascript
// 1. 检查节点存在性
if (!cellImagesXml['etc:cellImages']) {
  console.error('未找到etc:cellImages节点')
  // 尝试查找可能的替代节点
  const possibleKeys = Object.keys(cellImagesXml)
    .filter(key => key.includes('cellImage') || key.includes('cell'))
  console.warn('可能的节点键:', possibleKeys)
}

// 2. 验证必要属性
if (!pic || !pic['xdr:nvPicPr']) {
  console.error('cellImage节点结构不完整')
  continue
}

if (!cNvPr || !cNvPr.id) {
  console.error('缺少xdr:cNvPr或id属性')
  continue
}

if (!blip || !blip['r:embed']) {
  console.error('缺少a:blip或r:embed属性')
  continue
}

// 3. 验证关系映射
if (!relMap[relationshipId]) {
  console.warn(`关系ID ${relationshipId} 未在rels文件中找到`)
  continue
}
```

---

## 七、代码修改建议

### 7.1 修改buildCellImagesMappings函数

**当前问题：**
1. 使用`cellImage.ref`属性，但该属性不存在
2. 使用`cellImage.ext`属性，但应该使用`xdr:cNvPr.name`
3. 节点路径假设错误

**修改建议：**
```javascript
const buildCellImagesMappings = async (binaryData: string) => {
  // ... 现有代码 ...
  
  // 修改cellimages.xml解析部分
  const cellImagesXml = cellImagesXmlParser.parse(cellImagesContent)
  
  // 注意：使用etc:cellImages而不是cellImage
  const cellImages = cellImagesXml['etc:cellImages']?.cellImage
  
  if (!cellImages) {
    console.warn('未找到etc:cellImages.cellImage节点')
    return { relMap, cellImageMap }
  }
  
  const cellImageArray = Array.isArray(cellImages) ? cellImages : [cellImages]
  
  for (const cellImage of cellImageArray) {
    const pic = cellImage['xdr:pic']
    
    if (!pic) {
      console.warn('cellImage缺少xdr:pic节点')
      continue
    }
    
    const nvPicPr = pic['xdr:nvPicPr']
    const cNvPr = nvPicPr?.['xdr:cNvPr']
    
    if (!cNvPr) {
      console.warn('xdr:pic缺少xdr:cNvPr节点')
      continue
    }
    
    const imageId = cNvPr.id  // 图片内部ID
    const imageName = cNvPr.name  // 图片名称
    
    const blipFill = pic['xdr:blipFill']
    const blip = blipFill?.['a:blip']
    
    if (!blip) {
      console.warn('xdr:pic缺少xdr:blipFill.a:blip节点')
      continue
    }
    
    const relationshipId = blip['r:embed']  // 关系ID
    
    if (!relationshipId) {
      console.warn('a:blip缺少r:embed属性')
      continue
    }
    
    // 存储映射
    cellImageMap[relationshipId] = {
      cell: '',  // 当前文件没有ref属性
      imageId: imageId,
      imageName: imageName
    }
    
    console.log(`映射: rId=${relationshipId} -> imageId=${imageId}, name=${imageName}`)
  }
}
```

### 7.2 处理缺少ref属性的情况

**方案1：使用图片名称匹配**
```javascript
// 如果cellimages.xml没有ref属性
// 可以尝试通过图片名称匹配到工作表数据
const associateImagesByName = (processedData, cellImageMap) => {
  for (const [relationshipId, imageInfo] of Object.entries(cellImageMap)) {
    const imageName = imageInfo.imageName
    
    // 尝试在工作表数据中查找匹配的通行标识ID
    for (const row of processedData) {
      const rowId = row['通行标识ID']
      
      // 如果图片名称包含通行标识ID，则关联
      if (imageName.includes(rowId)) {
        if (!row['查核资料1']) {
          row['查核资料1'] = mediaFiles[imageInfo.filePath]
        } else if (!row['查核资料2']) {
          row['查核资料2'] = mediaFiles[imageInfo.filePath]
        }
        break
      }
    }
  }
}
```

**方案2：使用位置信息匹配**
```javascript
// 如果有位置信息（a:off, a:ext）
// 可以计算图片所在的单元格
const calculateCellFromPosition = (offX, offY, extCx, extCy) => {
  // EMU到像素转换：1像素 = 9525 EMU
  const pixelX = offX / 9525
  const pixelY = offY / 9525
  const widthPx = extCx / 9525
  const heightPx = extCy / 9525
  
  // 根据标准列宽和行高计算单元格位置
  // 这里需要sheet1.xml中的列宽信息
  const col = Math.floor(pixelX / 64)  // 假设列宽64像素
  const row = Math.floor(pixelY / 20)  // 假设行高20像素
  
  return `${String.fromCharCode(65 + col)}${row + 1}`
}
```

---

## 八、测试建议

### 8.1 调试步骤

1. **验证XML解析**
   - 检查cellImagesXml的根节点键
   - 确认包含`etc:cellImages`
   - 验证cellImage节点被正确解析为数组

2. **验证属性提取**
   - 检查每个cellImage的xdr:cNvPr.id
   - 检查每个cellImage的a:blip.r:embed
   - 确认关系ID格式正确（rId1, rId2等）

3. **验证关系映射**
   - 检查relMap是否正确建立
   - 验证relationshipId能找到对应的Target
   - 确认文件路径格式正确

4. **验证图片提取**
   - 检查mediaFiles是否包含所有图片
   - 验证Base64编码正确
   - 测试图片显示

### 8.2 日志输出

```javascript
console.log('========== cellimages.xml解析开始 ==========')
console.log('根节点键:', Object.keys(cellImagesXml))
console.log('cellImage数量:', cellImageArray.length)

for (let i = 0; i < Math.min(3, cellImageArray.length); i++) {
  const cellImage = cellImageArray[i]
  console.log(`\n--- cellImage ${i + 1} ---`)
  console.log('完整结构:', JSON.stringify(cellImage, null, 2))
  console.log('xdr:cNvPr.id:', cellImage['xdr:pic']?.['xdr:nvPicPr']?.['xdr:cNvPr']?.id)
  console.log('xdr:cNvPr.name:', cellImage['xdr:pic']?.['xdr:nvPicPr']?.['xdr:cNvPr']?.name)
  console.log('a:blip r:embed:', cellImage['xdr:pic']?.['xdr:blipFill']?.['a:blip']?.['r:embed'])
}
```

---

## 九、总结

### 9.1 关键发现

1. **WPS自定义格式**
   - 使用`etc:`命名空间
   - 节点结构与标准Excel略有不同

2. **缺少ref属性**
   - 无法直接关联到单元格
   - 需要使用其他方式定位

3. **正确的关联链**
   - `xdr:cNvPr.id` → 图片内部ID
   - `a:blip r:embed` → 关系ID
   - `Relationship.Id` → 图片文件路径

### 9.2 解析策略

1. 使用专用XML解析器配置
2. 正确处理命名空间
3. 提取正确的属性路径
4. 建立准确的关系映射
5. 处理缺少ref属性的情况

### 9.3 下一步行动

1. 修改`buildCellImagesMappings`函数
2. 调整节点路径以匹配WPS格式
3. 实现图片名称匹配或位置计算
4. 添加详细的错误处理和日志
5. 测试完整的解析流程

---

**文档生成时间：** 2026-02-26
**分析文件版本：** 42.2025年06月通行数据处理（完整）.xlsx
**文件大小：** cellimages.xml (228,972字节)
