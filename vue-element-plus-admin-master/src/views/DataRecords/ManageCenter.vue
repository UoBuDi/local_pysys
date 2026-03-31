<template>
  <div class="manage-center">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>管理中心</span>
        </div>
      </template>
      <el-empty description="管理中心功能页面" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped lang="scss">
.manage-center {
  padding: 20px;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}
</style>
