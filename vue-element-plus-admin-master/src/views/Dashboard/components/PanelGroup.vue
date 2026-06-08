<script setup lang="ts">
import { ElRow, ElCol, ElCard, ElSkeleton } from 'element-plus'
import { CountTo } from '@/components/CountTo'
import { useDesign } from '@/hooks/web/useDesign'
import { useI18n } from '@/hooks/web/useI18n'
import type { DashboardStatistics } from '@/api/scheduled-tasks'

const { t } = useI18n()

const { getPrefixCls } = useDesign()

const prefixCls = getPrefixCls('panel')

const props = defineProps<{
  loading?: boolean
  statistics?: DashboardStatistics | null
}>()
</script>

<template>
  <ElRow :gutter="20" justify="space-between" :class="prefixCls">
    <ElCol :xl="8" :lg="8" :md="12" :sm="24" :xs="24">
      <ElCard shadow="hover" class="mb-20px">
        <ElSkeleton :loading="props.loading" animated :rows="2">
          <template #default>
            <div :class="`${prefixCls}__item flex justify-between`">
              <div>
                <div
                  :class="`${prefixCls}__item--icon ${prefixCls}__item--peoples p-16px inline-block rounded-6px`"
                >
                  <Icon icon="ep:document" :size="40" />
                </div>
              </div>
              <div class="flex flex-col justify-between">
                <div
                  :class="`${prefixCls}__item--text text-16px text-[var(--el-text-color-regular)] text-right`"
                  >{{ t('analysis.totalTransactions') }}</div
                >
                <CountTo
                  class="text-20px font-700 text-right"
                  :start-val="0"
                  :end-val="props.statistics?.total_transactions || 0"
                  :duration="2600"
                />
              </div>
            </div>
          </template>
        </ElSkeleton>
      </ElCard>
    </ElCol>

    <ElCol :xl="8" :lg="8" :md="12" :sm="24" :xs="24">
      <ElCard shadow="hover" class="mb-20px">
        <ElSkeleton :loading="props.loading" animated :rows="2">
          <template #default>
            <div :class="`${prefixCls}__item flex justify-between`">
              <div>
                <div
                  :class="`${prefixCls}__item--icon ${prefixCls}__item--free p-16px inline-block rounded-6px`"
                >
                  <Icon icon="ep:tickets" :size="40" />
                </div>
              </div>
              <div class="flex flex-col justify-between">
                <div
                  :class="`${prefixCls}__item--text text-16px text-[var(--el-text-color-regular)] text-right`"
                  >{{ t('analysis.freeTransactions') }}</div
                >
                <CountTo
                  class="text-20px font-700 text-right"
                  :start-val="0"
                  :end-val="props.statistics?.free_transactions || 0"
                  :duration="2600"
                />
              </div>
            </div>
          </template>
        </ElSkeleton>
      </ElCard>
    </ElCol>

    <ElCol :xl="8" :lg="8" :md="12" :sm="24" :xs="24">
      <ElCard shadow="hover" class="mb-20px">
        <ElSkeleton :loading="props.loading" animated :rows="2">
          <template #default>
            <div :class="`${prefixCls}__item flex justify-between`">
              <div>
                <div
                  :class="`${prefixCls}__item--icon ${prefixCls}__item--money p-16px inline-block rounded-6px`"
                >
                  <Icon icon="ep:coin" :size="40" />
                </div>
              </div>
              <div class="flex flex-col justify-between">
                <div
                  :class="`${prefixCls}__item--text text-16px text-[var(--el-text-color-regular)] text-right`"
                  >{{ t('analysis.splitSectionAmount') }}</div
                >
                <CountTo
                  class="text-20px font-700 text-right"
                  :start-val="0"
                  :end-val="props.statistics?.split_section_amount || 0"
                  :duration="2600"
                  :decimals="2"
                />
              </div>
            </div>
          </template>
        </ElSkeleton>
      </ElCard>
    </ElCol>
  </ElRow>
</template>

<style lang="less" scoped>
@prefix-cls: ~'@{adminNamespace}-panel';

.@{prefix-cls} {
  &__item {
    &--peoples {
      color: #40c9c6;
      background: #e6f9f8;
    }

    &--free {
      color: #36a3f7;
      background: #e6f3fb;
    }

    &--money {
      color: #f4516c;
      background: #fce5e8;
    }

    &:hover {
      :deep(.@{adminNamespace}-icon) {
        color: #fff !important;
      }
      .@{prefix-cls}__item--icon {
        transition: all 0.38s ease-out;
      }
      .@{prefix-cls}__item--peoples {
        background: #40c9c6;
      }
      .@{prefix-cls}__item--free {
        background: #36a3f7;
      }
      .@{prefix-cls}__item--money {
        background: #f4516c;
      }
    }
  }
}
</style>
