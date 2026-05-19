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
          <el-button type="info" @click="handleSplitStatistics" :loading="statisticsLoading">
            拆分统计
          </el-button>
          <el-button @click="handleExport" :loading="exportLoading"> 导出数据 </el-button>
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
              reserve-keyword
              default-first-option
              style="width: 200px"
              @blur="handlePassIdBlur"
              @change="handlePassIdChange"
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

      <!-- 虚拟表格 -->
      <div class="table-container" v-if="selectedTable">
        <el-table
          :data="tableData"
          v-loading="tableLoading"
          style="width: 100%"
          height="840"
          border
          stripe
          :row-key="(row) => row['通行标识ID'] || Math.random()"
        >
          <el-table-column type="index" label="序号" width="55" :index="(index) => (currentPage - 1) * pageSize + index + 1" />
          <el-table-column prop="通行标识ID" label="通行标识ID" width="310">
            <template #default="{ row }">
              <el-button link @click="handleIdClick(row)" style="border: none; padding: 0">{{
                row['通行标识ID']
              }}</el-button>
            </template>
          </el-table-column>
          <el-table-column prop="车牌号码" label="车牌号码" min-width="120" />
          <el-table-column prop="核查通行标识" label="核查通行标识" width="310">
            <template #default="{ row }">
              <el-button link @click="handleIdClick(row)" style="border: none; padding: 0">{{
                row['核查通行标识'] || '-'
              }}</el-button>
            </template>
          </el-table-column>
          <el-table-column prop="复核情况" label="复核情况" min-width="100" />
          <el-table-column prop="备注" label="备注" min-width="160">
            <template #default="{ row }">
              <div
                style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis"
                :title="row['备注'] || ''"
              >
                {{ row['备注'] || '-' }}
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="门架通行时间" label="门架通行时间" min-width="150" />
          <el-table-column prop="入口时间" label="入口时间" min-width="150" />
          <el-table-column prop="收费车型" label="收费车型" min-width="100" />
          <el-table-column prop="特情" label="特情" min-width="100">
            <template #default="{ row }">
              <div style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis">
                {{ row['特情'] || '-' }}
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="核查拆分" label="核查拆分" min-width="100">
            <template #default="{ row }">
              <el-button
                v-if="row['核查拆分'] === '已拆'"
                link
                type="primary"
                @click="handleSplitDetailClick(row)"
                style="border: none; padding: 0"
              >
                {{ row['核查拆分'] }}
              </el-button>
              <span v-else>{{ row['核查拆分'] || '-' }}</span>
            </template>
          </el-table-column>
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
              v-for="key in sortedDetailFields"
              :key="key"
              :label="key"
              style="word-break: break-all; overflow-wrap: break-word"
            >
              <!-- 查核资料1字段（图片上传） -->
              <template v-if="key === '查核资料1'">
                <div>
                  <div style="margin-bottom: 5px; display: flex; align-items: center">
                    <el-radio v-model="activeImageField" label="查核资料1" size="small">
                      当前粘贴目标
                    </el-radio>
                  </div>
                  <div v-if="editedRow['查核资料1']" style="margin-bottom: 10px; position: relative">
                    <el-image
                      :src="editedRow['查核资料1']"
                      fit="cover"
                      style="width: 200px; height: 150px; cursor: pointer"
                      :preview-src-list="[]"
                      @click="handleTableImagePreview(editedRow, '查核资料1')"
                    />
                    <el-button
                      type="danger"
                      size="small"
                      circle
                      style="position: absolute; top: 5px; right: 5px"
                      @click.stop="handleImageDelete('查核资料1')"
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
                  <el-upload
                    class="upload-demo"
                    action="#"
                    :auto-upload="false"
                    :on-change="(file) => handleImageUpload(file, '查核资料1')"
                    :show-file-list="false"
                    accept="image/*"
                  >
                    <el-button type="primary" size="small">上传图片</el-button>
                  </el-upload>
                </div>
              </template>
              <!-- 查核资料2字段（图片上传） -->
              <template v-else-if="key === '查核资料2'">
                <div>
                  <div style="margin-bottom: 5px; display: flex; align-items: center">
                    <el-radio v-model="activeImageField" label="查核资料2" size="small">
                      当前粘贴目标
                    </el-radio>
                  </div>
                  <div v-if="editedRow['查核资料2']" style="margin-bottom: 10px; position: relative">
                    <el-image
                      :src="editedRow['查核资料2']"
                      fit="cover"
                      style="width: 200px; height: 150px; cursor: pointer"
                      :preview-src-list="[]"
                      @click="handleTableImagePreview(editedRow, '查核资料2')"
                    />
                    <el-button
                      type="danger"
                      size="small"
                      circle
                      style="position: absolute; top: 5px; right: 5px"
                      @click.stop="handleImageDelete('查核资料2')"
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
                  <el-upload
                    class="upload-demo"
                    action="#"
                    :auto-upload="false"
                    :on-change="(file) => handleImageUpload(file, '查核资料2')"
                    :show-file-list="false"
                    accept="image/*"
                  >
                    <el-button type="primary" size="small">上传图片</el-button>
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
                  <el-button
                    type="success"
                    :icon="Search"
                    @click="handleVerifyPassId(String(editedRow[key]), '核查通行标识')"
                    size="default"
                    :loading="verifyLoading"
                    :disabled="!editedRow[key]"
                  >
                    核查
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
                <!-- 通行标识ID字段（特殊处理：复制+核查） -->
                <div
                  v-if="key === '通行标识ID'"
                  style="
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    word-break: break-all;
                    overflow-wrap: break-word;
                    max-width: 400px;
                  "
                >
                  <span style="flex: 1">{{ editedRow[key] || '-' }}</span>
                  <el-button
                    type="primary"
                    :icon="CopyDocument"
                    @click="handleCopy(String(editedRow[key]))"
                    size="small"
                  >
                    复制
                  </el-button>
                  <el-button
                    type="success"
                    :icon="Search"
                    @click="handleVerifyPassId(String(editedRow[key]), '通行标识ID')"
                    size="small"
                    :loading="verifyLoading"
                    :disabled="!editedRow[key]"
                  >
                    核查
                  </el-button>
                </div>
                <!-- 车牌号码、车牌字段添加复制和人工核查功能 -->
                <div
                  v-else-if="['车牌号码', '车牌'].includes(key)"
                  style="
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    word-break: break-all;
                    overflow-wrap: break-word;
                    max-width: 400px;
                  "
                >
                  <span style="flex: 1">{{ editedRow[key] || '-' }}</span>
                  <el-button
                    type="primary"
                    :icon="CopyDocument"
                    @click="handleCopy(String(editedRow[key]))"
                    size="small"
                  >
                    复制
                  </el-button>
                  <el-button
                    type="warning"
                    :icon="Search"
                    @click="handleOpenCloudPortal"
                    size="small"
                  >
                    人工核查
                  </el-button>
                </div>
                <!-- 非图片字段正常显示 -->
                <div
                  v-else
                  style="word-break: break-all; overflow-wrap: break-word; max-width: 400px"
                >
                  {{ editedRow[key] || '-' }}
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

    <!-- 云门户人工核查对话框 -->
    <el-dialog
      v-model="cloudPortalDialogVisible"
      title="云门户人工核查"
      width="90%"
      top="2vh"
      draggable
      destroy-on-close
      :close-on-click-modal="false"
      class="compact-dialog"
    >
      <!-- 顶部：查询参数 + 信息填写 + 云门户登录 同一行 -->
      <div style="display: flex; gap: 8px; margin-bottom: 8px; align-items: stretch">
        <!-- 查询参数 -->
        <div style="flex: 1; min-height: 140px; overflow: hidden">
          <div
            style="
              font-size: 12px;
              font-weight: 500;
              color: #303133;
              margin-bottom: 6px;
              padding-bottom: 3px;
              border-bottom: 1px solid #e4e7ed;
            "
          >
            📋 查询参数
          </div>
          <el-descriptions :column="3" border size="small" class="query-params-desc">
            <el-descriptions-item label="通行标识ID" class-name="pass-id-content">
              <span style="font-weight: 500">{{ cloudPortalForm.passId || '-' }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="车牌号码">
              <span style="font-weight: 500; color: #409eff">{{
                cloudPortalForm.plateNumber || '-'
              }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="门架通行时间">
              <span style="font-weight: 500">{{ cloudPortalForm.gateTime || '-' }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="入口时间">
              <span style="font-weight: 500">{{ cloudPortalForm.entryTime || '-' }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="收费入口名称">
              <span style="font-weight: 500; color: #67c23a">{{
                cloudPortalForm.entryStationName || '-'
              }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="查询时长">
              <div style="display: flex; align-items: center; gap: 8px">
                <el-input-number
                  v-model="cloudPortalForm.hours"
                  :min="1"
                  :max="72"
                  size="small"
                  style="width: 90px"
                />
                <span>小时</span>
              </div>
            </el-descriptions-item>
            <el-descriptions-item label="图库条数">
              <div style="display: flex; align-items: center; gap: 8px">
                <el-input-number
                  v-model="cloudPortalForm.rows"
                  :min="10"
                  :max="100"
                  :step="10"
                  size="small"
                  style="width: 90px"
                />
                <span>条</span>
              </div>
            </el-descriptions-item>
            <el-descriptions-item label="通行门架名称" :span="3">
              <div
                v-if="cloudPortalForm.gantryNamesCombined"
                style="
                  cursor: pointer;
                  max-width: 100%;
                  overflow: hidden;
                  text-overflow: ellipsis;
                  white-space: nowrap;
                "
                @click="showGantryNamesDialog = true"
                title="点击查看完整内容"
              >
                <span style="color: #606266">{{ cloudPortalForm.gantryNamesCombined }}</span>
                <el-tag size="small" type="info" style="margin-left: 6px">点击查看</el-tag>
              </div>
              <span v-else style="color: #909399">-</span>
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 信息填写 -->
        <div style="flex: 1; min-height: 140px; overflow: hidden">
          <div
            style="
              font-size: 12px;
              font-weight: 500;
              color: #303133;
              margin-bottom: 6px;
              padding-bottom: 3px;
              border-bottom: 1px solid #e4e7ed;
            "
          >
            📝 信息填写
          </div>
          <div class="info-fill-card-compact">
            <el-row :gutter="8">
              <el-col :span="12">
                <div class="form-item-card-compact">
                  <div class="form-item-label-compact">复核情况</div>
                  <el-select
                    v-model="aiAuditReviewStatus"
                    placeholder="请选择"
                    style="width: 100%"
                    clearable
                    size="small"
                  >
                    <el-option label="拆分正常" value="拆分正常" />
                    <el-option label="拆分异常" value="拆分异常" />
                    <el-option label="待删除" value="待删除" />
                  </el-select>
                </div>
              </el-col>
              <el-col :span="12">
                <div class="form-item-card-compact">
                  <div class="form-item-label-compact">核查拆分</div>
                  <el-select
                    v-model="aiAuditCheckSplit"
                    placeholder="请选择"
                    style="width: 100%"
                    filterable
                    allow-create
                    clearable
                    size="small"
                  >
                    <el-option label="已拆" value="已拆" />
                    <el-option label="未拆" value="未拆" />
                  </el-select>
                </div>
              </el-col>
            </el-row>
            <el-row :gutter="8" style="margin-top: 6px">
              <el-col :span="12">
                <div class="form-item-card-compact">
                  <div class="form-item-label-compact"
                    >核查通行标识 <el-tag size="small" type="info">可核查</el-tag></div
                  >
                  <div style="display: flex; gap: 6px">
                    <el-input
                      v-model="aiAuditCheckPassId"
                      placeholder="请输入"
                      style="flex: 1"
                      clearable
                      size="small"
                    />
                    <el-button
                      type="success"
                      :icon="Search"
                      @click="handleVerifyPassId(aiAuditCheckPassId, '核查通行标识')"
                      :loading="verifyLoading"
                      :disabled="!aiAuditCheckPassId"
                      size="small"
                      >核查</el-button
                    >
                  </div>
                </div>
              </el-col>
              <el-col :span="12">
                <div class="form-item-card-compact">
                  <div class="form-item-label-compact">特情</div>
                  <el-autocomplete
                    v-model="aiAuditSpecialSituation"
                    :fetch-suggestions="querySpecialSituationHistory"
                    placeholder="请输入特情描述"
                    clearable
                    size="small"
                    style="width: 100%"
                    @blur="saveSpecialSituationHistory"
                  />
                </div>
              </el-col>
            </el-row>
            <el-row :gutter="8" style="margin-top: 6px">
              <el-col :span="24">
                <div class="form-item-card-compact">
                  <div class="form-item-label-compact">备注</div>
                  <el-autocomplete
                    v-model="aiAuditRemark"
                    :fetch-suggestions="queryRemarkHistory"
                    placeholder="请输入备注信息"
                    clearable
                    size="small"
                    style="width: 100%"
                    @blur="saveRemarkHistory"
                  />
                </div>
              </el-col>
            </el-row>
          </div>
        </div>

        <!-- 云门户登录 -->
        <div style="width: 280px; flex-shrink: 0">
          <div
            style="
              font-size: 12px;
              font-weight: 500;
              color: #303133;
              margin-bottom: 6px;
              padding-bottom: 3px;
              border-bottom: 1px solid #e4e7ed;
            "
          >
            🔐 云门户登录
          </div>
          <div
            style="border: 1px solid #e4e7ed; border-radius: 4px; padding: 6px; background: #fafafa"
          >
            <!-- 未登录状态 -->
            <div v-if="!cloudPortalLoggedIn">
              <div v-if="needManualCaptcha" style="margin-bottom: 6px">
                <div style="font-size: 12px; color: #606266; margin-bottom: 4px">验证码</div>
                <div style="display: flex; align-items: center; gap: 6px">
                  <el-input
                    v-model="cloudPortalForm.captcha"
                    placeholder="请输入验证码"
                    size="small"
                    style="width: 90px"
                    maxlength="4"
                  />
                  <div
                    v-if="captchaImage"
                    style="
                      width: 95px;
                      height: 30px;
                      border-radius: 4px;
                      overflow: hidden;
                      border: 1px solid #dcdfe6;
                      cursor: pointer;
                      transition: all 0.2s ease;
                    "
                    @click="refreshCaptcha()"
                    title="点击刷新验证码"
                  >
                    <img
                      :src="'data:image/jpeg;base64,' + captchaImage"
                      style="width: 100%; height: 100%; object-fit: cover; display: block"
                    />
                  </div>
                  <div
                    v-else
                    style="
                      width: 95px;
                      height: 30px;
                      border: 1px dashed #dcdfe6;
                      border-radius: 4px;
                      display: flex;
                      align-items: center;
                      justify-content: center;
                      font-size: 11px;
                      color: #909399;
                    "
                  >
                    加载中...
                  </div>
                </div>
              </div>

              <el-button
                type="primary"
                @click="handleCloudPortalLogin"
                :loading="loginLoading"
                :disabled="!cloudPortalForm.username"
                size="small"
                style="width: 100%"
              >
                {{ needManualCaptcha ? '手动登录' : '登录' }}
              </el-button>
            </div>

            <!-- 已登录状态 -->
            <div v-else>
              <el-alert type="success" :closable="false" style="margin-bottom: 6px" size="small">
                {{ cloudPortalUserInfo?.real_name || cloudPortalForm.username }}
              </el-alert>
              <div style="display: flex; justify-content: center; margin-bottom: 6px">
                <el-button
                  @click="handleCloudPortalLogoutWrapper"
                  size="small"
                  style="width: 172px; height: 35px"
                  >退出登录</el-button
                >
              </div>
              <div style="display: flex; justify-content: center">
                <el-button
                  type="primary"
                  @click="executeAIAuditBatchQuery"
                  :loading="aiAuditLoading"
                  size="small"
                  style="
                    width: 172px;
                    height: 35px;
                    background: linear-gradient(135deg, #409eff 0%, #67c23a 100%);
                    border: none;
                    font-weight: 500;
                    box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
                    transition: all 0.3s ease;
                  "
                >
                  🔍 AI稽核批量查询
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 主内容区域 -->
      <div style="display: flex; gap: 8px">
        <!-- 左侧：AI稽核查询结果 -->
        <div style="flex: 1; min-width: 0">
          <el-form :model="cloudPortalForm" label-width="120px">
            <!-- AI稽核查询结果 -->
            <div v-if="aiAuditResult" style="max-height: 55vh; overflow-y: auto">
              <el-tabs v-model="aiAuditActiveTab">
                <el-tab-pane label="车辆图库" name="vehicle_images">
                  <div v-if="aiAuditResult.vehicle_images?.success">
                    <div
                      style="
                        margin-bottom: 10px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                      "
                    >
                      <span>共 {{ filteredVehicleImagesTotal }} 张图片</span>
                      <div style="display: flex; gap: 10px; align-items: center">
                        <span style="font-size: 12px">排序：</span>
                        <el-radio-group
                          v-model="vehicleImagesSort"
                          size="small"
                          @change="handleVehicleImagesSortChange"
                        >
                          <el-radio-button value="picTime DESC">时间降序</el-radio-button>
                          <el-radio-button value="picTime ASC">时间升序</el-radio-button>
                        </el-radio-group>
                      </div>
                      <div style="display: flex; gap: 10px; align-items: center">
                        <span style="font-size: 12px">每页：</span>
                        <el-select v-model="vehicleImagesPageSize" size="small" style="width: 90px">
                          <el-option :label="'全部 (' + vehicleImagesTotal + ')'" :value="vehicleImagesTotal" />
                          <el-option :label="'20张'" :value="20" />
                          <el-option :label="'40张'" :value="40" />
                          <el-option :label="'60张'" :value="60" />
                          <el-option :label="'100张'" :value="100" />
                        </el-select>
                      </div>
                    </div>
                    <div
                      v-if="previewLoading"
                      style="
                        margin-bottom: 10px;
                        padding: 8px;
                        background: #fdf6ec;
                        border-radius: 4px;
                        display: flex;
                        align-items: center;
                        gap: 10px;
                      "
                    >
                      <el-icon class="is-loading" style="color: #e6a23c"><Loading /></el-icon>
                      <span style="color: #e6a23c; font-size: 13px">{{ previewLoadingText }}</span>
                    </div>
                    <div
                      v-loading="vehicleImagesLoading"
                      style="
                        display: flex;
                        flex-wrap: wrap;
                        gap: 10px;
                        max-height: none;
                        min-height: 200px;
                        overflow-y: visible;
                      "
                    >
                      <div
                        v-for="(img, idx) in filteredVehicleImages"
                        :key="idx"
                        :style="
                          isStationMatched(img.stationId)
                            ? 'width: 200px; border: 2px solid #409EFF; border-radius: 4px; padding: 5px; background: #ecf5ff'
                            : 'width: 200px; border: 1px solid #ddd; border-radius: 4px; padding: 5px'
                        "
                      >
                        <el-image
                          :src="getImageSrc(img.bigPositivePic)"
                          style="width: 100%; height: 120px"
                          fit="contain"
                          :preview-src-list="previewImageList"
                          @click="handleImagePreview(img)"
                        />
                        <div style="font-size: 12px; margin-top: 5px">
                          <div
                            :style="
                              isStationMatched(img.stationId)
                                ? 'font-weight: bold; color: #409EFF'
                                : ''
                            "
                            >{{ img.stationName }}</div
                          >
                          <div>{{ img.picTime }}</div>
                          <div style="margin-top: 5px">
                            <el-button
                              size="small"
                              :loading="originalImageLoading === `image1-${img.picturePath}`"
                              @click="selectImageForCheck(img, 'image1')"
                              >选为资料1</el-button
                            >
                            <el-button
                              size="small"
                              :loading="originalImageLoading === `image2-${img.picturePath}`"
                              @click="selectImageForCheck(img, 'image2')"
                              >选为资料2</el-button
                            >
                          </div>
                        </div>
                      </div>
                    </div>
                    <div
                      v-if="totalPages > 1"
                      style="
                        margin-top: 15px;
                        display: flex;
                        justify-content: center;
                        gap: 20px;
                        align-items: center;
                      "
                    >
                      <el-button
                        :disabled="vehicleImagesPage === 0"
                        size="small"
                        @click="handlePrevPage"
                        >上一页</el-button
                      >
                      <span style="font-size: 12px"
                        >第 {{ vehicleImagesPage + 1 }} 页 / 共 {{ totalPages }} 页 ({{
                          filteredVehicleImagesTotal
                        }}
                        张图片)</span
                      >
                      <el-button
                        :disabled="vehicleImagesPage >= maxPage"
                        size="small"
                        @click="handleNextPage"
                        >下一页</el-button
                      >
                    </div>
                    <div
                      v-else
                      style="margin-top: 10px; text-align: center; color: #909399; font-size: 12px"
                    >
                      已显示全部 {{ filteredVehicleImagesTotal }} 张图片
                    </div>
                  </div>
                  <el-alert v-else type="error" :closable="false">
                    {{ aiAuditResult.vehicle_images?.error || '查询失败' }}
                  </el-alert>
                </el-tab-pane>

                <el-tab-pane label="门架交易" name="gantry_trade">
                  <div v-if="aiAuditResult.gantry_trade?.success">
                    <div
                      style="
                        margin-bottom: 10px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                      "
                    >
                      <div style="display: flex; align-items: center; gap: 15px">
                        <span>共 {{ filteredGantryTradeRecords.length }} 条记录</span>
                        <el-checkbox v-model="excludeSpecialType186" size="small"
                          >排除特情186</el-checkbox
                        >
                      </div>
                      <div style="display: flex; gap: 10px">
                        <el-button
                          size="small"
                          type="primary"
                          @click="captureTable('gantry_trade', 'image1')"
                          >截图到资料1</el-button
                        >
                        <el-button
                          size="small"
                          type="success"
                          @click="captureTable('gantry_trade', 'image2')"
                          >截图到资料2</el-button
                        >
                      </div>
                    </div>
                    <el-table
                      ref="gantryTradeTableRef"
                      :data="filteredGantryTradeRecords"
                      border
                      max-height="450"
                      size="small"
                      stripe
                      :row-class-name="getGantryTradeRowClass"
                    >
                      <el-table-column
                        prop="vehiclePlate"
                        label="车牌号"
                        width="120"
                        show-overflow-tooltip
                      />
                      <el-table-column
                        prop="vehiclePlateColorName"
                        label="颜色"
                        width="85"
                        show-overflow-tooltip
                      />
                      <el-table-column
                        prop="passId"
                        label="通行标识ID"
                        width="330"
                        show-overflow-tooltip
                      />
                      <el-table-column
                        prop="gantryName"
                        label="门架名称"
                        width="260"
                        show-overflow-tooltip
                      >
                        <template #default="{ row }">
                          <span
                            :style="
                              isGantryMatched(row.gantryId)
                                ? 'font-weight: bold; color: #409EFF'
                                : ''
                            "
                            >{{ row.gantryName }}</span
                          >
                        </template>
                      </el-table-column>
                      <el-table-column
                        prop="transTime"
                        label="经过时间"
                        width="180"
                        show-overflow-tooltip
                      >
                        <template #default="{ row }">
                          <div style="display: flex; align-items: center; gap: 5px">
                            <span
                              :style="
                                isGateTimeMatched(row.transTime)
                                  ? 'font-weight: bold; color: #409EFF'
                                  : ''
                              "
                              >{{ row.transTime }}</span
                            >
                            <el-button
                              size="small"
                              type="primary"
                              link
                              @click="queryGantryImagesForRow(row)"
                              :loading="gantryImageLoading === row.gantryId"
                              :disabled="!row.gantryId"
                              >查</el-button
                            >
                          </div>
                        </template>
                      </el-table-column>
                      <el-table-column
                        prop="gantryOrderNumName"
                        label="门架顺序号"
                        show-overflow-tooltip
                      />
                      <el-table-column
                        prop="enVehicleTypeName"
                        label="入口车型"
                        show-overflow-tooltip
                      />
                      <el-table-column
                        prop="feeVehicleTypeName"
                        label="计费车型"
                        show-overflow-tooltip
                      />
                      <el-table-column
                        prop="mediaTypeName"
                        label="介质类型"
                        show-overflow-tooltip
                      />
                      <el-table-column
                        prop="tradeStatusName"
                        label="交易状态"
                        show-overflow-tooltip
                      />
                      <el-table-column
                        prop="receivableFee"
                        label="应收金额(元)"
                        show-overflow-tooltip
                      >
                        <template #default="{ row }">{{
                          formatFee(row.receivableFee || row.fee)
                        }}</template>
                      </el-table-column>
                      <el-table-column prop="actualFee" label="实收金额(元)" show-overflow-tooltip>
                        <template #default="{ row }">{{ formatFee(row.actualFee) }}</template>
                      </el-table-column>
                      <el-table-column prop="specialTypeName" label="特情" show-overflow-tooltip />
                    </el-table>
                  </div>
                  <el-alert v-else type="error" :closable="false">
                    {{ aiAuditResult.gantry_trade?.error || '查询失败' }}
                  </el-alert>
                </el-tab-pane>

                <el-tab-pane label="门架牌识" name="gantry_plate">
                  <div v-if="aiAuditResult.gantry_plate?.success">
                    <div
                      style="
                        margin-bottom: 10px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                      "
                    >
                      <span>共 {{ aiAuditResult.gantry_plate.total }} 条记录</span>
                      <div style="display: flex; gap: 10px">
                        <el-button
                          size="small"
                          type="primary"
                          @click="captureTable('gantry_plate', 'image1')"
                          >截图到资料1</el-button
                        >
                        <el-button
                          size="small"
                          type="success"
                          @click="captureTable('gantry_plate', 'image2')"
                          >截图到资料2</el-button
                        >
                      </div>
                    </div>
                    <el-table
                      ref="gantryPlateTableRef"
                      :data="aiAuditResult.gantry_plate.records"
                      border
                      max-height="450"
                      size="small"
                      stripe
                      :row-class-name="getGantryPlateRowClass"
                    >
                      <el-table-column
                        prop="vehiclePlate"
                        label="车牌号"
                        width="120"
                        show-overflow-tooltip
                      />
                      <el-table-column
                        prop="picId"
                        label="牌识流水"
                        width="300"
                        show-overflow-tooltip
                      />
                      <el-table-column prop="gantryName" label="门架名称" show-overflow-tooltip>
                        <template #default="{ row }">
                          <span
                            :style="
                              isGantryMatched(row.gantryId)
                                ? 'font-weight: bold; color: #409EFF'
                                : ''
                            "
                            >{{ row.gantryName }}</span
                          >
                        </template>
                      </el-table-column>
                      <el-table-column
                        prop="gantryOrderNumName"
                        label="门架顺序号"
                        show-overflow-tooltip
                      />
                      <el-table-column prop="picTime" label="经过时间" show-overflow-tooltip />
                      <el-table-column prop="vehicleTypeName" label="车型" show-overflow-tooltip />
                      <el-table-column prop="cameraId" label="相机编号" show-overflow-tooltip />
                    </el-table>
                  </div>
                  <el-alert v-else type="error" :closable="false">
                    {{ aiAuditResult.gantry_plate?.error || '查询失败' }}
                  </el-alert>
                </el-tab-pane>

                <el-tab-pane label="出口交易(ETC)" name="exit_trade_etc">
                  <div v-if="aiAuditResult.exit_trade_etc?.success">
                    <div
                      style="
                        margin-bottom: 10px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                      "
                    >
                      <span>共 {{ aiAuditResult.exit_trade_etc.total }} 条记录</span>
                      <div style="display: flex; gap: 10px">
                        <el-button
                          size="small"
                          type="primary"
                          @click="captureTable('exit_trade_etc', 'image1')"
                          >截图到资料1</el-button
                        >
                        <el-button
                          size="small"
                          type="success"
                          @click="captureTable('exit_trade_etc', 'image2')"
                          >截图到资料2</el-button
                        >
                      </div>
                    </div>
                    <el-table
                      ref="exitTradeEtcTableRef"
                      :data="aiAuditResult.exit_trade_etc.records"
                      border
                      max-height="300"
                      size="small"
                      stripe
                      :row-class-name="getExitTradeRowClass"
                    >
                      <el-table-column
                        prop="passid"
                        label="流水编号"
                        width="400"
                        show-overflow-tooltip
                      >
                        <template #default="{ row }">
                          <div style="display: flex; align-items: center; gap: 6px">
                            <span
                              :style="
                                row.passid === cloudPortalForm.passId
                                  ? 'font-weight: bold; color: #409EFF'
                                  : ''
                              "
                              >{{ row.passid }}</span
                            >
                            <el-button
                              size="small"
                              type="primary"
                              link
                              @click="aiAuditCheckPassId = row.passid"
                              >填</el-button
                            >
                          </div>
                        </template>
                      </el-table-column>
                      <el-table-column prop="plateNumber" label="出口车牌" show-overflow-tooltip />
                      <el-table-column
                        prop="enVehicleIdName"
                        label="入口车牌"
                        show-overflow-tooltip
                      />
                      <el-table-column
                        prop="identifyVehicleIdName"
                        label="识别车牌"
                        show-overflow-tooltip
                      />
                      <el-table-column
                        prop="entollstationname"
                        label="进站名"
                        show-overflow-tooltip
                      />
                      <el-table-column prop="entime" label="进站时间" show-overflow-tooltip />
                      <el-table-column
                        prop="enVehicleTypeName"
                        label="入口车型"
                        show-overflow-tooltip
                      />
                      <el-table-column
                        prop="exVehicleTypeName"
                        label="出口车型"
                        show-overflow-tooltip
                      />
                      <el-table-column
                        prop="extollstationname"
                        label="出站名"
                        show-overflow-tooltip
                      />
                      <el-table-column prop="extime" label="出站时间" show-overflow-tooltip />
                      <el-table-column
                        prop="mediaTypeName"
                        label="介质类型"
                        show-overflow-tooltip
                      />
                      <el-table-column prop="payfee" label="总应收金额(元)" show-overflow-tooltip>
                        <template #default="{ row }">{{ formatFee(row.payfee) }}</template>
                      </el-table-column>
                      <el-table-column prop="fee" label="总交易金额(元)" show-overflow-tooltip>
                        <template #default="{ row }">{{ formatFee(row.fee) }}</template>
                      </el-table-column>
                      <el-table-column
                        prop="discountfee"
                        label="总优惠金额(元)"
                        show-overflow-tooltip
                      >
                        <template #default="{ row }">{{ formatFee(row.discountfee) }}</template>
                      </el-table-column>
                      <el-table-column
                        prop="shortfee"
                        label="最小费额交易金额(元)"
                        show-overflow-tooltip
                      >
                        <template #default="{ row }">{{ formatFee(row.shortfee) }}</template>
                      </el-table-column>
                      <el-table-column
                        prop="FEEMILEAGE"
                        label="计费总里程数(公里)"
                        show-overflow-tooltip
                      >
                        <template #default="{ row }">{{
                          row.FEEMILEAGE ? (row.FEEMILEAGE / 1000).toFixed(2) : '-'
                        }}</template>
                      </el-table-column>
                      <el-table-column
                        prop="SHORTFEEMILEAGE"
                        label="最小费额里程数(公里)"
                        show-overflow-tooltip
                      >
                        <template #default="{ row }">{{
                          row.SHORTFEEMILEAGE ? (row.SHORTFEEMILEAGE / 1000).toFixed(2) : '-'
                        }}</template>
                      </el-table-column>
                      <el-table-column
                        prop="exitFeeTypeName"
                        label="计费方式"
                        show-overflow-tooltip
                      />
                      <el-table-column prop="specialtype" label="特情" show-overflow-tooltip />
                    </el-table>
                  </div>
                  <el-alert v-else type="error" :closable="false">
                    {{ aiAuditResult.exit_trade_etc?.error || '查询失败' }}
                  </el-alert>
                </el-tab-pane>

                <el-tab-pane label="出口交易(其它)" name="exit_trade_other">
                  <div v-if="aiAuditResult.exit_trade_other?.success">
                    <div
                      style="
                        margin-bottom: 10px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                      "
                    >
                      <span>共 {{ aiAuditResult.exit_trade_other.total }} 条记录</span>
                      <div style="display: flex; gap: 10px">
                        <el-button
                          size="small"
                          type="primary"
                          @click="captureTable('exit_trade_other', 'image1')"
                          >截图到资料1</el-button
                        >
                        <el-button
                          size="small"
                          type="success"
                          @click="captureTable('exit_trade_other', 'image2')"
                          >截图到资料2</el-button
                        >
                      </div>
                    </div>
                    <el-table
                      ref="exitTradeOtherTableRef"
                      :data="aiAuditResult.exit_trade_other.records"
                      border
                      max-height="300"
                      size="small"
                      stripe
                      :row-class-name="getExitTradeRowClass"
                    >
                      <el-table-column
                        prop="passid"
                        label="流水编号"
                        width="400"
                        show-overflow-tooltip
                      >
                        <template #default="{ row }">
                          <div style="display: flex; align-items: center; gap: 6px">
                            <span
                              :style="
                                row.passid === cloudPortalForm.passId
                                  ? 'font-weight: bold; color: #409EFF'
                                  : ''
                              "
                              >{{ row.passid }}</span
                            >
                            <el-button
                              size="small"
                              type="primary"
                              link
                              @click="aiAuditCheckPassId = row.passid"
                              >填</el-button
                            >
                          </div>
                        </template>
                      </el-table-column>
                      <el-table-column prop="plateNumber" label="出口车牌" show-overflow-tooltip />
                      <el-table-column
                        prop="enVehicleIdName"
                        label="入口车牌"
                        show-overflow-tooltip
                      />
                      <el-table-column
                        prop="identifyVehicleIdName"
                        label="识别车牌"
                        show-overflow-tooltip
                      />
                      <el-table-column
                        prop="entollstationname"
                        label="进站名"
                        show-overflow-tooltip
                      />
                      <el-table-column prop="entime" label="进站时间" show-overflow-tooltip />
                      <el-table-column
                        prop="enVehicleTypeName"
                        label="入口车型"
                        show-overflow-tooltip
                      />
                      <el-table-column
                        prop="exVehicleTypeName"
                        label="出口车型"
                        show-overflow-tooltip
                      />
                      <el-table-column
                        prop="extollstationname"
                        label="出站名"
                        show-overflow-tooltip
                      />
                      <el-table-column prop="extime" label="出站时间" show-overflow-tooltip />
                      <el-table-column
                        prop="mediaTypeName"
                        label="介质类型"
                        show-overflow-tooltip
                      />
                      <el-table-column prop="payfee" label="总应收金额(元)" show-overflow-tooltip>
                        <template #default="{ row }">{{ formatFee(row.payfee) }}</template>
                      </el-table-column>
                      <el-table-column prop="fee" label="总交易金额(元)" show-overflow-tooltip>
                        <template #default="{ row }">{{ formatFee(row.fee) }}</template>
                      </el-table-column>
                      <el-table-column
                        prop="discountfee"
                        label="总优惠金额(元)"
                        show-overflow-tooltip
                      >
                        <template #default="{ row }">{{ formatFee(row.discountfee) }}</template>
                      </el-table-column>
                      <el-table-column
                        prop="shortfee"
                        label="最小费额交易金额(元)"
                        show-overflow-tooltip
                      >
                        <template #default="{ row }">{{ formatFee(row.shortfee) }}</template>
                      </el-table-column>
                      <el-table-column
                        prop="FEEMILEAGE"
                        label="计费总里程数(公里)"
                        show-overflow-tooltip
                      >
                        <template #default="{ row }">{{
                          row.FEEMILEAGE ? (row.FEEMILEAGE / 1000).toFixed(2) : '-'
                        }}</template>
                      </el-table-column>
                      <el-table-column
                        prop="SHORTFEEMILEAGE"
                        label="最小费额里程数(公里)"
                        show-overflow-tooltip
                      >
                        <template #default="{ row }">{{
                          row.SHORTFEEMILEAGE ? (row.SHORTFEEMILEAGE / 1000).toFixed(2) : '-'
                        }}</template>
                      </el-table-column>
                      <el-table-column
                        prop="exitFeeTypeName"
                        label="计费方式"
                        show-overflow-tooltip
                      />
                      <el-table-column prop="specialtype" label="特情" show-overflow-tooltip />
                    </el-table>
                  </div>
                  <el-alert v-else type="error" :closable="false">
                    {{ aiAuditResult.exit_trade_other?.error || '查询失败' }}
                  </el-alert>
                </el-tab-pane>

                <el-tab-pane label="稽核工单" name="audit_order">
                  <div v-if="aiAuditResult.audit_order?.success">
                    <div
                      style="
                        margin-bottom: 10px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                      "
                    >
                      <span>共 {{ aiAuditResult.audit_order.total }} 条记录</span>
                      <div style="display: flex; gap: 10px">
                        <el-button
                          size="small"
                          type="primary"
                          @click="captureTable('audit_order', 'image1')"
                          >截图到资料1</el-button
                        >
                        <el-button
                          size="small"
                          type="success"
                          @click="captureTable('audit_order', 'image2')"
                          >截图到资料2</el-button
                        >
                      </div>
                    </div>
                    <el-table
                      ref="auditOrderTableRef"
                      :data="aiAuditResult.audit_order.records"
                      border
                      max-height="300"
                      size="small"
                      stripe
                    >
                      <el-table-column
                        prop="order_id"
                        label="工单编号"
                        width="200"
                        show-overflow-tooltip
                        fixed="left"
                      >
                        <template #default="{ row }">
                          <el-button
                            type="primary"
                            link
                            size="small"
                            @click="handleViewOrderDetail(row.order_id)"
                          >
                            {{ row.order_id }}
                          </el-button>
                        </template>
                      </el-table-column>
                      <el-table-column
                        prop="pass_id"
                        label="通行标识ID"
                        width="305"
                        show-overflow-tooltip
                      >
                        <template #default="{ row }">
                          <div style="display: flex; align-items: center; gap: 6px">
                            <span
                              :style="
                                row.pass_id === cloudPortalForm.passId
                                  ? 'font-weight: bold; color: #409EFF'
                                  : ''
                              "
                              >{{ row.pass_id }}</span
                            >
                            <el-button
                              size="small"
                              type="primary"
                              link
                              @click="aiAuditCheckPassId = row.pass_id"
                              >填</el-button
                            >
                          </div>
                        </template>
                      </el-table-column>
                      <el-table-column
                        prop="vehicle_no"
                        label="车牌号码"
                        width="98"
                        show-overflow-tooltip
                      />
                      <el-table-column prop="plate_color_name" label="车牌颜色" width="80" />
                      <el-table-column
                        prop="en_station_name"
                        label="入口站名"
                        width="110"
                        show-overflow-tooltip
                      />
                      <el-table-column
                        prop="ex_station_name"
                        label="出口站名"
                        width="110"
                        show-overflow-tooltip
                      />
                      <el-table-column
                        prop="en_time"
                        label="入口时间"
                        width="160"
                        show-overflow-tooltip
                      />
                      <el-table-column
                        prop="ex_time"
                        label="出口时间"
                        width="160"
                        show-overflow-tooltip
                      />
                      <el-table-column prop="en_vehicle_type_name" label="入口车型" width="100" />
                      <el-table-column prop="ex_vehicle_type_name" label="出口车型" width="100" />
                      <el-table-column prop="fee" label="通行费(分)" width="100">
                        <template #default="{ row }">{{ formatFee(row.fee) }}</template>
                      </el-table-column>
                      <el-table-column prop="label_code_name" label="标签名称" width="130">
                        <template #default="{ row }">
                          <div style="display: flex; align-items: center; gap: 4px">
                            <span>{{ row.label_code_name || '-' }}</span>
                            <el-button
                              v-if="row.label_code_name"
                              size="small"
                              type="primary"
                              link
                              @click="aiAuditSpecialSituation = row.label_code_name"
                              >填</el-button
                            >
                          </div>
                        </template>
                      </el-table-column>
                      <el-table-column prop="order_status_name" label="工单状态" width="130">
                        <template #default="{ row }">
                          <div style="display: flex; align-items: center; gap: 4px">
                            <el-tag :type="getOrderStatusType(row.order_status)" size="small">{{
                              row.order_status_name
                            }}</el-tag>
                            <el-button
                              v-if="row.order_status_name"
                              size="small"
                              type="primary"
                              link
                              @click="aiAuditRemark = row.order_status_name"
                              >填</el-button
                            >
                          </div>
                        </template>
                      </el-table-column>
                      <el-table-column prop="toll_fee" label="通行费(分)" width="100">
                        <template #default="{ row }">{{ formatFee(row.toll_fee) }}</template>
                      </el-table-column>
                      <el-table-column prop="penalty_fee" label="补缴金额(分)" width="110">
                        <template #default="{ row }">{{ formatFee(row.penalty_fee) }}</template>
                      </el-table-column>
                      <el-table-column prop="total_fee" label="总金额(分)" width="100">
                        <template #default="{ row }">{{ formatFee(row.total_fee) }}</template>
                      </el-table-column>
                      <el-table-column prop="review_name" label="审核人" width="80" />
                      <el-table-column
                        prop="review_time"
                        label="审核时间"
                        width="160"
                        show-overflow-tooltip
                      />
                      <el-table-column prop="operator_name" label="操作人" width="80" />
                      <el-table-column
                        prop="operate_time"
                        label="操作时间"
                        width="160"
                        show-overflow-tooltip
                      />
                      <el-table-column label="操作" width="80" fixed="right">
                        <template #default="{ row }">
                          <el-button
                            type="primary"
                            size="small"
                            @click="handleViewOrderDetail(row.order_id)"
                          >
                            查看
                          </el-button>
                        </template>
                      </el-table-column>
                    </el-table>
                  </div>
                  <el-alert v-else type="error" :closable="false">
                    {{ aiAuditResult.audit_order?.error || '查询失败' }}
                  </el-alert>
                </el-tab-pane>

                <el-tab-pane label="疑难车牌追查" name="suspected_car">
                  <div
                    v-if="aiAuditResult.suspected_car?.success"
                    style="max-height: 300px; overflow-y: auto"
                  >
                    <div
                      v-for="(item, idx) in aiAuditResult.suspected_car.trade_list"
                      :key="idx"
                      style="
                        margin-bottom: 15px;
                        padding: 10px;
                        border: 1px solid #ebeef5;
                        border-radius: 4px;
                      "
                    >
                      <el-descriptions :column="3" border size="small">
                        <el-descriptions-item label="车牌">{{
                          item.vehiclePlate
                        }}</el-descriptions-item>
                        <el-descriptions-item label="匹配率">
                          <el-tag :type="getRateType(item.rate)">
                            {{ formatMatchRate(item.rate) }}
                          </el-tag>
                        </el-descriptions-item>
                        <el-descriptions-item label="行程ID">{{
                          item.passId
                        }}</el-descriptions-item>
                      </el-descriptions>
                      <el-table
                        v-if="item.list && item.list.length > 0"
                        :data="item.list"
                        border
                        size="small"
                        style="margin-top: 10px"
                        max-height="150"
                      >
                        <el-table-column prop="matchingVehiclePlate" label="匹配车牌" width="100" />
                        <el-table-column
                          prop="matchingGantryName"
                          label="门架名称"
                          show-overflow-tooltip
                        />
                        <el-table-column
                          prop="matchingTransTime"
                          label="匹配时间"
                          width="160"
                          show-overflow-tooltip
                        />
                      </el-table>
                    </div>
                  </div>
                  <el-alert v-else type="error" :closable="false">
                    {{ aiAuditResult.suspected_car?.error || '查询失败' }}
                  </el-alert>
                </el-tab-pane>
              </el-tabs>

              <!-- 图片保存区域 -->
            </div>

            <!-- 查询结果 -->
            <div v-if="cloudPortalQueryResult && cloudPortalQueryResult.length > 0">
              <el-divider content-position="left">查询结果</el-divider>
              <el-table :data="cloudPortalQueryResult" border max-height="300">
                <el-table-column prop="field" label="字段" width="150" />
                <el-table-column prop="value" label="值" />
              </el-table>
            </div>
          </el-form>
        </div>

        <!-- 右侧：查核资料 -->
        <div style="width: 280px; flex-shrink: 0">
          <div
            style="border: 1px solid #e4e7ed; border-radius: 4px; padding: 8px; background: #fafafa"
          >
            <div style="font-weight: bold; margin-bottom: 8px; font-size: 12px; color: #303133">
              📷 查核资料
            </div>

            <!-- 查核资料1 -->
            <div style="margin-bottom: 8px">
              <div style="font-size: 11px; color: #606266; margin-bottom: 3px">查核资料1</div>
              <el-image
                v-if="aiAuditSelectedImage1"
                :src="getImageSrc(aiAuditSelectedImage1)"
                style="max-width: 100%; max-height: 120px"
                fit="contain"
              />
              <div
                v-else
                style="
                  color: #999;
                  border: 1px dashed #ddd;
                  padding: 12px;
                  text-align: center;
                  font-size: 11px;
                "
              >
                未选择图片
              </div>
            </div>

            <!-- 查核资料2 -->
            <div>
              <div style="font-size: 11px; color: #606266; margin-bottom: 3px">查核资料2</div>
              <el-image
                v-if="aiAuditSelectedImage2"
                :src="getImageSrc(aiAuditSelectedImage2)"
                style="max-width: 100%; max-height: 120px"
                fit="contain"
              />
              <div
                v-else
                style="
                  color: #999;
                  border: 1px dashed #ddd;
                  padding: 12px;
                  text-align: center;
                  font-size: 11px;
                "
              >
                未选择图片
              </div>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div style="display: flex; justify-content: flex-end; gap: 10px">
          <el-button @click="cloudPortalDialogVisible = false">关闭</el-button>
          <el-button
            type="primary"
            @click="saveImagesToDatabase"
            :loading="aiAuditSavingImages"
            :disabled="
              !(
                aiAuditSelectedImage1 ||
                aiAuditSelectedImage2 ||
                aiAuditReviewStatus ||
                aiAuditCheckPassId ||
                aiAuditSpecialSituation ||
                aiAuditCheckSplit ||
                aiAuditRemark
              )
            "
          >
            保存
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 通行门架名称组合详情对话框 -->
    <el-dialog v-model="showGantryNamesDialog" title="通行门架名称组合" width="600px" draggable>
      <div
        style="
          max-height: 400px;
          overflow-y: auto;
          padding: 10px;
          background: #f5f7fa;
          border-radius: 4px;
          word-break: break-all;
          line-height: 1.8;
        "
      >
        {{ cloudPortalForm.gantryNamesCombined || '-' }}
      </div>
      <template #footer>
        <el-button type="primary" @click="showGantryNamesDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 门架图库查询结果对话框 -->
    <el-dialog
      v-model="gantryImagesDialogVisible"
      title="门架图库查询结果"
      width="900px"
      destroy-on-close
      draggable
    >
      <div v-if="gantryImagesResult">
        <div style="margin-bottom: 15px; padding: 10px; background: #f5f7fa; border-radius: 4px">
          <div style="display: flex; gap: 30px; flex-wrap: wrap">
            <span><strong>门架名称:</strong> {{ gantryImagesResult.gantryName }}</span>
            <span><strong>经过时间:</strong> {{ gantryImagesResult.transTime }}</span>
            <span
              ><strong>查询范围:</strong> {{ gantryImagesResult.timeRange.startTime }} ~
              {{ gantryImagesResult.timeRange.endTime }}</span
            >
            <span><strong>共找到:</strong> {{ gantryImagesResult.total }} 张图片</span>
          </div>
        </div>

        <div
          v-if="gantryImagesResult.images.length > 0"
          style="display: flex; flex-wrap: wrap; gap: 15px"
        >
          <div
            v-for="(img, idx) in gantryImagesResult.images"
            :key="idx"
            style="width: 260px; border: 1px solid #ddd; border-radius: 4px; overflow: hidden"
          >
            <el-image
              :src="getImageSrc(img.bigPositivePic)"
              style="width: 100%; height: 150px; cursor: pointer"
              fit="contain"
              :preview-src-list="gantryImagesPreviewList"
              :initial-index="idx"
            />
            <div style="padding: 8px; font-size: 12px; background: #fafafa">
              <div style="margin-bottom: 4px">
                <strong>时间:</strong> {{ formatPicTime(img.picTime) }}
              </div>
              <div style="margin-bottom: 4px">
                <strong>车牌:</strong>
                <el-link
                  type="primary"
                  @click="queryVehicleDetail(img.vehPlate, img.picTime)"
                  style="cursor: pointer"
                  >{{ img.vehPlate }}</el-link
                >
              </div>
              <div style="margin-bottom: 8px"> <strong>门架:</strong> {{ img.stationName }} </div>
              <div style="display: flex; gap: 5px">
                <el-button size="small" @click="selectGantryImageAsCheck(img, 'image1')"
                  >选为资料1</el-button
                >
                <el-button size="small" @click="selectGantryImageAsCheck(img, 'image2')"
                  >选为资料2</el-button
                >
              </div>
            </div>
          </div>
        </div>

        <el-empty v-else description="未找到符合条件的图片" />
      </div>
    </el-dialog>

    <!-- 车辆详细信息对话框 -->
    <el-dialog
      v-model="vehicleDetailDialogVisible"
      :title="`车辆详细信息 - ${vehicleDetailPlate}`"
      width="95%"
      top="5vh"
      destroy-on-close
      draggable
    >
      <div v-if="vehicleDetailLoading" style="text-align: center; padding: 50px">
        <el-icon class="is-loading" style="font-size: 30px"><Loading /></el-icon>
        <div style="margin-top: 10px">正在查询车辆信息...</div>
      </div>

      <div v-else-if="vehicleDetailResult">
        <el-tabs v-model="vehicleDetailActiveTab">
          <el-tab-pane label="门架交易" name="gantry_trade">
            <el-table
              :data="vehicleDetailResult.gantry_trade?.records || []"
              border
              size="small"
              max-height="400"
            >
              <el-table-column prop="transTime" label="经过时间" width="160" />
              <el-table-column prop="gantryName" label="门架名称" show-overflow-tooltip />
              <el-table-column prop="fee" label="金额" width="100">
                <template #default="{ row }">{{ formatFee(row.fee) }}</template>
              </el-table-column>
              <el-table-column prop="vehiclePlateColorName" label="车牌颜色" width="100" />
              <el-table-column prop="feeVehicleTypeName" label="计费车型" width="120" />
            </el-table>
            <div style="margin-top: 10px; color: #909399">
              共 {{ vehicleDetailResult.gantry_trade?.total || 0 }} 条记录
            </div>
          </el-tab-pane>

          <el-tab-pane label="门架牌识" name="gantry_plate">
            <el-table
              :data="vehicleDetailResult.gantry_plate?.records || []"
              border
              size="small"
              max-height="400"
            >
              <el-table-column prop="picTime" label="拍摄时间" width="160" />
              <el-table-column prop="gantryName" label="门架名称" show-overflow-tooltip />
              <el-table-column prop="vehicleTypeName" label="车型" width="120" />
              <el-table-column prop="vehicleSpeed" label="车速" width="80" />
            </el-table>
            <div style="margin-top: 10px; color: #909399">
              共 {{ vehicleDetailResult.gantry_plate?.total || 0 }} 条记录
            </div>
          </el-tab-pane>

          <el-tab-pane label="出口交易(ETC)" name="exit_trade_etc">
            <el-table
              :data="vehicleDetailResult.exit_trade_etc?.records || []"
              border
              size="small"
              max-height="400"
            >
              <el-table-column prop="enTime" label="入口时间" width="160" />
              <el-table-column prop="exTime" label="出口时间" width="160" />
              <el-table-column prop="enStationName" label="入口站" show-overflow-tooltip />
              <el-table-column prop="exStationName" label="出口站" show-overflow-tooltip />
              <el-table-column prop="fee" label="金额" width="100">
                <template #default="{ row }">{{ formatFee(row.fee) }}</template>
              </el-table-column>
            </el-table>
            <div style="margin-top: 10px; color: #909399">
              共 {{ vehicleDetailResult.exit_trade_etc?.total || 0 }} 条记录
            </div>
          </el-tab-pane>

          <el-tab-pane label="出口交易(其它)" name="exit_trade_other">
            <el-table
              :data="vehicleDetailResult.exit_trade_other?.records || []"
              border
              size="small"
              max-height="400"
            >
              <el-table-column prop="enTime" label="入口时间" width="160" />
              <el-table-column prop="exTime" label="出口时间" width="160" />
              <el-table-column prop="enStationName" label="入口站" show-overflow-tooltip />
              <el-table-column prop="exStationName" label="出口站" show-overflow-tooltip />
              <el-table-column prop="fee" label="金额" width="100">
                <template #default="{ row }">{{ formatFee(row.fee) }}</template>
              </el-table-column>
            </el-table>
            <div style="margin-top: 10px; color: #909399">
              共 {{ vehicleDetailResult.exit_trade_other?.total || 0 }} 条记录
            </div>
          </el-tab-pane>

          <el-tab-pane label="稽核工单" name="audit_order">
            <el-table
              :data="vehicleDetailResult.audit_order?.records || []"
              border
              size="small"
              max-height="400"
            >
              <el-table-column prop="orderId" label="工单编号" show-overflow-tooltip />
              <el-table-column prop="orderTypeName" label="工单类型" width="120" />
              <el-table-column prop="createTime" label="创建时间" width="160" />
              <el-table-column prop="orderStatusName" label="状态" width="100" />
            </el-table>
            <div style="margin-top: 10px; color: #909399">
              共 {{ vehicleDetailResult.audit_order?.total || 0 }} 条记录
            </div>
          </el-tab-pane>
        </el-tabs>

        <div v-if="vehicleDetailResult.errors?.length > 0" style="margin-top: 10px; color: #e6a23c">
          部分查询失败: {{ vehicleDetailResult.errors.join('; ') }}
        </div>
      </div>
    </el-dialog>

    <!-- 工单详情对话框 -->
    <el-dialog
      v-model="showOrderDetailDialog"
      title="工单处理详情"
      width="92%"
      :close-on-click-modal="false"
      destroy-on-close
      draggable
      top="3vh"
    >

      <div v-if="orderDetailLoading" style="text-align: center; padding: 100px">
        <el-icon class="is-loading" :size="50"><Loading /></el-icon>
        <div style="margin-top: 20px; font-size: 16px">正在加载工单详情...</div>
      </div>

      <div v-else-if="currentOrderDetail" style="display: flex; gap: 16px; height: 82vh; overflow: hidden">
        <!-- 左侧：基本信息区域 -->
        <div style="width: 320px; flex-shrink: 0; overflow-y: auto; border: 1px solid #e4e7ed; border-radius: 4px; background: #fff">
          <!-- 工单基本信息 -->
          <div style="padding: 12px; border-bottom: 1px solid #ebeef5; background: #f5f7fa">
            <div style="font-weight: bold; font-size: 14px; color: #303133; margin-bottom: 8px">📋 基本信息</div>
            <el-descriptions :column="1" size="small" :labelStyle="{ width: '90px', color: '#909399' }">
              <el-descriptions-item label="车牌号码">{{ currentOrderDetail.labelVo?.vehicle_no || '-' }}</el-descriptions-item>
              <el-descriptions-item label="入口收费站">{{ currentOrderDetail.labelVo?.en_station_name || '-' }}</el-descriptions-item>
              <el-descriptions-item label="入口时间">{{ currentOrderDetail.labelVo?.en_time || '-' }}</el-descriptions-item>
              <el-descriptions-item label="出口收费站">{{ currentOrderDetail.labelVo?.ex_station_name || '-' }}</el-descriptions-item>
              <el-descriptions-item label="出口时间">{{ currentOrderDetail.labelVo?.ex_time || '-' }}</el-descriptions-item>
              <el-descriptions-item label="出口收费总额">
                <span style="color: #e6a23c; font-weight: bold">¥ {{ currentOrderDetail.pay_amount ? (currentOrderDetail.pay_amount / 100).toFixed(2) : '0.00' }} 元</span>
              </el-descriptions-item>
            </el-descriptions>
          </div>

          <!-- 标签信息 -->
          <div v-if="currentOrderDetail.labelCodeList && currentOrderDetail.labelCodeList.length > 0" style="padding: 12px; border-bottom: 1px solid #ebeef5">
            <div style="font-weight: bold; font-size: 14px; color: #303133; margin-bottom: 8px">🏷️ 标签信息</div>
            <div
              v-for="(label, idx) in currentOrderDetail.labelCodeList"
              :key="idx"
              style="margin-bottom: 8px; padding: 8px; background: #f5f7fa; border-radius: 4px"
            >
              <div style="display: flex; align-items: center; margin-bottom: 4px">
                <el-tag size="small" type="warning" style="margin-right: 8px">{{ label.labelCode }}</el-tag>
                <span style="font-weight: 500; font-size: 13px">{{ label.labelName }}</span>
              </div>
              <div v-if="label.auditMethod" style="font-size: 12px; color: #606266; line-height: 1.5; margin-top: 4px">
                {{ label.auditMethod }}
              </div>
            </div>
          </div>

          <!-- 稽核步骤配置 -->
          <div v-if="currentOrderDetail.auditCheckdescConfigs && currentOrderDetail.auditCheckdescConfigs.length > 0" style="padding: 12px; border-bottom: 1px solid #ebeef5">
            <div style="font-weight: bold; font-size: 14px; color: #303133; margin-bottom: 8px">✅ 稽核步骤</div>
            <div
              v-for="(config, idx) in currentOrderDetail.auditCheckdescConfigs"
              :key="idx"
              style="margin-bottom: 10px"
            >
              <div style="display: flex; align-items: center; margin-bottom: 6px">
                <span style="width: 18px; height: 18px; border-radius: 50%; background: #409eff; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 11px; margin-right: 6px">{{ Number(idx) + 1 }}</span>
                <span style="font-weight: 500; font-size: 13px">{{ config.checkStep1Name || config.checkStep2Name || config.checkStep3Name }}</span>
              </div>
              <div style="font-size: 12px; color: #606266; line-height: 1.5; padding-left: 24px">
                {{ config.checkStep1Desc || config.checkStep2Desc || config.checkStep3Desc }}
              </div>
            </div>
          </div>

          <!-- 图片列表 -->
          <div v-if="currentOrderDetail.picBeanVo?.picBeanList" style="padding: 12px">
            <div style="font-weight: bold; font-size: 14px; color: #303133; margin-bottom: 8px">
              📷 查看图片 ({{ currentOrderDetail.picBeanVo.total || currentOrderDetail.picBeanVo.picBeanList.length }})
            </div>
            <div style="max-height: 400px; overflow-y: auto">
              <div
                v-for="(pic, idx) in currentOrderDetail.picBeanVo.picBeanList"
                :key="idx"
                @click="selectedPicture = pic"
                style="
                  display: flex;
                  align-items: center;
                  padding: 6px;
                  margin-bottom: 4px;
                  cursor: pointer;
                  border-radius: 4px;
                  transition: all 0.2s;
                "
                :style="{
                  background: selectedPicture?.picId === pic.picId ? '#ecf5ff' : '#fff',
                  border: selectedPicture?.picId === pic.picId ? '1px solid #409eff' : '1px solid #ebeef5'
                }"
              >
                <img
                  v-if="pic.smallPositivePic"
                  :src="pic.smallPositivePic"
                  style="width: 48px; height: 36px; object-fit: cover; border-radius: 2px; margin-right: 8px; flex-shrink: 0"
                />
                <div style="flex: 1; min-width: 0">
                  <div style="font-size: 12px; font-weight: 500; color: #303133; white-space: nowrap; overflow: hidden; text-overflow: ellipsis">
                    {{ pic.stationName || ('图片 ' + (Number(idx) + 1)) }}
                  </div>
                  <div style="font-size: 11px; color: #909399; margin-top: 2px">{{ pic.picTime || '-' }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧：详细信息展示区域 -->
        <div style="flex: 1; overflow-y: auto; border: 1px solid #e4e7ed; border-radius: 4px; background: #fff; padding: 16px">
          <!-- 稽核信息 -->
          <div style="margin-bottom: 20px">
            <div style="display: flex; align-items: center; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid #409eff">
              <span style="font-size: 16px; font-weight: bold; color: #303133">📊 稽核信息</span>
            </div>
            <el-alert
              type="info"
              :closable="false"
              show-icon
              style="margin-bottom: 12px"
            >
              <template #title>
                <span style="font-size: 13px">【{{ currentOrderDetail.labelVo?.vehicle_no }}】稽核模型利用交易流水中"收费车型与真实车型不符"的特征值进行敏感性筛查，须稽查人员通过门架图片、监控录像等方式确认车辆车型信息。</span>
              </template>
            </el-alert>

            <!-- 处理结论展示 -->
            <div v-if="currentOrderDetail.labelVo?.audit_remark" style="background: linear-gradient(135deg, #f0f9eb 0%, #f5f7fa 100%); padding: 16px; border-radius: 8px; margin-bottom: 12px; border-left: 4px solid #67c23a; box-shadow: 0 2px 8px rgba(103, 194, 58, 0.1)">
              <div style="font-size: 14px; font-weight: bold; color: #67c23a; margin-bottom: 10px; display: flex; align-items: center">
                <el-icon :size="18" style="margin-right: 6px"><CircleCheck /></el-icon>
                处理结论
              </div>
              <div style="color: #606266; line-height: 1.8; font-size: 13px">
                {{ currentOrderDetail.labelVo.audit_remark }}
              </div>
            </div>

            <!-- 标签详情展示 -->
            <div v-if="currentOrderDetail.labelCodeList && currentOrderDetail.labelCodeList.length > 0" style="background: #fafafa; padding: 12px; border-radius: 4px; margin-bottom: 12px">
              <div style="font-weight: bold; font-size: 14px; color: #303133; margin-bottom: 8px">【主标签】</div>
              <div
                v-for="(label, idx) in currentOrderDetail.labelCodeList"
                :key="idx"
                style="display: inline-flex; align-items: center; margin: 4px 8px 4px 0"
              >
                <el-tag type="warning" effect="dark" size="large">{{ label.labelName }}</el-tag>
              </div>
            </div>

            <!-- 稽核流程步骤卡片 -->
            <div v-if="currentOrderDetail.auditCheckdescConfigs && currentOrderDetail.auditCheckdescConfigs.length > 0">
              <el-steps :active="3" finish-status="success" simple style="margin-bottom: 16px">
                <el-step title="车型确认" />
                <el-step title="费用测算" />
                <el-step title="稽核取证" />
              </el-steps>

              <div
                v-for="(config, idx) in currentOrderDetail.auditCheckdescConfigs"
                :key="idx"
                style="display: flex; gap: 16px; margin-bottom: 16px"
              >
                <!-- 步骤1：车型确认 -->
                <div style="flex: 1; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 16px; border-radius: 8px; color: #fff">
                  <div style="display: flex; align-items: center; margin-bottom: 8px">
                    <el-icon :size="24" style="margin-right: 8px"><CircleCheck /></el-icon>
                    <span style="font-weight: bold; font-size: 15px">{{ config.checkStep1Name || '车型确认' }}</span>
                  </div>
                  <div style="font-size: 13px; line-height: 1.6; opacity: 0.95">{{ config.checkStep1Desc || '通过图片和监控录像核实实际车型' }}</div>
                </div>

                <!-- 步骤2：费用测算 -->
                <div style="flex: 1; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 16px; border-radius: 8px; color: #fff">
                  <div style="display: flex; align-items: center; margin-bottom: 8px">
                    <el-icon :size="24" style="margin-right: 8px"><Money /></el-icon>
                    <span style="font-weight: bold; font-size: 15px">{{ config.checkStep2Name || '费用测算' }}</span>
                  </div>
                  <div style="font-size: 13px; line-height: 1.6; opacity: 0.95">{{ config.checkStep2Desc || '测算实际行驶路径应收费额，与出口实收或省域拆分金额校核是否一致' }}</div>
                </div>

                <!-- 步骤3：稽核取证 -->
                <div style="flex: 1; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 16px; border-radius: 8px; color: #fff">
                  <div style="display: flex; align-items: center; margin-bottom: 8px">
                    <el-icon :size="24" style="margin-right: 8px"><Camera /></el-icon>
                    <span style="font-weight: bold; font-size: 15px">{{ config.checkStep3Name || '稽核取证' }}</span>
                  </div>
                  <div style="font-size: 13px; line-height: 1.6; opacity: 0.95">{{ config.checkStep3Desc || '车型截图：门架图片或出入口录像\n金额截图：实际应收金额、出口实收金额' }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- 门架图片展示 -->
          <div v-if="selectedPicture">
            <div style="display: flex; align-items: center; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid #67c23a">
              <span style="font-size: 16px; font-weight: bold; color: #303133">🖼️ 门架图片</span>
              <el-tag style="margin-left: 12px" type="success">{{ selectedPicture.stationName || '图片详情' }}</el-tag>
            </div>

            <!-- 图片信息 -->
            <el-descriptions :column="4" border size="small" style="margin-bottom: 16px">
              <el-descriptions-item label="拍摄时间">{{ selectedPicture.picTime || '-' }}</el-descriptions-item>
              <el-descriptions-item label="车牌号码">{{ selectedPicture.vehPlate || '-' }}</el-descriptions-item>
              <el-descriptions-item label="站ID">{{ selectedPicture.stationId || '-' }}</el-descriptions-item>
              <el-descriptions-item label="拍摄位置">{{ selectedPicture.shootPosition === '1' ? '车头' : (selectedPicture.shootPosition === '2' ? '车尾' : '-') }}</el-descriptions-item>
            </el-descriptions>

            <!-- 大图展示 -->
            <div style="text-align: center; background: #f5f7fa; padding: 20px; border-radius: 8px; margin-bottom: 16px">
              <el-image
                v-if="selectedPicture.bigPositivePic"
                :src="selectedPicture.bigPositivePic"
                fit="contain"
                style="max-width: 100%; max-height: 500px; border-radius: 4px"
                :preview-src-list="[selectedPicture.bigPositivePic]"
                preview-teleported
                :z-index="9999"
              >
                <template #error>
                  <div class="image-slot" style="display: flex; justify-content: center; align-items: center; width: 100%; height: 300px; background: #f5f7fa; color: #909399">
                    <el-icon :size="48"><PictureFilled /></el-icon>
                  </div>
                </template>
              </el-image>
              <div v-else style="color: #909399; padding: 40px">
                <el-icon :size="64"><WarningFilled /></el-icon>
                <div style="margin-top: 12px; font-size: 14px">暂无大图</div>
              </div>
            </div>

            <!-- 小图对比展示 -->
            <div v-if="selectedPicture.smallPositivePic || selectedPicture.smallBackPic" style="display: flex; gap: 12px; margin-bottom: 16px">
              <div v-if="selectedPicture.smallPositivePic" style="flex: 1; text-align: center">
                <div style="font-size: 12px; color: #606266; margin-bottom: 6px">车头小图</div>
                <el-image
                  :src="selectedPicture.smallPositivePic"
                  fit="cover"
                  style="width: 100%; height: 180px; border-radius: 4px"
                  :preview-src-list="[selectedPicture.smallPositivePic]"
                  preview-teleported
                />
              </div>
              <div v-if="selectedPicture.smallBackPic" style="flex: 1; text-align: center">
                <div style="font-size: 12px; color: #606266; margin-bottom: 6px">车尾小图</div>
                <el-image
                  :src="selectedPicture.smallBackPic"
                  fit="cover"
                  style="width: 100%; height: 180px; border-radius: 4px"
                  :preview-src-list="[selectedPicture.smallBackPic]"
                  preview-teleported
                />
              </div>
            </div>
          </div>

          <!-- 无选中图片时的提示 -->
          <div v-else style="text-align: center; padding: 80px 20px; color: #909399">
            <el-icon :size="80"><PictureFilled /></el-icon>
            <div style="margin-top: 16px; font-size: 16px">请从左侧列表选择图片查看</div>
            <div style="margin-top: 8px; font-size: 13px">共 {{ currentOrderDetail.picBeanVo?.total || currentOrderDetail.picBeanVo?.picBeanList?.length || 0 }} 张图片</div>
          </div>

          <!-- 完整原始数据（可折叠） -->
          <el-collapse style="margin-top: 20px">
            <el-collapse-item name="raw_data">
              <template #title>
                <div style="display: flex; align-items: center; justify-content: space-between; width: 100%; padding-right: 16px">
                  <span>🔧 查看完整原始JSON数据</span>
                  <el-button
                    type="primary"
                    size="small"
                    :icon="CopyDocument"
                    @click.stop="copyRawJsonData"
                  >
                    一键复制
                  </el-button>
                </div>
              </template>
              <pre style="background: #f5f7fa; padding: 16px; border-radius: 4px; overflow-x: auto; font-size: 12px; line-height: 1.5; max-height: 400px; overflow-y: auto">{{ JSON.stringify(currentOrderDetail, null, 2) }}</pre>
            </el-collapse-item>
          </el-collapse>
        </div>
      </div>

      <div v-else style="text-align: center; padding: 100px; color: #909399">
        <el-icon :size="60"><WarningFilled /></el-icon>
        <div style="margin-top: 20px; font-size: 16px">暂无工单数据</div>
      </div>
    </el-dialog>

    <!-- 导出进度对话框 -->
    <el-dialog
      v-model="exportProgressVisible"
      title="导出进度"
      width="500px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
      draggable
    >
      <div style="padding: 20px 0">
        <el-progress
          :percentage="exportProgress"
          :stroke-width="20"
          :text-inside="true"
          style="margin-bottom: 20px"
        />
        <div style="text-align: center; color: #606266; font-size: 14px">
          {{ exportProgressText }}
        </div>
        <div
          v-if="exportTotalCount > 0"
          style="text-align: center; color: #909399; font-size: 12px; margin-top: 10px"
        >
          共 {{ exportTotalCount }} 条数据
        </div>
      </div>
    </el-dialog>

    <!-- 原图预览对话框 -->
    <el-dialog
      v-model="tableImagePreviewVisible"
      title="原图预览"
      width="800px"
      :close-on-click-modal="true"
      destroy-on-close
    >
      <div v-if="tableImagePreviewLoading" style="text-align: center; padding: 40px">
        <el-icon class="is-loading" :size="40">
          <Loading />
        </el-icon>
        <div style="margin-top: 10px; color: #909399">正在加载原图...</div>
      </div>
      <div v-else-if="tableImagePreviewUrl" style="text-align: center">
        <el-image
          :src="tableImagePreviewUrl"
          fit="contain"
          style="max-width: 100%; max-height: 600px"
          :preview-src-list="[tableImagePreviewUrl]"
          :preview-teleported="true"
          preview-z-index="9999"
        />
      </div>
    </el-dialog>

    <!-- 拆分统计弹窗 -->
    <el-dialog v-model="statisticsVisible" title="拆分统计" width="400px" destroy-on-close>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="通行量(车次)">
          {{ splitStatistics.split_count }}
        </el-descriptions-item>
        <el-descriptions-item label="拆回金额(元)">
          ¥{{ splitStatistics.total_split_amount.toFixed(2) }}
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 已拆详情弹窗 -->
    <el-dialog v-model="splitDetailVisible" title="拆分详情" width="80%" destroy-on-close>
      <div class="split-detail-wrapper">
        <el-descriptions v-if="splitDetailRow" :column="2" border size="small" class="split-detail-desc">
          <el-descriptions-item
            v-for="key in displayColumns.filter(k => k !== '拆分月份')"
            :key="key"
            :label="key"
            label-class-name="detail-label"
            class-name="detail-value"
          >
            <span
              class="value-text"
              @click="showFullValue(splitDetailRow[key] || '-', key)"
              :title="'点击查看完整内容'"
            >
              {{ splitDetailRow[key] || '-' }}
            </span>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>

    <!-- 完整值查看弹窗 -->
    <el-dialog v-model="fullValueVisible" title="字段详情" width="600px" append-to-body>
      <div class="full-value-container">
        <div class="field-name">{{ fullValueField }}</div>
        <div class="field-value">{{ fullValueContent }}</div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as XLSX from 'xlsx'
import JSZip from 'jszip'
import { XMLParser } from 'fast-xml-parser'
import { domToPng } from 'modern-screenshot'
import ExcelJS from 'exceljs'
import { saveAs } from 'file-saver'
import { processImageForExcel, createPlaceholderImage } from '@/utils/excelImageHelper'
import {
  ElMessage,
  ElNotification,
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
  ElRadio,
  ElTag,
  ElDivider,
  ElTabs,
  ElTabPane,
  ElProgress,
  ElMessageBox
} from 'element-plus'
import { CopyDocument, Picture, Search, Loading, WarningFilled, CircleCheck, Money, Camera, PictureFilled } from '@element-plus/icons-vue'
import {
  getSplitMatchTables,
  getSplitMatchData,
  executeSplitMatch,
  getExportSplitMatchData,
  previewSplitMatch,
  verifyPassId,
  aiAuditBatchQuery,
  aiAuditOrderDetail,
  aiAuditSaveImages,
  aiAuditOriginalImage,
  aiAuditVehicleImages,
  aiAuditGantryImages,
  getOriginalImage,
  updateSplitMatchData,
  getSplitStatistics,
  type AIAuditVehicleImage,
  type AIAuditGantryImage,
  type AIAuditBatchQueryResult,
  type AIAuditGantryTrade,
  keepCloudPortalAlive
} from '@/api/split-match'
import { useCloudPortal } from '@/hooks/split-match/useCloudPortal'
import request from '@/axios'
import { useUserStore } from '@/store/modules/user'

const userStore = useUserStore()

interface MatchResult {
  matched_count: number
  unmatched_count: number
  total: number
  pass_id_matched?: number
  check_id_matched?: number
  debug?: {
    total_time?: number
    count_duration?: number
    yc_duration?: number
    cf_duration?: number
    match_duration?: number
    select_sql?: string
    yc_query?: string
    cf_query?: string
    update_by_pass_id_query?: string
    update_by_check_id_query?: string
    records_source?: string
    records_count?: number
    valid_record_count?: number
    cf_record_count?: number
    cf_table?: string
    pass_id_matched_count?: number
    check_id_matched_count?: number
    pass_id_update_count?: number
    check_id_update_count?: number
    pass_id_batch_count?: number
    check_id_batch_count?: number
  }
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
const exportLoading = ref(false)
const exportProgress = ref(0)
const exportProgressText = ref('')
const exportProgressVisible = ref(false)
const exportTotalCount = ref(0)
const exportProcessedCount = ref(0)
const matchResult = ref<MatchResult | null>(null)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const selectedRow = ref<Record<string, unknown> | null>(null)
const dialogVisible = ref(false)
const editedRow = ref<Record<string, any> | null>(null)

// 详细信息窗口字段显示顺序
const detailFieldOrder = [
  '通行标识ID',
  '车牌号码',
  '车牌',
  '核查通行标识',
  '复核情况',
  '核查拆分',
  '备注',
  '特情',
  '查核资料1',
  '查核资料2',
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

// 计算属性：按顺序返回字段
const sortedDetailFields = computed(() => {
  if (!editedRow.value) return []
  
  const allFields = Object.keys(editedRow.value)
  const sortedFields: string[] = []
  
  // 首先添加预定义顺序中存在的字段
  detailFieldOrder.forEach((field) => {
    if (allFields.includes(field)) {
      sortedFields.push(field)
    }
  })
  
  // 然后添加其他未在预定义顺序中的字段
  allFields.forEach((field) => {
    if (!sortedFields.includes(field)) {
      sortedFields.push(field)
    }
  })
  
  return sortedFields
})

// 图片预览列表
const imagePreviewList = ref<Record<string, string[]>>({})
// 存储图片的二进制数据，用于上传到后端
const imageBinaryData = ref<Record<string, Blob>>({})
const activeImageField = ref<string>('查核资料1')

// 表格图片预览相关
const tableImagePreviewVisible = ref(false)
const tableImagePreviewUrl = ref('')
const tableImagePreviewLoading = ref(false)

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

const normalizeFilters = (filtersObj: Record<string, any>): Record<string, string> => {
  const normalized: Record<string, string> = {}
  for (const [key, value] of Object.entries(filtersObj)) {
    if (value !== null && value !== undefined && String(value).trim() !== '') {
      normalized[key] =
        typeof value === 'object' ? value.value || value.label || JSON.stringify(value) : String(value)
    }
  }
  return normalized
}

const handlePassIdBlur = (event: FocusEvent) => {
  const inputElement = event.target as HTMLInputElement
  const inputValue = inputElement?.value?.trim()
  
  if (!inputValue) return
  
  const currentValue = filters.value['通行标识ID']
  
  if (!currentValue || String(currentValue).trim() === '') {
    filters.value['通行标识ID'] = inputValue
  }
  
  if (!recentCheckIds.value.includes(inputValue)) {
    recentCheckIds.value.unshift(inputValue)
    if (recentCheckIds.value.length > 10) {
      recentCheckIds.value = recentCheckIds.value.slice(0, 10)
    }
    localStorage.setItem('recentCheckIds', JSON.stringify(recentCheckIds.value))
  }
}

const handlePassIdChange = (value: string | Record<string, any>) => {
  if (value && typeof value === 'object') {
    const strValue = value.value || value.label || ''
    filters.value['通行标识ID'] = strValue
  }
}

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
    const response = await getSplitMatchTables()

    if (response && response.code === 200 && Array.isArray(response.data)) {
      tableList.value = response.data.map((tableName: string) => {
        const label = tableName.replace('_yc', '')
        return {
          label,
          value: tableName
        }
      })
    } else {
      tableList.value = []
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
    const normalizedFilters = normalizeFilters(filters.value)

    const params = {
      table_name: selectedTable.value,
      filters: JSON.stringify(normalizedFilters),
      page: currentPage.value,
      page_size: pageSize.value
    }

    const response = await getSplitMatchData(params)

    let tableDataArray: any[] = []
    let columnsArray: string[] = []
    let totalCount = 0

    if (response && response.code === 200 && response.data) {
      const responseData = response.data
      tableDataArray = Array.isArray(responseData.data) ? responseData.data : []
      columnsArray = Array.isArray(responseData.columns) ? responseData.columns : []
      totalCount = typeof responseData.total === 'number' ? responseData.total : 0
    }

    tableData.value = tableDataArray
    displayColumns.value = columnsArray
    total.value = totalCount

    // 提取核查拆分字段的唯一值
    const splitValues = new Set<string>()
    splitValues.add('已拆')
    splitValues.add('未拆')
    tableDataArray.forEach((row) => {
      const value = row['核查拆分']
      if (value && typeof value === 'string') {
        splitValues.add(value)
      }
    })
    checkSplitOptions.value = Array.from(splitValues)
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

const handleTableChange = async () => {
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
    // 1. 先获取所有记录（不带分页）
    const exportParams = {
      table_name: selectedTable.value,
      filters: JSON.stringify(normalizeFilters(filters.value))
    }
    const exportResponse = await getExportSplitMatchData(exportParams)

    if (!exportResponse || exportResponse.code !== 200 || !exportResponse.data || !Array.isArray(exportResponse.data.data)) {
      ElMessage.error('获取记录失败')
      return
    }

    // 2. 提取所有记录的通行标识ID和核查通行标识
    const allRecords = exportResponse.data.data
    const recordsToMatch = allRecords.map((record: any) => ({
      id: record.id,
      通行标识ID: record['通行标识ID'],
      核查通行标识: record['核查通行标识']
    }))

    // 3. 将记录传给后端执行匹配
    const params = {
      table_name: selectedTable.value,
      records: recordsToMatch
    }

    // 4. 调用预览接口获取SQL
    const previewResponse = await previewSplitMatch(params)
    if (
      previewResponse &&
      previewResponse.code === 200 &&
      previewResponse.data?.sqls
    ) {
      // SQL preview available
    }

    // 5. 立即执行匹配
    const response = await executeSplitMatch(params)

    let responseData: MatchResult | null = null
    if (response && response.code === 200 && response.data) {
      responseData = response.data
    }

    if (responseData) {
      matchResult.value = responseData
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

// 拆分统计相关状态
const splitStatistics = ref({ split_count: 0, total_split_amount: 0 })
const statisticsLoading = ref(false)
const statisticsVisible = ref(false)

const handleSplitStatistics = async () => {
  if (!selectedTable.value) {
    ElMessage.warning('请先选择数据表')
    return
  }
  statisticsLoading.value = true
  try {
    const response = await getSplitStatistics({ table_name: selectedTable.value })
    if (response && response.code === 200 && response.data) {
      splitStatistics.value = response.data
      statisticsVisible.value = true
    } else {
      ElMessage.error('获取拆分统计失败')
    }
  } catch (error) {
    console.error('获取拆分统计失败:', error)
    ElMessage.error('获取拆分统计失败')
  } finally {
    statisticsLoading.value = false
  }
}

// 已拆详情弹窗相关状态
const splitDetailVisible = ref(false)
const splitDetailRow = ref<Record<string, unknown> | null>(null)

// 完整值查看弹窗相关状态
const fullValueVisible = ref(false)
const fullValueField = ref('')
const fullValueContent = ref('')

const showFullValue = (value: any, field: string) => {
  fullValueField.value = field
  fullValueContent.value = String(value || '-')
  fullValueVisible.value = true
}

const handleSplitDetailClick = async (row: Record<string, unknown>) => {
  const passIdById = String(row['通行标识ID'] || '').trim()
  const passIdByCheck = String(row['核查通行标识'] || '').trim()

  if (!passIdById && !passIdByCheck) {
    ElMessage.warning('未找到有效的通行标识ID或核查通行标识')
    return
  }

  splitDetailVisible.value = true
  splitDetailRow.value = { '加载中...': '正在查询数据库，请稍候...' }
  displayColumns.value = ['加载中...']

  try {
    const currentUser = userStore.getUserInfo

    const params: any = {
      pass_id: passIdById || passIdByCheck,
      verify_type: '通行标识ID',
      user_id: currentUser?.id,
      username: currentUser?.username
    }

    if (passIdById && passIdByCheck && passIdById !== passIdByCheck) {
      params.pass_id_secondary = passIdByCheck
    }

    const response = await verifyPassId(params)

    if (response && response.code === 200 && response.data) {
      const result = response.data as any

      if (result.exists && result.records && result.records.length > 0) {
        const record = result.records[0]
        splitDetailRow.value = record

        if (result.columns && result.columns.length > 0) {
          displayColumns.value = result.columns
        } else {
          displayColumns.value = Object.keys(record)
        }

        const valueCount = result.query_values?.length || 1
        ElMessage.success(`查询成功：找到 ${result.match_count} 条匹配记录 (查询了 ${valueCount} 个ID)`)
      } else {
        splitDetailRow.value = {
          '查询结果': `未找到匹配记录 (已查询通行标识ID: ${passIdById || '无'}${passIdByCheck ? ', ' + passIdByCheck : ''})`
        }
        displayColumns.value = ['查询结果']
        ElMessage.warning('未找到匹配记录')
      }
    } else {
      splitDetailRow.value = { '错误': response?.message || '查询失败' }
      displayColumns.value = ['错误']
      ElMessage.error(response?.message || '查询失败')
    }
  } catch (error: any) {
    console.error('查询拆分详情失败:', error)
    splitDetailRow.value = { '错误': error?.message || '查询失败，请稍后重试' }
    displayColumns.value = ['错误']
    ElMessage.error(error?.message || '查询失败，请稍后重试')
  }
}

const handleIdClick = async (row: Record<string, unknown>) => {
  selectedRow.value = row
  editedRow.value = { ...row, '查核资料1': null, '查核资料2': null }
  imagePreviewList.value = { 查核资料1: [], 查核资料2: [] }
  dialogVisible.value = true

  // 按需加载该行高清原图
  try {
    const passId = String(row['通行标识ID'] || '')
    if (passId && selectedTable.value) {
      const [resp1, resp2] = await Promise.all([
        getOriginalImage({ table_name: selectedTable.value, pass_id: passId, field: '查核资料1' }),
        getOriginalImage({ table_name: selectedTable.value, pass_id: passId, field: '查核资料2' })
      ])

      if (editedRow.value) {
        const image1 = resp1?.code === 200 && resp1.data ? resp1.data : null
        const image2 = resp2?.code === 200 && resp2.data ? resp2.data : null

        editedRow.value['查核资料1'] = image1
        editedRow.value['查核资料2'] = image2
        imagePreviewList.value = {
          查核资料1: image1 ? [String(image1)] : [],
          查核资料2: image2 ? [String(image2)] : []
        }
      }
    }
  } catch (error) {
    console.error('加载原图失败:', error)
  }

  // 添加粘贴事件监听
  setTimeout(() => {
    const dialogEl = document.querySelector('.el-dialog')
    if (dialogEl) {
      dialogEl.addEventListener('paste', handlePaste)
    }
  }, 100)
}

// 将图片转换为 WebP 格式的函数
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

const handleTableImagePreview = async (row: any, field: string) => {
  if (!selectedTable.value || !row['通行标识ID']) {
    ElMessage.warning('无法获取原图：缺少必要参数')
    return
  }

  tableImagePreviewLoading.value = true
  tableImagePreviewVisible.value = true
  tableImagePreviewUrl.value = ''

  try {
    const response = await getOriginalImage({
      table_name: selectedTable.value,
      pass_id: row['通行标识ID'],
      field: field
    })

    if (response && response.code === 200 && response.data) {
      let imageData: string = response.data
      if (imageData.startsWith('data:') && !imageData.startsWith('data:image/')) {
        ElMessage.error('该记录图片数据异常，无法预览')
        tableImagePreviewVisible.value = false
        return
      }
      if (!imageData.startsWith('data:')) {
        imageData = `data:image/jpeg;base64,${imageData}`
      }
      tableImagePreviewUrl.value = imageData
    } else {
      ElMessage.error('获取原图失败')
      tableImagePreviewVisible.value = false
    }
  } catch (error) {
    console.error('获取原图失败:', error)
    ElMessage.error('获取原图失败')
    tableImagePreviewVisible.value = false
  } finally {
    tableImagePreviewLoading.value = false
  }
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

const verifyLoading = ref(false)

const {
  cloudPortalDialogVisible,
  cloudPortalLoggedIn,
  cloudPortalUserInfo,
  cloudPortalForm,
  captchaImage,
  loginLoading,
  needManualCaptcha,
  loadCloudPortalCredentials,
  refreshCaptcha,
  handleCloudPortalLogin,
  handleCloudPortalLogout
} = useCloudPortal()

let keepAliveTimer: ReturnType<typeof setInterval> | null = null
const showGantryNamesDialog = ref(false)
const cloudPortalQueryResult = ref<any[]>([])

const aiAuditLoading = ref(false)
const aiAuditResult = ref<AIAuditBatchQueryResult | null>(null)
const aiAuditActiveTab = ref('vehicle_images')
const aiAuditSelectedImage1 = ref<string>('')
const aiAuditSelectedImage2 = ref<string>('')
const aiAuditSavingImages = ref(false)
const ORIGINAL_IMAGE_CACHE_MAX_SIZE = 100
const originalImageCache = new Map<string, string>()

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
const originalImageLoading = ref<string>('')
const previewLoading = ref<string>('')
const previewLoadingText = ref<string>('')

const gantryTradeTableRef = ref()
const gantryPlateTableRef = ref()
const exitTradeEtcTableRef = ref()
const exitTradeOtherTableRef = ref()
const auditOrderTableRef = ref()

const aiAuditReviewStatus = ref<string>('')
const aiAuditCheckPassId = ref<string>('')
const aiAuditSpecialSituation = ref<string>('')
const aiAuditCheckSplit = ref<string>('')
const aiAuditRemark = ref<string>('')

const gantryImageLoading = ref<string>('')
const gantryImagesDialogVisible = ref(false)
const gantryImagesResult = ref<{
  gantryName: string
  gantryId: string
  transTime: string
  timeRange: { startTime: string; endTime: string }
  images: AIAuditGantryImage[]
  total: number
} | null>(null)
const gantryImagesPreviewList = ref<string[]>([])

const vehicleDetailDialogVisible = ref(false)
const vehicleDetailPlate = ref('')
const vehicleDetailLoading = ref(false)
const vehicleDetailResult = ref<AIAuditBatchQueryResult | null>(null)
const vehicleDetailActiveTab = ref('gantry_trade')

const STORAGE_KEY_SPECIAL_SITUATION = 'split_match_special_situation_history'
const STORAGE_KEY_REMARK = 'split_match_remark_history'
const MAX_HISTORY = 10

const showOrderDetailDialog = ref(false)
const orderDetailLoading = ref(false)
const currentOrderDetail = ref<any>(null)
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
    }, userStore.getUserInfo?.id as number | undefined)

    if (response && response.code === 200 && response.data) {
      currentOrderDetail.value = response.data
      if (currentOrderDetail.value?.picBeanVo?.picBeanList?.length > 0) {
        selectedPicture.value = currentOrderDetail.value.picBeanVo.picBeanList[0]
      }
      ElMessage.success('获取工单详情成功')
    } else {
      ElMessage.error('获取工单详情失败')
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

const specialSituationHistory = ref<string[]>([])
const remarkHistory = ref<string[]>([])

const loadHistoryFromStorage = (key: string): string[] => {
  try {
    const data = localStorage.getItem(key)
    if (data) {
      return JSON.parse(data)
    }
  } catch (error) {
    console.error(`加载历史记录失败 (${key}):`, error)
  }
  return []
}

const saveHistoryToStorage = (key: string, history: string[]) => {
  try {
    localStorage.setItem(key, JSON.stringify(history))
  } catch (error) {
    console.error(`保存历史记录失败 (${key}):`, error)
  }
}

const addToHistory = (value: string, history: string[], storageKey: string) => {
  if (!value || !value.trim()) return
  const trimmedValue = value.trim()
  const index = history.indexOf(trimmedValue)
  if (index > -1) {
    history.splice(index, 1)
  }
  history.unshift(trimmedValue)
  if (history.length > MAX_HISTORY) {
    history.pop()
  }
  saveHistoryToStorage(storageKey, history)
}

const querySpecialSituationHistory = (queryString: string, cb: (arg: any) => void) => {
  const results = queryString
    ? specialSituationHistory.value.filter((item) =>
        item.toLowerCase().includes(queryString.toLowerCase())
      )
    : specialSituationHistory.value
  cb(results.map((item) => ({ value: item })))
}

const queryRemarkHistory = (queryString: string, cb: (arg: any) => void) => {
  const results = queryString
    ? remarkHistory.value.filter((item) => item.toLowerCase().includes(queryString.toLowerCase()))
    : remarkHistory.value
  cb(results.map((item) => ({ value: item })))
}

const saveSpecialSituationHistory = () => {
  addToHistory(
    aiAuditSpecialSituation.value,
    specialSituationHistory.value,
    STORAGE_KEY_SPECIAL_SITUATION
  )
}

const saveRemarkHistory = () => {
  addToHistory(aiAuditRemark.value, remarkHistory.value, STORAGE_KEY_REMARK)
}

const vehicleImagesPage = ref(0)
const vehicleImagesPageSize = ref(20)
const vehicleImagesSort = ref('picTime DESC')
const vehicleImagesTotal = ref(0)
const vehicleImagesLoading = ref(false)

const excludeSpecialType186 = ref(true)

const filteredVehicleImages = computed(() => {
  if (!aiAuditResult.value?.vehicle_images?.images) return []

  const allImages = aiAuditResult.value.vehicle_images.images

  const startIndex = vehicleImagesPage.value * vehicleImagesPageSize.value
  const endIndex = startIndex + vehicleImagesPageSize.value

  return allImages.slice(startIndex, endIndex)
})

const filteredVehicleImagesTotal = computed(() => {
  return filteredVehicleImages.value.length
})

const filteredGantryTradeRecords = computed(() => {
  if (!aiAuditResult.value?.gantry_trade?.records) return []
  if (excludeSpecialType186.value) {
    return aiAuditResult.value.gantry_trade.records.filter(
      (record: any) => record.specialType !== 186 && record.specialType !== '186'
    )
  }
  return aiAuditResult.value.gantry_trade.records
})

const totalPages = computed(() => {
  if (vehicleImagesPageSize.value >= vehicleImagesTotal.value) {
    return 1
  }
  return Math.ceil(vehicleImagesTotal.value / vehicleImagesPageSize.value)
})

const maxPage = computed(() => {
  return Math.max(0, totalPages.value - 1)
})

const isStationMatched = (stationId: string): boolean => {
  if (!editedRow.value || !stationId) return false

  const gantryCombination = String(editedRow.value['通行门架组合'] || '')
  if (!gantryCombination) return false

  const gantryIds = gantryCombination
    .split('|')
    .map((id) => id.trim())
    .filter((id) => id)

  for (const gantryId of gantryIds) {
    if (stationId.startsWith(gantryId.substring(0, 16))) {
      return true
    }
  }

  return false
}

const isGantryMatched = (gantryId: string): boolean => {
  if (!editedRow.value || !gantryId) return false

  const gantryCombination = String(editedRow.value['通行门架组合'] || '')
  if (!gantryCombination) return false

  const gantryIds = gantryCombination
    .split('|')
    .map((id) => id.trim())
    .filter((id) => id)

  for (const id of gantryIds) {
    if (gantryId.startsWith(id.substring(0, 16))) {
      return true
    }
  }

  return false
}

const isGateTimeMatched = (transTime: string): boolean => {
  if (!cloudPortalForm.value.gateTime || !transTime) return false
  return transTime === cloudPortalForm.value.gateTime
}

const getGantryTradeRowClass = ({ row }: { row: any }): string => {
  if (isGantryMatched(row.gantryId)) {
    return 'matched-gantry-row'
  }
  return ''
}

const getGantryPlateRowClass = ({ row }: { row: any }): string => {
  if (isGantryMatched(row.gantryId)) {
    return 'matched-gantry-row'
  }
  return ''
}

const getExitTradeRowClass = ({ row }: { row: any }): string => {
  if (row.passid && cloudPortalForm.value.passId && row.passid === cloudPortalForm.value.passId) {
    return 'matched-passid-row'
  }
  return ''
}

const formatDateTime = (dateTimeStr: string): string => {
  if (!dateTimeStr) return ''
  return dateTimeStr.replace('T', ' ')
}

const handleCloudPortalLogoutWrapper = async () => {
  await handleCloudPortalLogout()
  cloudPortalQueryResult.value = []
  aiAuditResult.value = null
}

const handleOpenCloudPortal = async () => {
  if (!editedRow.value) return

  cloudPortalForm.value.passId = String(editedRow.value['通行标识ID'] || '')
  cloudPortalForm.value.plateNumber = String(
    editedRow.value['车牌号码'] || editedRow.value['车牌'] || ''
  )
  cloudPortalForm.value.gateTime = formatDateTime(String(editedRow.value['门架通行时间'] || ''))
  cloudPortalForm.value.entryTime = formatDateTime(String(editedRow.value['入口时间'] || ''))
  cloudPortalForm.value.entryStationName = String(editedRow.value['收费入口名称'] || '')
  cloudPortalForm.value.gantryNamesCombined = String(editedRow.value['通行门架名称组合'] || '')

  aiAuditReviewStatus.value = String(editedRow.value['复核情况'] || '')
  aiAuditCheckSplit.value = String(editedRow.value['核查拆分'] || '')
  aiAuditCheckPassId.value = String(editedRow.value['核查通行标识'] || '')
  aiAuditSpecialSituation.value = String(editedRow.value['特情'] || '')
  aiAuditRemark.value = String(editedRow.value['备注'] || '')

  if (editedRow.value['查核资料1']) {
    aiAuditSelectedImage1.value = String(editedRow.value['查核资料1'])
  } else {
    aiAuditSelectedImage1.value = ''
  }

  if (editedRow.value['查核资料2']) {
    aiAuditSelectedImage2.value = String(editedRow.value['查核资料2'])
  } else {
    aiAuditSelectedImage2.value = ''
  }

  cloudPortalDialogVisible.value = true
  needManualCaptcha.value = false

  await loadCloudPortalCredentials()

  if (!cloudPortalLoggedIn.value) {
    await refreshCaptcha()
  }
}

const executeAIAuditBatchQuery = async () => {
  if (
    !cloudPortalForm.value.plateNumber ||
    !cloudPortalForm.value.entryTime ||
    !cloudPortalForm.value.gateTime
  ) {
    ElMessage.warning('缺少必要的查询参数')
    return
  }

  aiAuditLoading.value = true
  aiAuditResult.value = null

  try {
    const response = await aiAuditBatchQuery({
      plate_number: cloudPortalForm.value.plateNumber,
      entry_time: cloudPortalForm.value.entryTime,
      gate_time: cloudPortalForm.value.gateTime,
      pass_id: cloudPortalForm.value.passId || undefined,
      hours: cloudPortalForm.value.hours,
      rows: cloudPortalForm.value.rows
    }, userStore.getUserInfo?.id as number | undefined)

    if (response && response.code === 200) {
      aiAuditResult.value = response.data as any
      if ((response.data as any)?.time_range) {
        vehicleImagesTotal.value = (response.data as any)?.vehicle_images?.total || 0
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
    const errMsg = error?.message || ''
    if (errMsg.includes('status=401') || errMsg.includes('502')) {
      ElMessage.warning('云门户会话已过期，请重新登录')
      cloudPortalLoggedIn.value = false
    } else {
      ElMessage.error(errMsg || 'AI稽核查询失败')
    }
  } finally {
    aiAuditLoading.value = false
  }
}

const loadVehicleImagesPage = async () => {
  if (
    !cloudPortalLoggedIn.value ||
    !cloudPortalForm.value.plateNumber ||
    !aiAuditResult.value?.time_range
  ) {
    return
  }

  vehicleImagesLoading.value = true

  try {
    const response = await aiAuditVehicleImages({
      plate_number: cloudPortalForm.value.plateNumber.split('_')[0],
      start_time: aiAuditResult.value.time_range.start_time,
      end_time: aiAuditResult.value.time_range.end_time,
      page: vehicleImagesPage.value,
      page_size: vehicleImagesPageSize.value,
      sort: vehicleImagesSort.value
    }, userStore.getUserInfo?.id as number | undefined)

    if (response && response.code === 200 && response.data?.success) {
      if (aiAuditResult.value) {
        aiAuditResult.value.vehicle_images = response.data
        vehicleImagesTotal.value = response.data.total || 0
      }
    } else {
      ElMessage.error('加载车辆图库失败')
    }
  } catch (error: any) {
    ElMessage.error(error?.message || '加载车辆图库失败')
  } finally {
    vehicleImagesLoading.value = false
  }
}

const handlePrevPage = () => {
  if (vehicleImagesPage.value > 0) {
    vehicleImagesPage.value--
  }
}

const handleNextPage = () => {
  if (vehicleImagesPage.value < maxPage.value) {
    vehicleImagesPage.value++
  }
}

const handleVehicleImagesSortChange = (sort: string) => {
  vehicleImagesSort.value = sort
  vehicleImagesPage.value = 0
  loadVehicleImagesPage()
}

const fetchOriginalImageWithRetry = async (
  picturePath: string,
  maxRetries: number = 2
): Promise<string | null> => {
  if (!cloudPortalLoggedIn.value) {
    return null
  }

  let lastError: string = ''
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const response = await aiAuditOriginalImage({
        picture_path: picturePath
      }, userStore.getUserInfo?.id as number | undefined)

      if (response && response.code === 200 && response.data?.image) {
        return response.data.image
      } else {
        lastError = '获取原图失败'
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

const selectOriginalImageAsCheck = async (
  source: { picturePath?: string; bigPositivePic: string },
  target: 'image1' | 'image2',
  onComplete?: () => void
) => {
  if (!source.picturePath) {
    if (target === 'image1') {
      aiAuditSelectedImage1.value = source.bigPositivePic
    } else {
      aiAuditSelectedImage2.value = source.bigPositivePic
    }
    ElMessage.success(`已选择压缩图片作为查核资料${target === 'image1' ? '1' : '2'}`)
    onComplete?.()
    return
  }

  const loadingKey = `${target}-${source.picturePath}`
  if (originalImageLoading.value === loadingKey) {
    return
  }

  originalImageLoading.value = loadingKey
  try {
    const cachedImage = originalImageCache.get(source.picturePath)
    let originalImage: string

    if (cachedImage) {
      originalImage = cachedImage
    } else {
      if (!cloudPortalLoggedIn.value) {
        ElMessage.warning('请先登录云门户')
        return
      }

      originalImage = (await fetchOriginalImageWithRetry(source.picturePath, 2)) || ''

      if (!originalImage) {
        ElMessage.warning('获取原图失败，使用压缩图片')
        if (target === 'image1') {
          aiAuditSelectedImage1.value = source.bigPositivePic
        } else {
          aiAuditSelectedImage2.value = source.bigPositivePic
        }
        onComplete?.()
        return
      }

      setOriginalImageCache(source.picturePath, originalImage)
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
      aiAuditSelectedImage1.value = source.bigPositivePic
    } else {
      aiAuditSelectedImage2.value = source.bigPositivePic
    }
  } finally {
    originalImageLoading.value = ''
    onComplete?.()
  }
}

const selectImageForCheck = async (image: AIAuditVehicleImage, target: 'image1' | 'image2') => {
  await selectOriginalImageAsCheck(image, target)
}

const getPreviewImages = async (image: AIAuditVehicleImage): Promise<string[]> => {
  if (!image.picturePath) {
    return [getImageSrc(image.bigPositivePic)]
  }

  const cachedImage = originalImageCache.get(image.picturePath)
  if (cachedImage) {
    return [getImageSrc(cachedImage)]
  }

  const originalImage = await fetchOriginalImageWithRetry(image.picturePath, 2)
  if (originalImage) {
    setOriginalImageCache(image.picturePath, originalImage)
    return [getImageSrc(originalImage)]
  }

  return [getImageSrc(image.bigPositivePic)]
}

const previewImageList = ref<string[]>([])
const handleImagePreview = async (image: AIAuditVehicleImage) => {
  previewImageList.value = [getImageSrc(image.bigPositivePic)]

  if (!image.picturePath) {
    return
  }

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

    if (originalImageCache.has(image.picturePath)) {
      ElMessage.success('高清原图加载完成')
    }
  } catch (error: any) {
    console.error('预览原图失败:', error)
  } finally {
    previewLoading.value = ''
    previewLoadingText.value = ''
  }
}

const getImageSrc = (base64Data: string | undefined): string => {
  if (!base64Data) return ''
  if (base64Data.startsWith('data:image')) {
    return base64Data
  }
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
  if (picTime.length >= 19) {
    return picTime.substring(11, 19)
  }
  return picTime
}

const queryGantryImagesForRow = async (row: AIAuditGantryTrade) => {
  if (!cloudPortalLoggedIn.value) {
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
    }, userStore.getUserInfo?.id as number | undefined)

    if (response && response.code === 200 && response.data?.success) {
      const images = response.data.images || []
      gantryImagesResult.value = {
        gantryName: row.gantryName,
        gantryId: row.gantryId,
        transTime: row.transTime,
        timeRange: { startTime, endTime },
        images: images,
        total: response.data.total || 0
      }
      gantryImagesPreviewList.value = images.map((img: AIAuditGantryImage) =>
        getImageSrc(img.bigPositivePic)
      )
      gantryImagesDialogVisible.value = true
    } else {
      ElMessage.error('查询门架图库失败')
    }
  } catch (error: any) {
    ElMessage.error(error?.message || '查询门架图库失败')
  } finally {
    gantryImageLoading.value = ''
  }
}

const selectGantryImageAsCheck = async (img: AIAuditGantryImage, target: 'image1' | 'image2') => {
  await selectOriginalImageAsCheck(img, target, () => {
    gantryImagesDialogVisible.value = false
  })
}

const queryVehicleDetail = async (plateNumber: string, picTime: string) => {
  if (!cloudPortalLoggedIn.value) {
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

  const startTime = formatDateTimeForQuery(startDate)
  const endTime = formatDateTimeForQuery(endDate)

  try {
    const response = await aiAuditBatchQuery({
      plate_number: plateNumber,
      entry_time: startTime,
      gate_time: endTime,
      hours: 48,
      rows: 100
    }, userStore.getUserInfo?.id as number | undefined)

    if (response && response.code === 200 && response.data) {
      vehicleDetailResult.value = response.data
    } else {
      ElMessage.error('查询车辆信息失败')
    }
  } catch (error: any) {
    ElMessage.error(error?.message || '查询车辆信息失败')
  } finally {
    vehicleDetailLoading.value = false
  }
}

const captureTable = async (tableName: string, targetImage: 'image1' | 'image2') => {
  let tableRef: any = null
  let tableLabel = ''

  switch (tableName) {
    case 'gantry_trade':
      tableRef = gantryTradeTableRef.value
      tableLabel = '门架交易'
      break
    case 'gantry_plate':
      tableRef = gantryPlateTableRef.value
      tableLabel = '门架牌识'
      break
    case 'exit_trade_etc':
      tableRef = exitTradeEtcTableRef.value
      tableLabel = '出口交易(ETC)'
      break
    case 'exit_trade_other':
      tableRef = exitTradeOtherTableRef.value
      tableLabel = '出口交易(其它)'
      break
    case 'audit_order':
      tableRef = auditOrderTableRef.value
      tableLabel = '稽核工单'
      break
  }

  if (!tableRef) {
    ElMessage.warning('表格未加载完成，请稍后再试')
    return
  }

  const tableEl = tableRef.$el
  if (!tableEl) {
    ElMessage.warning('无法获取表格元素')
    return
  }

  ElMessage.info(`正在截取${tableLabel}表格...`)

  await nextTick()

  const startTime = performance.now()
  
  try {
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
      }
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
      ElMessage.success(`${tableLabel}表格已截图到查核资料1 (${duration.toFixed(0)}ms)`)
    } else {
      aiAuditSelectedImage2.value = dataUrl
      ElMessage.success(`${tableLabel}表格已截图到查核资料2 (${duration.toFixed(0)}ms)`)
    }
  } catch (error: any) {
    const errorTime = performance.now() - startTime
    console.error(`[Screenshot] ${tableLabel} 截图失败 (${errorTime.toFixed(0)}ms):`, error)
    ElMessage.error(`截图失败: ${error.message || '未知错误'}`)
  }
}

const saveImagesToDatabase = async () => {
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

  if (!selectedTable.value || !cloudPortalForm.value.passId) {
    ElMessage.warning('缺少表名或记录ID')
    return
  }

  aiAuditSavingImages.value = true
  try {
    const image1Base64 = aiAuditSelectedImage1.value
    const image2Base64 = aiAuditSelectedImage2.value

    const isValidImageData = (val: string): val is string => {
      if (!val) return false
      if (val.startsWith('data:image/')) return true
      if (val.startsWith('data:')) return false
      return val.length >= 100
    }

    const extractBase64 = (val: string): string | undefined => {
      if (!isValidImageData(val)) return undefined
      if (val.startsWith('data:image/')) return val.split(',')[1]
      return val
    }

    const base64ToSave1 = extractBase64(image1Base64)
    const base64ToSave2 = extractBase64(image2Base64)

    const response = await aiAuditSaveImages({
      table_name: selectedTable.value,
      record_id: cloudPortalForm.value.passId,
      image1_base64: base64ToSave1,
      image2_base64: base64ToSave2,
      review_status: aiAuditReviewStatus.value || undefined,
      check_pass_id: aiAuditCheckPassId.value || undefined,
      special_situation: aiAuditSpecialSituation.value || undefined,
      check_split: aiAuditCheckSplit.value || undefined,
      remark: aiAuditRemark.value || undefined,
      clear_empty: true
    })

    if (response && response.code === 200) {
      ElMessage.success(`成功保存 ${(response.data as any)?.affected_rows || 0} 条记录`)

      request.clearCache('/api/split-match/')

      await loadTableData()

      if (editedRow.value) {
        const updatedRow = tableData.value.find(
          (row: any) => row['通行标识ID'] === cloudPortalForm.value.passId
        )
        if (updatedRow) {
          editedRow.value = { ...updatedRow }
          
          // 保留用户选择的图片值，不重新从 tableData 获取
          // 因为图片是异步加载的，此时 tableData 中的图片字段还是 null
          // aiAuditSelectedImage1 和 aiAuditSelectedImage2 保持用户选择的值
          // 更新 editedRow 中的图片字段为用户选择的值
          if (aiAuditSelectedImage1.value) {
            editedRow.value['查核资料1'] = aiAuditSelectedImage1.value
          }
          if (aiAuditSelectedImage2.value) {
            editedRow.value['查核资料2'] = aiAuditSelectedImage2.value
          }
        }
      }
    } else {
      ElMessage.error(response?.message || '保存图片失败')
    }
  } catch (error: any) {
    ElMessage.error(error?.message || '保存图片失败')
  } finally {
    aiAuditSavingImages.value = false
  }
}

const formatFee = (fee: number) => {
  if (fee === null || fee === undefined) return '-'
  return (fee / 100).toFixed(2) + '元'
}

const formatMatchRate = (rate: number): string => {
  if (rate === null || rate === undefined) return '-'
  if (rate > 1) {
    return rate.toFixed(1) + '%'
  }
  return (rate * 100).toFixed(1) + '%'
}

const getRateType = (rate: number): 'success' | 'warning' | 'info' | 'danger' => {
  if (rate === null || rate === undefined) return 'info'
  const actualRate = rate > 1 ? rate : rate * 100
  if (actualRate >= 80) return 'success'
  if (actualRate >= 50) return 'warning'
  return 'info'
}

const getOrderStatusType = (status: number): 'success' | 'primary' | 'warning' | 'info' | 'danger' => {
  if (status === null || status === undefined) return 'info'
  switch (status) {
    case 1:
      return 'warning'
    case 2:
      return 'warning'
    case 3:
      return 'primary'
    case 4:
      return 'primary'
    case 5:
      return 'info'
    case 6:
      return 'info'
    case 7:
      return 'success'
    case 8:
      return 'success'
    default:
      return 'info'
  }
}

const handleVerifyPassId = async (passId: string, verifyType: string) => {
  if (!passId || !passId.trim()) {
    ElMessage.warning('通行标识ID不能为空')
    return
  }

  verifyLoading.value = true
  try {
    const currentUser = userStore.getUserInfo
    const response = await verifyPassId({
      pass_id: passId.trim(),
      verify_type: verifyType,
      user_id: currentUser?.id,
      username: currentUser?.username
    })

    if (response && response.code === 200 && response.data) {
      const result = response.data as any

      if (result.exists) {
        ElMessage.success(`核查成功：找到 ${result.match_count} 条匹配记录`)
        aiAuditCheckSplit.value = '已拆'

        if (result.records && result.records.length > 0) {
          const record = result.records[0]
          const details = [
            `车牌: ${record['实际车辆车牌号码+颜色'] || '-'}`,
            `入口: ${record['收费入口名称'] || '-'}`,
            `出口: ${record['收费出口名称'] || '-'}`,
            `车型: ${record['收费车型'] || '-'}`,
            `介质: ${record['通行介质'] || '-'}`
          ].join('\n')

          ElNotification({
            title: `核查结果 (${result.match_count} 条匹配)`,
            message: details,
            type: 'success',
            duration: 8000,
            position: 'top-right'
          })
        }
      } else {
        ElMessage.warning('核查结果：未找到匹配记录')
        aiAuditCheckSplit.value = '未拆'

        ElNotification({
          title: '核查结果',
          message: `通行标识ID "${passId}" 在详单查询表中不存在`,
          type: 'warning',
          duration: 5000,
          position: 'top-right'
        })
      }
    } else {
      ElMessage.error(response?.message || '核查失败')
    }
  } catch (error: any) {
    console.error('核查失败:', error)
    ElMessage.error(error?.message || '核查失败，请稍后重试')
  } finally {
    verifyLoading.value = false
  }
}

const fallbackCopy = (text: string) => {
  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.style.position = 'fixed'
  textarea.style.left = '-9999px'
  textarea.style.top = '-9999px'
  textarea.style.opacity = '0'
  document.body.appendChild(textarea)
  textarea.select()
  textarea.setSelectionRange(0, text.length)
  const success = document.execCommand('copy')
  document.body.removeChild(textarea)
  return success
}

const handleCopy = async (text: string) => {
  if (!text) {
    ElMessage.warning('没有内容可复制')
    return
  }

  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
      ElMessage.success('复制成功')
    } else {
      const success = fallbackCopy(text)
      if (success) {
        ElMessage.success('复制成功')
      } else {
        ElMessage.error('复制失败，请手动复制')
      }
    }
  } catch (error) {
    console.warn('Clipboard API failed, using fallback:', error)
    try {
      const success = fallbackCopy(text)
      if (success) {
        ElMessage.success('复制成功')
      } else {
        ElMessage.error('复制失败，请手动复制')
      }
    } catch (fallbackError) {
      console.error('Fallback copy also failed:', fallbackError)
      ElMessage.error('复制失败，请手动复制')
    }
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

const handleExport = async () => {
  if (!selectedTable.value) {
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
      table_name: selectedTable.value,
      filters: JSON.stringify(normalizeFilters(filters.value))
    })

    let exportData: any[] = []
    let headers: string[] = []
    let columnTypes: Record<string, string> = {}

    if (response && response.code === 200 && response.data) {
      exportData = Array.isArray(response.data.data) ? response.data.data : []
      headers = Array.isArray(response.data.columns) ? response.data.columns : []
      columnTypes = response.data.column_types || {}
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
    const IMAGE_WIDTH_PX = 93
    const IMAGE_HEIGHT_PX = 50
    const IMAGE_COL_WIDTH = 13.23
    const IMAGE_ROW_HEIGHT = 37.42
    const NORMAL_COL_WIDTH = 15

    worksheet.columns = headers.map((header) => ({
      header: header,
      key: header,
      width: IMAGE_COLUMNS.includes(header) ? IMAGE_COL_WIDTH : NORMAL_COL_WIDTH
    }))

    const headerRow = worksheet.getRow(1)
    headerRow.height = 25
    headerRow.eachCell((cell) => {
      cell.font = { bold: true, size: 11 }
      cell.fill = {
        type: 'pattern',
        pattern: 'solid',
        fgColor: { argb: 'FFE0E0E0' }
      }
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
          if (IMAGE_COLUMNS.includes(header)) {
            return ''
          }
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
                const imageId = workbook.addImage({
                  base64: placeholderBase64,
                  extension: 'png'
                })

                worksheet.addImage(imageId, {
                  tl: { col: colIndex, row: rowIndex + 1, colOff: 0, rowOff: 0 } as any,
                  br: { col: colIndex + 1, row: rowIndex + 2, colOff: 0, rowOff: 0 } as any,
                  editAs: 'oneCell'
                })
              }
            } else {
              const imageId = workbook.addImage({
                base64: result.data,
                extension: result.extension
              })

              worksheet.addImage(imageId, {
                tl: { col: colIndex, row: rowIndex + 1, colOff: 0, rowOff: 0 } as any,
                br: { col: colIndex + 1, row: rowIndex + 2, colOff: 0, rowOff: 0 } as any,
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

    const fileName = `${selectedTable.value}_${new Date()
      .toISOString()
      .slice(0, 19)
      .replace(/[:T]/g, '-')}.xlsx`
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
  try {
    const zip = new JSZip()
    const workbook = await zip.loadAsync(binaryData)
    const filePaths = Object.keys(workbook.files)

    const hasCellImages = filePaths.some((path) => path === 'xl/cellimages.xml')
    const hasCellImagesRels = filePaths.some((path) => path === 'xl/_rels/cellimages.xml.rels')
    const hasDrawings = filePaths.some((path) => path === 'xl/drawings/drawing1.xml')
    const hasDrawingsRels = filePaths.some((path) => path === 'xl/drawings/_rels/drawing1.xml.rels')

    if (!hasCellImages && !hasDrawings) {
      return 'no_image'
    }

    const nodeCounts: Record<string, number> = {}

    if (hasCellImages) {
      const cellImagesFile = workbook.file('xl/cellimages.xml')
      if (cellImagesFile) {
        const content = await cellImagesFile.async('text')
        const count = countXMLNodes(content)
        nodeCounts['cellimages.xml'] = count
      }
    }

    if (hasCellImagesRels) {
      const cellImagesRelsFile = workbook.file('xl/_rels/cellimages.xml.rels')
      if (cellImagesRelsFile) {
        const content = await cellImagesRelsFile.async('text')
        const count = countXMLNodes(content)
        nodeCounts['cellimages.xml.rels'] = count
      }
    }

    if (hasDrawings) {
      const drawingFile = workbook.file('xl/drawings/drawing1.xml')
      if (drawingFile) {
        const content = await drawingFile.async('text')
        const count = countXMLNodes(content)
        nodeCounts['drawing1.xml'] = count
      }
    }

    if (hasDrawingsRels) {
      const drawingRelsFile = workbook.file('xl/drawings/_rels/drawing1.xml.rels')
      if (drawingRelsFile) {
        const content = await drawingRelsFile.async('text')
        const count = countXMLNodes(content)
        nodeCounts['drawing1.xml.rels'] = count
      }
    }

    for (const [_fileName, _count] of Object.entries(nodeCounts)) {
    }

    let maxNodes = 0
    let targetFormat: 'drawings' | 'cellimages' = 'drawings'

    if (hasCellImages && hasCellImagesRels) {
      const cellImagesNodes =
        (nodeCounts['cellimages.xml'] || 0) + (nodeCounts['cellimages.xml.rels'] || 0)

      if (cellImagesNodes > maxNodes) {
        maxNodes = cellImagesNodes
        targetFormat = 'cellimages'
      }
    }

    if (hasDrawings && hasDrawingsRels) {
      const drawingNodes =
        (nodeCounts['drawing1.xml'] || 0) + (nodeCounts['drawing1.xml.rels'] || 0)

      if (drawingNodes > maxNodes) {
        maxNodes = drawingNodes
        targetFormat = 'drawings'
      }
    }

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

    return count
  } catch (e) {
    console.error('统计XML节点失败:', e)
    return 0
  }
}

const extractImagesFromExcel = async (
  binaryData: string
): Promise<{ mediaFiles: Record<string, string>; count: number }> => {
  const mediaFiles: Record<string, string> = {}
  let count = 0

  try {
    const zip = new JSZip()
    const workbook = await zip.loadAsync(binaryData)

    const allFilePaths = Object.keys(workbook.files)
    const mediaFilePaths = allFilePaths.filter(
      (path) => path.startsWith('xl/media/') && !path.endsWith('/')
    )

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
          })
          .catch((e) => {
            console.warn('处理图片文件失败:', filePath, e)
          })
        mediaPromises.push(promise)
      }
    }

    await Promise.all(mediaPromises)
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
  isArray: (name) => {
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
  const relMap: Record<string, string> = {}
  const cellImageMap: Record<string, { cell: string; imageId: string; imageName: string }> = {}
  const sheet1XmlData: Record<string, string> = {}

  try {
    const zip = new JSZip()
    const workbook = await zip.loadAsync(binaryData)

    const cellImagesRelsPath = 'xl/_rels/cellimages.xml.rels'
    const cellImagesRelsFile = workbook.file(cellImagesRelsPath)

    if (cellImagesRelsFile) {
      try {
        const relsContent = await cellImagesRelsFile.async('text')

        const relsXml = xmlParser.parse(relsContent)
        const relationships = relsXml.Relationships?.Relationship
        if (!relationships) {
          console.warn('  未找到Relationship节点')
          return { relMap, cellImageMap, sheet1XmlData }
        }

        const relArray = Array.isArray(relationships) ? relationships : [relationships]

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
            }
          }
        }
      } catch (e) {
        console.warn('读取cellimages.xml.rels失败:', e)
      }
    }

    const cellImagesPath = 'xl/cellimages.xml'
    const cellImagesFile = workbook.file(cellImagesPath)

    if (cellImagesFile) {
      try {
        const cellImagesContent = await cellImagesFile.async('text')

        const cellImagesXml = cellImagesXmlParser.parse(cellImagesContent)

        const etcCellImages = cellImagesXml['etc:cellImages']

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

          if (relationshipId) {
            cellImageMap[relationshipId] = {
              cell: '',
              imageId: imageId || '',
              imageName: imageName || ''
            }
            foundImages++
            if (foundImages <= 5) {
            }
          } else {
            console.warn(`    警告: r:embed属性为空`)
          }
        }
      } catch (e: any) {
        console.error('读取cellimages.xml失败:', e)
        return { relMap, cellImageMap, sheet1XmlData }
      }
    } else {
      console.warn('cellimages.xml文件不存在')
    }

    const sheet1Path = 'xl/worksheets/sheet1.xml'
    const sheet1File = workbook.file(sheet1Path)

    if (sheet1File) {
      try {
        const sheet1Content = await sheet1File.async('text')

        // 使用DOMParser解析XML，参照文档方案
        const domParser = new DOMParser()
        const xmlDoc = domParser.parseFromString(sheet1Content, 'text/xml')

        // 遍历所有单元格节点（<c>）
        const cellNodes = xmlDoc.getElementsByTagName('c')

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

          // 精准匹配目标图片ID（ID_+32位十六进制）
          const imageIdRegex = /ID_[0-9A-Fa-f]{32}/i
          const match = cleanFormula.match(imageIdRegex)
          if (match) {
            const imageName = match[0]
            sheet1XmlData[imageName] = cellRef
            dispimgCount++
            if (dispimgCount <= 5) {
            }
          }
        }
      } catch (e: any) {
        console.error('读取sheet1.xml失败:', e)
      }
    } else {
      console.warn('sheet1.xml文件不存在')
    }

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
  const relMap: Record<string, string> = {}
  const drawingMap: Record<string, { row: number; col: number; imageId: string }> = {}

  try {
    const zip = new JSZip()
    const workbook = await zip.loadAsync(binaryData)

    const filePaths = Object.keys(workbook.files)

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

    for (const relsPath of relsFiles) {
      const relsFile = workbook.file(relsPath)
      if (relsFile) {
        try {
          const relsContent = await relsFile.async('text')

          const relsXml = xmlParser.parse(relsContent)
          const relationships = relsXml.Relationships?.Relationship
          if (!relationships) {
            console.warn('  未找到Relationship节点')
            continue
          }

          const relArray = Array.isArray(relationships) ? relationships : [relationships]

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
              }
            }
          }
        } catch (e) {
          console.warn('读取rels文件失败:', relsPath, e)
        }
      }
    }

    for (const drawingPath of drawingFiles) {
      const drawingFile = workbook.file(drawingPath)
      if (drawingFile) {
        try {
          const drawingContent = await drawingFile.async('text')

          const drawingXml = xmlParser.parse(drawingContent)

          const wsDr = drawingXml['xdr:wsDr'] || drawingXml
          if (!wsDr) {
            console.warn('  未找到wsDr节点')
            continue
          }

          let twoCellAnchors = wsDr['xdr:twoCellAnchor']
          let oneCellAnchors = wsDr['xdr:oneCellAnchor']

          if (twoCellAnchors && !Array.isArray(twoCellAnchors)) {
            twoCellAnchors = [twoCellAnchors]
          }
          if (oneCellAnchors && !Array.isArray(oneCellAnchors)) {
            oneCellAnchors = [oneCellAnchors]
          }
          if (twoCellAnchors && twoCellAnchors.length > 0) {
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
        } catch (e) {
          console.warn('读取drawing文件失败:', drawingPath, e)
        }
      }
    }

    if (Object.keys(relMap).length > 0) {
    }
    if (Object.keys(drawingMap).length > 0) {
    }
  } catch (e) {
    console.error('构建图片映射失败:', e)
  }

  return { relMap, drawingMap }
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

const associateCellImagesWithRows = (
  processedData: any[],
  mediaFiles: Record<string, string>,
  relMap: Record<string, string>,
  cellImageMap: Record<string, { cell: string; imageId: string; imageName: string }>,
  sheet1XmlData: Record<string, string>
): void => {
  const imageCellMap: Record<string, string> = {}

  for (const imageName in sheet1XmlData) {
    if (Object.prototype.hasOwnProperty.call(sheet1XmlData, imageName)) {
      const cellRef = sheet1XmlData[imageName]
      imageCellMap[imageName] = cellRef
    }
  }

  const imageNameToDataMap: Record<string, { imageId: string; imageData: string }[]> = {}

  for (const relationshipId in cellImageMap) {
    if (Object.prototype.hasOwnProperty.call(cellImageMap, relationshipId)) {
      const info = cellImageMap[relationshipId]
      const imageName = info.imageName
      const imageId = info.imageId

      const imageFileName = relMap[relationshipId]
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
      } else {
        console.warn(
          `  ✗ 未找到图片文件: 关系ID="${relationshipId}", 映射文件名="${imageFileName}"`
        )
      }
    }
  }

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

        if (colNumber === 7) {
          if (images.length >= 1) {
            targetRow['查核资料1'] = images[0].imageData
            successCount++
          }
        } else if (colNumber === 8) {
          if (images.length >= 1) {
            targetRow['查核资料2'] = images[0].imageData
            successCount++
          }
        } else {
          console.warn(`  ⚠ 单元格${cellRef}列号${colNumber}不在G列(7)或H列(8)范围内，跳过此图片`)
        }
      } else {
        console.warn(`  ⚠ 行号${rowNumber}超出数据范围(0-${processedData.length})`)
      }
    }
  }
}

const associateImagesWithRows = (
  processedData: any[],
  mediaFiles: Record<string, string>,
  relMap: Record<string, string>,
  drawingMap: Record<string, { row: number; col: number; imageId: string }>
): void => {
  const rowImagesMap: Record<number, { imageId: string; imageData: string; col: number }[]> = {}

  for (const relationshipId in drawingMap) {
    if (Object.prototype.hasOwnProperty.call(drawingMap, relationshipId)) {
      const info = drawingMap[relationshipId]
      const row = info.row
      const col = info.col
      const imageId = info.imageId

      const imageFileName = relMap[relationshipId]
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
      } else {
        console.warn(
          `  ✗ 未找到图片文件: 关系ID="${relationshipId}", 映射文件名="${imageFileName}"`
        )
      }
    }
  }

  let successCount = 0

  for (const row in rowImagesMap) {
    const excelRowNum = parseInt(row)
    const dataRowIndex = excelRowNum - 2
    const images = [...rowImagesMap[excelRowNum]]

    images.sort((a, b) => a.col - b.col)

    if (dataRowIndex >= 0 && dataRowIndex < processedData.length) {
      const targetRow = processedData[dataRowIndex]

      if (images.length >= 1) {
        targetRow['查核资料1'] = images[0].imageData
        successCount++
      }

      if (images.length >= 2) {
        targetRow['查核资料2'] = images[1].imageData
        successCount++
      }

      if (images.length > 2) {
      }
    } else {
      console.warn(
        `  ✗ 数据索引${dataRowIndex}超出范围(0-${processedData.length - 1}), Excel行号=${excelRowNum}`
      )
    }
  }

  let rowsWithImage1 = 0
  let rowsWithImage2 = 0
  for (const row of processedData) {
    if (row['查核资料1']) rowsWithImage1++
    if (row['查核资料2']) rowsWithImage2++
  }
}

const parseExcelAsync = async (
  binaryData: string,
  onProgress: (progress: number, status: string) => void
): Promise<{ data: any[]; extractedImagesCount: number }> => {
  onProgress(5, '正在检测Excel格式...')

  const excelFormat = await detectExcelFormat(binaryData)

  if (excelFormat === 'no_image') {
    ElMessage.warning('当前Excel文件无嵌入图片')
    onProgress(100, '文件解析完成')
    return { data: [], extractedImagesCount: 0 }
  }

  onProgress(10, '正在解析Excel工作簿...')

  const xlsxWorkbook = XLSX.read(binaryData, { type: 'binary' })
  const sheetName = xlsxWorkbook.SheetNames[0]

  const worksheet = xlsxWorkbook.Sheets[sheetName]
  const jsonData = XLSX.utils.sheet_to_json(worksheet, { range: 0 })

  const totalRows = jsonData.length

  if (totalRows > 0) {
  }

  onProgress(20, '正在处理数据...')

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

  onProgress(50, '正在提取图片...')

  const { mediaFiles, count } = await extractImagesFromExcel(binaryData)

  onProgress(60, '正在建立图片关联...')

  if (excelFormat === 'cellimages') {
    const { relMap, cellImageMap, sheet1XmlData } =
      await buildCellImagesMappingsWithSheet1(binaryData)
    onProgress(75, '正在关联图片到数据行...')

    associateCellImagesWithRows(processedData, mediaFiles, relMap, cellImageMap, sheet1XmlData)
  } else {
    const { relMap, drawingMap } = await buildImageMappings(binaryData)
    onProgress(75, '正在关联图片到数据行...')

    associateImagesWithRows(processedData, mediaFiles, relMap, drawingMap)
  }

  onProgress(95, '正在完成...')

  await new Promise((resolve) => setTimeout(resolve, 0))

  onProgress(100, '文件解析完成')

  return { data: processedData, extractedImagesCount: count }
}

// 文件上传处理函数
const handleFileUpload = async (file: any) => {
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
      try {
        const data = e.target?.result
        if (!data) {
          throw new Error('文件读取失败')
        }

        uploadProgressText.value = '文件读取完成'

        const result = await parseExcelAsync(data as string, (progress: number, status: string) => {
          uploadProgress.value = progress
          uploadProgressText.value = status
        })
        importData.value = result.data
        extractedImagesCount.value = result.extractedImagesCount
        uploadProgress.value = 100
        uploadProgressText.value = '文件解析完成'
        uploadLoading.value = false
        importPreviewVisible.value = true
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
    // 调用API获取所有数据，不使用分页参数
    const response = await getSplitMatchData({
      table_name: selectedTable.value,
      filters: JSON.stringify(normalizeFilters(filters.value)),
      // 不使用分页，获取所有数据
      page: 1,
      page_size: 10000 // 设置一个足够大的值
    })

    let allData: any[] = []
    if (response && response.code === 200 && response.data) {
      allData = Array.isArray(response.data.data) ? response.data.data : []
    }

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
  importProgress.value = 20
  importProgressText.value = '开始匹配数据...'

  // 构建Map索引，将O(n*m)降为O(n+m)
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

  for (let i = 0; i < importData.value.length; i++) {
    const importRow = importData.value[i]
    const 通行标识ID = importRow['通行标识ID']

    if (!通行标识ID) {
      importProgress.value = 20 + Math.round(((i + 1) / total) * 70)
      importProgressText.value = `正在匹配 ${i + 1}/${total}...`
      continue
    }

    const importId = String(通行标识ID)
      .trim()
      .replace(/[^a-zA-Z0-9]/g, '')
      .toLowerCase()

    const matchedRow = tableDataMap.get(importId)

    if (matchedRow) {
      matchResult.push({
        通行标识ID,
        原始数据: matchedRow,
        导入数据: importRow,
        匹配状态: '已匹配'
      })
    } else {
      unmatchedImportIds.push(通行标识ID)
    }

    importProgress.value = 20 + Math.round(((i + 1) / total) * 70)
    importProgressText.value = `正在匹配 ${i + 1}/${total}...`

    // 避免UI阻塞
    await new Promise((resolve) => setTimeout(resolve, 10))
  }

  importResult.value = matchResult
  importProgress.value = 100
  importProgressText.value = '匹配完成'

  // 输出匹配结果统计// 显示匹配结果提示
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
        const webpBlob = await convertToWebP(processedRow['查核资料1'])
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
        const webpBlob = await convertToWebP(processedRow['查核资料2'])
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

        await updateSplitMatchData({
          table_name: selectedTable.value,
          row_id: String(item.通行标识ID),
          data: updateData
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

const SAVE_FIELD_MAPPING: Record<string, string> = {
  '查核资料1': 'image1_base64',
  '查核资料2': 'image2_base64',
  '复核情况': 'review_status',
  '核查通行标识': 'check_pass_id',
  '特情': 'special_situation',
  '核查拆分': 'check_split',
  '备注': 'remark'
}

const handleSave = async () => {
  if (!editedRow.value || !selectedTable.value) {
    ElMessage.warning('数据不完整，无法保存')
    return
  }

  try {
    await ElMessageBox.confirm('保存将覆盖数据库中的原有数据，是否继续？', '确认保存', {
      confirmButtonText: '确认覆盖',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }

  try {
    const rowId = String(editedRow.value['通行标识ID'])

    const saveData: Record<string, unknown> = {}

    // 处理图片字段：始终将当前图片数据写入 saveData，不再判断数据库是否已有值
    for (const [cnKey, enKey] of Object.entries(SAVE_FIELD_MAPPING)) {
      if (cnKey === '查核资料1' || cnKey === '查核资料2') {
        if (imageBinaryData.value[cnKey]) {
          const arrayBuffer = await imageBinaryData.value[cnKey].arrayBuffer()
          const base64String = btoa(
            new Uint8Array(arrayBuffer).reduce((data, byte) => data + String.fromCharCode(byte), '')
          )
          saveData[enKey] = base64String
        } else {
          const imageData = editedRow.value[cnKey]
          if (imageData && typeof imageData === 'string') {
            if (imageData.startsWith('data:')) {
              const base64Part = imageData.split(',')[1]
              if (base64Part) {
                saveData[enKey] = base64Part
              }
            } else {
              saveData[enKey] = imageData
            }
          }
        }
      } else {
        const val = editedRow.value[cnKey]
        if (val !== undefined && val !== null && val !== '') {
          saveData[enKey] = val
        }
      }
    }

    if (Object.keys(saveData).length === 0) {
      ElMessage.warning('没有需要保存的修改')
      return
    }

    const apiParams = {
      table_name: selectedTable.value,
      row_id: rowId,
      data: saveData
    }

    try {
      const response = await updateSplitMatchData(apiParams)

      if (response && response.code === 200) {
        ElMessage.success('保存成功')

        request.clearCache('/api/split-match/')

        loadTableData().catch((e) => console.error('保存后刷新表格失败:', e))

        if (editedRow.value) {
          const currentImage1 = editedRow.value['查核资料1']
          const currentImage2 = editedRow.value['查核资料2']

          imagePreviewList.value = {
            查核资料1: currentImage1 ? [String(currentImage1)] : [],
            查核资料2: currentImage2 ? [String(currentImage2)] : []
          }

          imageBinaryData.value = {}
        }
      } else {
        ElMessage.error('保存失败，请检查后端服务')
      }
    } catch (error) {
      ElMessage.error('保存失败，请检查网络连接')
    }
  } catch (error) {
    ElMessage.error('保存失败，请检查网络连接')
  }
}

onMounted(() => {
  loadTableList()
  specialSituationHistory.value = loadHistoryFromStorage(STORAGE_KEY_SPECIAL_SITUATION)
  remarkHistory.value = loadHistoryFromStorage(STORAGE_KEY_REMARK)

  keepAliveTimer = setInterval(() => {
    if (cloudPortalLoggedIn.value) {
      keepCloudPortalAlive(userStore.getUserInfo?.id as number | undefined).catch(() => {})
    }
  }, 5 * 60 * 1000)
})

onUnmounted(() => {
  clearOriginalImageCache()
  if (keepAliveTimer) {
    clearInterval(keepAliveTimer)
    keepAliveTimer = null
  }
})
</script>

<style scoped>
.split-match {
  padding: 20px;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 125px);
  overflow: hidden;
}

.table-container {
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

.query-params-desc :deep(.el-descriptions__label) {
  width: 90px;
  white-space: nowrap;
}

.query-params-desc :deep(.el-descriptions__body) {
  table-layout: fixed;
}

.query-params-desc :deep(.el-descriptions__table) {
  table-layout: fixed;
}

.query-params-desc :deep(.el-descriptions__cell) {
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.query-params-desc :deep(.el-descriptions__content) {
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.query-params-desc :deep(.el-descriptions__body tr td:nth-child(6)) {
  max-width: 170px;
  width: 170px;
}

.query-params-desc :deep(.pass-id-content) {
  max-width: 280px;
  width: 280px;
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

.image-placeholder {
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  border-radius: 4px;
  color: #c0c4cc;
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

/* 匹配结果详细信息 */
.match-detail {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  margin-top: 10px;
}

.match-stat {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  background-color: #fff;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.stat-label {
  color: #909399;
  margin-right: 8px;
  font-size: 14px;
}

.stat-value {
  font-size: 16px;
  font-weight: bold;
  color: #303133;

  &.success {
    color: #67c23a;
  }

  &.warning {
    color: #e6a23c;
  }

  &.info {
    color: #409eff;
  }

  &.primary {
    color: #9093ff;
  }
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

/* 匹配门架行高亮样式 */
::deep(.matched-gantry-row) {
  background-color: #ecf5ff !important;
}

::deep(.matched-gantry-row:hover > td) {
  background-color: #d9ecff !important;
}

/* 匹配流水编号行高亮样式 */
::deep(.matched-passid-row) {
  background-color: #f0f9ff !important;
}

::deep(.matched-passid-row:hover > td) {
  background-color: #e0f2fe !important;
}

/* 紧凑对话框样式 */
.compact-dialog ::deep(.el-dialog__header) {
  padding: 5px 15px;
  margin: 0;
  height: 30px;
  line-height: 20px;
}

.compact-dialog ::deep(.el-dialog__title) {
  font-size: 14px;
}

.compact-dialog ::deep(.el-dialog__body) {
  padding: 12px 15px;
}

.compact-dialog ::deep(.el-dialog__footer) {
  padding: 10px 15px;
}

/* 信息填写区域样式 */
.info-fill-card {
  background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.info-fill-card-compact {
  background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 6px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.form-item-card {
  background: #ffffff;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 8px 10px;
  transition: all 0.3s ease;
}

.form-item-card-compact {
  background: #ffffff;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 5px 6px;
  transition: all 0.3s ease;
}

.form-item-card:hover,
.form-item-card-compact:hover {
  border-color: #409eff;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.15);
}

.form-item-label {
  display: flex;
  align-items: center;
  margin-bottom: 6px;
  padding-bottom: 4px;
  border-bottom: 1px solid #f0f0f0;
}

.form-item-label-compact {
  font-size: 11px;
  font-weight: 500;
  color: #606266;
  margin-bottom: 3px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.form-item-label .label-text {
  font-size: 12px;
  font-weight: 500;
  color: #303133;
  position: relative;
  padding-left: 8px;
}

.form-item-label .label-text::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 14px;
  background: linear-gradient(180deg, #409eff 0%, #66b1ff 100%);
  border-radius: 2px;
}

.split-detail-wrapper {
  overflow-x: auto;
}

.split-detail-desc {
  width: 100%;
}

.split-detail-desc :deep(.el-descriptions__table) {
  table-layout: fixed;
  width: 100%;
}

.split-detail-desc :deep(.el-descriptions__label) {
  width: 160px;
  min-width: 160px;
  max-width: 200px;
  white-space: nowrap;
  font-weight: 500;
  color: #606266;
  vertical-align: middle;
  padding: 8px 12px;
}

.split-detail-desc :deep(.el-descriptions__content) {
  min-width: 0;
  word-break: break-all;
  vertical-align: middle;
  padding: 8px 12px;
}

.detail-label :deep(.el-descriptions__label) {
  white-space: nowrap;
  font-weight: 500;
  color: #606266;
}

.detail-value :deep(.el-descriptions__content) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
  color: #409eff;
  max-width: 100%;
}

.detail-value :deep(.el-descriptions__content:hover) {
  text-decoration: underline;
}

.value-text {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
  color: #409eff;
}

.value-text:hover {
  text-decoration: underline;
}

.full-value-container {
  padding: 20px;
}

.full-value-container .field-name {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 2px solid #409eff;
}

.full-value-container .field-value {
  background-color: #f5f7fa;
  border-radius: 4px;
  padding: 20px;
  font-size: 14px;
  line-height: 1.8;
  word-break: break-all;
  word-wrap: break-word;
  color: #606266;
  max-height: 400px;
  overflow-y: auto;
}
</style>
