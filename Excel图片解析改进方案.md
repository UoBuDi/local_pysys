# Excel图片解析改进方案

## 一、现状分析

### 1.1 当前实现方式
当前项目使用**正则表达式**解析XML文件，存在以下问题：

| 问题 | 描述 | 影响 |
|------|------|------|
| XML命名空间处理不完善 | 正则表达式无法正确处理`xdr:`、`a:`等命名空间 | 部分Excel文件解析失败 |
| 行号计算可能不准确 | 从`<xdr:row>`直接提取，未考虑`<xdr:from>`结构 | 图片位置偏移 |
| 属性顺序依赖 | 正则匹配依赖属性顺序(Id在前或Target在前) | 某些格式无法识别 |
| 错误处理不健壮 | 正则匹配失败时难以定位问题 | 调试困难 |

### 1.2 项目现有依赖
```
jszip: ^3.10.1    ✓ 已安装
xlsx: ^0.18.5     ✓ 已安装
xml2js: 未安装    ✗ 需要安装
```

## 二、改进方案

### 2.1 技术选型
采用**xml2js**库替代正则表达式解析XML，优势如下：

1. **结构化解析**：将XML转为JSON对象，易于操作
2. **命名空间支持**：正确处理`xdr:`、`a:`、`r:`等命名空间
3. **属性提取准确**：不依赖属性顺序
4. **错误处理完善**：提供详细的解析错误信息

### 2.2 核心映射关系

```
┌─────────────────────────────────────────────────────────────────┐
│                    四层关联架构                                   │
├─────────────────────────────────────────────────────────────────┤
│  第1层: drawing1.xml.rels                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Relationship Id="rId1" Target="../media/image1.png"    │    │
│  │  Relationship Id="rId2" Target="../media/image2.png"    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                          ↓                                       │
│  第2层: drawing1.xml                                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  twoCellAnchor → from → row:2, col:7 → r:embed="rId1"   │    │
│  │  twoCellAnchor → from → row:2, col:9 → r:embed="rId2"   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                          ↓                                       │
│  第3层: xl/media/                                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  image1.png → Base64数据                                │    │
│  │  image2.png → Base64数据                                │    │
│  └─────────────────────────────────────────────────────────┘    │
│                          ↓                                       │
│  第4层: 表格数据                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  行3(索引2) → 查核资料1: image1, 查核资料2: image2       │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 关键文件结构

#### drawing1.xml.rels 结构
```xml
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/image1.png"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/image2.png"/>
</Relationships>
```

#### drawing1.xml 结构
```xml
<xdr:wsDr xmlns:xdr="http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing">
  <xdr:twoCellAnchor>
    <xdr:from>
      <xdr:col>7</xdr:col>    <!-- 列号，从0开始 -->
      <xdr:row>2</xdr:row>    <!-- 行号，从0开始，对应Excel第3行 -->
    </xdr:from>
    <xdr:to>
      <xdr:col>8</xdr:col>
      <xdr:row>3</xdr:row>
    </xdr:to>
    <xdr:blipFill>
      <a:blip xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" r:embed="rId1"/>
    </xdr:blipFill>
  </xdr:twoCellAnchor>
</xdr:wsDr>
```

## 三、开发计划

### 阶段一：环境准备（预计0.5小时）

| 序号 | 任务 | 命令/操作 | 验证标准 |
|------|------|-----------|----------|
| 1.1 | 安装xml2js | `pnpm add xml2js` | package.json中出现依赖 |
| 1.2 | 安装类型定义 | `pnpm add -D @types/xml2js` | TypeScript无类型错误 |
| 1.3 | 验证安装 | 检查node_modules | 模块可正常导入 |

### 阶段二：重构解析函数（预计2小时）

| 序号 | 任务 | 文件位置 | 详细说明 |
|------|------|----------|----------|
| 2.1 | 创建XML解析工具函数 | SplitMatch.vue | 封装xml2js解析逻辑 |
| 2.2 | 重构buildImageMappings函数 | SplitMatch.vue | 使用xml2js解析rels和drawing文件 |
| 2.3 | 改进行号计算逻辑 | SplitMatch.vue | 从`<xdr:from>`正确提取行号 |
| 2.4 | 完善错误处理 | SplitMatch.vue | 添加详细的错误日志 |

#### 2.1 XML解析工具函数设计
```typescript
import { parseString } from 'xml2js'

const parseXmlAsync = (xmlContent: string): Promise<any> => {
  return new Promise((resolve, reject) => {
    parseString(xmlContent, {
      explicitArray: false,
      mergeAttrs: false,
      xmlns: true
    }, (err, result) => {
      if (err) reject(err)
      else resolve(result)
    })
  })
}
```

#### 2.2 重构后的buildImageMappings函数
```typescript
const buildImageMappings = async (binaryData: string): Promise<{
  relMap: Record<string, string>,
  drawingMap: Record<string, { row: number, col: number, imageId: string }>
}> => {
  const zip = new JSZip()
  const workbook = await zip.loadAsync(binaryData)
  
  // 1. 解析rels文件
  const relMap: Record<string, string> = {}
  const relsFiles = Object.keys(workbook.files).filter(f => 
    f.includes('drawings/') && f.endsWith('.xml.rels')
  )
  
  for (const relsPath of relsFiles) {
    const relsContent = await workbook.file(relsPath)?.async('text')
    if (relsContent) {
      const relsXml = await parseXmlAsync(relsContent)
      const relationships = Array.isArray(relsXml.Relationships.Relationship)
        ? relsXml.Relationships.Relationship
        : [relsXml.Relationships.Relationship]
      
      for (const rel of relationships) {
        const id = rel.$.Id
        const target = rel.$.Target
        const fileName = target.replace('../', 'xl/')
        relMap[id] = fileName
      }
    }
  }
  
  // 2. 解析drawing文件
  const drawingMap: Record<string, { row: number, col: number, imageId: string }> = {}
  const drawingFiles = Object.keys(workbook.files).filter(f =>
    f.includes('drawings/') && f.endsWith('.xml') && !f.includes('.rels')
  )
  
  for (const drawingPath of drawingFiles) {
    const drawingContent = await workbook.file(drawingPath)?.async('text')
    if (drawingContent) {
      const drawingXml = await parseXmlAsync(drawingContent)
      const wsDr = drawingXml['xdr:wsDr'] || drawingXml.wsDr
      
      // 处理twoCellAnchor
      const twoCellAnchors = Array.isArray(wsDr['xdr:twoCellAnchor'])
        ? wsDr['xdr:twoCellAnchor']
        : wsDr['xdr:twoCellAnchor'] ? [wsDr['xdr:twoCellAnchor']] : []
      
      for (const anchor of twoCellAnchors) {
        const from = anchor['xdr:from']
        const row = parseInt(from['xdr:row']._ || from['xdr:row']) + 1
        const col = parseInt(from['xdr:col']._ || from['xdr:col'])
        
        const blipFill = anchor['xdr:blipFill']
        const blip = blipFill['a:blip'] || blipFill['a:blip']
        const relId = blip.$['r:embed'] || blip.$.embed
        
        const pic = anchor['xdr:pic']
        const imageId = pic?.['xdr:nvPicPr']?.['xdr:cNvPr']?.$.name || ''
        
        drawingMap[relId] = { row, col, imageId }
      }
      
      // 处理oneCellAnchor（如果有）
      const oneCellAnchors = Array.isArray(wsDr['xdr:oneCellAnchor'])
        ? wsDr['xdr:oneCellAnchor']
        : wsDr['xdr:oneCellAnchor'] ? [wsDr['xdr:oneCellAnchor']] : []
      
      for (const anchor of oneCellAnchors) {
        // 类似处理逻辑...
      }
    }
  }
  
  return { relMap, drawingMap }
}
```

### 阶段三：优化图片关联逻辑（预计1小时）

| 序号 | 任务 | 详细说明 |
|------|------|----------|
| 3.1 | 按行号分组图片 | 将同一行的多张图片收集到数组 |
| 3.2 | 分配到查核资料列 | 第一张→查核资料1，第二张→查核资料2 |
| 3.3 | 处理边界情况 | 无图片、单图片、多图片的处理 |

### 阶段四：测试验证（预计1小时）

| 序号 | 测试场景 | 预期结果 |
|------|----------|----------|
| 4.1 | 无图片Excel | 正常解析数据，查核资料列为空 |
| 4.2 | 单图片Excel | 图片正确显示在查核资料1 |
| 4.3 | 多图片同单元格 | 第一张→查核资料1，第二张→查核资料2 |
| 4.4 | 多图片不同行 | 按行号正确分配 |
| 4.5 | 复杂命名空间 | 正确解析带命名空间的XML |

## 四、风险与应对

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| xml2js解析性能 | 低 | 中 | 对于大文件采用流式解析 |
| XML结构变化 | 中 | 高 | 添加多种格式兼容处理 |
| 图片格式不支持 | 低 | 低 | 支持常见格式(png/jpg/gif/webp) |

## 五、时间估算

| 阶段 | 预计时间 | 累计时间 |
|------|----------|----------|
| 阶段一：环境准备 | 0.5小时 | 0.5小时 |
| 阶段二：重构解析函数 | 2小时 | 2.5小时 |
| 阶段三：优化关联逻辑 | 1小时 | 3.5小时 |
| 阶段四：测试验证 | 1小时 | 4.5小时 |
| **总计** | **4.5小时** | - |

## 六、验收标准

1. ✅ 成功安装xml2js依赖
2. ✅ 使用xml2js正确解析rels和drawing文件
3. ✅ 图片按行号正确关联到数据行
4. ✅ 同一行的多张图片正确分配到查核资料1和查核资料2
5. ✅ 控制台输出详细的解析日志
6. ✅ 无TypeScript类型错误
7. ✅ 无运行时错误

## 七、后续优化建议

1. **性能优化**：对于大型Excel文件，考虑使用Web Worker后台处理
2. **格式支持**：扩展支持更多图片格式(如emf、wmf)
3. **错误恢复**：解析失败时提供部分数据恢复功能
4. **缓存机制**：对已解析的文件进行缓存，避免重复解析
