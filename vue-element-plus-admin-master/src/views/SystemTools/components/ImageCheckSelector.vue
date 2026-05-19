<template>
  <div class="image-check-selector">
    <div class="image-check-header">
      <el-radio v-model="activeField" :label="field" size="small">当前粘贴目标</el-radio>
    </div>
    <div v-if="imageSrc" class="image-check-preview">
      <el-image
        :src="imageSrc"
        fit="cover"
        class="image-check-img"
        :preview-src-list="previewList"
      />
      <el-button
        type="danger"
        size="small"
        circle
        class="image-check-delete"
        @click.stop="handleDelete"
      >
        <template #icon>
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 6h18" />
            <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
            <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
          </svg>
        </template>
      </el-button>
    </div>
    <el-upload
      action="#"
      :auto-upload="false"
      :on-change="handleUpload"
      :show-file-list="false"
      accept="image/*"
    >
      <el-button type="primary" size="small">上传图片</el-button>
    </el-upload>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  field: '查核资料1' | '查核资料2'
  imageSrc: string
  previewList: string[]
}>()

const emit = defineEmits<{
  (e: 'upload', file: any, field: string): void
  (e: 'delete', field: string): void
  (e: 'active-change', field: string): void
}>()

const activeField = computed({
  get: () => props.field,
  set: (val: string) => emit('active-change', val)
})

const handleUpload = (file: any) => {
  emit('upload', file, props.field)
}

const handleDelete = () => {
  emit('delete', props.field)
}
</script>

<style scoped>
.image-check-selector {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.image-check-header {
  margin-bottom: 5px;
  display: flex;
  align-items: center;
}

.image-check-preview {
  margin-bottom: 10px;
  position: relative;
}

.image-check-img {
  width: 200px;
  height: 150px;
  cursor: pointer;
}

.image-check-delete {
  position: absolute;
  top: 5px;
  right: 5px;
}
</style>
