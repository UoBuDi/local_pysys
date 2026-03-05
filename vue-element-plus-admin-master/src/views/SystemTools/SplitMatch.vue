<template>
  <div class="split-match">
    <el-card class="control-panel">
      <template #header>
        <div class="card-header">
          <span>拆分匹配</span>
        </div>
      </template>

      <el-form :inline="true" class="control-form">
        <el-form-item label="选择数据表">
          <el-select
            v-model="selectedTable"
            placeholder="请选择数据表"
            filterable
            style="width: 250px"
            @change="handleTableChange"
          >
            <el-option
              v-for="table in tableList"
              :key="table.value"
              :label="table.label"
              :value="table.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button
            type="success"
            @click="handleExecuteMatch"
            :disabled="!selectedTable || matchLoading"
            :loading="matchLoading"
          >
            执行匹配
          </el-button>
          <el-button @click="loadTableList"> 刷新列表 </el-button>
          <el-button @click="handleExport"> 导出数据 </el-button>
          <el-upload
            v-if="selectedTable"
            class="upload-demo"
            action="#"
            :auto-upload="false"
            :on-change="handleFileUpload"
            :show-file-list="false"
            accept=".xlsx"
            style="margin-left: 8px"
          >
            <el-button type="warning"> 导入数据 </el-button>
          </el-upload>
        </el-form-item>

        <!-- 筛选功能区域 -->
        <el-form :inline="true" class="filter-form" v-if="selectedTable">
          <el-form-item label="通行标识ID">
            <el-select
              v-model="filters.通行标识ID"
              placeholder="请输入或选择通行标识ID"
              clearable
              filterable
              allow-create
              style="width: 200px"
            >
              <el-option v-for="id in recentCheckIds" :key="id" :label="id" :value="id" />
            </el-select>
          </el-form-item>
          <el-form-item label="车牌号码">
            <el-input
              v-model="filters.车牌号码"
              placeholder="请输入车牌号码"
              clearable
              style="width: 150px"
            />
          </el-form-item>
          <el-form-item label="核查通行标识">
            <el-input
              v-model="filters.核查通行标识"
              placeholder="请输入核查通行标识"
              clearable
              style="width: 200px"
            />
          </el-form-item>
          <el-form-item label="复核情况">
            <el-input
              v-model="filters.复核情况"
              placeholder="请输入复核情况"
              clearable
              style="width: 150px"
            />
          </el-form-item>
          <el-form-item label="备注">
            <el-input
              v-model="filters.备注"
              placeholder="请输入备注"
              clearable
              style="width: 150px"
            />
          </el-form-item>
          <el-form-item label="收费车型">
            <el-input
              v-model="filters.收费车型"
              placeholder="请输入收费车型"
              clearable
              style="width: 100px"
            />
          </el-form-item>
          <el-form-item label="特情">
            <el-input
              v-model="filters.特情"
              placeholder="请输入特情"
              clearable
              style="width: 100px"
            />
          </el-form-item>
          <el-form-item label="核查拆分">
            <el-select
              v-model="filters.核查拆分"
              placeholder="请选择核查拆分"
              clearable
              style="width: 100px"
            >
              <el-option
                v-for="option in checkSplitOptions"
                :key="option"
                :label="option"
                :value="option"
              />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleFilter"> 筛选 </el-button>
            <el-button @click="handleResetFilter"> 重置筛选 </el-button>
          </el-form-item>
        </el-form>
      </el-form>

      <div class="match-result" v-if="matchResult">
        <el-alert
          :title="`匹配完成`"
          :type="matchResult.matched_count > 0 ? 'success' : 'warning'"
          :description="`已拆回: ${matchResult.matched_count} 条, 未拆回: ${matchResult.unmatched_count} 条`"
          show-icon
          :closable="false"
        />
      </div>

      <!-- 虚拟表格 -->
      <div class="table-container" v-if="selectedTable">
        <el-table
          :data="tableData"
          v-loading="tableLoading"
          style="width: 100%"
          max-height="500"
          border
          stripe
          :row-key="(row) => row['通行标识ID'] || Math.random()"
        >
          <el-table-column type="index" label="序号" width="55" />
          <el-table-column prop="通行标识ID" label="通行标识ID" width="310">
            <template #default="{ row }">
              <el-button type="link" @click="handleIdClick(row)" style="border: none; padding: 0">{{
                row['通行标识ID']
              }}</el-button>
            </template>
          </el-table-column>
          <el-table-column prop="车牌号码" label="车牌号码" min-width="120" />
          <el-table-column prop="核查通行标识" label="核查通行标识" width="310">
            <template #default="{ row }">
              <el-button type="link" @click="handleIdClick(row)" style="border: none; padding: 0">{{
                row['核查通行标识'] || '-'
              }}</el-button>
            </template>
          </el-table-column>
          <el-table-column prop="复核情况" label="复核情况" min-width="100" />
          <el-table-column prop="备注" label="备注" width="160" />
          <el-table-column prop="门架通行时间" label="门架通行时间" min-width="150" />
          <el-table-column prop="入口时间" label="入口时间" min-width="150" />
          <el-table-column prop="收费车型" label="收费车型" min-width="100" />
          <el-table-column prop="查核资料1" label="查核资料1" min-width="150">
            <template #default="{ row }">
              <div v-if="row['查核资料1']">
                <el-image
                  :src="row['查核资料1']"
                  fit="cover"
                  style="width: 50px; height: 50px; cursor: pointer"
                  :preview-src-list="[row['查核资料1']]"
                  :preview-teleported="true"
                  preview-z-index="9999"
                />
              </div>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="查核资料2" label="查核资料2" min-width="150">
            <template #default="{ row }">
              <div v-if="row['查核资料2']">
                <el-image
                  :src="row['查核资料2']"
                  fit="cover"
                  style="width: 50px; height: 50px; cursor: pointer"
                  :preview-src-list="[row['查核资料2']]"
                  :preview-teleported="true"
                  preview-z-index="9999"
                />
              </div>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="特情" label="特情" min-width="100">
            <template #default="{ row }">
              <div style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis">
                {{ row['特情'] || '-' }}
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="核查拆分" label="核查拆分" min-width="100" />
        </el-table>

        <div class="pagination-container">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[20, 50, 100]"
            :total="total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
            :disabled="!selectedTable"
          />
        </div>
      </div>

      <!-- 详细信息对话框 -->
      <el-dialog
        v-model="dialogVisible"
        title="详细信息"
        width="70%"
        :before-close="handleDialogClose"
        destroy-on-close
        ref="dialogRef"
      >
        <div class="dialog-content" style="max-height: 600px; overflow-y: auto">
          <el-descriptions v-if="editedRow" :column="2" border style="table-layout: fixed">
            <el-descriptions-item
              v-for="(value, key) in editedRow"
              :key="key"
              :label="key"
              style="word-break: break-all; overflow-wrap: break-word"
            >
              <!-- 图片上传字段 -->
              <template v-if="['查核资料1', '查核资料2'].includes(key)">
                <div>
                  <!-- 激活状态指示器 -->
                  <div style="margin-bottom: 5px; display: flex; align-items: center">
                    <el-radio v-model="activeImageField" :label="key" size="small">
                      当前粘贴目标
                    </el-radio>
                  </div>
                  <!-- 已上传图片预览 -->
                  <div v-if="editedRow[key]" style="margin-bottom: 10px; position: relative">
                    <el-image
                      :src="editedRow[key]"
                      fit="cover"
                      style="width: 200px; height: 150px; cursor: pointer"
                      :preview-src-list="imagePreviewList[key] || []"
                    />
                    <el-button
                      type="danger"
                      size="small"
                      circle
                      style="position: absolute; top: 5px; right: 5px"
                      @click.stop="handleImageDelete(key)"
                    >
                      <template #icon>
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          width="16"
                          height="16"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="2"
                          stroke-linecap="round"
                          stroke-linejoin="round"
                        >
                          <path d="M3 6h18" />
                          <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
                          <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
                        </svg>
                      </template>
                    </el-button>
                  </div>
                  <!-- 上传组件 -->
                  <el-upload
                    class="upload-demo"
                    action="#"
                    :auto-upload="false"
                    :on-change="(file) => handleImageUpload(file, key)"
                    :show-file-list="false"
                    accept="image/*"
                    @paste="
                      (event) => {
                        // 检查是否有图片数据
                        const items = event.clipboardData?.items
                        if (items) {
                          for (let i = 0; i < items.length; i++) {
                            if (items[i].type.indexOf('image') === 0) {
                              // 阻止 el-upload 处理图片粘贴
                              event.preventDefault()
                              break
                            }
                          }
                        }
                      }
                    "
                  >
                    <el-button type="primary">上传图片</el-button>
                    <span style="margin-left: 10px; color: #909399"
                      >请先用 Win+Shift+S 截图再按 Ctrl+V 粘贴</span
                    >
                  </el-upload>
                </div>
              </template>
              <!-- 核查通行标识字段（特殊处理） -->
              <template v-else-if="key === '核查通行标识'">
                <div style="display: flex; align-items: center; gap: 8px">
                  <el-input
                    v-model="editedRow[key]"
                    type="text"
                    :maxlength="40"
                    show-word-limit
                    placeholder="请输入核查通行标识"
                    @input="handleCheckIdInput"
                    style="flex: 1; min-width: 300px"
                  />
                  <el-button
                    type="primary"
                    :icon="CopyDocument"
                    @click="handleCopy(String(editedRow[key]))"
                    size="default"
                  >
                    复制
                  </el-button>
                </div>
              </template>
              <!-- 复核情况字段（下拉选择） -->
              <template v-else-if="key === '复核情况'">
                <el-select
                  v-model="editedRow[key]"
                  placeholder="请选择复核情况"
                  style="width: 100%; min-width: 300px"
                >
                  <el-option label="拆分正常" value="拆分正常" />
                  <el-option label="拆分异常" value="拆分异常" />
                  <el-option label="待删除" value="待删除" />
                </el-select>
              </template>
              <!-- 其他可编辑字段 -->
              <template v-else-if="['备注', '特情'].includes(key)">
                <el-input
                  v-model="editedRow[key]"
                  type="textarea"
                  :rows="3"
                  :maxlength="2000"
                  show-word-limit
                  style="width: 100%; min-width: 300px"
                />
              </template>
              <!-- 核查拆分字段（支持编辑的下拉框） -->
              <template v-else-if="key === '核查拆分'">
                <el-select
                  v-model="editedRow[key]"
                  placeholder="请选择或输入核查拆分状态"
                  style="width: 260px"
                  filterable
                  allow-create
                  :maxlength="100"
                  show-word-limit
                >
                  <el-option label="已拆" value="已拆" />
                  <el-option label="未拆" value="未拆" />
                </el-select>
              </template>
              <!-- 其他只读字段 -->
              <template v-else>
                <!-- 图片字段不显示 blob URL -->
                <div
                  v-if="['查核资料1', '查核资料2'].includes(key)"
                  style="word-break: break-all; overflow-wrap: break-word; max-width: 400px"
                >
                  <!-- 图片已在上方预览区域显示 -->
                </div>
                <!-- 通行标识ID、车牌号码、车牌字段添加复制功能 -->
                <div
                  v-else-if="['通行标识ID', '车牌号码', '车牌'].includes(key)"
                  style="
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    word-break: break-all;
                    overflow-wrap: break-word;
                    max-width: 400px;
                  "
                >
                  <span style="flex: 1">{{ value || '-' }}</span>
                  <el-button
                    type="primary"
                    :icon="CopyDocument"
                    @click="handleCopy(String(value))"
                    size="small"
                  >
                    复制
                  </el-button>
                </div>
                <!-- 非图片字段正常显示 -->
                <div
                  v-else
                  style="word-break: break-all; overflow-wrap: break-word; max-width: 400px"
                >
                  {{ value || '-' }}
                </div>
              </template>
            </el-descriptions-item>
          </el-descriptions>
          <div v-else class="no-data">暂无数据</div>
        </div>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="dialogVisible = false">关闭</el-button>
            <el-button type="primary" @click="handleSave">保存</el-button>
          </span>
        </template>
      </el-dialog>

      <!-- 上传进度对话框 -->
      <el-dialog
        v-model="uploadLoading"
        title="文件上传"
        width="400px"
        :close-on-click-modal="false"
        :close-on-press-escape="false"
        :show-close="false"
        destroy-on-close
        custom-class="modern-upload-dialog"
      >
        <div class="modern-upload-container" style="padding: 40px 20px">
          <!-- 现代加载动画 -->
          <div class="modern-loading-animation" style="margin-bottom: 20px; text-align: center">
            <div style="display: inline-block; position: relative; width: 40px; height: 40px">
              <div
                style="
                  position: absolute;
                  width: 100%;
                  height: 100%;
                  border-radius: 50%;
                  border: 3px solid #ecf5ff;
                  border-top-color: #409eff;
                  animation: spin 1s linear infinite;
                "
              ></div>
              <div
                style="
                  position: absolute;
                  top: 50%;
                  left: 50%;
                  transform: translate(-50%, -50%);
                  width: 24px;
                  height: 24px;
                  border-radius: 50%;
                  border: 3px solid #ecf5ff;
                  border-top-color: #69c0ff;
                  animation: spin 1.5s linear infinite;
                "
              ></div>
            </div>
          </div>

          <!-- 现代进度条 -->
          <div style="margin-bottom: 30px">
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px">
              <span style="color: #606266; font-size: 14px">{{ uploadProgressText }}</span>
              <span style="color: #409eff; font-size: 14px; font-weight: 500"
                >{{ uploadProgress }}%</span
              >
            </div>
            <div
              style="
                position: relative;
                height: 10px;
                background-color: #ecf5ff;
                border-radius: 5px;
                overflow: hidden;
              "
            >
              <div
                class="progress-bar-fill"
                style="
                  position: absolute;
                  top: 0;
                  left: 0;
                  height: 100%;
                  background: linear-gradient(90deg, #409eff, #69c0ff);
                  border-radius: 5px;
                  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                "
                :style="{ width: uploadProgress + '%' }"
              >
                <div
                  class="progress-glow"
                  style="
                    position: absolute;
                    top: 0;
                    right: 0;
                    width: 40px;
                    height: 100%;
                    background: linear-gradient(
                      90deg,
                      transparent,
                      rgba(255, 255, 255, 0.6),
                      transparent
                    );
                    animation: glow 1.5s ease-in-out infinite;
                  "
                ></div>
              </div>
            </div>
          </div>

          <!-- 动态状态提示 -->
          <div class="status-indicator" style="text-align: center">
            <div
              class="status-dot"
              :style="{ backgroundColor: getStatusColor() }"
              style="
                display: inline-block;
                width: 8px;
                height: 8px;
                border-radius: 50%;
                margin-right: 8px;
              "
            ></div>
            <span style="color: #606266; font-size: 13px">{{ getUploadStatusText() }}</span>
          </div>

          <!-- 进度阶段指示 -->
          <div class="progress-steps" style="margin-top: 30px">
            <div
              class="step-container"
              style="display: flex; justify-content: space-between; align-items: center"
            >
              <div
                class="step"
                :class="{ active: uploadProgress >= 0 }"
                style="flex: 1; text-align: center"
              >
                <div
                  class="step-dot"
                  :class="{ active: uploadProgress >= 0 }"
                  style="
                    width: 20px;
                    height: 20px;
                    border-radius: 50%;
                    background-color: #c0c4cc;
                    margin: 0 auto 8px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.3s ease;
                  "
                >
                  <span v-if="uploadProgress >= 0" style="color: #fff; font-size: 12px">1</span>
                </div>
                <div
                  class="step-text"
                  style="font-size: 12px; color: #909399; transition: all 0.3s ease"
                  >初始化</div
                >
              </div>
              <div
                class="step-line"
                :class="{ active: uploadProgress >= 33 }"
                style="
                  height: 2px;
                  background-color: #e4e7ed;
                  flex: 1;
                  margin: 0 10px;
                  transition: all 0.3s ease;
                "
              ></div>
              <div
                class="step"
                :class="{ active: uploadProgress >= 33 }"
                style="flex: 1; text-align: center"
              >
                <div
                  class="step-dot"
                  :class="{ active: uploadProgress >= 33 }"
                  style="
                    width: 20px;
                    height: 20px;
                    border-radius: 50%;
                    background-color: #c0c4cc;
                    margin: 0 auto 8px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.3s ease;
                  "
                >
                  <span v-if="uploadProgress >= 33" style="color: #fff; font-size: 12px">2</span>
                </div>
                <div
                  class="step-text"
                  style="font-size: 12px; color: #909399; transition: all 0.3s ease"
                  >解析</div
                >
              </div>
              <div
                class="step-line"
                :class="{ active: uploadProgress >= 66 }"
                style="
                  height: 2px;
                  background-color: #e4e7ed;
                  flex: 1;
                  margin: 0 10px;
                  transition: all 0.3s ease;
                "
              ></div>
              <div
                class="step"
                :class="{ active: uploadProgress >= 66 }"
                style="flex: 1; text-align: center"
              >
                <div
                  class="step-dot"
                  :class="{ active: uploadProgress >= 66 }"
                  style="
                    width: 20px;
                    height: 20px;
                    border-radius: 50%;
                    background-color: #c0c4cc;
                    margin: 0 auto 8px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.3s ease;
                  "
                >
                  <span v-if="uploadProgress >= 66" style="color: #fff; font-size: 12px">3</span>
                </div>
                <div
                  class="step-text"
                  style="font-size: 12px; color: #909399; transition: all 0.3s ease"
                  >完成</div
                >
              </div>
            </div>
          </div>
        </div>
      </el-dialog>

      <!-- 导入预览对话框 -->
      <el-dialog
        v-model="importPreviewVisible"
        :title="getImportDialogTitle()"
        width="70%"
        destroy-on-close
      >
        <div class="import-preview-content" style="max-height: 600px; overflow-y: auto">
          <!-- 错误提示 -->
          <div v-if="importError" class="error">
            {{ importError }}
          </div>

          <!-- 预览数据 -->
          <div v-else-if="importStep === 'preview'">
            <el-alert
              :title="`Excel文件数据`"
              type="info"
              :description="`共读取到 ${importData.length} 条数据，提取到 ${extractedImagesCount} 张图片`"
              show-icon
              :closable="false"
              style="margin-bottom: 20px"
            />
            <el-table :data="importData" style="width: 100%" border max-height="400" size="small">
              <!-- 动态生成列 -->
              <el-table-column
                v-for="column in getImportDataColumns()"
                :key="column"
                :prop="column"
                :label="column"
                :width="getColumnWidth(column)"
              >
                <!-- 图片预览 -->
                <template v-if="['查核资料1', '查核资料2'].includes(column)" #default="{ row }">
                  <div v-if="row[column]">
                    <!-- WPS图片格式 -->
                    <div
                      v-if="typeof row[column] === 'string' && row[column].startsWith('=DISPIMG(')"
                      style="
                        width: 80px;
                        height: 60px;
                        border: 1px solid #ebeef5;
                        border-radius: 4px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        background-color: #f9fafc;
                      "
                    >
                      <el-icon style="color: #c0c4cc">
                        <Picture />
                      </el-icon>
                      <span style="margin-left: 5px; font-size: 12px; color: #909399">WPS图片</span>
                    </div>
                    <!-- 普通图片格式 -->
                    <el-image
                      v-else-if="
                        row[column] &&
                        typeof row[column] === 'string' &&
                        (isImageData(row[column]) || row[column].startsWith('data:image/'))
                      "
                      :src="row[column]"
                      fit="cover"
                      style="width: 80px; height: 60px; cursor: pointer"
                      :preview-src-list="[row[column]]"
                      :preview-teleported="true"
                      preview-z-index="9999"
                    />
                    <!-- 调试信息 -->
                    <div
                      v-else-if="row[column]"
                      style="
                        font-size: 12px;
                        color: #909399;
                        width: 80px;
                        height: 60px;
                        border: 1px solid #ebeef5;
                        border-radius: 4px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        background-color: #f9fafc;
                      "
                    >
                      <span>{{ typeof row[column] }}</span>
                    </div>
                    <span v-else>{{ row[column] }}</span>
                  </div>
                  <span v-else>-</span>
                </template>
                <!-- 通行标识ID列，根据匹配状态显示不同颜色 -->
                <template v-else-if="column === '通行标识ID'" #default="{ row }">
                  <!-- 动态判断匹配状态 -->
                  <span v-if="isIdMatched(row[column])" style="color: #67c23a">{{
                    row[column]
                  }}</span>
                  <span v-else style="color: #f56c6c">{{ row[column] }}</span>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- 匹配和导入进度 -->
          <div
            v-else-if="importStep === 'matching' || importStep === 'importing'"
            class="import-progress-container"
          >
            <!-- 加载动画 -->
            <div class="loading-animation" style="margin-bottom: 20px; text-align: center">
              <div style="display: inline-block; position: relative; width: 40px; height: 40px">
                <div
                  style="
                    position: absolute;
                    width: 100%;
                    height: 100%;
                    border-radius: 50%;
                    border: 3px solid #ecf5ff;
                    border-top-color: #409eff;
                    animation: spin 1s linear infinite;
                  "
                ></div>
                <div
                  style="
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    width: 24px;
                    height: 24px;
                    border-radius: 50%;
                    border: 3px solid #ecf5ff;
                    border-top-color: #69c0ff;
                    animation: spin 1.5s linear infinite;
                  "
                ></div>
              </div>
            </div>

            <!-- 进度条 -->
            <div style="margin-bottom: 20px">
              <el-progress
                :percentage="importProgress"
                :status="importProgress === 100 ? 'success' : ''"
                :stroke-width="15"
                :show-text="false"
              />
              <div
                style="
                  margin-top: 15px;
                  text-align: center;
                  color: #409eff;
                  font-size: 16px;
                  font-weight: 500;
                "
              >
                {{ importProgressText }}
              </div>
              <div style="margin-top: 5px; text-align: center; color: #606266; font-size: 14px">
                {{ importProgress }}%
              </div>
            </div>

            <!-- 匹配结果 -->
            <div
              v-if="importResult.length > 0 && importStep === 'importing'"
              class="match-result-container"
            >
              <el-alert
                :title="`匹配结果`"
                type="info"
                :description="`共匹配到 ${importResult.length} 条数据`"
                show-icon
                :closable="false"
                style="margin-bottom: 20px"
              />
              <el-table :data="importResult" style="width: 100%" border max-height="400">
                <el-table-column prop="通行标识ID" label="通行标识ID" width="300" />
                <el-table-column label="匹配状态" width="100">
                  <template #default="{ row }">
                    <el-tag type="success">{{ row.匹配状态 }}</el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>

          <!-- 无数据提示 -->
          <div v-else-if="importData.length === 0" class="no-data"> 没有读取到数据 </div>
        </div>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="handleImportCancel">取消</el-button>
            <el-button
              v-if="importStep === 'preview'"
              type="primary"
              @click="startImport"
              :disabled="importData.length === 0"
            >
              开始导入
            </el-button>
            <el-button
              v-else-if="importStep === 'importing'"
              type="primary"
              @click="importPreviewVisible = false"
              :disabled="importLoading"
            >
              完成
            </el-button>
          </span>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import * as XLSX from 'xlsx'
import JSZip from 'jszip'
import { XMLParser } from 'fast-xml-parser'
import {
  ElMessage,
  ElCard,
  ElForm,
  ElFormItem,
  ElSelect,
  ElOption,
  ElButton,
  ElAlert,
  ElDialog,
  ElTable,
  ElTableColumn,
  ElPagination,
  ElDescriptions,
  ElDescriptionsItem,
  ElInput,
  ElUpload,
  ElImage,
  ElRadio
} from 'element-plus'
import { CopyDocument, Picture } from '@element-plus/icons-vue'
import { getSplitMatchTables, getSplitMatchData, executeSplitMatch } from '@/api/split-match'

interface MatchResult {
  matched_count: number
  unmatched_count: number
  total: number
}

interface TableOption {
  label: string
  value: string
}

const tableList = ref<TableOption[]>([])
const selectedTable = ref('')
const tableData = ref<Record<string, unknown>[]>([])
const displayColumns = ref<string[]>([])
const tableLoading = ref(false)
const matchLoading = ref(false)
const matchResult = ref<MatchResult | null>(null)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const selectedRow = ref<Record<string, unknown> | null>(null)
const dialogVisible = ref(false)
const editedRow = ref<Record<string, any> | null>(null)

// 图片预览列表
const imagePreviewList = ref<Record<string, string[]>>({})
// 存储图片的二进制数据，用于上传到后端
const imageBinaryData = ref<Record<string, Blob>>({})
const activeImageField = ref<string>('查核资料1')

// 导入数据相关状态
const importData = ref<any[]>([])
const importPreviewVisible = ref(false)
const importLoading = ref(false)
const importResult = ref<any[]>([])
const importError = ref('')
const importProgress = ref(0)
const importProgressText = ref('')
const importStep = ref('preview') // preview, matching, importing
const importTotalCount = ref(0)
const uploadProgress = ref(0)
const uploadProgressText = ref('')
const uploadLoading = ref(false)
const extractedImagesCount = ref(0)

// 最近输入的通行标识ID列表，最多保留10条
const loadRecentCheckIds = (): string[] => {
  // 从本地存储加载最近十条记录
  const saved = localStorage.getItem('recentCheckIds')
  try {
    const parsed = saved ? JSON.parse(saved) : []
    return Array.isArray(parsed) ? parsed : []
  } catch (error) {
    console.error('解析 recentCheckIds 失败:', error)
    return []
  }
}

const recentCheckIds = ref<string[]>(loadRecentCheckIds())

const filters = ref({
  通行标识ID: '',
  车牌号码: '',
  核查通行标识: '',
  复核情况: '',
  备注: '',
  收费车型: '',
  特情: '',
  核查拆分: ''
})

const checkSplitOptions = ref<string[]>([])

const loadTableList = async () => {
  try {
    console.log('开始获取表列表...')
    const response = await getSplitMatchTables()
    console.log('获取表列表结果:', response)

    if (response && Array.isArray(response.data)) {
      tableList.value = response.data.map((tableName: string) => {
        const label = tableName.replace('_yc', '')
        return {
          label,
          value: tableName
        }
      })
      console.log('处理后的tableList:', tableList.value)
    } else {
      tableList.value = []
      console.log('data为空，tableList设置为空数组')
    }
  } catch (error) {
    console.error('获取表列表失败:', error)
    ElMessage.error('获取表列表失败')
  }
}

const loadTableData = async () => {
  if (!selectedTable.value) {
    tableData.value = []
    displayColumns.value = []
    total.value = 0
    return
  }

  tableLoading.value = true
  try {
    console.log('开始获取表数据，表名:', selectedTable.value)
    console.log('筛选条件:', filters.value)
    const response = await getSplitMatchData({
      table_name: selectedTable.value,
      filters: JSON.stringify(filters.value),
      page: currentPage.value,
      page_size: pageSize.value
    })
    console.log('获取表数据结果:', response)

    let tableDataArray: any[] = []
    let columnsArray: string[] = []
    let totalCount = 0

    if (response && typeof response === 'object') {
      if (response.code === 200 && response.data) {
        tableDataArray = Array.isArray(response.data.data) ? response.data.data : []
        columnsArray = Array.isArray((response.data as any).columns)
          ? (response.data as any).columns
          : []
        totalCount =
          typeof (response.data as any).total === 'number' ? (response.data as any).total : 0
      } else {
        tableDataArray = Array.isArray(response.data) ? response.data : []
        columnsArray = Array.isArray((response as any).columns) ? (response as any).columns : []
        totalCount = typeof (response as any).total === 'number' ? (response as any).total : 0
      }
    }

    tableData.value = tableDataArray
    displayColumns.value = columnsArray
    total.value = totalCount
    matchResult.value = null
    console.log('获取到的表数据:', tableDataArray)
    console.log('获取到的列名:', displayColumns.value)
    console.log('数据总量:', total.value)

    // 处理图片字段，转换为 data URL 格式
    const processedData = tableDataArray.map((row: any) => {
      const processedRow: any = { ...row }
      // 处理查核资料1和查核资料2字段，转换为 data URL
      if (processedRow['查核资料1'] && typeof processedRow['查核资料1'] === 'string') {
        const imageData = processedRow['查核资料1']
        if (!imageData.startsWith('data:') && !imageData.startsWith('blob:')) {
          // 如果是纯 Base64 字符串，转换为 data URL
          processedRow['查核资料1'] = `data:image/webp;base64,${imageData}`
        }
      }
      if (processedRow['查核资料2'] && typeof processedRow['查核资料2'] === 'string') {
        const imageData = processedRow['查核资料2']
        if (!imageData.startsWith('data:') && !imageData.startsWith('blob:')) {
          // 如果是纯 Base64 字符串，转换为 data URL
          processedRow['查核资料2'] = `data:image/webp;base64,${imageData}`
        }
      }
      return processedRow
    })

    tableData.value = processedData

    // 提取核查拆分字段的唯一值，用于填充下拉选择框
    const splitValues = new Set<string>()
    processedData.forEach((row) => {
      const value = row['核查拆分']
      if (value && typeof value === 'string') {
        splitValues.add(value)
      }
    })

    // 确保至少包含'已拆'和'未拆'选项
    splitValues.add('已拆')
    splitValues.add('未拆')

    checkSplitOptions.value = Array.from(splitValues)
    console.log('核查拆分选项:', checkSplitOptions.value)
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
  console.log('选中的表:', selectedTable.value)
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
    console.log('开始执行匹配，表名:', selectedTable.value)
    const response = await executeSplitMatch({ table_name: selectedTable.value })
    console.log('执行匹配结果:', response)
    if (response && typeof response === 'object') {
      matchResult.value = response as unknown as MatchResult
      ElMessage.success('匹配完成')
      loadTableData()
    } else {
      ElMessage.error('执行匹配失败')
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

const handleIdClick = (row: Record<string, unknown>) => {
  selectedRow.value = row
  // 创建浅拷贝用于编辑，避免 JSON.stringify 导致 blob URL 失效
  editedRow.value = { ...row }

  // 初始化图片预览列表
  imagePreviewList.value = {
    查核资料1: editedRow.value['查核资料1'] ? [String(editedRow.value['查核资料1'])] : [],
    查核资料2: editedRow.value['查核资料2'] ? [String(editedRow.value['查核资料2'])] : []
  }

  dialogVisible.value = true

  // 添加粘贴事件监听
  setTimeout(() => {
    const dialogEl = document.querySelector('.el-dialog')
    if (dialogEl) {
      dialogEl.addEventListener('paste', handlePaste)
    }
  }, 100)
}

// 将图片转换为 WebP 格式的函数
const convertToWebP = (file: File): Promise<Blob> => {
  return new Promise((resolve, reject) => {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    const img = new Image()

    img.onload = () => {
      // 设置 canvas 尺寸与图片一致
      canvas.width = img.width
      canvas.height = img.height

      // 绘制图片到 canvas
      ctx?.drawImage(img, 0, 0)

      // 将 canvas 转换为 WebP 格式的 Blob
      canvas.toBlob(
        (blob) => {
          if (blob) {
            resolve(blob)
          } else {
            reject(new Error('无法转换图片为 WebP 格式'))
          }
        },
        'image/webp',
        0.8 // 质量参数，0-1 之间
      )
    }

    img.onerror = () => {
      reject(new Error('图片加载失败'))
    }

    // 加载图片
    img.src = URL.createObjectURL(file)
  })
}

const handleImageUpload = async (file: any, field: string) => {
  if (!file.raw) return

  try {
    // 将图片转换为 WebP 格式
    const webpBlob = await convertToWebP(file.raw)

    // 将 Blob 转换为 Base64 字符串
    const arrayBuffer = await webpBlob.arrayBuffer()
    const base64String = btoa(
      new Uint8Array(arrayBuffer).reduce((data, byte) => data + String.fromCharCode(byte), '')
    )

    // 创建 data URL 用于预览显示
    const dataUrl = `data:image/webp;base64,${base64String}`

    // 存储 dataUrl 用于预览显示
    editedRow.value![field] = dataUrl
    // 存储 Base64 字符串，用于上传到后端
    imageBinaryData.value[field] = webpBlob
    // 更新图片预览列表
    imagePreviewList.value[field] = [dataUrl]
    ElMessage.success('图片上传成功并转换为 WebP 格式')
  } catch (error) {
    console.error('图片转换失败:', error)
    ElMessage.error('图片转换失败')
  }
}

const handlePaste = (event: ClipboardEvent) => {
  const items = event.clipboardData?.items
  if (!items) return

  // 检查是否有图片数据
  let hasImage = false
  for (let i = 0; i < items.length; i++) {
    if (items[i].type.indexOf('image') === 0) {
      const file = items[i].getAsFile()
      if (file) {
        // 上传到当前激活的图片字段
        handleImageUpload({ raw: file }, activeImageField.value)
        hasImage = true
        break
      }
    }
  }

  // 如果有图片数据，阻止默认粘贴行为
  if (hasImage) {
    event.preventDefault()
  }
}

const handleDialogClose = () => {
  // 移除粘贴事件监听
  const dialogEl = document.querySelector('.el-dialog')
  if (dialogEl) {
    dialogEl.removeEventListener('paste', handlePaste)
  }

  // 清空二进制数据存储
  imageBinaryData.value = {}

  dialogVisible.value = false
}

const handleImageDelete = (field: string) => {
  // 清空图片数据
  editedRow.value![field] = ''
  // 清空二进制数据存储
  delete imageBinaryData.value[field]
  // 清空预览列表
  imagePreviewList.value[field] = []
  // 显示删除成功消息
  ElMessage.success('图片已删除')
}

const handleFilter = () => {
  // 保存最近输入的通行标识ID，最多保留10条
  const checkId = filters.value['通行标识ID']
  if (checkId) {
    // 确保 recentCheckIds.value 是数组
    if (!Array.isArray(recentCheckIds.value)) {
      recentCheckIds.value = []
    }
    // 移除重复项
    recentCheckIds.value = recentCheckIds.value.filter((id) => id !== checkId)
    // 添加到列表开头
    recentCheckIds.value.unshift(checkId)
    // 最多保留10条
    if (recentCheckIds.value.length > 10) {
      recentCheckIds.value = recentCheckIds.value.slice(0, 10)
    }
    // 保存到本地存储
    localStorage.setItem('recentCheckIds', JSON.stringify(recentCheckIds.value))
  }

  // 重置页码，从第一页开始显示筛选结果
  currentPage.value = 1
  // 重新加载数据，应用筛选条件
  loadTableData()
}

const handleCheckIdInput = (value: string) => {
  if (!editedRow.value) return

  // 删除数据前后的空格
  const trimmedValue = value.trim()

  // 禁止输入符号，只允许字母、数字和下划线
  const sanitizedValue = trimmedValue.replace(/[^a-zA-Z0-9_]/g, '')

  // 更新值
  editedRow.value['核查通行标识'] = sanitizedValue
}

const handleCopy = (text: string) => {
  if (!text) {
    ElMessage.warning('没有内容可复制')
    return
  }

  try {
    navigator.clipboard
      .writeText(text)
      .then(() => {
        ElMessage.success('复制成功')
      })
      .catch(() => {
        // 如果 clipboard API 失败，使用传统方法
        const textarea = document.createElement('textarea')
        textarea.value = text
        textarea.style.position = 'fixed'
        textarea.style.opacity = '0'
        document.body.appendChild(textarea)
        textarea.select()
        document.execCommand('copy')
        document.body.removeChild(textarea)
        ElMessage.success('复制成功')
      })
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败')
  }
}

const handleResetFilter = () => {
  // 清空所有筛选条件
  filters.value = {
    通行标识ID: '',
    车牌号码: '',
    核查通行标识: '',
    复核情况: '',
    备注: '',
    收费车型: '',
    特情: '',
    核查拆分: ''
  }
  // 重置页码
  currentPage.value = 1
  // 重新加载数据
  loadTableData()
}

const handleExport = () => {
  if (!selectedTable.value || tableData.value.length === 0) {
    ElMessage.warning('没有数据可导出')
    return
  }

  try {
    // 获取表头
    const headers = Object.keys(tableData.value[0] || {})

    // 构建CSV内容
    let csvContent = headers.join(',') + '\n'

    // 添加数据行
    tableData.value.forEach((row) => {
      const rowData = headers.map((header) => {
        const value = row[header]
        // 处理包含逗号或引号的值
        if (
          typeof value === 'string' &&
          (value.includes(',') || value.includes('"') || value.includes('\n'))
        ) {
          return '"' + value.replace(/"/g, '""') + '"'
        }
        return value === null || value === undefined ? '' : value
      })
      csvContent += rowData.join(',') + '\n'
    })

    // 创建Blob对象
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })

    // 创建下载链接
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)

    // 设置文件名
    const fileName = `${selectedTable.value}_${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.csv`

    // 触发下载
    link.setAttribute('href', url)
    link.setAttribute('download', fileName)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    ElMessage.success('数据导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('数据导出失败')
  }
}

const isAlphaNumericUnderscore = (char: string): boolean => {
  const code = char.charCodeAt(0)
  return (
    (code >= 65 && code <= 90) ||
    (code >= 97 && code <= 122) ||
    (code >= 48 && code <= 57) ||
    code === 95
  )
}

const cleanIdValue = (value: string): string => {
  let cleaned = value.trim()
  while (cleaned.length > 0 && !isAlphaNumericUnderscore(cleaned[0])) {
    cleaned = cleaned.substring(1)
  }
  while (cleaned.length > 0 && !isAlphaNumericUnderscore(cleaned[cleaned.length - 1])) {
    cleaned = cleaned.substring(0, cleaned.length - 1)
  }
  let result = ''
  for (let j = 0; j < cleaned.length; j++) {
    const charCode = cleaned.charCodeAt(j)
    if (charCode !== 10 && charCode !== 13) {
      result += cleaned[j]
    }
  }
  return result
}

const processDataRow = (row: any, index: number): any => {
  const processedRow: any = {}

  for (const key in row) {
    if (Object.prototype.hasOwnProperty.call(row, key)) {
      processedRow[key] = row[key]
    }
  }

  const excelRowNumber = index + 1
  processedRow['_excelRowNumber'] = excelRowNumber
  processedRow['序号'] = excelRowNumber

  if (processedRow['通行标识ID'] !== undefined) {
    try {
      processedRow['通行标识ID'] = cleanIdValue(String(processedRow['通行标识ID']))
    } catch (e) {
      processedRow['通行标识ID'] = ''
    }
  }

  if (processedRow['核查通行标识'] !== undefined) {
    try {
      processedRow['核查通行标识'] = cleanIdValue(String(processedRow['核查通行标识']))
    } catch (e) {
      processedRow['核查通行标识'] = ''
    }
  }

  processedRow['查核资料1'] = null
  processedRow['查核资料2'] = null

  return processedRow
}

const detectExcelFormat = async (
  binaryData: string
): Promise<'drawings' | 'cellimages' | 'no_image'> => {
  console.log('========== 开始检测Excel格式 ==========')
  try {
    const zip = new JSZip()
    const workbook = await zip.loadAsync(binaryData)
    const filePaths = Object.keys(workbook.files)
    console.log('ZIP内所有文件数:', filePaths.length)

    const hasCellImages = filePaths.some((path) => path === 'xl/cellimages.xml')
    const hasCellImagesRels = filePaths.some((path) => path === 'xl/_rels/cellimages.xml.rels')
    const hasDrawings = filePaths.some((path) => path === 'xl/drawings/drawing1.xml')
    const hasDrawingsRels = filePaths.some((path) => path === 'xl/drawings/_rels/drawing1.xml.rels')

    console.log(`检测到 cellimages.xml: ${hasCellImages}`)
    console.log(`检测到 cellimages.xml.rels: ${hasCellImagesRels}`)
    console.log(`检测到 drawing1.xml: ${hasDrawings}`)
    console.log(`检测到 drawing1.xml.rels: ${hasDrawingsRels}`)

    if (!hasCellImages && !hasDrawings) {
      console.log('========== 检测结果: 无图片 ==========')
      return 'no_image'
    }

    console.log('\n========== 开始统计XML文件节点数 ==========')
    const nodeCounts: Record<string, number> = {}

    if (hasCellImages) {
      const cellImagesFile = workbook.file('xl/cellimages.xml')
      if (cellImagesFile) {
        const content = await cellImagesFile.async('text')
        const count = countXMLNodes(content)
        nodeCounts['cellimages.xml'] = count
        console.log(`cellimages.xml 节点数: ${count}`)
      }
    }

    if (hasCellImagesRels) {
      const cellImagesRelsFile = workbook.file('xl/_rels/cellimages.xml.rels')
      if (cellImagesRelsFile) {
        const content = await cellImagesRelsFile.async('text')
        const count = countXMLNodes(content)
        nodeCounts['cellimages.xml.rels'] = count
        console.log(`cellimages.xml.rels 节点数: ${count}`)
      }
    }

    if (hasDrawings) {
      const drawingFile = workbook.file('xl/drawings/drawing1.xml')
      if (drawingFile) {
        const content = await drawingFile.async('text')
        const count = countXMLNodes(content)
        nodeCounts['drawing1.xml'] = count
        console.log(`drawing1.xml 节点数: ${count}`)
      }
    }

    if (hasDrawingsRels) {
      const drawingRelsFile = workbook.file('xl/drawings/_rels/drawing1.xml.rels')
      if (drawingRelsFile) {
        const content = await drawingRelsFile.async('text')
        const count = countXMLNodes(content)
        nodeCounts['drawing1.xml.rels'] = count
        console.log(`drawing1.xml.rels 节点数: ${count}`)
      }
    }

    console.log('\n--- 节点数统计结果 ---')
    for (const [fileName, count] of Object.entries(nodeCounts)) {
      console.log(`  ${fileName}: ${count} 个节点`)
    }

    console.log('\n--- 选择节点数量最多的文件作为目标 ---')
    let maxNodes = 0
    let targetFormat: 'drawings' | 'cellimages' = 'drawings'

    if (hasCellImages && hasCellImagesRels) {
      const cellImagesNodes =
        (nodeCounts['cellimages.xml'] || 0) + (nodeCounts['cellimages.xml.rels'] || 0)
      console.log(`cellimages型总节点数: ${cellImagesNodes}`)
      if (cellImagesNodes > maxNodes) {
        maxNodes = cellImagesNodes
        targetFormat = 'cellimages'
      }
    }

    if (hasDrawings && hasDrawingsRels) {
      const drawingNodes =
        (nodeCounts['drawing1.xml'] || 0) + (nodeCounts['drawing1.xml.rels'] || 0)
      console.log(`drawings型总节点数: ${drawingNodes}`)
      if (drawingNodes > maxNodes) {
        maxNodes = drawingNodes
        targetFormat = 'drawings'
      }
    }

    console.log(`========== 检测结果: ${targetFormat} (节点数: ${maxNodes}) ==========`)
    return targetFormat
  } catch (e) {
    console.error('检测Excel格式失败:', e)
    return 'no_image'
  }
}

const countXMLNodes = (xmlContent: string): number => {
  let count = 0

  const parser = new XMLParser({
    ignoreAttributes: false,
    attributeNamePrefix: '',
    textNodeName: '#text',
    parseAttributeValue: true,
    trimValues: true
  })

  try {
    const parsed = parser.parse(xmlContent)

    const countNodes = (obj: any): number => {
      if (!obj || typeof obj !== 'object') {
        return 0
      }

      let nodeCount = 1

      for (const key in obj) {
        if (Object.prototype.hasOwnProperty.call(obj, key)) {
          const value = obj[key]

          if (key === '#text') {
            continue
          }

          if (Array.isArray(value)) {
            for (const item of value) {
              nodeCount += countNodes(item)
            }
          } else if (typeof value === 'object' && value !== null) {
            nodeCount += countNodes(value)
          }
        }
      }

      return nodeCount
    }

    count = countNodes(parsed)
    console.log(`  元素节点: ${count} 个`)

    return count
  } catch (e) {
    console.error('统计XML节点失败:', e)
    return 0
  }
}

const extractImagesFromExcel = async (
  binaryData: string
): Promise<{ mediaFiles: Record<string, string>; count: number }> => {
  console.log('========== 开始提取图片 ==========')
  const mediaFiles: Record<string, string> = {}
  let count = 0

  try {
    const zip = new JSZip()
    const workbook = await zip.loadAsync(binaryData)
    console.log('ZIP文件加载成功，文件列表:', Object.keys(workbook.files).slice(0, 20))

    const allFilePaths = Object.keys(workbook.files)
    const mediaFilePaths = allFilePaths.filter(
      (path) => path.startsWith('xl/media/') && !path.endsWith('/')
    )
    console.log(`找到xl/media目录下 ${mediaFilePaths.length} 个文件`)

    const mediaPromises: Promise<void>[] = []

    for (const filePath of mediaFilePaths) {
      const file = workbook.file(filePath)
      if (file && !file.dir) {
        const promise = file
          .async('base64')
          .then((content) => {
            const extension = filePath.split('.').pop() || 'png'
            mediaFiles[filePath] = `data:image/${extension};base64,${content}`
            count++
            console.log(
              `图片提取成功 [${count}]: ${filePath}, 大小: ${content.length} 字符, 格式: ${extension}`
            )
          })
          .catch((e) => {
            console.warn('处理图片文件失败:', filePath, e)
          })
        mediaPromises.push(promise)
      }
    }

    await Promise.all(mediaPromises)
    console.log(`========== 图片提取完成，共提取 ${count} 张图片 ==========`)
  } catch (e) {
    console.error('提取图片失败:', e)
  }

  return { mediaFiles, count }
}

const xmlParser = new XMLParser({
  ignoreAttributes: false,
  attributeNamePrefix: '',
  textNodeName: '#text',
  parseAttributeValue: true,
  trimValues: true
})

const cellImagesXmlParser = new XMLParser({
  ignoreAttributes: false,
  attributeNamePrefix: '',
  textNodeName: '#text',
  parseAttributeValue: true,
  trimValues: true,
  removeNSPrefix: false,
  isArray: (name, jpath, isLeafNode, isAttribute) => {
    // 处理带命名空间的节点
    if (name === 'cellImage' || name === 'etc:cellImage' || name === 'Relationship') {
      return true
    }
    return false
  }
})

const buildCellImagesMappingsWithSheet1 = async (
  binaryData: string
): Promise<{
  relMap: Record<string, string>
  cellImageMap: Record<string, { cell: string; imageId: string; imageName: string }>
  sheet1XmlData: Record<string, string>
}> => {
  console.log('========== 开始构建cellimages型图片映射（含sheet1.xml） ==========')
  const relMap: Record<string, string> = {}
  const cellImageMap: Record<string, { cell: string; imageId: string; imageName: string }> = {}
  const sheet1XmlData: Record<string, string> = {}

  try {
    const zip = new JSZip()
    const workbook = await zip.loadAsync(binaryData)

    const filePaths = Object.keys(workbook.files)
    console.log('ZIP内所有文件数:', filePaths.length)

    console.log('\n--- 步骤1: 解析cellimages.xml.rels ---')
    const cellImagesRelsPath = 'xl/_rels/cellimages.xml.rels'
    const cellImagesRelsFile = workbook.file(cellImagesRelsPath)

    if (cellImagesRelsFile) {
      try {
        const relsContent = await cellImagesRelsFile.async('text')
        console.log(`解析cellimages.xml.rels, 长度: ${relsContent.length}`)

        const relsXml = xmlParser.parse(relsContent)
        const relationships = relsXml.Relationships?.Relationship
        if (!relationships) {
          console.warn('  未找到Relationship节点')
          return { relMap, cellImageMap, sheet1XmlData }
        }

        const relArray = Array.isArray(relationships) ? relationships : [relationships]
        console.log(`  找到 ${relArray.length} 个Relationship节点`)

        let foundRels = 0
        for (const rel of relArray) {
          const id = rel.Id
          const target = rel.Target

          if (id && target) {
            let fileName = target
            if (fileName.startsWith('../')) {
              fileName = fileName.substring(3)
            }
            if (!fileName.startsWith('xl/')) {
              fileName = 'xl/' + fileName
            }
            relMap[id] = fileName
            foundRels++
            if (foundRels <= 5) {
              console.log(`  Rels映射 [${foundRels}]: Id="${id}" -> 文件名="${fileName}"`)
            }
          }
        }

        console.log(`  从 cellimages.xml.rels 解析出 ${foundRels} 个关系映射`)
      } catch (e) {
        console.warn('读取cellimages.xml.rels失败:', e)
      }
    }

    console.log('\n--- 步骤2: 解析cellimages.xml ---')
    const cellImagesPath = 'xl/cellimages.xml'
    const cellImagesFile = workbook.file(cellImagesPath)

    if (cellImagesFile) {
      try {
        const cellImagesContent = await cellImagesFile.async('text')
        console.log(`解析cellimages.xml, 长度: ${cellImagesContent.length}`)
        console.log('cellimages.xml内容前200字符:', cellImagesContent.substring(0, 200))

        const cellImagesXml = cellImagesXmlParser.parse(cellImagesContent)
        console.log('  cellImagesXml根节点键:', Object.keys(cellImagesXml))
        console.log('  cellImagesXml完整结构:', JSON.stringify(cellImagesXml, null, 2))

        const etcCellImages = cellImagesXml['etc:cellImages']
        console.log('  etc:cellImages节点:', etcCellImages)
        console.log('  etc:cellImages类型:', typeof etcCellImages)
        console.log('  etc:cellImages键:', etcCellImages ? Object.keys(etcCellImages) : 'null')

        const cellImages = etcCellImages?.cellImage || etcCellImages?.['etc:cellImage']

        if (!cellImages) {
          console.warn('  未找到cellImage节点')
          console.warn('  尝试查找可能的替代节点键...')
          const possibleKeys = Object.keys(cellImagesXml).filter(
            (key) =>
              key.toLowerCase().includes('cell') ||
              key.toLowerCase().includes('image') ||
              key.toLowerCase().includes('img')
          )
          console.warn('  可能的节点键:', possibleKeys)

          if (etcCellImages) {
            const etcKeys = Object.keys(etcCellImages)
            console.warn('  etc:cellImages的子节点键:', etcKeys)
          }

          return { relMap, cellImageMap, sheet1XmlData }
        }

        const cellImageArray = Array.isArray(cellImages) ? cellImages : [cellImages]
        console.log(`  找到 ${cellImageArray.length} 个cellImage节点`)

        let foundImages = 0
        for (const cellImage of cellImageArray) {
          const pic = cellImage['xdr:pic']

          if (!pic) {
            console.warn('  cellImage缺少xdr:pic节点')
            continue
          }

          const nvPicPr = pic['xdr:nvPicPr']
          const cNvPr = nvPicPr?.['xdr:cNvPr']

          if (!cNvPr) {
            console.warn('  xdr:pic缺少xdr:cNvPr节点')
            continue
          }

          const imageId = cNvPr.id
          const imageName = cNvPr.name

          const blipFill = pic['xdr:blipFill']
          const blip = blipFill?.['a:blip']

          if (!blip) {
            console.warn('  xdr:pic缺少xdr:blipFill.a:blip节点')
            continue
          }

          const relationshipId = blip['r:embed']

          console.log(`  处理cellImage节点: imageId="${imageId}", imageName="${imageName}"`)
          console.log(`    提取到的r:embed: "${relationshipId}"`)

          if (relationshipId) {
            cellImageMap[relationshipId] = {
              cell: '',
              imageId: imageId || '',
              imageName: imageName || ''
            }
            foundImages++
            if (foundImages <= 5) {
              console.log(
                `  CellImage映射 [${foundImages}]: r:embed="${relationshipId}" -> imageId="${imageId}", name="${imageName}"`
              )
            }
          } else {
            console.warn(`    警告: r:embed属性为空`)
          }
        }

        console.log(`  从 cellimages.xml 解析出 ${foundImages} 个图片位置映射`)
      } catch (e) {
        console.error('读取cellimages.xml失败:', e)
        console.error('错误堆栈:', e.stack)
        return { relMap, cellImageMap, sheet1XmlData }
      }
    } else {
      console.warn('cellimages.xml文件不存在')
    }

    console.log('\n--- 步骤3: 解析sheet1.xml以提取DISPIMG函数单元格 ---')
    const sheet1Path = 'xl/worksheets/sheet1.xml'
    const sheet1File = workbook.file(sheet1Path)

    if (sheet1File) {
      try {
        const sheet1Content = await sheet1File.async('text')
        console.log(`解析sheet1.xml, 长度: ${sheet1Content.length}`)

        // 使用DOMParser解析XML，参照文档方案
        const domParser = new DOMParser()
        const xmlDoc = domParser.parseFromString(sheet1Content, 'text/xml')
        console.log('  DOMParser解析完成')

        // 遍历所有单元格节点（<c>）
        const cellNodes = xmlDoc.getElementsByTagName('c')
        console.log(`  找到 ${cellNodes.length} 个单元格节点`)

        let dispimgCount = 0
        for (let i = 0; i < cellNodes.length; i++) {
          const cellNode = cellNodes[i]
          // 提取单元格坐标属性（如r="G3"）
          const cellRef = cellNode.getAttribute('r')
          if (!cellRef) continue

          // 查找当前单元格下的公式节点（<f>）
          const formulaNodes = cellNode.getElementsByTagName('f')
          if (formulaNodes.length === 0) continue

          // 获取公式文本并处理转义符（&quot; → "）
          const formulaText = formulaNodes[0].textContent || ''
          const cleanFormula = formulaText.replace(/&quot;/g, '"')
          console.log(`  单元格${cellRef}的公式: ${cleanFormula}`)

          // 精准匹配目标图片ID（ID_+32位十六进制）
          const imageIdRegex = /ID_[0-9A-Fa-f]{32}/i
          const match = cleanFormula.match(imageIdRegex)
          if (match) {
            const imageName = match[0]
            sheet1XmlData[imageName] = cellRef
            dispimgCount++
            if (dispimgCount <= 5) {
              console.log(
                `  DISPIMG单元格 [${dispimgCount}]: imageName="${imageName}" -> cell="${cellRef}"`
              )
            }
          }
        }

        console.log(`  从 sheet1.xml 解析出 ${dispimgCount} 个DISPIMG单元格`)
      } catch (e) {
        console.error('读取sheet1.xml失败:', e)
        console.error('错误堆栈:', e.stack)
      }
    } else {
      console.warn('sheet1.xml文件不存在')
    }

    console.log('\n========== cellimages型图片映射构建完成 ==========')
    console.log(`relMap条数: ${Object.keys(relMap).length}`)
    console.log(`cellImageMap条数: ${Object.keys(cellImageMap).length}`)
    console.log(`sheet1XmlData条数: ${Object.keys(sheet1XmlData).length}`)

    return { relMap, cellImageMap, sheet1XmlData }
  } catch (e) {
    console.error('构建cellimages型图片映射失败:', e)
    return { relMap, cellImageMap, sheet1XmlData }
  }
}

const buildImageMappings = async (
  binaryData: string
): Promise<{
  relMap: Record<string, string>
  drawingMap: Record<string, { row: number; col: number; imageId: string }>
}> => {
  console.log('========== 开始构建图片映射(fast-xml-parser) ==========')
  const relMap: Record<string, string> = {}
  const drawingMap: Record<string, { row: number; col: number; imageId: string }> = {}

  try {
    const zip = new JSZip()
    const workbook = await zip.loadAsync(binaryData)

    const filePaths = Object.keys(workbook.files)
    console.log('ZIP内所有文件数:', filePaths.length)

    const drawingFiles: string[] = []
    const relsFiles: string[] = []

    for (const filePath of filePaths) {
      if (filePath.includes('drawings/')) {
        if (filePath.endsWith('.xml') && !filePath.endsWith('.rels')) {
          drawingFiles.push(filePath)
        } else if (filePath.endsWith('.xml.rels')) {
          relsFiles.push(filePath)
        }
      }
    }

    console.log(`找到drawing文件: ${drawingFiles.length} 个`, drawingFiles)
    console.log(`找到rels文件: ${relsFiles.length} 个`, relsFiles)

    console.log('\n--- 步骤1: 解析rels文件 ---')
    for (const relsPath of relsFiles) {
      const relsFile = workbook.file(relsPath)
      if (relsFile) {
        try {
          const relsContent = await relsFile.async('text')
          console.log(`解析rels文件: ${relsPath}, 长度: ${relsContent.length}`)

          const relsXml = xmlParser.parse(relsContent)
          const relationships = relsXml.Relationships?.Relationship
          if (!relationships) {
            console.warn('  未找到Relationship节点')
            continue
          }

          const relArray = Array.isArray(relationships) ? relationships : [relationships]
          console.log(`  找到 ${relArray.length} 个Relationship节点`)

          let foundRels = 0
          for (const rel of relArray) {
            const id = rel.Id
            const target = rel.Target

            if (id && target) {
              let fileName = target
              if (fileName.startsWith('../')) {
                fileName = fileName.substring(3)
              }
              if (!fileName.startsWith('xl/')) {
                fileName = 'xl/' + fileName
              }
              relMap[id] = fileName
              foundRels++
              if (foundRels <= 5) {
                console.log(`  Rels映射 [${foundRels}]: Id="${id}" -> 文件名="${fileName}"`)
              }
            }
          }

          console.log(`  从 ${relsPath} 解析出 ${foundRels} 个关系映射`)
        } catch (e) {
          console.warn('读取rels文件失败:', relsPath, e)
        }
      }
    }

    console.log('\n--- 步骤2: 解析drawing文件 ---')
    for (const drawingPath of drawingFiles) {
      const drawingFile = workbook.file(drawingPath)
      if (drawingFile) {
        try {
          const drawingContent = await drawingFile.async('text')
          console.log(`解析drawing文件: ${drawingPath}, 长度: ${drawingContent.length}`)

          const drawingXml = xmlParser.parse(drawingContent)
          console.log('  drawingXml根节点键:', Object.keys(drawingXml))

          const wsDr = drawingXml['xdr:wsDr'] || drawingXml
          if (!wsDr) {
            console.warn('  未找到wsDr节点')
            continue
          }
          console.log('  wsDr节点键:', Object.keys(wsDr))

          let twoCellAnchors = wsDr['xdr:twoCellAnchor']
          let oneCellAnchors = wsDr['xdr:oneCellAnchor']

          if (twoCellAnchors && !Array.isArray(twoCellAnchors)) {
            twoCellAnchors = [twoCellAnchors]
          }
          if (oneCellAnchors && !Array.isArray(oneCellAnchors)) {
            oneCellAnchors = [oneCellAnchors]
          }

          console.log(
            `  找到 twoCellAnchor: ${twoCellAnchors?.length || 0} 个, oneCellAnchor: ${oneCellAnchors?.length || 0} 个`
          )

          if (twoCellAnchors && twoCellAnchors.length > 0) {
            console.log(
              '  第一个twoCellAnchor内容:',
              JSON.stringify(twoCellAnchors[0], null, 2).substring(0, 2000)
            )
          }

          let foundAnchors = 0

          const processAnchor = (anchor: any) => {
            if (!anchor) return

            const from = anchor['xdr:from']
            if (!from) return

            const rowNode = from['xdr:row']
            const colNode = from['xdr:col']

            const row = parseInt(String(rowNode?.['#text'] ?? rowNode ?? 0)) + 1
            const col = parseInt(String(colNode?.['#text'] ?? colNode ?? 0))

            let relationshipId = ''
            let imageId = ''
            const pic = anchor['xdr:pic']
            if (pic) {
              const nvPicPr = pic['xdr:nvPicPr']
              if (nvPicPr) {
                const cNvPr = nvPicPr['xdr:cNvPr']
                if (cNvPr) {
                  imageId = cNvPr.name || ''
                }
              }
              const blipFill = pic['xdr:blipFill']
              if (blipFill) {
                const blip = blipFill['a:blip']
                if (blip) {
                  relationshipId = blip['r:embed'] || blip.embed || ''
                }
              }
            }

            if (relationshipId && row > 0) {
              drawingMap[relationshipId] = {
                row: row,
                col: col,
                imageId: imageId
              }
              foundAnchors++
              if (foundAnchors <= 5) {
                console.log(
                  `  Drawing映射 [${foundAnchors}]: r:embed="${relationshipId}" -> 行号=${row}, 列号=${col}, 图片ID="${imageId}"`
                )
              }
            }
          }

          if (twoCellAnchors) {
            for (const anchor of twoCellAnchors) {
              processAnchor(anchor)
            }
          }
          if (oneCellAnchors) {
            for (const anchor of oneCellAnchors) {
              processAnchor(anchor)
            }
          }

          console.log(`  从 ${drawingPath} 解析出 ${foundAnchors} 个图片位置映射`)
        } catch (e) {
          console.warn('读取drawing文件失败:', drawingPath, e)
        }
      }
    }

    console.log('\n========== 图片映射构建完成 ==========')
    console.log(`relMap条数: ${Object.keys(relMap).length}`)
    console.log(`drawingMap条数: ${Object.keys(drawingMap).length}`)
    if (Object.keys(relMap).length > 0) {
      const sampleKeys = Object.keys(relMap).slice(0, 3)
      console.log(
        `relMap示例:`,
        sampleKeys.map((k) => `${k}->${relMap[k]}`)
      )
    }
    if (Object.keys(drawingMap).length > 0) {
      const sampleKeys = Object.keys(drawingMap).slice(0, 3)
      console.log(
        `drawingMap示例:`,
        sampleKeys.map((k) => `${k}->${JSON.stringify(drawingMap[k])}`)
      )
    }
  } catch (e) {
    console.error('构建图片映射失败:', e)
  }

  return { relMap, drawingMap }
}

const extractImageNameFromCell = (cellValue: any): string | null => {
  if (!cellValue || typeof cellValue !== 'string') {
    return null
  }

  // 匹配各种形式的DISPIMG函数
  const dispimgMatch = cellValue.match(
    /(?:_xlfn\.)?DISPIMG\s*\(\s*["']([^"']+)["']\s*,\s*\d+\s*\)|=(?:_xlfn\.)?DISPIMG\s*\(\s*["']([^"']+)["']\s*,\s*\d+\s*\)/i
  )

  if (dispimgMatch) {
    // 返回第一个捕获组或第二个捕获组（取决于哪种匹配成功）
    return dispimgMatch[1] || dispimgMatch[2] || null
  }

  return null
}

const parseCellRef = (cellRef: string): { row: number; col: number } | null => {
  const match = cellRef.match(/^([A-Z]+)(\d+)$/)
  if (!match) {
    return null
  }

  const colStr = match[1]
  const rowStr = match[2]

  let col = 0
  for (let i = 0; i < colStr.length; i++) {
    col = col * 26 + (colStr.charCodeAt(i) - 64)
  }

  return {
    row: parseInt(rowStr),
    col: col
  }
}

const buildImageCellMap = (processedData: any[]): Record<string, string> => {
  console.log('========== 开始建立图片名称到单元格的映射 ==========')
  const imageCellMap: Record<string, string> = {}

  for (let i = 0; i < processedData.length; i++) {
    const row = processedData[i]
    for (const [columnName, cellValue] of Object.entries(row)) {
      if (typeof cellValue !== 'string') {
        continue
      }

      const imageName = extractImageNameFromCell(cellValue)

      if (imageName) {
        imageCellMap[imageName] = columnName
        console.log(`  图片 "${imageName}" 关联到单元格 ${columnName}`)
      }
    }
  }

  console.log(`  建立了 ${Object.keys(imageCellMap).length} 个图片-单元格映射`)
  return imageCellMap
}

const associateCellImagesWithRows = (
  processedData: any[],
  mediaFiles: Record<string, string>,
  relMap: Record<string, string>,
  cellImageMap: Record<string, { cell: string; imageId: string; imageName: string }>,
  sheet1XmlData: Record<string, string>
): void => {
  console.log('========== 开始关联cellimages型图片到数据行 ==========')
  console.log(`数据行总数: ${processedData.length}`)
  console.log(`图片文件数: ${Object.keys(mediaFiles).length}`)
  console.log(`关系映射数: ${Object.keys(relMap).length}`)
  console.log(`单元格映射数: ${Object.keys(cellImageMap).length}`)
  console.log(`sheet1XmlData数: ${Object.keys(sheet1XmlData).length}`)

  console.log('\n--- 步骤1: 使用sheet1.xml数据建立图片名称到单元格的映射 ---')
  const imageCellMap: Record<string, string> = {}

  for (const imageName in sheet1XmlData) {
    if (Object.prototype.hasOwnProperty.call(sheet1XmlData, imageName)) {
      const cellRef = sheet1XmlData[imageName]
      imageCellMap[imageName] = cellRef
      console.log(`  图片 "${imageName}" 关联到单元格 ${cellRef}`)
    }
  }

  console.log(`  建立了 ${Object.keys(imageCellMap).length} 个图片-单元格映射`)

  console.log('\n--- 步骤2: 构建图片名称到图片数据的映射 ---')
  const imageNameToDataMap: Record<string, { imageId: string; imageData: string }[]> = {}

  for (const relationshipId in cellImageMap) {
    if (Object.prototype.hasOwnProperty.call(cellImageMap, relationshipId)) {
      const info = cellImageMap[relationshipId]
      const imageName = info.imageName
      const imageId = info.imageId

      const imageFileName = relMap[relationshipId]
      console.log(
        `处理关系ID "${relationshipId}": imageName="${imageName}", imageId="${imageId}", 映射文件名="${imageFileName}"`
      )

      let actualImagePath: string | null = null
      if (imageFileName) {
        if (mediaFiles[imageFileName]) {
          actualImagePath = imageFileName
        } else {
          const mediaFileKeys = Object.keys(mediaFiles)
          const imageNameFromPath = imageFileName.split('/').pop()
          if (imageNameFromPath) {
            actualImagePath = mediaFileKeys.find((key) => key.endsWith(imageNameFromPath)) || null
          }
        }
      }

      if (actualImagePath && mediaFiles[actualImagePath]) {
        if (!imageNameToDataMap[imageName]) {
          imageNameToDataMap[imageName] = []
        }
        imageNameToDataMap[imageName].push({
          imageId: imageId,
          imageData: mediaFiles[actualImagePath]
        })
        console.log(
          `  ✓ 图片名称"${imageName}"添加图片: imageId="${imageId}", 文件="${actualImagePath}"`
        )
      } else {
        console.warn(
          `  ✗ 未找到图片文件: 关系ID="${relationshipId}", 映射文件名="${imageFileName}"`
        )
        console.log(`  可用的图片文件示例:`, Object.keys(mediaFiles).slice(0, 10))
      }
    }
  }

  console.log('\n--- 步骤3: 按图片名称分组结果 ---')
  for (const imageName in imageNameToDataMap) {
    console.log(
      `图片名称${imageName}: ${imageNameToDataMap[imageName].length} 张图片`,
      imageNameToDataMap[imageName].map((img) => img.imageId)
    )
  }

  console.log('\n--- 步骤4: 将图片关联到数据行 ---')
  console.log('说明: 根据DISPIMG函数匹配图片名称到单元格，再根据单元格列位置关联到对应字段')
  console.log('  G列(列号7)图片 -> 查核资料1')
  console.log('  H列(列号8)图片 -> 查核资料2')
  console.log('  imageCellMap键:', Object.keys(imageCellMap).slice(0, 10))
  console.log('  imageNameToDataMap键:', Object.keys(imageNameToDataMap).slice(0, 10))
  let successCount = 0

  for (const imageName in imageNameToDataMap) {
    if (Object.prototype.hasOwnProperty.call(imageNameToDataMap, imageName)) {
      const images = imageNameToDataMap[imageName]
      const cellRef = imageCellMap[imageName]

      if (!cellRef) {
        console.warn(`  ⚠ 图片名称"${imageName}"未找到对应的单元格`)
        console.warn(`    可能的原因: sheet1XmlData中不存在此图片名称`)
        console.warn(`    imageCellMap中可用的键:`, Object.keys(imageCellMap).slice(0, 10))
        continue
      }

      console.log(`  图片名称"${imageName}"关联到单元格"${cellRef}"`)

      const cellRefInfo = parseCellRef(cellRef)
      if (!cellRefInfo) {
        console.warn(`  ⚠ 无法解析单元格引用: ${cellRef}`)
        continue
      }

      const rowNumber = cellRefInfo.row
      const colNumber = cellRefInfo.col
      const dataRowIndex = rowNumber - 2

      if (dataRowIndex >= 0 && dataRowIndex < processedData.length) {
        const targetRow = processedData[dataRowIndex]
        const rowId = targetRow['通行标识ID'] || '未知ID'

        const colLetter = String.fromCharCode(64 + colNumber)
        console.log(`  单元格${cellRef} -> 列号${colNumber}(${colLetter}列), 数据行索引${dataRowIndex}`)

        if (colNumber === 7) {
          if (images.length >= 1) {
            targetRow['查核资料1'] = images[0].imageData
            successCount++
            console.log(
              `  ✓ 行${dataRowIndex}(通行标识ID="${rowId}") "查核资料1" = imageId="${images[0].imageId}" (G列)`
            )
          }
        } else if (colNumber === 8) {
          if (images.length >= 1) {
            targetRow['查核资料2'] = images[0].imageData
            successCount++
            console.log(
              `  ✓ 行${dataRowIndex}(通行标识ID="${rowId}") "查核资料2" = imageId="${images[0].imageId}" (H列)`
            )
          }
        } else {
          console.warn(
            `  ⚠ 单元格${cellRef}列号${colNumber}不在G列(7)或H列(8)范围内，跳过此图片`
          )
        }
      } else {
        console.warn(`  ⚠ 行号${rowNumber}超出数据范围(0-${processedData.length})`)
      }
    }
  }

  console.log('\n========== cellimages型图片关联完成 ==========')
  console.log(`成功关联图片: ${successCount} 张`)
}

const associateImagesWithRows = (
  processedData: any[],
  mediaFiles: Record<string, string>,
  relMap: Record<string, string>,
  drawingMap: Record<string, { row: number; col: number; imageId: string }>
): void => {
  console.log('========== 开始关联图片到数据行 ==========')
  console.log(`数据行总数: ${processedData.length}`)
  console.log(`图片文件数: ${Object.keys(mediaFiles).length}`)
  console.log(`关系映射数: ${Object.keys(relMap).length}`)
  console.log(`位置映射数: ${Object.keys(drawingMap).length}`)

  console.log('\n--- 步骤1: 按行号分组图片 ---')
  const rowImagesMap: Record<number, { imageId: string; imageData: string; col: number }[]> = {}

  for (const relationshipId in drawingMap) {
    if (Object.prototype.hasOwnProperty.call(drawingMap, relationshipId)) {
      const info = drawingMap[relationshipId]
      const row = info.row
      const col = info.col
      const imageId = info.imageId

      const imageFileName = relMap[relationshipId]
      console.log(
        `处理关系ID "${relationshipId}": 行号=${row}, 列号=${col}, imageId="${imageId}", 映射文件名="${imageFileName}"`
      )

      let actualImagePath: string | null = null
      if (imageFileName) {
        if (mediaFiles[imageFileName]) {
          actualImagePath = imageFileName
        } else {
          const mediaFileKeys = Object.keys(mediaFiles)
          const imageNameFromPath = imageFileName.split('/').pop()
          if (imageNameFromPath) {
            actualImagePath = mediaFileKeys.find((key) => key.endsWith(imageNameFromPath)) || null
          }
        }
      }

      if (actualImagePath && mediaFiles[actualImagePath]) {
        if (!rowImagesMap[row]) {
          rowImagesMap[row] = []
        }
        rowImagesMap[row].push({
          imageId: imageId,
          imageData: mediaFiles[actualImagePath],
          col: col
        })
        console.log(
          `  ✓ 行${row}添加图片: imageId="${imageId}", 列号=${col}, 文件="${actualImagePath}"`
        )
      } else {
        console.warn(
          `  ✗ 未找到图片文件: 关系ID="${relationshipId}", 映射文件名="${imageFileName}"`
        )
        console.log(`  可用的图片文件示例:`, Object.keys(mediaFiles).slice(0, 10))
      }
    }
  }

  console.log('\n--- 步骤2: 按行号分组结果 ---')
  for (const row in rowImagesMap) {
    console.log(
      `行${row}: ${rowImagesMap[row].length} 张图片`,
      rowImagesMap[row].map((img) => `(${img.col}列:${img.imageId})`)
    )
  }

  console.log('\n--- 步骤3: 将图片关联到数据行 ---')
  console.log('说明: Excel行号=drawing row+1, 数据索引=Excel行号-2(跳过表头)')
  let successCount = 0

  for (const row in rowImagesMap) {
    const excelRowNum = parseInt(row)
    const dataRowIndex = excelRowNum - 2
    const images = [...rowImagesMap[excelRowNum]]

    images.sort((a, b) => a.col - b.col)

    if (dataRowIndex >= 0 && dataRowIndex < processedData.length) {
      const targetRow = processedData[dataRowIndex]
      const rowId = targetRow['通行标识ID'] || '未知ID'

      if (images.length >= 1) {
        targetRow['查核资料1'] = images[0].imageData
        successCount++
        console.log(
          `  ✓ Excel行${excelRowNum}(索引${dataRowIndex}) "查核资料1" = imageId="${images[0].imageId}", 列号=${images[0].col}, 通行标识ID="${rowId}"`
        )
      }

      if (images.length >= 2) {
        targetRow['查核资料2'] = images[1].imageData
        successCount++
        console.log(
          `  ✓ Excel行${excelRowNum}(索引${dataRowIndex}) "查核资料2" = imageId="${images[1].imageId}", 列号=${images[1].col}, 通行标识ID="${rowId}"`
        )
      }

      if (images.length > 2) {
        console.log(`  ⚠ Excel行${excelRowNum}有${images.length}张图片，仅保留前2张`)
      }
    } else {
      console.warn(
        `  ✗ 数据索引${dataRowIndex}超出范围(0-${processedData.length - 1}), Excel行号=${excelRowNum}`
      )
    }
  }

  console.log('\n========== 图片关联完成 ==========')
  console.log(`成功关联: ${successCount} 张`)

  let rowsWithImage1 = 0
  let rowsWithImage2 = 0
  for (const row of processedData) {
    if (row['查核资料1']) rowsWithImage1++
    if (row['查核资料2']) rowsWithImage2++
  }
  console.log(
    `最终统计: 查核资料1有图片的行数=${rowsWithImage1}, 查核资料2有图片的行数=${rowsWithImage2}`
  )
}

const parseExcelAsync = async (
  binaryData: string,
  onProgress: (progress: number, status: string) => void
): Promise<{ data: any[]; extractedImagesCount: number }> => {
  console.log('==================== 开始解析Excel文件 ====================')
  console.log(`文件数据大小: ${binaryData.length} 字符`)

  onProgress(5, '正在检测Excel格式...')
  console.log('[步骤1] 检测Excel格式...')

  const excelFormat = await detectExcelFormat(binaryData)

  if (excelFormat === 'no_image') {
    ElMessage.warning('当前Excel文件无嵌入图片')
    onProgress(100, '文件解析完成')
    return { data: [], extractedImagesCount: 0 }
  }

  onProgress(10, '正在解析Excel工作簿...')
  console.log(`[步骤2] 检测到格式: ${excelFormat}`)
  console.log('[步骤3] 解析Excel工作簿...')

  const xlsxWorkbook = XLSX.read(binaryData, { type: 'binary' })
  const sheetName = xlsxWorkbook.SheetNames[0]
  console.log(`工作表名称: ${sheetName}`)
  console.log(`所有工作表: ${xlsxWorkbook.SheetNames.join(', ')}`)

  const worksheet = xlsxWorkbook.Sheets[sheetName]
  const jsonData = XLSX.utils.sheet_to_json(worksheet, { range: 0 })

  const totalRows = jsonData.length
  console.log(`解析到 ${totalRows} 行数据`)
  if (totalRows > 0) {
    console.log('第一行数据示例:', jsonData[0])
    console.log('第一行字段:', Object.keys(jsonData[0]))
  }

  onProgress(20, '正在处理数据...')
  console.log('[步骤4] 处理数据行...')

  const processedData: any[] = []
  const chunkSize = 50

  for (let i = 0; i < jsonData.length; i += chunkSize) {
    const chunk = jsonData.slice(i, i + chunkSize)

    for (let j = 0; j < chunk.length; j++) {
      const globalIndex = i + j
      const row = chunk[j]
      const processedRow = processDataRow(row, globalIndex)
      processedData.push(processedRow)
    }

    const progress = 20 + Math.round((i / totalRows) * 30)
    onProgress(progress, `正在处理数据 ${Math.round((i / totalRows) * 100)}%`)

    await new Promise((resolve) => setTimeout(resolve, 0))
  }

  console.log(`数据处理完成，共 ${processedData.length} 行`)

  onProgress(50, '正在提取图片...')
  console.log('[步骤5] 提取图片...')

  const { mediaFiles, count } = await extractImagesFromExcel(binaryData)

  onProgress(60, '正在建立图片关联...')
  console.log('[步骤6] 构建图片映射...')

  if (excelFormat === 'cellimages') {
    const { relMap, cellImageMap, sheet1XmlData } =
      await buildCellImagesMappingsWithSheet1(binaryData)
    onProgress(75, '正在关联图片到数据行...')
    console.log('[步骤7] 关联图片到数据行(cellimages型)...')
    associateCellImagesWithRows(processedData, mediaFiles, relMap, cellImageMap, sheet1XmlData)
  } else {
    const { relMap, drawingMap } = await buildImageMappings(binaryData)
    onProgress(75, '正在关联图片到数据行...')
    console.log('[步骤7] 关联图片到数据行(drawings型)...')
    associateImagesWithRows(processedData, mediaFiles, relMap, drawingMap)
  }

  onProgress(95, '正在完成...')
  console.log('[步骤8] 完成解析...')

  await new Promise((resolve) => setTimeout(resolve, 0))

  onProgress(100, '文件解析完成')
  console.log('==================== Excel文件解析完成 ====================')
  console.log(`最终结果: ${processedData.length} 行数据, ${count} 张图片`)

  return { data: processedData, extractedImagesCount: count }
}

// 文件上传处理函数
const handleFileUpload = async (file: any) => {
  console.log('==================== 文件上传开始 ====================')
  console.log('上传文件信息:', {
    name: file.name,
    size: file.size,
    type: file.raw?.type,
    lastModified: file.raw?.lastModified
  })

  if (!selectedTable.value) {
    ElMessage.warning('请先选择数据表')
    return
  }

  uploadLoading.value = true
  uploadProgress.value = 0
  uploadProgressText.value = '正在读取文件...'
  importError.value = ''
  importStep.value = 'preview'

  try {
    const reader = new FileReader()

    reader.onload = async (e) => {
      console.log('FileReader.onload 触发')
      try {
        const data = e.target?.result
        if (!data) {
          throw new Error('文件读取失败')
        }

        console.log(`文件读取成功，数据大小: ${(data as string).length} 字符`)
        uploadProgressText.value = '文件读取完成'

        const result = await parseExcelAsync(data as string, (progress: number, status: string) => {
          uploadProgress.value = progress
          uploadProgressText.value = status
        })

        console.log('Excel解析结果:', {
          数据行数: result.data.length,
          提取图片数: result.extractedImagesCount
        })

        importData.value = result.data
        extractedImagesCount.value = result.extractedImagesCount
        uploadProgress.value = 100
        uploadProgressText.value = '文件解析完成'
        uploadLoading.value = false
        importPreviewVisible.value = true
        console.log('==================== 文件上传处理完成 ====================')
      } catch (error) {
        console.error('解析Excel文件失败:', error)
        importError.value =
          '解析Excel文件失败: ' + (error instanceof Error ? error.message : '未知错误')
        ElMessage.error('解析Excel文件失败')
        uploadLoading.value = false
      }
    }

    reader.onerror = (error) => {
      console.error('FileReader读取错误:', error)
      importError.value = '读取文件失败'
      ElMessage.error('读取文件失败')
      uploadLoading.value = false
    }

    console.log('开始读取文件...')
    reader.readAsBinaryString(file.raw)
  } catch (error) {
    console.error('处理文件上传失败:', error)
    importError.value = '处理文件上传失败'
    ElMessage.error('处理文件上传失败')
    uploadLoading.value = false
  }
}

// 匹配导入数据
// 获取所有表格数据（不分页）
const getAllTableData = async (): Promise<any[]> => {
  if (!selectedTable.value) {
    return []
  }

  try {
    console.log('开始获取所有表格数据，表名:', selectedTable.value)
    // 调用API获取所有数据，不使用分页参数
    const response = await getSplitMatchData({
      table_name: selectedTable.value,
      filters: JSON.stringify(filters.value),
      // 不使用分页，获取所有数据
      page: 1,
      page_size: 10000 // 设置一个足够大的值
    })
    console.log('获取所有表格数据结果:', response)

    let allData: any[] = []
    if (response && typeof response === 'object') {
      if (response.code === 200 && response.data) {
        allData = Array.isArray(response.data.data) ? response.data.data : []
      } else {
        allData = Array.isArray(response.data) ? response.data : []
      }
    }

    console.log('获取到的所有表格数据条数:', allData.length)
    return allData
  } catch (error) {
    console.error('获取所有表格数据失败:', error)
    ElMessage.error('获取所有表格数据失败')
    return []
  }
}

const matchImportData = async () => {
  if (!selectedTable.value) {
    ElMessage.warning('没有数据可匹配')
    importLoading.value = false
    return
  }

  // 显示加载状态
  importProgress.value = 10
  importProgressText.value = '正在获取所有表格数据...'

  // 获取所有表格数据用于匹配
  const allTableData = await getAllTableData()

  if (allTableData.length === 0) {
    ElMessage.warning('没有数据可匹配')
    importLoading.value = false
    return
  }

  const matchResult: any[] = []
  const unmatchedImportIds: string[] = []
  const total = importData.value.length

  console.log('开始匹配导入数据:', {
    导入数据条数: total,
    表格数据条数: allTableData.length
  })

  // 更新进度
  importProgress.value = 20
  importProgressText.value = '开始匹配数据...'

  // 遍历导入数据
  for (let i = 0; i < importData.value.length; i++) {
    const importRow = importData.value[i]
    const 通行标识ID = importRow['通行标识ID']

    if (!通行标识ID) {
      console.log(`第 ${i + 1} 条导入数据：通行标识ID为空`)
      // 更新进度
      importProgress.value = 20 + Math.round(((i + 1) / total) * 70)
      importProgressText.value = `正在匹配 ${i + 1}/${total}...`
      continue
    }

    console.log(`第 ${i + 1} 条导入数据：通行标识ID = ${通行标识ID}`)

    // 在所有表格数据中查找匹配的记录
    const matchedRow = allTableData.find((tableRow) => {
      // 清理表格ID：移除所有非字母数字字符，转换为小写
      const tableId = String(tableRow['通行标识ID'])
        .trim()
        .replace(/[^a-zA-Z0-9]/g, '')
        .toLowerCase()

      // 清理导入ID：移除所有非字母数字字符，转换为小写
      const importId = String(通行标识ID)
        .trim()
        .replace(/[^a-zA-Z0-9]/g, '')
        .toLowerCase()

      const isMatch = tableId === importId
      if (isMatch) {
        console.log(
          `找到匹配记录：表格ID = ${String(tableRow['通行标识ID'])}，清理后 = ${tableId}；导入ID = ${通行标识ID}，清理后 = ${importId}`
        )
      }
      return isMatch
    })

    if (matchedRow) {
      // 创建匹配结果
      matchResult.push({
        通行标识ID,
        原始数据: matchedRow,
        导入数据: importRow,
        匹配状态: '已匹配'
      })
    } else {
      unmatchedImportIds.push(通行标识ID)
      console.log(`未找到匹配记录：导入ID = ${通行标识ID}`)
    }

    // 更新进度
    importProgress.value = 20 + Math.round(((i + 1) / total) * 70)
    importProgressText.value = `正在匹配 ${i + 1}/${total}...`

    // 避免UI阻塞
    await new Promise((resolve) => setTimeout(resolve, 10))
  }

  importResult.value = matchResult
  importProgress.value = 100
  importProgressText.value = '匹配完成'

  // 输出匹配结果统计
  console.log('匹配结果统计:', {
    总导入数据条数: total,
    匹配成功条数: matchResult.length,
    匹配失败条数: unmatchedImportIds.length,
    未匹配的通行标识ID: unmatchedImportIds
  })

  // 显示匹配结果提示
  ElMessage.info(
    `匹配完成：共 ${total} 条导入数据，成功匹配 ${matchResult.length} 条，未匹配 ${unmatchedImportIds.length} 条`
  )
}

// 获取导入数据的所有列
const getImportDataColumns = () => {
  if (importData.value.length === 0) {
    return []
  }

  // 定义用户指定的列顺序
  const userDefinedOrder = [
    '序号',
    '通行标识ID',
    '车牌号码',
    '车牌',
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

  // 收集所有行的所有键
  const allColumns = new Set<string>()
  importData.value.forEach((row) => {
    Object.keys(row).forEach((key) => {
      // 过滤掉_excelRowNumber字段，不将其作为列显示
      if (key !== '_excelRowNumber') {
        allColumns.add(key)
      }
    })
  })

  // 按照用户指定的顺序排列列
  const sortedColumns: string[] = []

  // 首先添加用户定义顺序中存在的列
  userDefinedOrder.forEach((column) => {
    if (allColumns.has(column)) {
      sortedColumns.push(column)
      allColumns.delete(column)
    }
  })

  // 然后添加其他未在用户定义顺序中的列
  allColumns.forEach((column) => {
    sortedColumns.push(column)
  })

  console.log('按用户指定顺序排列的列:', sortedColumns)
  return sortedColumns
}

// 根据列名获取合适的宽度（更紧凑）
const getColumnWidth = (column: string) => {
  const widthMap: Record<string, number> = {
    通行标识ID: 200,
    核查通行标识: 200,
    查核资料1: 100,
    查核资料2: 100
  }
  return widthMap[column] || 120
}

// 判断是否为图片数据
const isImageData = (data: any): boolean => {
  if (typeof data !== 'string') {
    return false
  }
  // 检查是否为WPS图片格式
  if (data.startsWith('=DISPIMG(')) {
    return true
  }
  // 检查是否为data URL
  return data.startsWith('data:image/')
}

// 判断通行标识ID是否已匹配
const isIdMatched = (id: any): boolean => {
  if (!id) {
    return false
  }

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

// 获取上传状态文本
const getUploadStatusText = () => {
  if (uploadProgress.value < 30) {
    return '正在初始化文件读取...'
  } else if (uploadProgress.value < 70) {
    return '正在解析Excel文件内容...'
  } else if (uploadProgress.value < 100) {
    return '正在处理数据...'
  } else {
    return '文件读取完成，准备导入...'
  }
}

// 获取状态颜色
const getStatusColor = () => {
  if (uploadProgress.value < 30) {
    return '#409eff' // 蓝色
  } else if (uploadProgress.value < 70) {
    return '#67c23a' // 绿色
  } else if (uploadProgress.value < 100) {
    return '#e6a23c' // 橙色
  } else {
    return '#67c23a' // 绿色
  }
}

// 处理导入的图片数据
const processImportedImages = async (importRow: any) => {
  const processedRow: any = { ...importRow }

  // 处理查核资料1
  if (processedRow['查核资料1']) {
    try {
      // 检查是否为WPS图片格式
      if (
        typeof processedRow['查核资料1'] === 'string' &&
        processedRow['查核资料1'].startsWith('=DISPIMG(')
      ) {
        // 保留WPS图片格式，不做转换
        return processedRow
      }
      // 检查是否是base64字符串
      if (
        typeof processedRow['查核资料1'] === 'string' &&
        processedRow['查核资料1'].includes(',')
      ) {
        // 转换为WebP格式
        const webpBlob = await convertToWebPFromBase64(processedRow['查核资料1'])
        // 转换为base64字符串用于存储
        const arrayBuffer = await webpBlob.arrayBuffer()
        const base64String = btoa(
          new Uint8Array(arrayBuffer).reduce((data, byte) => data + String.fromCharCode(byte), '')
        )
        processedRow['查核资料1'] = base64String
      }
    } catch (error) {
      console.error('处理查核资料1图片失败:', error)
      // 保留原始值
    }
  }

  // 处理查核资料2
  if (processedRow['查核资料2']) {
    try {
      // 检查是否为WPS图片格式
      if (
        typeof processedRow['查核资料2'] === 'string' &&
        processedRow['查核资料2'].startsWith('=DISPIMG(')
      ) {
        // 保留WPS图片格式，不做转换
        return processedRow
      }
      // 检查是否是base64字符串
      if (
        typeof processedRow['查核资料2'] === 'string' &&
        processedRow['查核资料2'].includes(',')
      ) {
        // 转换为WebP格式
        const webpBlob = await convertToWebPFromBase64(processedRow['查核资料2'])
        // 转换为base64字符串用于存储
        const arrayBuffer = await webpBlob.arrayBuffer()
        const base64String = btoa(
          new Uint8Array(arrayBuffer).reduce((data, byte) => data + String.fromCharCode(byte), '')
        )
        processedRow['查核资料2'] = base64String
      }
    } catch (error) {
      console.error('处理查核资料2图片失败:', error)
      // 保留原始值
    }
  }

  return processedRow
}

// 从base64字符串转换为WebP格式
const convertToWebPFromBase64 = (base64String: string): Promise<Blob> => {
  return new Promise((resolve, reject) => {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    const img = new Image()

    img.onload = () => {
      // 设置canvas尺寸与图片一致
      canvas.width = img.width
      canvas.height = img.height

      // 绘制图片到canvas
      ctx?.drawImage(img, 0, 0)

      // 将canvas转换为WebP格式的Blob
      canvas.toBlob(
        (blob) => {
          if (blob) {
            resolve(blob)
          } else {
            reject(new Error('无法转换图片为WebP格式'))
          }
        },
        'image/webp',
        0.8 // 质量参数，0-1之间
      )
    }

    img.onerror = () => {
      reject(new Error('图片加载失败'))
    }

    // 加载图片
    img.src = base64String
  })
}

// 获取导入对话框标题
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

// 处理导入取消
const handleImportCancel = () => {
  // 重置导入状态
  importData.value = []
  importResult.value = []
  importError.value = ''
  importProgress.value = 0
  importProgressText.value = ''
  importStep.value = 'preview'
  importTotalCount.value = 0
  importPreviewVisible.value = false
}

// 开始导入
const startImport = async () => {
  if (!selectedTable.value || importData.value.length === 0) {
    ElMessage.warning('没有数据可导入')
    return
  }

  importStep.value = 'matching'
  importProgress.value = 0
  importProgressText.value = '正在匹配数据...'
  importTotalCount.value = importData.value.length
  importResult.value = []

  try {
    // 执行数据匹配
    await matchImportData()

    // 开始导入
    importStep.value = 'importing'
    importProgress.value = 0
    importProgressText.value = '正在导入数据...'
    await executeImport()
  } catch (error) {
    console.error('导入过程失败:', error)
    importError.value = '导入过程失败'
    ElMessage.error('导入过程失败')
    importStep.value = 'preview'
  } finally {
    importLoading.value = false
  }
}

// 执行导入
const executeImport = async () => {
  if (!selectedTable.value || importResult.value.length === 0) {
    ElMessage.warning('没有数据可导入')
    return
  }

  importLoading.value = true
  let successCount = 0
  let errorCount = 0
  const total = importResult.value.length

  try {
    // 遍历匹配结果，逐条更新
    for (let i = 0; i < importResult.value.length; i++) {
      const item = importResult.value[i]
      try {
        // 更新进度
        importProgress.value = Math.round(((i + 1) / total) * 100)
        importProgressText.value = `正在导入 ${i + 1}/${total}...`

        // 处理图片数据
        const processedImportData = await processImportedImages(item.导入数据)

        // 构建更新数据
        const updateData: any = {
          核查通行标识: processedImportData['核查通行标识'],
          复核情况: processedImportData['复核情况'],
          备注: processedImportData['备注'],
          查核资料1: processedImportData['查核资料1'],
          查核资料2: processedImportData['查核资料2'],
          特情: processedImportData['特情']
        }

        // 移除undefined值
        Object.keys(updateData).forEach((key) => {
          if (updateData[key] === undefined) {
            delete updateData[key]
          }
        })

        // 调用API更新数据
        await import('axios').then(({ default: axios }) => {
          return axios.post(import.meta.env.VITE_API_BASE_PATH + '/api/split-match/update/', {
            table_name: selectedTable.value,
            row_id: String(item.通行标识ID),
            data: updateData
          })
        })

        successCount++
      } catch (error) {
        console.error(`更新数据失败，通行标识ID: ${item.通行标识ID}`, error)
        errorCount++
      }

      // 避免UI阻塞
      await new Promise((resolve) => setTimeout(resolve, 50))
    }

    // 更新进度为100%
    importProgress.value = 100
    importProgressText.value = '导入完成'

    // 显示导入结果
    ElMessage.success(`导入完成，成功: ${successCount} 条，失败: ${errorCount} 条`)

    // 重新加载数据
    loadTableData()
  } catch (error) {
    console.error('导入数据失败:', error)
    ElMessage.error('导入数据失败')
  } finally {
    importLoading.value = false
  }
}

const handleSave = async () => {
  if (!editedRow.value || !selectedTable.value) {
    ElMessage.warning('数据不完整，无法保存')
    return
  }

  try {
    console.log('开始保存编辑数据:', editedRow.value)

    // 获取通行标识ID作为唯一标识符
    const rowId = String(editedRow.value['通行标识ID'])

    // 准备保存数据，替换图片字段为二进制数据
    const saveData = { ...editedRow.value }

    // 处理图片字段，使用二进制数据而不是 data URL
    if (imageBinaryData.value['查核资料1']) {
      // 将Blob转换为ArrayBuffer，然后转换为Base64字符串
      const arrayBuffer = await imageBinaryData.value['查核资料1'].arrayBuffer()
      const base64String = btoa(
        new Uint8Array(arrayBuffer).reduce((data, byte) => data + String.fromCharCode(byte), '')
      )
      saveData['查核资料1'] = base64String
    } else {
      // 如果没有新的图片数据，保持原有的 data URL，但需要转换为纯 Base64
      const imageData = editedRow.value['查核资料1']
      if (imageData && typeof imageData === 'string' && imageData.startsWith('data:')) {
        // 从 data URL 中提取 Base64 字符串
        const base64Part = imageData.split(',')[1]
        if (base64Part) {
          saveData['查核资料1'] = base64Part
        }
      }
    }

    if (imageBinaryData.value['查核资料2']) {
      // 将Blob转换为ArrayBuffer，然后转换为Base64字符串
      const arrayBuffer = await imageBinaryData.value['查核资料2'].arrayBuffer()
      const base64String = btoa(
        new Uint8Array(arrayBuffer).reduce((data, byte) => data + String.fromCharCode(byte), '')
      )
      saveData['查核资料2'] = base64String
    } else {
      // 如果没有新的图片数据，保持原有的 data URL，但需要转换为纯 Base64
      const imageData = editedRow.value['查核资料2']
      if (imageData && typeof imageData === 'string' && imageData.startsWith('data:')) {
        // 从 data URL 中提取 Base64 字符串
        const base64Part = imageData.split(',')[1]
        if (base64Part) {
          saveData['查核资料2'] = base64Part
        }
      }
    }

    const apiParams = {
      table_name: selectedTable.value,
      row_id: rowId,
      data: saveData
    }

    console.log('准备调用API，参数:', apiParams)
    console.log('API基础URL:', import.meta.env.VITE_API_BASE_PATH)
    console.log('是否启用Mock:', import.meta.env.VITE_USE_MOCK)

    // 直接使用 axios 实例发起请求，确保路径正确
    console.log('开始直接使用 axios 发起请求')

    // 导入 axios
    import('axios').then(({ default: axios }) => {
      console.log('axios 导入成功')
      console.log(
        '准备发起请求到:',
        import.meta.env.VITE_API_BASE_PATH + '/api/split-match/update/'
      )

      // 直接使用 axios 发起请求
      axios
        .post(import.meta.env.VITE_API_BASE_PATH + '/api/split-match/update/', apiParams)
        .then((response) => {
          console.log('axios请求成功，响应:', response)
          if (
            response &&
            response.data &&
            (response.data.code === 200 || response.data.data?.updated)
          ) {
            ElMessage.success('保存成功')
            loadTableData()
            dialogVisible.value = false
          } else {
            console.error('保存失败，响应数据:', response)
            ElMessage.error('保存失败，请检查后端服务')
          }
        })
        .catch((error) => {
          console.error('axios请求失败，详细错误:', error)
          console.error('错误配置:', error.config)
          console.error('错误代码:', error.code)
          console.error('错误消息:', error.message)
          console.error('错误响应:', error.response)
          ElMessage.error('保存失败，请检查控制台错误信息')
        })
    })
  } catch (error) {
    console.error('保存失败，详细错误:', error)
    console.error('错误类型:', typeof error)
    console.error('错误对象:', error)
    ElMessage.error('保存失败，请检查控制台错误信息')
  }
}

onMounted(() => {
  loadTableList()
})
</script>

<style scoped>
.split-match {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.control-form {
  margin-bottom: 20px;
}

.match-result {
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.loading-container,
.no-data,
.no-table-selected {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 500px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  background-color: #f9fafc;
}

.loading-container {
  gap: 12px;
  color: #409eff;
}

.no-data,
.no-table-selected {
  color: #909399;
  font-size: 14px;
}

/* 导入进度容器 */
.import-progress-container {
  padding: 20px;
  background-color: #f9fafc;
  border-radius: 8px;
  border: 1px solid #ebeef5;
}

/* 加载动画 */
.loading-animation {
  margin: 40px 0;
}

/* 匹配结果容器 */
.match-result-container {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px dashed #ebeef5;
}

/* 旋转动画 */
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 导入预览表格样式 */
:deep(.el-table__row:hover) {
  background-color: #ecf5ff !important;
}

/* 进度条样式 */
:deep(.el-progress__bar) {
  border-radius: 7px;
}

:deep(.el-progress__bar__inner) {
  border-radius: 7px;
  background-color: #409eff;
  transition: width 0.3s ease;
}

/* 现代上传对话框样式 */
:deep(.modern-upload-dialog .el-dialog__body) {
  padding: 0;
}

/* 旋转动画 */
@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

/* 发光动画 */
@keyframes glow {
  0% {
    transform: translateX(-100%);
    opacity: 0;
  }
  50% {
    opacity: 1;
  }
  100% {
    transform: translateX(300%);
    opacity: 0;
  }
}

/* 步骤指示器样式 */
:deep(.step-dot.active) {
  background-color: #409eff !important;
  transform: scale(1.1);
}

:deep(.step.active .step-text) {
  color: #409eff !important;
  font-weight: 500;
}

:deep(.step-line.active) {
  background-color: #409eff !important;
}

/* 进度条样式增强 */
:deep(.el-progress__bar__inner) {
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}
</style>
