<template>
  <div>
    <div class="page-bar">
      <h2>入场核验</h2>
      <el-select
        v-if="gates.length"
        v-model="selectedGate"
        placeholder="选择核验通道"
        style="width: 220px; margin-right: 10px"
      >
        <el-option v-for="g in gates" :key="g.id" :label="`${g.name} (${g.gate_type})`" :value="g.id" />
      </el-select>
      <el-button type="primary" @click="openGateDialog()">
        <el-icon><Plus /></el-icon>新建通道
      </el-button>
    </div>

    <el-row :gutter="16" style="margin-top: 10px">
      <el-col :span="14">
        <div class="verify-card card-shadow">
          <h3 class="panel-title">扫码 / 输入核验码</h3>
          <div class="verify-input-row">
            <el-input
              v-model="verifyCode"
              placeholder="请输入 TC 开头的票码或 BT 开头的摊主核验码，或扫描二维码"
              size="large"
              clearable
              @keyup.enter="handleVerify"
            >
              <template #prefix>
                <el-icon :size="20"><Search /></el-icon>
              </template>
            </el-input>
            <el-button type="primary" size="large" :loading="verifying" @click="handleVerify">
              <el-icon><CircleCheckFilled /></el-icon>核验
            </el-button>
          </div>

          <div class="verify-result" :class="resultType">
            <template v-if="verifyResult">
              <div class="result-icon">
                <el-icon v-if="verifyResult.status === 'success'" :size="56" color="#67c23a">
                  <CircleCheckFilled />
                </el-icon>
                <el-icon v-else :size="56" color="#f56c6c"><CircleCloseFilled /></el-icon>
              </div>
              <div class="result-main">
                <div class="result-status" :class="verifyResult.status">
                  {{ verifyResult.message }}
                </div>
                <div class="result-type">
                  <el-tag>{{ verifyResult.type_display }}</el-tag>
                </div>
                <div class="result-person" v-if="verifyResult.person_name">
                  {{ verifyResult.person_name }}
                </div>
                <div class="result-info" v-if="verifyResult.person_info">
                  <div v-for="(v, k) in verifyResult.person_info" :key="k" class="info-item">
                    <span class="k">{{ k }}：</span>
                    <span class="v">{{ v }}</span>
                  </div>
                </div>
                <div class="result-time">{{ formatTime() }}</div>
              </div>
            </template>
            <template v-else>
              <div class="placeholder">
                <el-icon :size="48" color="#c0c4cc"><Connection /></el-icon>
                <p>等待核验...</p>
                <p class="hint">观众票码以 TC 开头，摊主核验码以 BT 开头</p>
              </div>
            </template>
          </div>
        </div>

        <div class="gates-card card-shadow" style="margin-top: 16px">
          <h3 class="panel-title">核验通道列表</h3>
          <el-table :data="gates" stripe size="small">
            <el-table-column prop="name" label="通道名称" min-width="160" />
            <el-table-column label="类型" width="100">
              <template #default="{ row }">
                <el-tag size="small">{{ { ticket: '观众', exhibitor: '摊主', vip: 'VIP', staff: '工作人员', media: '媒体' }[row.gate_type] }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="location" label="位置" min-width="140" show-overflow-tooltip />
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
                  {{ row.is_active ? '启用' : '停用' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>

      <el-col :span="10">
        <div class="stats-card card-shadow">
          <h3 class="panel-title">今日核验概览</h3>
          <el-row :gutter="10">
            <el-col :span="12">
              <div class="mini-stat success">
                <div class="num">{{ stats.today || 0 }}</div>
                <div class="lbl">今日核验</div>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="mini-stat primary">
                <div class="num">{{ stats.total || 0 }}</div>
                <div class="lbl">累计核验</div>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="mini-stat warning">
                <div class="num">{{ stats.ticket_count || 0 }}</div>
                <div class="lbl">观众入场</div>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="mini-stat danger">
                <div class="num">{{ stats.exhibitor_count || 0 }}</div>
                <div class="lbl">摊主签到</div>
              </div>
            </el-col>
          </el-row>
        </div>

        <div class="history-card card-shadow" style="margin-top: 16px">
          <h3 class="panel-title">最近核验</h3>
          <el-table v-loading="loading" :data="recentRecords" stripe size="small" max-height="480">
            <el-table-column label="类型" width="70">
              <template #default="{ row }">
                <el-tag size="small">
                  {{ { ticket: '观众', exhibitor: '摊主', vip: 'VIP' }[row.checkin_type] || row.checkin_type }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="人员" min-width="110" show-overflow-tooltip>
              <template #default="{ row }">
                <div>{{ row.person_name || '匿名' }}</div>
                <div style="color: #909399; font-size: 11px" v-if="row.code_used">{{ row.code_used }}</div>
              </template>
            </el-table-column>
            <el-table-column label="结果" width="70">
              <template #default="{ row }">
                <el-tag size="small" :type="row.status === 'success' ? 'success' : 'danger'" effect="plain">
                  {{ row.status === 'success' ? '通过' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="时间" width="130" prop="checkin_time" />
          </el-table>
        </div>
      </el-col>
    </el-row>

    <el-dialog v-model="gateVisible" title="新建核验通道" width="440px">
      <el-form ref="gateFormRef" :model="gateForm" :rules="gateRules" label-width="100px">
        <el-form-item label="通道名称" prop="name">
          <el-input v-model="gateForm.name" />
        </el-form-item>
        <el-form-item label="通道类型">
          <el-select v-model="gateForm.gate_type" style="width: 100%">
            <el-option label="观众入口" value="ticket" />
            <el-option label="摊主签到" value="exhibitor" />
            <el-option label="VIP通道" value="vip" />
            <el-option label="工作人员" value="staff" />
            <el-option label="媒体通道" value="media" />
          </el-select>
        </el-form-item>
        <el-form-item label="位置">
          <el-input v-model="gateForm.location" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="gateForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="gateVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveGate">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useExhibitionStore } from '@/stores/exhibition'
import { getActiveExhibitions } from '@/api/exhibitions'
import { getGateList, createGate, verifyCheckin, getCheckinRecords, getCheckinStats } from '@/api/checkins'

const exhibitionStore = useExhibitionStore()
const loading = ref(false)
const verifying = ref(false)
const saving = ref(false)
const exhibitions = ref([])
const currentExhibitionId = ref(exhibitionStore.currentId || null)
const gates = ref([])
const selectedGate = ref(null)

const verifyCode = ref('')
const verifyResult = ref(null)
const resultTime = ref('')

const stats = ref({})
const recentRecords = ref([])

const gateVisible = ref(false)
const gateFormRef = ref(null)
const gateForm = reactive({
  exhibition: null, name: '', gate_type: 'ticket',
  location: '', is_active: true,
})
const gateRules = {
  name: [{ required: true, message: '请输入通道名称', trigger: 'blur' }],
}

const resultType = computed(() => verifyResult.value?.status || '')

function formatTime() { return resultTime.value }

async function loadAll() {
  if (!currentExhibitionId.value) return
  exhibitionStore.currentId = currentExhibitionId.value
  gateForm.exhibition = currentExhibitionId.value
  await Promise.all([loadGates(), loadStats(), loadRecent()])
}

async function loadGates() {
  gates.value = await getGateList({ exhibition_id: currentExhibitionId.value })
  if (gates.value.length && !selectedGate.value) selectedGate.value = gates.value[0].id
}

async function loadStats() {
  try { stats.value = await getCheckinStats(currentExhibitionId.value) } catch {}
}

async function loadRecent() {
  loading.value = true
  try {
    const data = await getCheckinRecords({
      exhibition_id: currentExhibitionId.value, page_size: 20, ordering: '-checkin_time',
    })
    recentRecords.value = data.results || data || []
  } finally {
    loading.value = false
  }
}

async function handleVerify() {
  const code = verifyCode.value.trim()
  if (!code) {
    ElMessage.warning('请输入核验码')
    return
  }
  verifying.value = true
  try {
    const res = await verifyCheckin({ code, gate_id: selectedGate.value || null })
    verifyResult.value = res.result
    resultTime.value = new Date().toLocaleString()
    if (res.result.status === 'success') {
      ElMessage.success(res.result.message)
    } else {
      ElMessage.warning(res.result.message)
    }
    verifyCode.value = ''
    await Promise.all([loadStats(), loadRecent()])
  } finally {
    verifying.value = false
  }
}

function openGateDialog() {
  Object.assign(gateForm, {
    exhibition: currentExhibitionId.value, name: '', gate_type: 'ticket',
    location: '', is_active: true,
  })
  gateVisible.value = true
}

async function saveGate() {
  await gateFormRef.value?.validate()
  saving.value = true
  try {
    await createGate({ ...gateForm, exhibition: currentExhibitionId.value })
    ElMessage.success('通道创建成功')
    gateVisible.value = false
    await loadGates()
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  exhibitions.value = await getActiveExhibitions()
  if (!currentExhibitionId.value && exhibitions.value.length) currentExhibitionId.value = exhibitions.value[0].id
  watch(currentExhibitionId, loadAll)
  await loadAll()
})
</script>

<style lang="scss" scoped>
.page-bar {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 10px;
  h2 { margin: 0; font-size: 22px; }
}
.panel-title {
  margin: 0 0 16px;
  font-size: 16px;
  border-left: 3px solid #409eff;
  padding-left: 10px;
}

.verify-card {
  padding: 24px; border-radius: 10px;

  .verify-input-row {
    display: flex; gap: 10px; margin-bottom: 24px;
    :deep(.el-input) { flex: 1; }
  }

  .verify-result {
    min-height: 240px;
    padding: 24px;
    border-radius: 12px;
    background: #fafafa;
    border: 2px dashed #dcdfe6;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 24px;

    &.success { border-color: #67c23a; background: #f0f9eb; }
    &.invalid_code, &.already_checked, &.expired, &.not_paid {
      border-color: #f56c6c; background: #fef0f0;
    }

    .placeholder { text-align: center; color: #909399; p { margin: 8px 0; } .hint { font-size: 12px; } }

    .result-icon { flex-shrink: 0; }
    .result-main {
      .result-status { font-size: 22px; font-weight: 700; margin-bottom: 8px;
        &.success { color: #67c23a; }
        &:not(.success) { color: #f56c6c; }
      }
      .result-type { margin-bottom: 10px; }
      .result-person { font-size: 16px; margin-bottom: 10px; font-weight: 600; }
      .result-info { background: rgba(255,255,255,0.6); padding: 10px 14px; border-radius: 8px; margin-bottom: 10px;
        .info-item { font-size: 13px; margin: 4px 0;
          .k { color: #909399; }
        }
      }
      .result-time { color: #909399; font-size: 12px; }
    }
  }
}
.gates-card { padding: 20px; border-radius: 10px; }

.stats-card {
  padding: 20px; border-radius: 10px;

  .mini-stat {
    padding: 16px;
    border-radius: 10px;
    text-align: center;
    margin-bottom: 12px;

    &.success { background: linear-gradient(135deg, #d4edda, #c3e6cb); }
    &.primary { background: linear-gradient(135deg, #cce5ff, #b8daff); }
    &.warning { background: linear-gradient(135deg, #fff3cd, #ffeeba); }
    &.danger { background: linear-gradient(135deg, #f8d7da, #f5c6cb); }

    .num { font-size: 28px; font-weight: 800; color: #303133; }
    .lbl { font-size: 12px; color: #606266; margin-top: 4px; }
  }
}

.history-card { padding: 20px; border-radius: 10px; }
</style>
