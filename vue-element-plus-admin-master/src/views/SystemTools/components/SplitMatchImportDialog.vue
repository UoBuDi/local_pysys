<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="70%"
    destroy-on-close
    @close="handleClose"
  >
    <div class="import-preview-content">
      <div v-if="error" class="import-error">{{ error }}</div>

      <div v-else-if="step === 'preview'">
        <el-alert
          title="Excel文件数据"
          type="info"
          :description="`共读取到 ${data.length} 条数据，提取到 ${extractedImagesCount} 张图片`"
          show-icon
          :closable="false"
          style="margin-bottom: 20px"
        />
        <el-table :data="data" style="width: 100%" border max-height="400" size="small">
          <el-table-column
            v-for="column in columns"
            :key="column"
            :prop="column"
            :label="column"
            :width="getColumnWidth(column)"
          >
            <template v-if="['查核资料1', '查核资料2'].includes(column)" #default="{ row }">
              <div v-if="row[column]">
                <div
                  v-if="typeof row[column] === 'string' && row[column].startsWith('=DISPIMG(')"
                  class="import-wps-image"
                >
                  <el-icon style="color: #c0c4cc"><Picture /></el-icon>
                  <span style="margin-left: 5px; font-size: 12px; color: #909399">WPS图片</span>
                </div>
                <el-image
                  v-else-if="
                    typeof row[column] === 'string' &&
                    (isImageDataCheck(row[column]) || row[column].startsWith('data:image/'))
                  "
                  :src="row[column]"
                  fit="cover"
                  class="import-data-image"
                  :preview-src-list="[row[column]]"
                  :preview-teleported="true"
                  preview-z-index="9999"
                />
                <div v-else class="import-data-type">
                  <span>{{ typeof row[column] }}</span>
                </div>
              </div>
              <span v-else>-</span>
            </template>
            <template v-else-if="column === '通行标识ID'" #default="{ row }">
              <span :style="{ color: isIdMatched(row[column]) ? '#67c23a' : '#f56c6c' }">{{
                row[column]
              }}</span>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div
        v-else-if="step === 'matching' || step === 'importing'"
        class="import-progress-container"
      >
        <div class="import-loading-animation">
          <div class="import-spinner-outer"></div>
          <div class="import-spinner-inner"></div>
        </div>

        <div style="margin-bottom: 20px">
          <el-progress
            :percentage="progress"
            :status="progress === 100 ? 'success' : ''"
            :stroke-width="15"
            :show-text="false"
          />
          <div class="import-progress-label">{{ progressText }}</div>
          <div class="import-progress-percent">{{ progress }}%</div>
        </div>

        <div v-if="matchResult.length > 0 && step === 'importing'" class="import-match-result">
          <el-alert
            title="匹配结果"
            type="info"
            :description="`共匹配到 ${matchResult.length} 条数据`"
            show-icon
            :closable="false"
            style="margin-bottom: 20px"
          />
          <el-table :data="matchResult" style="width: 100%" border max-height="400">
            <el-table-column prop="通行标识ID" label="通行标识ID" width="300" />
            <el-table-column label="匹配状态" width="100">
              <template #default="{ row }">
                <el-tag type="success">{{ row.匹配状态 }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <div v-else-if="data.length === 0" class="import-no-data">没有读取到数据</div>
    </div>

    <template #footer>
      <el-button @click="handleCancel">取消</el-button>
      <el-button
        v-if="step === 'preview'"
        type="primary"
        @click="$emit('start-import')"
        :disabled="data.length === 0"
      >
        开始导入
      </el-button>
      <el-button
        v-else-if="step === 'importing'"
        type="primary"
        @click="visible = false"
        :disabled="loading"
      >
        完成
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { Picture } from '@element-plus/icons-vue'

interface ImportMatchResult {
  通行标识ID: string
  匹配状态: string
  导入数据: any
}

const props = defineProps<{
  modelValue: boolean
  step: 'preview' | 'matching' | 'importing'
  data: any[]
  columns: string[]
  error: string
  progress: number
  progressText: string
  loading: boolean
  extractedImagesCount: number
  matchResult: ImportMatchResult[]
  matchedIds: Set<string>
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'cancel'): void
  (e: 'start-import'): void
}>()

const visible = ref(props.modelValue)

watch(
  () => props.modelValue,
  (val) => {
    visible.value = val
  }
)
watch(visible, (val) => {
  emit('update:modelValue', val)
})

const dialogTitle = computed(() => {
  switch (props.step) {
    case 'preview':
      return '导入数据预览'
    case 'matching':
      return '正在匹配数据'
    case 'importing':
      return '正在导入数据'
    default:
      return '导入数据预览'
  }
})

const isImageDataCheck = (data: string): boolean => {
  return data.startsWith('=DISPIMG(') || data.startsWith('data:image/')
}

const isIdMatched = (id: any): boolean => {
  if (!id) return false
  const importId = String(id)
    .trim()
    .replace(/[^a-zA-Z0-9]/g, '')
    .toLowerCase()
  return props.matchedIds.has(importId)
}

const getColumnWidth = (column: string) => {
  const widthMap: Record<string, number> = {
    通行标识ID: 200,
    核查通行标识: 200,
    查核资料1: 100,
    查核资料2: 100
  }
  return widthMap[column] || 120
}

const handleCancel = () => {
  emit('cancel')
}

const handleClose = () => {
  emit('cancel')
}
</script>

<style scoped>
.import-preview-content {
  max-height: 600px;
  overflow-y: auto;
}

.import-error {
  color: #f56c6c;
}

.import-wps-image {
  width: 80px;
  height: 60px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f9fafc;
}

.import-data-image {
  width: 80px;
  height: 60px;
  cursor: pointer;
}

.import-data-type {
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
}

.import-loading-animation {
  margin-bottom: 20px;
  text-align: center;
  display: inline-block;
  position: relative;
  width: 40px;
  height: 40px;
}

.import-spinner-outer {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 3px solid #ecf5ff;
  border-top-color: #409eff;
  animation: spin 1s linear infinite;
}

.import-spinner-inner {
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
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.import-progress-label {
  margin-top: 15px;
  text-align: center;
  color: #409eff;
  font-size: 16px;
  font-weight: 500;
}

.import-progress-percent {
  margin-top: 5px;
  text-align: center;
  color: #606266;
  font-size: 14px;
}

.import-match-result {
  margin-top: 20px;
}

.import-no-data {
  text-align: center;
  padding: 40px;
  color: #909399;
}
</style>
