<template>
  <div class="scheduling">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>排班日历</span>
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
            <el-button type="danger" @click="handleResetMonth" style="margin-left: 10px">
              <el-icon><Refresh /></el-icon>
              重置当月
            </el-button>
          </div>
        </div>
      </template>
      
      <div class="filter-section">
        <el-form :inline="true" :model="filterForm" class="filter-form">
          <el-form-item label="年份">
            <el-date-picker
              v-model="filterForm.yearMonth"
              type="month"
              placeholder="选择年月"
              format="YYYY年MM月"
              value-format="YYYY-MM"
              @change="handleMonthChange"
            />
          </el-form-item>
          <el-form-item label="班组">
            <el-select v-model="filterForm.groupId" placeholder="选择班组" clearable @change="handleGroupChange">
              <el-option
                v-for="group in groups"
                :key="group.id"
                :label="group.name"
                :value="group.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="openAddScheduleDialog">
              <el-icon><Plus /></el-icon>
              添加排班
            </el-button>
          </el-form-item>
        </el-form>
      </div>
      
      <div class="calendar-container">
        <div class="calendar-header">
          <div class="weekday" v-for="day in weekdays" :key="day">{{ day }}</div>
        </div>
        <div class="calendar-body">
          <div
            v-for="(day, index) in calendarDays"
            :key="index"
            class="calendar-day"
            :class="{ 'other-month': day.isOtherMonth, 'today': day.isToday }"
            @click="handleDayClick(day)"
          >
            <div class="day-number">{{ day.day }}</div>
            <div class="day-schedules">
              <div
                v-for="schedule in day.schedules"
                :key="schedule.id"
                class="schedule-item"
                :style="{ backgroundColor: getShiftColor(schedule.shift_id) }"
                @click.stop="handleScheduleClick(schedule)"
              >
                <div class="schedule-name">{{ schedule.staff_name }}</div>
                <div class="schedule-shift">{{ schedule.shift_name }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>
    
    <el-dialog
      v-model="addScheduleDialogVisible"
      title="添加排班"
      width="500px"
    >
      <el-form :model="scheduleForm" label-width="80px">
        <el-form-item label="日期">
          <el-date-picker
            v-model="scheduleForm.schedule_date"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="班组">
          <el-select v-model="scheduleForm.group_id" placeholder="选择班组" style="width: 100%">
            <el-option
              v-for="group in groups"
              :key="group.id"
              :label="group.name"
              :value="group.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="人员">
          <el-select v-model="scheduleForm.staff_id" placeholder="选择人员" style="width: 100%" filterable>
            <el-option
              v-for="staff in filteredStaff"
              :key="staff.id"
              :label="staff.name"
              :value="staff.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="班次">
          <el-select v-model="scheduleForm.shift_id" placeholder="选择班次" style="width: 100%">
            <el-option
              v-for="shift in shifts"
              :key="shift.id"
              :label="`${shift.name} (${shift.start_time} - ${shift.end_time})`"
              :value="shift.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="scheduleForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addScheduleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAddSchedule">确定</el-button>
      </template>
    </el-dialog>
    
    <el-dialog
      v-model="editScheduleDialogVisible"
      title="编辑排班"
      width="500px"
    >
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="日期">
          <el-date-picker
            v-model="editForm.schedule_date"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="班组">
          <el-select v-model="editForm.group_id" placeholder="选择班组" style="width: 100%">
            <el-option
              v-for="group in groups"
              :key="group.id"
              :label="group.name"
              :value="group.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="人员">
          <el-select v-model="editForm.staff_id" placeholder="选择人员" style="width: 100%" filterable>
            <el-option
              v-for="staff in filteredStaffForEdit"
              :key="staff.id"
              :label="staff.name"
              :value="staff.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="班次">
          <el-select v-model="editForm.shift_id" placeholder="选择班次" style="width: 100%">
            <el-option
              v-for="shift in shifts"
              :key="shift.id"
              :label="`${shift.name} (${shift.start_time} - ${shift.end_time})`"
              :value="shift.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="editForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editScheduleDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="handleDeleteSchedule">删除</el-button>
        <el-button type="primary" @click="handleUpdateSchedule">保存</el-button>
      </template>
    </el-dialog>
    
    <el-dialog
      v-model="dayScheduleDialogVisible"
      :title="`${selectedDay?.dateStr} 排班详情`"
      width="600px"
    >
      <div class="day-schedule-list" v-if="selectedDay">
        <el-table :data="selectedDay.schedules" border stripe>
          <el-table-column prop="staff_name" label="姓名" width="100" />
          <el-table-column prop="group_name" label="班组" width="80" />
          <el-table-column prop="shift_name" label="班次" width="80" />
          <el-table-column prop="remark" label="备注" />
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button type="primary" link @click="handleEditFromDay(row)">编辑</el-button>
              <el-button type="danger" link @click="handleDeleteFromDay(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="dayScheduleDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleAddFromDay">添加排班</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Upload, Refresh, Plus } from '@element-plus/icons-vue'
import request from '@/axios'

interface Group {
  id: number
  name: string
  description?: string
}

interface Shift {
  id: number
  name: string
  start_time: string
  end_time: string
  description?: string
}

interface Staff {
  id: number
  name: string
  group_id?: number
  phone?: string
}

interface Schedule {
  id: number
  staff_id: number
  staff_name: string
  group_id: number
  group_name: string
  shift_id: number
  shift_name: string
  schedule_date: string
  remark?: string
}

interface CalendarDay {
  date: Date
  dateStr: string
  day: number
  isOtherMonth: boolean
  isToday: boolean
  schedules: Schedule[]
}

const weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

const groups = ref<Group[]>([])
const shifts = ref<Shift[]>([])
const staff = ref<Staff[]>([])
const schedules = ref<Schedule[]>([])

const filterForm = reactive({
  yearMonth: new Date().toISOString().slice(0, 7),
  groupId: null as number | null
})

const scheduleForm = reactive({
  schedule_date: '',
  group_id: null as number | null,
  staff_id: null as number | null,
  shift_id: null as number | null,
  remark: ''
})

const editForm = reactive({
  id: null as number | null,
  schedule_date: '',
  group_id: null as number | null,
  staff_id: null as number | null,
  shift_id: null as number | null,
  remark: ''
})

const addScheduleDialogVisible = ref(false)
const editScheduleDialogVisible = ref(false)
const dayScheduleDialogVisible = ref(false)
const selectedDay = ref<CalendarDay | null>(null)

const filteredStaff = computed(() => {
  if (!scheduleForm.group_id) return staff.value
  return staff.value.filter(s => s.group_id === scheduleForm.group_id)
})

const filteredStaffForEdit = computed(() => {
  if (!editForm.group_id) return staff.value
  return staff.value.filter(s => s.group_id === editForm.group_id)
})

const calendarDays = computed(() => {
  const [year, month] = filterForm.yearMonth.split('-').map(Number)
  const firstDay = new Date(year, month - 1, 1)
  const lastDay = new Date(year, month, 0)
  
  const days: CalendarDay[] = []
  
  const firstDayOfWeek = firstDay.getDay() || 7
  const prevMonthLastDay = new Date(year, month - 1, 0).getDate()
  
  for (let i = firstDayOfWeek - 1; i > 0; i--) {
    const date = new Date(year, month - 2, prevMonthLastDay - i + 1)
    days.push({
      date,
      dateStr: date.toISOString().slice(0, 10),
      day: date.getDate(),
      isOtherMonth: true,
      isToday: false,
      schedules: []
    })
  }
  
  const today = new Date().toISOString().slice(0, 10)
  
  for (let i = 1; i <= lastDay.getDate(); i++) {
    const date = new Date(year, month - 1, i)
    const dateStr = date.toISOString().slice(0, 10)
    const daySchedules = schedules.value.filter(s => s.schedule_date === dateStr)
    
    days.push({
      date,
      dateStr,
      day: i,
      isOtherMonth: false,
      isToday: dateStr === today,
      schedules: daySchedules
    })
  }
  
  const remainingDays = 42 - days.length
  for (let i = 1; i <= remainingDays; i++) {
    const date = new Date(year, month, i)
    days.push({
      date,
      dateStr: date.toISOString().slice(0, 10),
      day: i,
      isOtherMonth: true,
      isToday: false,
      schedules: []
    })
  }
  
  return days
})

const shiftColors = [
  '#e3f2fd', '#f3e5f5', '#e8f5e9', '#fff3e0', '#fce4ec',
  '#e0f7fa', '#f1f8e9', '#fff8e1', '#efebe9', '#eceff1'
]

const getShiftColor = (shiftId: number) => {
  const index = shifts.value.findIndex(s => s.id === shiftId)
  return shiftColors[index % shiftColors.length]
}

const loadGroups = async () => {
  try {
    const res = await request.get({ url: '/api/scheduling/groups/' })
    if (res.code === 200) {
      groups.value = res.data
    }
  } catch (error) {
    console.error('加载班组失败:', error)
  }
}

const loadShifts = async () => {
  try {
    const res = await request.get({ url: '/api/scheduling/shifts/' })
    if (res.code === 200) {
      shifts.value = res.data
    }
  } catch (error) {
    console.error('加载班次失败:', error)
  }
}

const loadStaff = async () => {
  try {
    const res = await request.get({ url: '/api/scheduling/staff/' })
    if (res.code === 200) {
      staff.value = res.data
    }
  } catch (error) {
    console.error('加载人员失败:', error)
  }
}

const loadSchedules = async () => {
  try {
    const [year, month] = filterForm.yearMonth.split('-')
    const params: any = { year: parseInt(year), month: parseInt(month) }
    if (filterForm.groupId) {
      params.group_id = filterForm.groupId
    }
    
    const res = await request.get({ url: '/api/scheduling/records/', params })
    if (res.code === 200) {
      schedules.value = res.data
    }
  } catch (error) {
    console.error('加载排班记录失败:', error)
  }
}

const handleMonthChange = () => {
  loadSchedules()
}

const handleGroupChange = () => {
  loadSchedules()
}

const openAddScheduleDialog = () => {
  scheduleForm.schedule_date = ''
  scheduleForm.group_id = filterForm.groupId
  scheduleForm.staff_id = null
  scheduleForm.shift_id = null
  scheduleForm.remark = ''
  addScheduleDialogVisible.value = true
}

const handleAddSchedule = async () => {
  if (!scheduleForm.schedule_date || !scheduleForm.group_id || !scheduleForm.shift_id) {
    ElMessage.warning('请填写日期、班组和班次')
    return
  }
  
  try {
    const res = await request.post({
      url: '/api/scheduling/records/',
      data: scheduleForm
    })
    
    if (res.code === 200) {
      ElMessage.success(res.message || '添加成功')
      addScheduleDialogVisible.value = false
      loadSchedules()
    } else {
      ElMessage.error(res.message || '添加失败')
    }
  } catch (error) {
    console.error('添加排班失败:', error)
    ElMessage.error('添加失败')
  }
}

const handleScheduleClick = (schedule: Schedule) => {
  editForm.id = schedule.id
  editForm.schedule_date = schedule.schedule_date
  editForm.group_id = schedule.group_id
  editForm.staff_id = schedule.staff_id
  editForm.shift_id = schedule.shift_id
  editForm.remark = schedule.remark || ''
  editScheduleDialogVisible.value = true
}

const handleUpdateSchedule = async () => {
  if (!editForm.id) return
  
  try {
    const res = await request.put({
      url: `/api/scheduling/records/${editForm.id}`,
      data: editForm
    })
    
    if (res.code === 200) {
      ElMessage.success('更新成功')
      editScheduleDialogVisible.value = false
      loadSchedules()
    } else {
      ElMessage.error(res.message || '更新失败')
    }
  } catch (error) {
    console.error('更新排班失败:', error)
    ElMessage.error('更新失败')
  }
}

const handleDeleteSchedule = async () => {
  if (!editForm.id) return
  
  try {
    await ElMessageBox.confirm('确定要删除这条排班记录吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const res = await request.delete({
      url: `/api/scheduling/records/${editForm.id}`
    })
    
    if (res.code === 200) {
      ElMessage.success('删除成功')
      editScheduleDialogVisible.value = false
      loadSchedules()
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除排班失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const handleDayClick = (day: CalendarDay) => {
  if (day.isOtherMonth) return
  selectedDay.value = day
  dayScheduleDialogVisible.value = true
}

const handleEditFromDay = (schedule: Schedule) => {
  dayScheduleDialogVisible.value = false
  handleScheduleClick(schedule)
}

const handleDeleteFromDay = async (schedule: Schedule) => {
  try {
    await ElMessageBox.confirm('确定要删除这条排班记录吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const res = await request.delete({
      url: `/api/scheduling/records/${schedule.id}`
    })
    
    if (res.code === 200) {
      ElMessage.success('删除成功')
      loadSchedules()
      if (selectedDay.value) {
        selectedDay.value.schedules = selectedDay.value.schedules.filter(s => s.id !== schedule.id)
      }
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除排班失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const handleAddFromDay = () => {
  if (selectedDay.value) {
    scheduleForm.schedule_date = selectedDay.value.dateStr
    scheduleForm.group_id = filterForm.groupId
    scheduleForm.staff_id = null
    scheduleForm.shift_id = null
    scheduleForm.remark = ''
    dayScheduleDialogVisible.value = false
    addScheduleDialogVisible.value = true
  }
}

const handleExport = async () => {
  try {
    const [year, month] = filterForm.yearMonth.split('-')
    const params: any = { year: parseInt(year), month: parseInt(month) }
    if (filterForm.groupId) {
      params.group_id = filterForm.groupId
    }
    
    const res = await request.get({
      url: '/api/scheduling/export/',
      params,
      responseType: 'blob'
    })
    
    const blobData = res.data || res
    const blob = new Blob([blobData], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `排班表_${filterForm.yearMonth}_${new Date().toISOString().slice(0, 10)}.xlsx`
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
      url: '/api/scheduling/import/',
      data: formData,
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    if (res.code === 200) {
      ElMessage.success(`导入成功，共导入 ${res.data.count} 条记录`)
      loadSchedules()
    } else {
      ElMessage.error(res.message || '导入失败')
    }
  } catch (error) {
    console.error('导入失败:', error)
    ElMessage.error('导入失败')
  }
  
  return false
}

const handleResetMonth = async () => {
  try {
    await ElMessageBox.confirm('确定要重置当月所有排班记录吗？此操作不可恢复！', '确认重置', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const [year, month] = filterForm.yearMonth.split('-')
    const params: any = { year: parseInt(year), month: parseInt(month) }
    if (filterForm.groupId) {
      params.group_id = filterForm.groupId
    }
    
    const res = await request.delete({
      url: '/api/scheduling/records/',
      params
    })
    
    if (res.code === 200) {
      ElMessage.success(res.message)
      loadSchedules()
    } else {
      ElMessage.error(res.message || '重置失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('重置失败:', error)
      ElMessage.error('重置失败')
    }
  }
}

onMounted(() => {
  loadGroups()
  loadShifts()
  loadStaff()
  loadSchedules()
})
</script>

<style lang="scss" scoped>
.scheduling {
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
  
  .calendar-container {
    border: 1px solid #ebeef5;
    border-radius: 4px;
    overflow: hidden;
    
    .calendar-header {
      display: grid;
      grid-template-columns: repeat(7, 1fr);
      background-color: #f5f7fa;
      border-bottom: 1px solid #ebeef5;
      
      .weekday {
        padding: 12px;
        text-align: center;
        font-weight: bold;
        color: #606266;
        border-right: 1px solid #ebeef5;
        
        &:last-child {
          border-right: none;
        }
      }
    }
    
    .calendar-body {
      display: grid;
      grid-template-columns: repeat(7, 1fr);
      
      .calendar-day {
        min-height: 100px;
        padding: 8px;
        border-right: 1px solid #ebeef5;
        border-bottom: 1px solid #ebeef5;
        cursor: pointer;
        transition: background-color 0.2s;
        
        &:nth-child(7n) {
          border-right: none;
        }
        
        &:hover {
          background-color: #f5f7fa;
        }
        
        &.other-month {
          background-color: #fafafa;
          color: #c0c4cc;
        }
        
        &.today {
          background-color: #ecf5ff;
        }
        
        .day-number {
          font-size: 16px;
          font-weight: bold;
          margin-bottom: 8px;
          color: #303133;
        }
        
        .day-schedules {
          .schedule-item {
            padding: 4px 8px;
            margin-bottom: 4px;
            border-radius: 4px;
            font-size: 12px;
            cursor: pointer;
            transition: transform 0.2s;
            
            &:hover {
              transform: scale(1.02);
            }
            
            .schedule-name {
              font-weight: bold;
              color: #303133;
            }
            
            .schedule-shift {
              color: #606266;
              font-size: 11px;
            }
          }
        }
      }
    }
  }
  
  .day-schedule-list {
    max-height: 400px;
    overflow-y: auto;
  }
}
</style>
