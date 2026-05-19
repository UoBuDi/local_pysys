<template>
  <el-dialog
    v-model="visible"
    title="导出进度"
    width="500px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="false"
    draggable
  >
    <div class="export-progress-content">
      <el-progress
        :percentage="percentage"
        :stroke-width="20"
        :text-inside="true"
        class="export-progress-bar"
      />
      <div class="export-progress-text">{{ progressText }}</div>
      <div v-if="totalCount > 0" class="export-progress-total">
        共 {{ totalCount }} 条数据
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  modelValue: boolean
  percentage: number
  progressText: string
  totalCount: number
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const visible = ref(props.modelValue)

watch(() => props.modelValue, (val) => {
  visible.value = val
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})
</script>

<style scoped>
.export-progress-content {
  padding: 20px 0;
}

.export-progress-bar {
  margin-bottom: 20px;
}

.export-progress-text {
  text-align: center;
  color: #606266;
  font-size: 14px;
}

.export-progress-total {
  text-align: center;
  color: #909399;
  font-size: 12px;
  margin-top: 10px;
}
</style>
