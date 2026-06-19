<template>
  <div>
    <div class="page-bar">
      <h2>展会管理</h2>
      <el-button type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon>新建展会
      </el-button>
    </div>

    <div class="data-card">
      <el-table v-loading="loading" :data="list" stripe>
        <el-table-column prop="name" label="展会名称" min-width="180">
          <template #default="{ row }">
            <router-link :to="`/exhibition/${row.id}`" style="color: #409eff">
              {{ row.name }}
            </router-link>
          </template>
        </el-table-column>
        <el-table-column prop="subtitle" label="副标题" min-width="160" show-overflow-tooltip />
        <el-table-column prop="venue" label="地点" width="180" show-overflow-tooltip />
        <el-table-column label="展期" width="220">
          <template #default="{ row }">{{ row.start_date }} ~ {{ row.end_date }}</template>
        </el-table-column>
        <el-table-column label="开放时间" width="130">
          <template #default="{ row }">{{ row.open_time }} - {{ row.close_time }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ row.status_display }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
            <el-button
              v-if="row.status === 'draft'"
              link type="success"
              @click="handlePublish(row)"
            >发布</el-button>
            <el-button link type="primary" @click="$router.push(`/admin/applications?exhibition=${row.id}`)">
              申请
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="visible" :title="form.id ? '编辑展会' : '新建展会'" width="680px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
        <el-row :gutter="16">
          <el-col :span="24">
            <el-form-item label="展会名称" prop="name">
              <el-input v-model="form.name" maxlength="200" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="副标题" prop="subtitle">
              <el-input v-model="form.subtitle" maxlength="300" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="展会介绍">
              <el-input v-model="form.description" type="textarea" :rows="3" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="举办地点" prop="venue">
              <el-input v-model="form.venue" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="详细地址">
              <el-input v-model="form.address" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="开始日期" prop="start_date">
              <el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束日期" prop="end_date">
              <el-date-picker v-model="form.end_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="开放时间">
              <el-time-picker v-model="form.open_time" value-format="HH:mm" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="闭馆时间">
              <el-time-picker v-model="form.close_time" value-format="HH:mm" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-select v-model="form.status" style="width: 100%">
                <el-option label="草稿" value="draft" />
                <el-option label="已发布" value="published" />
                <el-option label="进行中" value="ongoing" />
                <el-option label="已结束" value="ended" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="预计观众人数">
              <el-input-number v-model="form.max_visitors" :min="1" :max="100000" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="主办方联系方式">
              <el-input v-model="form.organizer_contact" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveForm">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getExhibitionList, createExhibition, updateExhibition, publishExhibition } from '@/api/exhibitions'

const loading = ref(false)
const saving = ref(false)
const list = ref([])
const visible = ref(false)
const formRef = ref(null)
const form = reactive({
  id: null, name: '', subtitle: '', description: '',
  venue: '', address: '',
  start_date: '', end_date: '',
  open_time: '09:00', close_time: '17:00',
  status: 'draft', max_visitors: 5000, organizer_contact: '',
})

const rules = {
  name: [{ required: true, message: '请输入展会名称', trigger: 'blur' }],
  venue: [{ required: true, message: '请输入举办地点', trigger: 'blur' }],
  start_date: [{ required: true, message: '请选择开始日期', trigger: 'change' }],
  end_date: [{ required: true, message: '请选择结束日期', trigger: 'change' }],
}

function statusType(s) {
  return { draft: 'info', published: 'success', ongoing: 'success', ended: 'danger', cancelled: 'danger' }[s] || 'info'
}

async function load() {
  loading.value = true
  try {
    const data = await getExhibitionList({ page_size: 100 })
    list.value = data.results || data || []
  } finally {
    loading.value = false
  }
}

function openDialog(row) {
  if (row) {
    Object.assign(form, row)
  } else {
    Object.assign(form, {
      id: null, name: '', subtitle: '', description: '',
      venue: '', address: '', start_date: '', end_date: '',
      open_time: '09:00', close_time: '17:00', status: 'draft',
      max_visitors: 5000, organizer_contact: '',
    })
  }
  visible.value = true
}

async function saveForm() {
  await formRef.value?.validate()
  saving.value = true
  try {
    if (form.id) {
      await updateExhibition(form.id, { ...form })
      ElMessage.success('更新成功')
    } else {
      await createExhibition({ ...form })
      ElMessage.success('创建成功')
    }
    visible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

async function handlePublish(row) {
  await ElMessageBox.confirm(`确定发布展会《${row.name}》？`, '确认发布', { type: 'warning' })
  try {
    await publishExhibition(row.id)
    ElMessage.success('已发布')
    await load()
  } catch {}
}

onMounted(load)
</script>

<style lang="scss" scoped>
.page-bar {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 16px;
  h2 { margin: 0; font-size: 22px; }
}
.data-card {
  background: #fff; border-radius: 10px; padding: 16px;
}
</style>
