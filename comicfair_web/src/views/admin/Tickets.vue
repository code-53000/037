<template>
  <div>
    <div class="page-bar">
      <h2>票务管理</h2>
      <div class="filter-bar">
        <el-select
          v-if="exhibitions.length"
          v-model="filters.exhibition"
          placeholder="选择展会"
          style="width: 200px; margin-right: 8px"
          @change="loadAll"
        >
          <el-option v-for="e in exhibitions" :key="e.id" :label="e.name" :value="e.id" />
        </el-select>
        <el-button type="primary" @click="openTierDialog()">
          <el-icon><Plus /></el-icon>新建票种
        </el-button>
      </div>
    </div>

    <el-tabs v-model="tab" class="tabs">
      <el-tab-pane label="票种配置" name="tiers">
        <div class="data-card">
          <el-table v-loading="loading" :data="tiers" stripe>
            <el-table-column prop="name" label="票种名称" min-width="140" />
            <el-table-column label="类型" width="100">
              <template #default="{ row }">
                <el-tag size="small">{{ row.ticket_type_display }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="价格" width="100">
              <template #default="{ row }">
                <span style="color: #f56c6c; font-weight: 600">¥{{ row.price }}</span>
              </template>
            </el-table-column>
            <el-table-column label="总票量" width="100">
              <template #default="{ row }">
                {{ row.quantity === 0 ? '不限' : row.quantity }}
              </template>
            </el-table-column>
            <el-table-column label="已售" width="90" prop="sold_count" />
            <el-table-column label="剩余" width="90">
              <template #default="{ row }">
                <el-tag size="small" :type="(row.quantity > 0 && row.remaining <= 0) ? 'danger' : 'success'">
                  {{ row.quantity === 0 ? '∞' : row.remaining }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="row.on_sale && row.is_available ? 'success' : 'info'" size="small">
                  {{ row.on_sale && row.is_available ? '在售' : '停售' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="退票政策" width="110">
              <template #default="{ row }">
                {{ { no_refund: '不退不换', full_refund: '全额退款', partial_refund: '部分退款' }[row.refund_policy] }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="140" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openTierDialog(row)">编辑</el-button>
                <el-button link type="primary" @click="toggleSale(row)">
                  {{ row.on_sale ? '停售' : '开售' }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <el-tab-pane label="售票记录" name="tickets">
        <div class="data-card">
          <div class="sub-filter">
            <el-select v-model="ticketFilters.status" placeholder="状态" clearable style="width: 120px; margin-right: 8px">
              <el-option label="待支付" value="unpaid" />
              <el-option label="已支付" value="paid" />
              <el-option label="已使用" value="used" />
              <el-option label="已退票" value="refunded" />
            </el-select>
            <el-input v-model="ticketFilters.keyword" placeholder="搜索票号/持票人" clearable style="width: 220px" @keyup.enter="loadTickets" />
            <el-button type="primary" size="small" @click="loadTickets">查询</el-button>
          </div>
          <el-table v-loading="ticketsLoading" :data="tickets" stripe style="margin-top: 12px">
            <el-table-column prop="ticket_no" label="票号" width="180" />
            <el-table-column label="持票人" min-width="130">
              <template #default="{ row }">
                <div>{{ row.holder_name || row.user_name }}</div>
                <div v-if="row.holder_phone" style="color: #909399; font-size: 12px">{{ row.holder_phone }}</div>
              </template>
            </el-table-column>
            <el-table-column prop="tier_name" label="票种" width="140" />
            <el-table-column label="类型" width="90">
              <template #default="{ row }">
                <el-tag size="small">{{ row.ticket_type_display }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="金额" width="100">
              <template #default="{ row }">¥{{ row.price }}</template>
            </el-table-column>
            <el-table-column label="有效期" width="160">
              <template #default="{ row }">
                <template v-if="row.valid_from === row.valid_to">{{ row.valid_from }}</template>
                <template v-else>{{ row.valid_from }} ~ {{ row.valid_to }}</template>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="ticketStatusType(row.status)" size="small">{{ row.status_display }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="支付时间" width="160" prop="paid_at" />
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button
                  v-if="row.status === 'paid'"
                  link type="danger"
                  @click="handleRefund(row)"
                >退票</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div style="margin-top: 16px; text-align: right">
            <el-pagination
              v-model:current-page="ticketPage.page"
              v-model:page-size="ticketPage.pageSize"
              :page-sizes="[20, 50, 100]"
              :total="ticketPage.total"
              layout="total, sizes, prev, pager, next, jumper"
              @current-change="loadTickets"
              @size-change="loadTickets"
            />
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="tierVisible" :title="tierForm.id ? '编辑票种' : '新建票种'" width="520px">
      <el-form ref="tierFormRef" :model="tierForm" :rules="tierRules" label-width="100px">
        <el-form-item label="票种名称" prop="name">
          <el-input v-model="tierForm.name" />
        </el-form-item>
        <el-form-item label="票类型">
          <el-select v-model="tierForm.ticket_type" style="width: 100%">
            <el-option label="单日票" value="single_day" />
            <el-option label="通票" value="multi_day" />
            <el-option label="VIP票" value="vip" />
            <el-option label="参展商证" value="exhibitor" />
            <el-option label="媒体证" value="media" />
          </el-select>
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="tierForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-row :gutter="10">
          <el-col :span="12">
            <el-form-item label="价格" prop="price">
              <el-input-number v-model="tierForm.price" :min="0" :precision="2" :step="10" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="总票量">
              <el-input-number v-model="tierForm.quantity" :min="0" style="width: 100%" />
              <span style="color: #909399; font-size: 12px">0 表示不限量</span>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="限购数">
              <el-input-number v-model="tierForm.max_per_order" :min="1" :max="50" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="有效日期">
              <el-date-picker
                v-if="tierForm.ticket_type === 'single_day'"
                v-model="tierForm.valid_date"
                type="date"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
              <span v-else style="color: #909399">按展会展期</span>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="是否在售">
          <el-switch v-model="tierForm.on_sale" />
        </el-form-item>
        <el-form-item label="退票政策">
          <el-select v-model="tierForm.refund_policy" style="width: 100%">
            <el-option label="不退不换" value="no_refund" />
            <el-option label="全额退款" value="full_refund" />
            <el-option label="部分退款（80%）" value="partial_refund" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="tierVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveTier">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useExhibitionStore } from '@/stores/exhibition'
import { getActiveExhibitions } from '@/api/exhibitions'
import {
  getTicketTierList, createTicketTier, updateTicketTier,
  getTicketList, refundTicket,
} from '@/api/tickets'

const exhibitionStore = useExhibitionStore()
const loading = ref(false)
const ticketsLoading = ref(false)
const saving = ref(false)
const exhibitions = ref([])
const filters = reactive({ exhibition: exhibitionStore.currentId || null })
const ticketFilters = reactive({ status: '', keyword: '' })

const tab = ref('tiers')
const tiers = ref([])
const tickets = ref([])
const ticketPage = reactive({ page: 1, pageSize: 20, total: 0 })

const tierVisible = ref(false)
const tierFormRef = ref(null)
const tierForm = reactive({
  id: null, exhibition: null, name: '', ticket_type: 'single_day',
  description: '', price: 0, quantity: 0, max_per_order: 5,
  on_sale: true, valid_date: null, refund_policy: 'no_refund',
})
const tierRules = {
  name: [{ required: true, message: '请输入票种名称', trigger: 'blur' }],
  price: [{ required: true, message: '请输入价格', trigger: 'blur' }],
}

function ticketStatusType(s) {
  return { paid: 'success', used: 'info', refunded: 'danger', unpaid: 'warning', expired: 'info' }[s] || 'info'
}

async function loadAll() {
  if (!filters.exhibition) return
  exhibitionStore.currentId = filters.exhibition
  ticketPage.page = 1
  await Promise.all([loadTiers(), loadTickets()])
}

async function loadTiers() {
  loading.value = true
  try {
    tiers.value = await getTicketTierList({ exhibition_id: filters.exhibition, page_size: 100 })
  } finally {
    loading.value = false
  }
}

async function loadTickets() {
  ticketsLoading.value = true
  try {
    const params = {
      exhibition: filters.exhibition,
      page: ticketPage.page, page_size: ticketPage.pageSize,
    }
    if (ticketFilters.status) params.status = ticketFilters.status
    const data = await getTicketList(params)
    let list = data.results || data || []
    if (ticketFilters.keyword) {
      const kw = ticketFilters.keyword.toLowerCase()
      list = list.filter((t) =>
        (t.ticket_no || '').toLowerCase().includes(kw) ||
        (t.holder_name || '').toLowerCase().includes(kw) ||
        (t.user_name || '').toLowerCase().includes(kw)
      )
    }
    tickets.value = list
    ticketPage.total = data.count || list.length
  } finally {
    ticketsLoading.value = false
  }
}

function openTierDialog(row) {
  if (row) {
    Object.assign(tierForm, row)
  } else {
    Object.assign(tierForm, {
      id: null, exhibition: filters.exhibition, name: '', ticket_type: 'single_day',
      description: '', price: 0, quantity: 0, max_per_order: 5,
      on_sale: true, valid_date: null, refund_policy: 'no_refund',
    })
  }
  tierVisible.value = true
}

async function saveTier() {
  await tierFormRef.value?.validate()
  saving.value = true
  try {
    const payload = { ...tierForm, exhibition: filters.exhibition }
    if (tierForm.id) {
      await updateTicketTier(tierForm.id, payload)
    } else {
      await createTicketTier(payload)
    }
    ElMessage.success('保存成功')
    tierVisible.value = false
    await loadTiers()
  } finally {
    saving.value = false
  }
}

async function toggleSale(row) {
  try {
    await updateTicketTier(row.id, { ...row, on_sale: !row.on_sale })
    ElMessage.success(row.on_sale ? '已停售' : '已开售')
    await loadTiers()
  } catch {}
}

async function handleRefund(row) {
  try {
    const { value } = await ElMessageBox.prompt(
      `输入退款金额（票价 ¥${row.price}）`,
      '退票确认',
      { inputPattern: /^\d+(\.\d{1,2})?$/, inputValue: String(row.price) },
    )
    await refundTicket(row.id, { refund_amount: value, reason: '主办方操作退票' })
    ElMessage.success('退票成功')
    await Promise.all([loadTiers(), loadTickets()])
  } catch {}
}

onMounted(async () => {
  exhibitions.value = await getActiveExhibitions()
  if (!filters.exhibition && exhibitions.value.length) filters.exhibition = exhibitions.value[0].id
  if (filters.exhibition) await loadAll()
})
</script>

<style lang="scss" scoped>
.page-bar {
  display: flex; justify-content: space-between; align-items: flex-end;
  margin-bottom: 12px; flex-wrap: wrap; gap: 10px;
  h2 { margin: 0; font-size: 22px; }
  .filter-bar { display: flex; align-items: center; gap: 8px; }
}
.tabs { margin-top: 10px; }
.data-card {
  background: #fff; border-radius: 10px; padding: 16px;
}
.sub-filter {
  display: flex; align-items: center; flex-wrap: wrap;
}
</style>
