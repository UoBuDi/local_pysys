<template>
  <div class="scheduling-staff">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>人员管理</span>
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
              新增人员
            </el-button>
          </div>
        </div>
      </template>
      
      <div class="filter-section">
        <el-form :inline="true">
          <el-form-item label="班组">
            <el-select v-model="filterGroupId" placeholder="全部班组" clearable @change="loadData">
              <el-option
                v-for="group in groups"
                :key="group.id"
                :label="group.name"
                :value="group.id"
              />
            </el-select>
          </el-form-item>
        </el-form>
      </div>
      
      <el-table :data="tableData" border stripe v-loading="loading">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="name" label="姓名" min-width="100" />
        <el-table-column prop="group_name" label="所属班组" min-width="100" />
        <el-table-column prop="phone" label="联系电话" min-width="120" />
        <el-table-column prop="status" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'">
              {{ row.status === 1 ? '在职' : '离职' }}
            </el-tag>
          </template>
        </el-table-column>
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
    
    <el-dialog v-model="dialogVisible" :title="editForm.id ? '编辑人员' : '新增人员'" width="500px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="姓名" required>
          <el-input v-model="editForm.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="所属班组">
          <el-select v-model="editForm.group_id" placeholder="请选择班组" style="width: 100%">
            <el-option
              v-for="group in groups"
              :key="group.id"
              :label="group.name"
              :value="group.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="editForm.phone" placeholder="请输入联系电话" />
        </el-form-item>
        <el-form-item label="状态" v-if="editForm.id">
          <el-radio-group v-model="editForm.status">
            <el-radio :value="1">在职</el-radio>
            <el-radio :value="0">离职</el-radio>
          </el-radio-group>
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

interface Group {
  id: number
  name: string
}

interface Staff {
  id: number
  name: string
  group_id?: number
  group_name?: string
  phone?: string
  status: number
}

const loading = ref(false)
const tableData = ref<Staff[]>([])
const groups = ref<Group[]>([])
const filterGroupId = ref<number | null>(null)
const dialogVisible = ref(false)

const editForm = reactive({
  id: null as number | null,
  name: '',
  group_id: null as number | null,
  phone: '',
  status: 1
})

const loadGroups = async () => {
  try {
    const res = await request.get({ url: '/api/scheduling/groups/' })
    if (res.code === 200) {
      groups.value = res.data || []
    }
  } catch (error) {
    console.error('加载班组数据失败:', error)
  }
}

const loadData = async () => {
  try {
    loading.value = true
    const params: any = {}
    if (filterGroupId.value) {
      params.group_id = filterGroupId.value
    }
    const res = await request.get({ url: '/api/scheduling/staff/', params })
    if (res.code === 200) {
      tableData.value = res.data || []
    }
  } catch (error) {
    console.error('加载人员数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  editForm.id = null
  editForm.name = ''
  editForm.group_id = null
  editForm.phone = ''
  editForm.status = 1
  dialogVisible.value = true
}

const handleEdit = (row: Staff) => {
  editForm.id = row.id
  editForm.name = row.name
  editForm.group_id = row.group_id || null
  editForm.phone = row.phone || ''
  editForm.status = row.status
  dialogVisible.value = true
}

const handleSave = async () => {
  if (!editForm.name) {
    ElMessage.warning('请输入姓名')
    return
  }
  
  try {
    if (editForm.id) {
      const res = await request.put({
        url: `/api/scheduling/staff/${editForm.id}`,
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
        url: '/api/scheduling/staff/',
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

const handleDelete = async (row: Staff) => {
  try {
    await ElMessageBox.confirm('确定要删除该人员吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const res = await request.delete({ url: `/api/scheduling/staff/${row.id}` })
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
    const params: any = {}
    if (filterGroupId.value) {
      params.group_id = filterGroupId.value
    }
    const res = await request.get({
      url: '/api/scheduling/staff/export/',
      params,
      responseType: 'blob'
    })
    
    const blobData = res.data || res
    const blob = new Blob([blobData], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `人员数据_${new Date().toISOString().slice(0, 10)}.xlsx`
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
      url: '/api/scheduling/staff/import/',
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
  loadGroups()
  loadData()
})
</script>

<style lang="scss" scoped>
.scheduling-staff {
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
  
  .filter-section {
    margin-bottom: 20px;
  }
}
</style>
