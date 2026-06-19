<template>
  <div>
    <div class="page-bar">
      <h2>签到记录</h2>
      <div class="filter-bar">
        <el-select
          v-if="exhibitions.length"
          v-model="filters.exhibition"
          placeholder="选择展会"
          style="width: 200px; margin-right: 8px"
          @change="loadList"
        >
          <el-option v-for="e in exhibitions" :key="e.id" :label="e.name" :value="e.id" />
        </el-select>
        <el-select
          v-model="filters.checkin_type"
          placeholder="类型"
          clearable
          style="width: 130px; margin-right: 8px"
          @change="loadList"
        >
          <el-option label="观众" value="ticket" />
          <el-option label="摊主" value="exhibitor" />
          <el-option label="VIP" value="vip" />
          <el-option label="工作人员" value="staff" />
          <el-option label="媒体" value="media" />
        </el-select>
        <el-select
          v-model="filters.status"
          placeholder="结果"
          clearable
          style="width: 130px; margin-right: 8px"
          @change="loadList"
        >
          <el-option label="通过" value="success" />
          <el-option label="重复" value="already_checked" />
          <el-option label="无效" value="invalid_code" />
          <el-option label="过期" value="expired" />
          <el-option label="未支付" value="not_paid" />
        </el-select>
        <el-switch
          v-model="filters.today"
          active-text="仅今天"
          style="margin-right: 8px"
          @change="loadList"
        />
        <el-button type="primary" @click="loadList">查询</el-button>
        <el-button @click="exportCsv" style="margin-left: 8px">
          <el-icon><Download /></el-icon>导出
        </el-button>
      </div>
    </div>

    <el-row :gutter="16" style="margin: 12px 0">
      <el-col :span="4">
        <div class="stat-box">
          <div class="label">核验总数</div>
          <div class="value primary">{{ summary.total }}</div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="stat-box">
          <div class="label">通过</div>
          <div class="value success">{{ summary.success }}</div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="stat-box">
          <div class="label">今日</div>
          <div class="value warning">{{ summary.today }}</div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="stat-box">
          <div class="label">观众</div>
          <div class="value info">{{ summary.ticket }}</div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="stat-box">
          <div class="label">摊主</div>
          <div class="value danger">{{ summary.exhibitor }}</div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="stat-box">
          <div class="label">失败</div>
          <div class="value muted">{{ summary.total - summary.success }}</div>
        </div>
      </el-col>
    </el-row>

    <div class="data-card">
      <el-table v-loading="loading" :data="list" stripe>
        <el-table-column label="时间" width="170" prop="checkin_time" sortable fixed />
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">
              {{ { ticket: '观众', exhibitor: '摊主', vip: 'VIP', staff: '工作人员', media: '媒体' }[row.checkin_type] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="核验结果" width="100">
          <template #default="{ row }">
            <el-tag
              size="small"
              :type="row.status === 'success' ? 'success' : 'danger'"
              effect="plain"
            >
              {{ row.status_display }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="人员姓名" width="140" prop="person_name" show-overflow-tooltip />
        <el-table-column label="核验码" width="170" prop="code_used" show-overflow-tooltip />
        <el-table-column label="通道" width="160" prop="gate_name" show-overflow-tooltip />
        <el-table-column label="操作人" width="120" prop="operator_name" />
        <el-table-column label="附加信息" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <template v-if="row.person_info && Object.keys(row.person_info).length">
              <div v-for="(v, k) in row.person_info" :key="k" class="info-line">
                <span style="color: #909399">{{ k }}：</span>{{ v }}
              </div>
            </template>
            <span v-else style="color: #c0c4cc">-</span>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top: 16px; text-align: right">
        <el-pagination
          v-model:current-page="page.page"
          v-model:page-size="page.pageSize"
          :page-sizes="[20, 50, 100, 200]"
          :total="page.total"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="loadList"
          @size-change="loadList"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useExhibitionStore } from '@/stores/exhibition'
import { getActiveExhibitions } from '@/api/exhibitions'
import { getCheckinRecords, getCheckinStats } from '@/api/checkins'

const exhibitionStore = useExhibitionStore()
const loading = ref(false)
const exhibitions = ref([])
const list = ref([])
const page = reactive({ page: 1, pageSize: 50, total: 0 })
const filters = reactive({
  exhibition: exhibitionStore.currentId || null,
  checkin_type: '', status: '', today: true,
})

const allRecords = ref([])

const summary = computed(() => {
  const base = { total: 0, success: 0, today: 0, ticket: 0, exhibitor: 0 }
  allRecords.value.forEach((r) => {
    base.total++
    if (r.status === 'success') base.success++
    if (r.checkin_type === 'ticket') base.ticket++
    if (r.checkin_type === 'exhibitor') base.exhibitor++
  })
  if (checkinStats.value) {
    base.total = checkinStats.value.total || base.total
    base.success = checkinStats.value.success || base.success
    base.today = checkinStats.value.today || 0
    base.ticket = checkinStats.value.ticket_count || base.ticket
    base.exhibitor = checkinStats.value.exhibitor_count || base.exhibitor
  }
  return base
})

const checkinStats = ref({})

async function loadList() {
  loading.value = true
  try {
    const params = {
      page: page.page, page_size: page.pageSize,
      exhibition_id: filters.exhibition,
      ...(filters.checkin_type ? { checkin_type: filters.checkin_type } : {}),
      ...(filters.status ? { status: filters.status } : {}),
      ...(filters.today ? { today: 'true' } : {}),
      ordering: '-checkin_time',
    }
    const data = await getCheckinRecords(params)
    list.value = data.results || data || []
    page.total = data.count || list.value.length
    if (filters.exhibition) {
      try { checkinStats.value = await getCheckinStats(filters.exhibition) } catch {}
    }
  } finally {
    loading.value = false
  }
}

function exportCsv() {
  const rows = [['时间', '类型', '结果', '姓名', '核验码', '通道', '操作人', '附加信息']]
  list.value.forEach((r) => {
    rows.push([
      r.checkin_time, r.checkin_type_display, r.status_display,
      r.person_name || '', r.code_used || '', r.gate_name || '',
      r.operator_name || '',
      JSON.stringify(r.person_info || {}),
    ])
  })
  const csv = rows.map((row) => row.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n')
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `checkin_records_${Date.now()}.csv`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}

onMounted(async () => {
  exhibitions.value = await getActiveExhibitions()
  if (!filters.exhibition && exhibitions.value.length) filters.exhibition = exhibitions.value[0].id
  if (filters.exhibition) await loadList()
})
</script>

<style lang="scss" scoped>
.page-bar {
  display: flex; justify-content: space-between; align-items: flex-end;
  margin-bottom: 10px; flex-wrap: wrap; gap: 10px;
  h2 { margin: 0; font-size: 22px; }
  .filter-bar { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
}
.stat-box {
  background: #fff; border-radius: 10px; padding: 16px; text-align: center;
  .label { font-size: 12px; color: #909399; margin-bottom: 6px; }
  .value { font-size: 24px; font-weight: 700;
    &.primary { color: #409eff; }
    &.success { color: #67c23a; }
    &.warning { color: #e6a23c; }
    &.info { color: #909399; }
    &.danger { color: #f56c6c; }
    &.muted { color: #c0c4cc; }
  }
}
.data-card {
  background: #fff; border-radius: 10px; padding: 16px;
  .info-line { font-size: 12px; margin: 2px 0; }
}
</style>
