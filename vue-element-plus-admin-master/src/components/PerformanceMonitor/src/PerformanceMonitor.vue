<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { performanceMonitor, getWebVitals, getResourceStats } from '@/utils/performanceMonitor'
import { ElCard, ElRow, ElCol, ElStatistic, ElProgress, ElTable, ElTableColumn } from 'element-plus'

const showPanel = ref(false)
const autoRefresh = ref(true)
const refreshInterval = ref<number>(5000)

const webVitals = ref<any>({})
const resourceStats = ref<any>({})
const customMetrics = ref<any[]>([])

let refreshTimer: number | null = null

const loadStats = () => {
  webVitals.value = getWebVitals()
  resourceStats.value = getResourceStats()
  customMetrics.value = performanceMonitor.getMetrics()
}

const formatBytes = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatTime = (ms: number) => {
  if (ms < 1000) return `${ms.toFixed(0)}ms`
  return `${(ms / 1000).toFixed(2)}s`
}

const getScore = (value: number, thresholds: { good: number; poor: number }) => {
  if (value <= thresholds.good) return { score: 100, status: 'good', label: '优秀' }
  if (value <= thresholds.poor) return { score: 75, status: 'needs-improvement', label: '需改进' }
  return { score: 25, status: 'poor', label: '较差' }
}

const fcpScore = computed(() => getScore(webVitals.value.FCP || 0, { good: 1800, poor: 3000 }))
const ttfbScore = computed(() => getScore(webVitals.value.TTFB || 0, { good: 800, poor: 1800 }))
const loadScore = computed(() => getScore(webVitals.value.Load || 0, { good: 3000, poor: 5000 }))

const startAutoRefresh = () => {
  if (refreshTimer) clearInterval(refreshTimer)
  refreshTimer = window.setInterval(loadStats, refreshInterval.value)
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

const togglePanel = () => {
  showPanel.value = !showPanel.value
  if (showPanel.value) {
    loadStats()
    if (autoRefresh.value) startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}

const clearMetrics = () => {
  performanceMonitor.clearMetrics()
  loadStats()
}

onMounted(() => {
  loadStats()
  if (autoRefresh.value) startAutoRefresh()
})

onBeforeUnmount(() => {
  stopAutoRefresh()
})
</script>

<template>
  <div class="performance-monitor">
    <div class="monitor-toggle" @click="togglePanel">
      <span class="toggle-icon">📊</span>
    </div>

    <div v-if="showPanel" class="monitor-panel">
      <ElCard class="panel-card">
        <template #header>
          <div class="panel-header">
            <span>性能监控面板</span>
            <div class="panel-actions">
              <el-button size="small" @click="loadStats">刷新</el-button>
              <el-button size="small" @click="clearMetrics">清除</el-button>
              <el-button size="small" @click="togglePanel">关闭</el-button>
            </div>
          </div>
        </template>

        <ElRow :gutter="20">
          <ElCol :span="24">
            <h3>Web Vitals</h3>
          </ElCol>
        </ElRow>

        <ElRow :gutter="20" class="vitals-row">
          <ElCol :span="6">
            <ElCard shadow="hover">
              <ElStatistic title="首次内容绘制 (FCP)" :value="formatTime(webVitals.FCP || 0)">
                <template #suffix>
                  <div class="score-badge" :class="fcpScore.status">
                    {{ fcpScore.label }}
                  </div>
                </template>
              </ElStatistic>
              <ElProgress
                :percentage="fcpScore.score"
                :status="
                  fcpScore.status === 'good'
                    ? 'success'
                    : fcpScore.status === 'poor'
                      ? 'exception'
                      : 'warning'
                "
              />
            </ElCard>
          </ElCol>

          <ElCol :span="6">
            <ElCard shadow="hover">
              <ElStatistic title="首字节时间 (TTFB)" :value="formatTime(webVitals.TTFB || 0)">
                <template #suffix>
                  <div class="score-badge" :class="ttfbScore.status">
                    {{ ttfbScore.label }}
                  </div>
                </template>
              </ElStatistic>
              <ElProgress
                :percentage="ttfbScore.score"
                :status="
                  ttfbScore.status === 'good'
                    ? 'success'
                    : ttfbScore.status === 'poor'
                      ? 'exception'
                      : 'warning'
                "
              />
            </ElCard>
          </ElCol>

          <ElCol :span="6">
            <ElCard shadow="hover">
              <ElStatistic title="页面加载时间" :value="formatTime(webVitals.Load || 0)">
                <template #suffix>
                  <div class="score-badge" :class="loadScore.status">
                    {{ loadScore.label }}
                  </div>
                </template>
              </ElStatistic>
              <ElProgress
                :percentage="loadScore.score"
                :status="
                  loadScore.status === 'good'
                    ? 'success'
                    : loadScore.status === 'poor'
                      ? 'exception'
                      : 'warning'
                "
              />
            </ElCard>
          </ElCol>

          <ElCol :span="6">
            <ElCard shadow="hover">
              <ElStatistic title="DOM内容加载" :value="formatTime(webVitals.DCL || 0)" />
            </ElCard>
          </ElCol>
        </ElRow>

        <ElRow :gutter="20" class="stats-row">
          <ElCol :span="12">
            <h3>资源统计</h3>
            <ElCard shadow="hover">
              <ElStatistic title="资源总数" :value="resourceStats.total || 0" />
              <div class="resource-types">
                <div
                  v-for="(stats, type) in resourceStats.byType"
                  :key="type"
                  class="resource-type"
                >
                  <span class="type-name">{{ type }}</span>
                  <span class="type-count">{{ stats.count }}个</span>
                  <span class="type-size">{{ formatBytes(stats.size) }}</span>
                </div>
              </div>
            </ElCard>
          </ElCol>

          <ElCol :span="12">
            <h3>最慢资源 (Top 5)</h3>
            <ElTable
              :data="resourceStats.slowest?.slice(0, 5) || []"
              style="width: 100%"
              max-height="300"
            >
              <ElTableColumn prop="name" label="资源" width="200" show-overflow-tooltip />
              <ElTableColumn prop="duration" label="耗时" width="100">
                <template #default="{ row }">
                  {{ formatTime(row.duration) }}
                </template>
              </ElTableColumn>
              <ElTableColumn prop="size" label="大小" width="100">
                <template #default="{ row }">
                  {{ formatBytes(row.size) }}
                </template>
              </ElTableColumn>
            </ElTable>
          </ElCol>
        </ElRow>

        <ElRow :gutter="20" class="metrics-row">
          <ElCol :span="24">
            <h3>自定义指标</h3>
            <ElTable :data="customMetrics" style="width: 100%" max-height="300">
              <ElTableColumn prop="name" label="指标名称" width="200" />
              <ElTableColumn prop="value" label="值" width="150">
                <template #default="{ row }">
                  {{ formatTime(row.value) }}
                </template>
              </ElTableColumn>
              <ElTableColumn prop="type" label="类型" width="120" />
              <ElTableColumn prop="timestamp" label="时间戳" width="180">
                <template #default="{ row }">
                  {{ new Date(row.timestamp).toLocaleString() }}
                </template>
              </ElTableColumn>
            </ElTable>
          </ElCol>
        </ElRow>
      </ElCard>
    </div>
  </div>
</template>

<style scoped lang="less">
.performance-monitor {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 9999;
}

.monitor-toggle {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;

  &:hover {
    transform: scale(1.1);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
  }

  .toggle-icon {
    font-size: 24px;
  }
}

.monitor-panel {
  position: absolute;
  bottom: 60px;
  right: 0;
  width: 900px;
  max-height: 80vh;
  overflow-y: auto;
  background: white;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.panel-card {
  border: none;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  span {
    font-size: 18px;
    font-weight: bold;
  }
}

.panel-actions {
  display: flex;
  gap: 8px;
}

.vitals-row,
.stats-row,
.metrics-row {
  margin-top: 20px;
}

h3 {
  margin-bottom: 12px;
  font-size: 16px;
  font-weight: bold;
  color: #333;
}

.score-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;

  &.good {
    background-color: #52c41a;
    color: white;
  }

  &.needs-improvement {
    background-color: #faad14;
    color: white;
  }

  &.poor {
    background-color: #ff4d4f;
    color: white;
  }
}

.resource-types {
  margin-top: 12px;
}

.resource-type {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;

  &:last-child {
    border-bottom: none;
  }

  .type-name {
    font-weight: bold;
    color: #333;
  }

  .type-count,
  .type-size {
    color: #666;
    font-size: 14px;
  }
}
</style>
