<template>
  <el-dialog
    v-model="visible"
    title="工单处理详情"
    width="92%"
    :close-on-click-modal="false"
    destroy-on-close
    draggable
    top="3vh"
    @close="handleClose"
  >
    <div v-if="loading" style="text-align: center; padding: 100px">
      <el-icon class="is-loading" :size="50"><Loading /></el-icon>
      <div style="margin-top: 20px; font-size: 16px">正在加载工单详情...</div>
    </div>

    <div v-else-if="detail" style="display: flex; gap: 16px; height: 82vh; overflow: hidden">
      <div class="order-detail-left">
        <div class="order-detail-section">
          <div class="order-detail-section-title">📋 基本信息</div>
          <el-descriptions :column="1" size="small" :labelStyle="{ width: '90px', color: '#909399' }">
            <el-descriptions-item label="车牌号码">{{ detail.labelVo?.vehicle_no || '-' }}</el-descriptions-item>
            <el-descriptions-item label="入口收费站">{{ detail.labelVo?.en_station_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="入口时间">{{ detail.labelVo?.en_time || '-' }}</el-descriptions-item>
            <el-descriptions-item label="出口收费站">{{ detail.labelVo?.ex_station_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="出口时间">{{ detail.labelVo?.ex_time || '-' }}</el-descriptions-item>
            <el-descriptions-item label="出口收费总额">
              <span style="color: #e6a23c; font-weight: bold">¥ {{ detail.pay_amount ? (detail.pay_amount / 100).toFixed(2) : '0.00' }} 元</span>
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <div v-if="detail.labelCodeList && detail.labelCodeList.length > 0" class="order-detail-section">
          <div class="order-detail-section-title">🏷️ 标签信息</div>
          <div
            v-for="(label, idx) in detail.labelCodeList"
            :key="idx"
            class="order-detail-label-item"
          >
            <div style="display: flex; align-items: center; margin-bottom: 4px">
              <el-tag size="small" type="warning" style="margin-right: 8px">{{ label.labelCode }}</el-tag>
              <span style="font-weight: 500; font-size: 13px">{{ label.labelName }}</span>
            </div>
            <div v-if="label.auditMethod" class="order-detail-label-method">{{ label.auditMethod }}</div>
          </div>
        </div>

        <div v-if="detail.auditCheckdescConfigs && detail.auditCheckdescConfigs.length > 0" class="order-detail-section">
          <div class="order-detail-section-title">✅ 稽核步骤</div>
          <div v-for="(config, idx) in detail.auditCheckdescConfigs" :key="idx" style="margin-bottom: 10px">
            <div style="display: flex; align-items: center; margin-bottom: 6px">
              <span class="order-detail-step-number">{{ idx + 1 }}</span>
              <span style="font-weight: 500; font-size: 13px">{{ config.checkStep1Name || config.checkStep2Name || config.checkStep3Name }}</span>
            </div>
            <div style="font-size: 12px; color: #606266; line-height: 1.5; padding-left: 24px">
              {{ config.checkStep1Desc || config.checkStep2Desc || config.checkStep3Desc }}
            </div>
          </div>
        </div>

        <div v-if="detail.picBeanVo?.picBeanList" class="order-detail-section">
          <div class="order-detail-section-title">
            📷 查看图片 ({{ detail.picBeanVo.total || detail.picBeanVo.picBeanList.length }})
          </div>
          <div class="order-detail-image-list">
            <div
              v-for="(pic, idx) in detail.picBeanVo.picBeanList"
              :key="idx"
              class="order-detail-image-item"
              :class="{ 'is-selected': selectedPicture?.picId === pic.picId }"
              @click="selectedPicture = pic"
            >
              <img
                v-if="pic.smallPositivePic"
                :src="pic.smallPositivePic"
                class="order-detail-image-thumb"
              />
              <div style="flex: 1; min-width: 0">
                <div class="order-detail-image-name">{{ pic.stationName || ('图片 ' + (idx + 1)) }}</div>
                <div class="order-detail-image-time">{{ pic.picTime || '-' }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="order-detail-right">
        <div style="margin-bottom: 20px">
          <div class="order-detail-divider-title">📊 稽核信息</div>
          <el-alert type="info" :closable="false" show-icon style="margin-bottom: 12px">
            <template #title>
              <span style="font-size: 13px">【{{ detail.labelVo?.vehicle_no }}】稽核模型利用交易流水中"收费车型与真实车型不符"的特征值进行敏感性筛查，须稽查人员通过门架图片、监控录像等方式确认车辆车型信息。</span>
            </template>
          </el-alert>

          <div v-if="detail.labelVo?.audit_remark" class="order-detail-conclusion">
            <div class="order-detail-conclusion-title">
              <el-icon :size="18" style="margin-right: 6px"><CircleCheck /></el-icon>
              处理结论
            </div>
            <div class="order-detail-conclusion-content">{{ detail.labelVo.audit_remark }}</div>
          </div>

          <div v-if="detail.labelCodeList && detail.labelCodeList.length > 0" class="order-detail-tags-section">
            <div style="font-weight: bold; font-size: 14px; color: #303133; margin-bottom: 8px">【主标签】</div>
            <div v-for="(label, idx) in detail.labelCodeList" :key="idx" style="display: inline-flex; align-items: center; margin: 4px 8px 4px 0">
              <el-tag type="warning" effect="dark" size="large">{{ label.labelName }}</el-tag>
            </div>
          </div>

          <div v-if="detail.auditCheckdescConfigs && detail.auditCheckdescConfigs.length > 0">
            <el-steps :active="3" finish-status="success" simple style="margin-bottom: 16px">
              <el-step title="车型确认" />
              <el-step title="费用测算" />
              <el-step title="稽核取证" />
            </el-steps>
            <div v-for="(config, idx) in detail.auditCheckdescConfigs" :key="idx" class="order-detail-steps-row">
              <div class="order-detail-step-card order-detail-step-1">
                <div style="display: flex; align-items: center; margin-bottom: 8px">
                  <el-icon :size="24" style="margin-right: 8px"><CircleCheck /></el-icon>
                  <span style="font-weight: bold; font-size: 15px">{{ config.checkStep1Name || '车型确认' }}</span>
                </div>
                <div style="font-size: 13px; line-height: 1.6; opacity: 0.95">{{ config.checkStep1Desc || '通过图片和监控录像核实实际车型' }}</div>
              </div>
              <div class="order-detail-step-card order-detail-step-2">
                <div style="display: flex; align-items: center; margin-bottom: 8px">
                  <el-icon :size="24" style="margin-right: 8px"><Money /></el-icon>
                  <span style="font-weight: bold; font-size: 15px">{{ config.checkStep2Name || '费用测算' }}</span>
                </div>
                <div style="font-size: 13px; line-height: 1.6; opacity: 0.95">{{ config.checkStep2Desc || '测算实际行驶路径应收费额，与出口实收或省域拆分金额校核是否一致' }}</div>
              </div>
              <div class="order-detail-step-card order-detail-step-3">
                <div style="display: flex; align-items: center; margin-bottom: 8px">
                  <el-icon :size="24" style="margin-right: 8px"><Camera /></el-icon>
                  <span style="font-weight: bold; font-size: 15px">{{ config.checkStep3Name || '稽核取证' }}</span>
                </div>
                <div style="font-size: 13px; line-height: 1.6; opacity: 0.95">{{ config.checkStep3Desc || '车型截图：门架图片或出入口录像\n金额截图：实际应收金额、出口实收金额' }}</div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="selectedPicture">
          <div class="order-detail-divider-title" style="border-bottom-color: #67c23a">
            🖼️ 门架图片
            <el-tag style="margin-left: 12px" type="success">{{ selectedPicture.stationName || '图片详情' }}</el-tag>
          </div>

          <el-descriptions :column="4" border size="small" style="margin-bottom: 16px">
            <el-descriptions-item label="拍摄时间">{{ selectedPicture.picTime || '-' }}</el-descriptions-item>
            <el-descriptions-item label="车牌号码">{{ selectedPicture.vehPlate || '-' }}</el-descriptions-item>
            <el-descriptions-item label="站ID">{{ selectedPicture.stationId || '-' }}</el-descriptions-item>
            <el-descriptions-item label="拍摄位置">{{ selectedPicture.shootPosition === '1' ? '车头' : (selectedPicture.shootPosition === '2' ? '车尾' : '-') }}</el-descriptions-item>
          </el-descriptions>

          <div class="order-detail-big-image">
            <el-image
              v-if="selectedPicture.bigPositivePic"
              :src="selectedPicture.bigPositivePic"
              fit="contain"
              class="order-detail-preview-image"
              :preview-src-list="[selectedPicture.bigPositivePic]"
              preview-teleported
              :z-index="9999"
            >
              <template #error>
                <div class="image-slot">
                  <el-icon :size="48"><PictureFilled /></el-icon>
                </div>
              </template>
            </el-image>
            <div v-else class="order-detail-no-image">
              <el-icon :size="64"><WarningFilled /></el-icon>
              <div style="margin-top: 12px; font-size: 14px">暂无大图</div>
            </div>
          </div>

          <div v-if="selectedPicture.smallPositivePic || selectedPicture.smallBackPic" class="order-detail-small-images">
            <div v-if="selectedPicture.smallPositivePic" class="order-detail-small-image-item">
              <div class="order-detail-small-image-label">车头小图</div>
              <el-image
                :src="selectedPicture.smallPositivePic"
                fit="cover"
                class="order-detail-small-image"
                :preview-src-list="[selectedPicture.smallPositivePic]"
                preview-teleported
              />
            </div>
            <div v-if="selectedPicture.smallBackPic" class="order-detail-small-image-item">
              <div class="order-detail-small-image-label">车尾小图</div>
              <el-image
                :src="selectedPicture.smallBackPic"
                fit="cover"
                class="order-detail-small-image"
                :preview-src-list="[selectedPicture.smallBackPic]"
                preview-teleported
              />
            </div>
          </div>
        </div>

        <div v-else class="order-detail-empty-pictures">
          <el-icon :size="80"><PictureFilled /></el-icon>
          <div style="margin-top: 16px; font-size: 16px">请从左侧列表选择图片查看</div>
          <div style="margin-top: 8px; font-size: 13px">共 {{ detail.picBeanVo?.total || detail.picBeanVo?.picBeanList?.length || 0 }} 张图片</div>
        </div>

        <el-collapse style="margin-top: 20px">
          <el-collapse-item name="raw_data">
            <template #title>
              <div class="order-detail-raw-title">
                <span>🔧 查看完整原始JSON数据</span>
                <el-button type="primary" size="small" :icon="CopyDocument" @click.stop="handleCopyJson">一键复制</el-button>
              </div>
            </template>
            <pre class="order-detail-json-pre">{{ JSON.stringify(detail, null, 2) }}</pre>
          </el-collapse-item>
        </el-collapse>
      </div>
    </div>

    <div v-else style="text-align: center; padding: 100px; color: #909399">
      <el-icon :size="60"><WarningFilled /></el-icon>
      <div style="margin-top: 20px; font-size: 16px">暂无工单数据</div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { CopyDocument, Loading, WarningFilled, CircleCheck, Money, Camera, PictureFilled } from '@element-plus/icons-vue'

const props = defineProps<{
  modelValue: boolean
  loading: boolean
  detail: any
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const visible = ref(props.modelValue)
const selectedPicture = ref<any>(null)

watch(() => props.modelValue, (val) => {
  visible.value = val
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

watch(() => props.detail, (newDetail) => {
  if (newDetail?.picBeanVo?.picBeanList?.length > 0) {
    selectedPicture.value = newDetail.picBeanVo.picBeanList[0]
  } else {
    selectedPicture.value = null
  }
})

const handleClose = () => {
  selectedPicture.value = null
}

const handleCopyJson = async () => {
  try {
    const jsonString = JSON.stringify(props.detail, null, 2)
    await navigator.clipboard.writeText(jsonString)
    ElMessage.success('JSON数据已复制到剪贴板')
  } catch (error) {
    const textArea = document.createElement('textarea')
    textArea.value = JSON.stringify(props.detail, null, 2)
    textArea.style.position = 'fixed'
    textArea.style.left = '-9999px'
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    document.body.removeChild(textArea)
    ElMessage.success('JSON数据已复制到剪贴板')
  }
}
</script>

<style scoped>
.order-detail-left {
  width: 320px;
  flex-shrink: 0;
  overflow-y: auto;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background: #fff;
}

.order-detail-section {
  padding: 12px;
  border-bottom: 1px solid #ebeef5;
}

.order-detail-section:first-child {
  background: #f5f7fa;
}

.order-detail-section-title {
  font-weight: bold;
  font-size: 14px;
  color: #303133;
  margin-bottom: 8px;
}

.order-detail-label-item {
  margin-bottom: 8px;
  padding: 8px;
  background: #f5f7fa;
  border-radius: 4px;
}

.order-detail-label-method {
  font-size: 12px;
  color: #606266;
  line-height: 1.5;
  margin-top: 4px;
}

.order-detail-step-number {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #409eff;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  margin-right: 6px;
}

.order-detail-image-list {
  max-height: 400px;
  overflow-y: auto;
}

.order-detail-image-item {
  display: flex;
  align-items: center;
  padding: 6px;
  margin-bottom: 4px;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
  background: #fff;
  border: 1px solid #ebeef5;
}

.order-detail-image-item.is-selected {
  background: #ecf5ff;
  border: 1px solid #409eff;
}

.order-detail-image-thumb {
  width: 48px;
  height: 36px;
  object-fit: cover;
  border-radius: 2px;
  margin-right: 8px;
  flex-shrink: 0;
}

.order-detail-image-name {
  font-size: 12px;
  font-weight: 500;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.order-detail-image-time {
  font-size: 11px;
  color: #909399;
  margin-top: 2px;
}

.order-detail-right {
  flex: 1;
  overflow-y: auto;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background: #fff;
  padding: 16px;
}

.order-detail-divider-title {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #409eff;
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.order-detail-conclusion {
  background: linear-gradient(135deg, #f0f9eb 0%, #f5f7fa 100%);
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 12px;
  border-left: 4px solid #67c23a;
  box-shadow: 0 2px 8px rgba(103, 194, 58, 0.1);
}

.order-detail-conclusion-title {
  font-size: 14px;
  font-weight: bold;
  color: #67c23a;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
}

.order-detail-conclusion-content {
  color: #606266;
  line-height: 1.8;
  font-size: 13px;
}

.order-detail-tags-section {
  background: #fafafa;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 12px;
}

.order-detail-steps-row {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.order-detail-step-card {
  flex: 1;
  padding: 16px;
  border-radius: 8px;
  color: #fff;
}

.order-detail-step-1 {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.order-detail-step-2 {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.order-detail-step-3 {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.order-detail-big-image {
  text-align: center;
  background: #f5f7fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.order-detail-preview-image {
  max-width: 100%;
  max-height: 500px;
  border-radius: 4px;
}

.image-slot {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 300px;
  background: #f5f7fa;
  color: #909399;
}

.order-detail-no-image {
  color: #909399;
  padding: 40px;
  text-align: center;
}

.order-detail-small-images {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.order-detail-small-image-item {
  flex: 1;
  text-align: center;
}

.order-detail-small-image-label {
  font-size: 12px;
  color: #606266;
  margin-bottom: 6px;
}

.order-detail-small-image {
  width: 100%;
  height: 180px;
  border-radius: 4px;
}

.order-detail-empty-pictures {
  text-align: center;
  padding: 80px 20px;
  color: #909399;
}

.order-detail-raw-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding-right: 16px;
}

.order-detail-json-pre {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
  line-height: 1.5;
  max-height: 400px;
  overflow-y: auto;
}
</style>
