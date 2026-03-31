<template>
  <div class="scheduling-shifts">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>班次管理</span>
          <div class="header-actions">
            <el-button type="primary" @click="handleExport">
              <el-icon><Download /></el-icon>
              导出
            </el-button>
            <el-upload
              :show-file-list="false"
              :before-upload="handleImport"
              accept=".xlsx,.xls"
              style="margin-left: 10px"
            >
              <el-button type="warning">
                <el-icon><Upload /></el-icon>
                导入
              </el-button>
            </el-upload>
            <el-button type="primary" @click="handleAdd" style="margin-left: 10px">
              <el-icon><Plus /></el-icon>
              新增班次
            </el-button>
          </div>
        </div>
      </template>
      
      <el-table :data="tableData" border stripe v-loading="loading">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="name" label="班次名称" min-width="100" />
        <el-table-column prop="start_time" label="开始时间" width="120" align="center" />
        <el-table-column prop="end_time" label="结束时间" width="120" align="center" />
        <el-table-column prop="description" label="描述" min-width="150" />
        <el-table-column label="操作" width="150" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button type="danger" link @click="handleDelete(row)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-dialog v-model="dialogVisible" :title="editForm.id ? '编辑班次' : '新增班次'" width="500px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="班次名称" required>
          <el-input v-model="editForm.name" placeholder="请输入班次名称，如：早班、中班、晚班" />
        </el-form-item>
        <el-form-item label="开始时间" required>
          <el-time-picker
            v-model="editForm.start_time"
            placeholder="选择开始时间"
            format="HH:mm"
            value-format="HH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="结束时间" required>
          <el-time-picker
            v-model="editForm.end_time"
            placeholder="选择结束时间"
            format="HH:mm"
            value-format="HH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Upload, Plus, Edit, Delete } from '@element-plus/icons-vue'
import request from '@/axios'

interface Shift {
  id: number
  name: string
  start_time: string
  end_time: string
  description?: string
}

const loading = ref(false)
const tableData = ref<Shift[]>([])
const dialogVisible = ref(false)

const editForm = reactive({
  id: null as number | null,
  name: '',
  start_time: '',
  end_time: '',
  description: ''
})

const loadData = async () => {
  try {
    loading.value = true
    const res = await request.get({ url: '/api/scheduling/shifts/' })
    if (res.code === 200) {
      tableData.value = res.data || []
    }
  } catch (error) {
    console.error('加载班次数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  editForm.id = null
  editForm.name = ''
  editForm.start_time = ''
  editForm.end_time = ''
  editForm.description = ''
  dialogVisible.value = true
}

const handleEdit = (row: Shift) => {
  editForm.id = row.id
  editForm.name = row.name
  editForm.start_time = row.start_time
  editForm.end_time = row.end_time
  editForm.description = row.description || ''
  dialogVisible.value = true
}

const handleSave = async () => {
  if (!editForm.name) {
    ElMessage.warning('请输入班次名称')
    return
  }
  if (!editForm.start_time) {
    ElMessage.warning('请选择开始时间')
    return
  }
  if (!editForm.end_time) {
    ElMessage.warning('请选择结束时间')
    return
  }
  
  try {
    if (editForm.id) {
      const res = await request.put({
        url: `/api/scheduling/shifts/${editForm.id}`,
        data: editForm
      })
      if (res.code === 200) {
        ElMessage.success('更新成功')
        dialogVisible.value = false
        loadData()
      } else {
        ElMessage.error(res.message || '更新失败')
      }
    } else {
      const res = await request.post({
        url: '/api/scheduling/shifts/',
        data: editForm
      })
      if (res.code === 200) {
        ElMessage.success('创建成功')
        dialogVisible.value = false
        loadData()
      } else {
        ElMessage.error(res.message || '创建失败')
      }
    }
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  }
}

const handleDelete = async (row: Shift) => {
  try {
    await ElMessageBox.confirm('确定要删除该班次吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const res = await request.delete({ url: `/api/scheduling/shifts/${row.id}` })
    if (res.code === 200) {
      ElMessage.success('删除成功')
      loadData()
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const handleExport = async () => {
  try {
    const res = await request.get({
      url: '/api/scheduling/shifts/export/',
      responseType: 'blob'
    })
    
    const blobData = res.data || res
    const blob = new Blob([blobData], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `班次数据_${new Date().toISOString().slice(0, 10)}.xlsx`
    link.click()
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

const handleImport = async (file: File) => {
  try {
    const formData = new FormData()
    formData.append('file', file)
    
    const res = await request.post({
      url: '/api/scheduling/shifts/import/',
      data: formData,
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    if (res.code === 200) {
      ElMessage.success(`导入成功，共导入 ${res.data.count} 条记录`)
      loadData()
    } else {
      ElMessage.error(res.message || '导入失败')
    }
  } catch (error) {
    console.error('导入失败:', error)
    ElMessage.error('导入失败')
  }
  
  return false
}

onMounted(() => {
  loadData()
})
</script>

<style lang="scss" scoped>
.scheduling-shifts {
  padding: 20px;
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .header-actions {
      display: flex;
      align-items: center;
    }
  }
}
</style>
