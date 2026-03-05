# 前端Excel图片提取与位置预览功能开发提示词

（用于同步需求给开发人员Trae，包含完整技术方案、实现要求与交付标准）

## 一、功能开发背景与核心目标

1. **处理文件**：需适配2份Excel文件的差异化格式

    - 文件1（2025年08月通行数据处理 (2).xlsx）：图片关联信息存储于`xl/drawings/`目录（drawing1.xml + drawing1.xml.rels）

    - 文件2（42.2025年06月通行数据处理（完整）.xlsx）：图片关联信息存储于`xl/cellimages.xml` + `xl/_rels/cellimages.xml.rels`

2. **核心目标**：在Vue3+Element Plus项目中，实现“Excel上传→图片提取+位置解析→预览窗口精准渲染”全流程，支持多文件同时处理

## 二、技术栈与依赖库要求

1. **基础框架**：Vue3（Composition API）+ Element Plus

2. **核心依赖库**（需指定版本以避免兼容性问题）

    - `jszip@^3.10.1`：解压Excel文件（.xlsx本质为ZIP压缩包）

    - `xmldom@^0.8.10`：解析XML文件（提取关系映射与位置信息）

    - `file-saver@^2.0.5`：可选，支持图片批量下载

    - 无需额外后端服务，纯前端实现

## 三、核心功能模块与实现逻辑

需按“文件上传→格式判断→差异化解析→预览渲染”4个模块开发，每个模块需满足以下要求：

### 模块1：文件上传（基于Element Plus）

1. 使用`<el-upload>`组件，配置支持：

    - 多文件上传（同时处理6月、8月表）

    - 仅允许.xlsx格式，限制单个文件≤20MB

    - 上传前校验文件格式，不符合时提示“仅支持Excel 2007及以上格式（.xlsx）”

2. 上传后触发解析函数，将File对象传入解析逻辑

### 模块2：Excel格式判断（前置核心步骤）

1. 逻辑要求：通过解压Excel文件，判断图片存储类型，决定后续解析方式

    - 解压文件：用`jszip.loadAsync(file)`读取文件二进制流，获取内部文件列表

    - 判断规则：

        - 若存在`xl/cellimages.xml` → 判定为“cellimages型”（6月表）

        - 若存在`xl/drawings/drawing1.xml` → 判定为“drawings型”（8月表）

        - 若均不存在 → 提示“当前Excel文件无嵌入图片”

2. 输出：返回格式类型标识（`cellimages`/`drawings`/`no_image`），作为解析分支依据

### 模块3：差异化解析（核心业务逻辑）

需分别实现两种格式的解析逻辑，最终输出**统一格式的图片信息数组**（便于后续预览复用）

#### 3.1 解析“drawings型”（8月表）

基于`xl/drawings/drawing1.xml` + `xl/drawings/_rels/drawing1.xml.rels`

1. 步骤1：解析`drawing1.xml.rels`，建立“rId→图片路径”映射

    - 筛选`<Relationship>`标签中`Type`包含`image`的节点

    - 提取`Id`（如rId99）和`Target`（如../media/image99.png），补全路径为`xl/media/image99.png`

    - 存储映射表：`{ "rId99": "xl/media/image99.png" }`

2. 步骤2：解析`drawing1.xml`，提取“位置信息→rId”

    - 遍历`<xdr:twoCellAnchor>`标签（单个标签对应1张图片）

    - 提取位置数据：

        - 单元格：`xdr:from`下的`col`（列号）、`row`（行号）→ 转换为A1格式（如col=7→H列，row=2→H2）

        - 偏移量：`colOff`/`rowOff`（单位：EMU，后续需转换为像素：1像素=9525 EMU）

        - 尺寸：`to.colOff - from.colOff`（宽度）、`to.rowOff - from.rowOff`（高度）

    - 提取`xdr:blip`标签的`r:embed`属性（如rId99），关联rId

3. 步骤3：合并映射 → 输出单张图片信息（包含path、position、后续需加base64）

#### 3.2 解析“cellimages型”（6月表）

基于`xl/cellimages.xml` + `xl/_rels/cellimages.xml.rels`

1. 步骤1：解析`cellimages.xml.rels`，建立“rId→图片路径”映射

    - 逻辑同3.1步骤1，注意`Target`需补全为`xl/media/xxx.png`

2. 步骤2：解析`cellimages.xml`，提取“位置信息→rId”

    - 遍历`<cellImage>`标签（单个标签对应1张图片）

    - 提取位置数据：

        - 单元格：直接读取`ref`属性（如H2，无需转换）

        - 尺寸：读取`<ext>`标签的`cx`（宽度）、`cy`（高度）（单位：EMU）

        - 偏移量：默认0（该格式无偏移信息）

    - 提取`<blip>`标签的`r:embed`属性（如rId1），关联rId

3. 步骤3：合并映射 → 输出与“drawings型”统一格式的图片信息

#### 3.3 统一输出格式

两种格式解析后，需返回结构一致的数组，示例：

```JavaScript

[
  {
    imgPath: "xl/media/image1.png", // 图片在Excel内的路径
    base64: "data:image/png;base64,iVBORw0KGgo...", // 图片Base64编码（用于预览）
    position: {
      cell: "H2", // 图片所在单元格（A1格式）
      colOff: 17145, // 偏移量（EMU）
      rowOff: 17780,
      width: 1126490, // 图片宽度（EMU）
      height: 521335 // 图片高度（EMU）
    }
  }
]
```

### 模块4：预览窗口渲染（精准定位要求）

1. **表格渲染**：用Element Plus `<el-table>`展示Excel数据，需：

    - 支持表格滚动（横向+纵向）

    - 通过`ref="excelTable"`获取表格DOM，用于计算单元格位置

2. **图片定位渲染**：

    - 位置计算：

        - 根据`cell`（如H2）找到表格中对应单元格的DOM元素

        - 用`getBoundingClientRect()`获取单元格绝对位置（top/left）

        - 将EMU单位转换为像素（偏移量/尺寸 ÷ 9525）

        - 计算图片最终位置：`top + 偏移量像素`、`left + 偏移量像素`

    - 渲染逻辑：

        - 创建`<img>`标签，设置`position: absolute`、`z-index: 10`，src为base64

        - 将图片挂载到表格容器（`.el-table__body-wrapper`）中

        - 监听表格滚动事件（`scroll`），同步更新图片位置（避免滚动时图片偏移）

3. **交互优化**：

    - 鼠标hover图片时显示放大预览（可用Element Plus `<el-image>`的`preview-src-list`）

    - 支持批量下载图片（用`file-saver`将base64转为Blob下载）

## 四、异常处理与边界条件

1. **文件解析异常**：

    - 加密Excel文件：解析失败时提示“无法解析加密的Excel文件，请先解密”

    - 损坏文件：捕获`jszip`解压错误，提示“Excel文件损坏，请检查文件完整性”

2. **图片处理异常**：

    - 解析到图片路径但无对应文件：跳过该图片，控制台打印警告（不阻断整体流程）

    - 图片格式不支持（非png/jpg）：提示“存在不支持的图片格式，仅支持png/jpg”

3. **性能优化**：

    - 大文件（10-20MB）：解析时显示加载动画（Element Plus `<el-loading>`）

    - 多图片（如8月表203张）：采用图片懒加载（滚动到可视区域再渲染）

## 五、交付标准

1. **代码交付**：

    - 按模块拆分组件（如`ExcelUpload.vue`上传组件、`ExcelImageParser.js`解析工具、`ImagePreview.vue`预览组件）

    - 工具函数单独封装（如格式判断、XML解析、位置计算），便于复用与维护

    - 代码添加必要注释（尤其是解析逻辑部分）

2. **功能验证**：

    - 提供测试用的2份Excel文件（6月、8月表），确保均可正常解析

    - 预览时图片位置与Excel中完全一致，无偏移

    - 支持多文件同时上传、解析、预览

要不要我帮你补充一份**核心函数的伪代码模板**？可以直接给Trae作为开发参考，减少逻辑理解成本。
> （注：文档部分内容可能由 AI 生成）