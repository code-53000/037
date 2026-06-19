<template>
  <div>
    <div class="page-header">
      <div>
        <h2 class="page-title">我的门票</h2>
        <p class="subtitle">查看已购门票和入场凭证</p>
      </div>
      <el-button type="primary" @click="$router.push('/tickets')">
        <el-icon><Plus /></el-icon>去购票
      </el-button>
    </div>

    <el-tabs v-model="tab" class="app-tabs">
      <el-tab-pane label="全部" name="all" />
      <el-tab-pane label="待使用" name="paid" />
      <el-tab-pane label="已使用" name="used" />
      <el-tab-pane label="已退票" name="refunded" />
    </el-tabs>

    <div v-loading="loading" class="ticket-list">
      <el-empty v-if="!filteredList.length" description="暂无门票" />
      <div
        v-for="ticket in filteredList"
        :key="ticket.id"
        class="ticket-card"
        :class="ticket.status"
      >
        <div class="ticket-left">
          <div class="ticket-type">{{ ticket.tier_name }}</div>
          <div class="ticket-name">{{ ticket.ticket_type_display }}</div>
          <div class="ticket-valid">
            <template v-if="ticket.valid_from === ticket.valid_to">{{ ticket.valid_from }}</template>
            <template v-else>{{ ticket.valid_from }} ~ {{ ticket.valid_to }}</template>
          </div>
          <div class="ticket-price-row">
            <span class="price">¥{{ ticket.price }}</span>
            <el-tag size="small" :type="tagType(ticket.status)" effect="dark">
              {{ ticket.status_display }}
            </el-tag>
          </div>
        </div>
        <div class="ticket-divider">
          <div class="circle top"></div>
          <div class="line"></div>
          <div class="circle bottom"></div>
        </div>
        <div class="ticket-right">
          <div class="ticket-no">票号：{{ ticket.ticket_no }}</div>
          <div class="qr-wrap" @click="showTicket(ticket)">
            <template v-if="ticket.status === 'paid'">
              <img :src="getQr(ticket)" alt="入场码" class="qr-img" />
              <div class="qr-tip">点击查看详情</div>
            </template>
            <template v-else-if="ticket.status === 'used'">
              <el-icon :size="48" color="#909399"><CircleCheckFilled /></el-icon>
              <div class="used-time">{{ ticket.used_at?.slice(0, 16) }}</div>
            </template>
            <template v-else-if="ticket.status === 'refunded'">
              <el-icon :size="48" color="#f56c6c"><RefreshLeft /></el-icon>
              <div class="used-time">已退款 ¥{{ ticket.refund_amount }}</div>
            </template>
            <template v-else>
              <el-icon :size="48" color="#e6a23c"><WarningFilled /></el-icon>
              <div class="used-time">{{ ticket.status_display }}</div>
            </template>
          </div>
          <div class="ticket-actions">
            <el-button
              v-if="ticket.status === 'paid'"
              size="small" type="primary"
              @click="showTicket(ticket)"
            >出示入场码</el-button>
            <el-button
              v-if="ticket.status === 'paid' && ticket.tier?.refund_policy !== 'no_refund'"
              size="small" type="danger" plain
              @click="handleRefund(ticket)"
            >申请退票</el-button>
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="detailVisible" title="门票详情" width="380px">
      <div v-if="currentTicket" class="ticket-detail">
        <div class="qr-center">
          <img :src="qrCodeUrl" alt="入场码" class="big-qr" />
        </div>
        <div class="code-text">
          入场码：<strong style="letter-spacing: 2px">{{ currentTicket.ticket_code }}</strong>
        </div>
        <p class="tip">开场前凭此码在闸机或入口处扫码入场</p>
        <el-descriptions :column="1" border size="small" style="margin-top: 12px">
          <el-descriptions-item label="展会">{{ currentTicket.exhibition_name }}</el-descriptions-item>
          <el-descriptions-item label="票种">{{ currentTicket.tier_name }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ currentTicket.ticket_type_display }}</el-descriptions-item>
          <el-descriptions-item label="有效期">
            <template v-if="currentTicket.valid_from === currentTicket.valid_to">{{ currentTicket.valid_from }}</template>
            <template v-else>{{ currentTicket.valid_from }} 至 {{ currentTicket.valid_to }}</template>
          </el-descriptions-item>
          <el-descriptions-item label="持票人">{{ currentTicket.holder_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="购票时间">{{ currentTicket.created_at?.slice(0, 16) }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import QRCode from 'qrcode'
import { getMyTickets, refundTicket } from '@/api/tickets'

const loading = ref(false)
const tab = ref('all')
const list = ref([])
const qrCache = reactive({})

const detailVisible = ref(false)
const currentTicket = ref(null)
const qrCodeUrl = ref('')

const filteredList = computed(() => {
  if (tab.value === 'all') return list.value
  return list.value.filter((t) => t.status === tab.value)
})

function tagType(s) {
  return { paid: 'success', used: 'info', refunded: 'danger', unpaid: 'warning', expired: 'info' }[s] || 'info'
}

async function loadList() {
  loading.value = true
  try {
    const data = await getMyTickets()
    list.value = data.results || data || []
    for (const t of list.value) {
      if (t.status === 'paid' && !qrCache[t.ticket_code]) {
        qrCache[t.ticket_code] = await QRCode.toDataURL(t.ticket_code, { width: 140, margin: 1 })
      }
    }
  } finally {
    loading.value = false
  }
}

function getQr(ticket) {
  return qrCache[ticket.ticket_code] || ''
}

async function showTicket(ticket) {
  currentTicket.value = ticket
  qrCodeUrl.value = await QRCode.toDataURL(ticket.ticket_code, { width: 240, margin: 1 })
  detailVisible.value = true
}

async function handleRefund(ticket) {
  await ElMessageBox.confirm(
    `确定退票吗？将按政策退还部分或全部票款（¥${ticket.price}）。`,
    '退票确认',
    { type: 'warning' },
  )
  try {
    await refundTicket(ticket.id, { reason: '用户主动申请退票' })
    ElMessage.success('退票成功')
    await loadList()
  } catch {}
}

onMounted(loadList)
</script>

<style lang="scss" scoped>
.subtitle { margin: 6px 0 0; color: #909399; font-size: 14px; }
.app-tabs { margin-bottom: 20px; }

.ticket-list {
  display: flex; flex-direction: column; gap: 16px;
}

.ticket-card {
  display: flex;
  min-height: 180px;
  border-radius: 14px;
  overflow: hidden;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);

  &.used { background: linear-gradient(135deg, #64748b 0%, #475569 100%); box-shadow: 0 4px 20px rgba(100, 116, 139, 0.3); }
  &.refunded { background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%); opacity: 0.85; }
  &.vip { background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%); }

  .ticket-left {
    padding: 24px;
    flex: 1.2;
    background: rgba(255, 255, 255, 0.08);

    .ticket-type { font-size: 20px; font-weight: 700; margin-bottom: 4px; }
    .ticket-name { font-size: 13px; opacity: 0.8; margin-bottom: 16px; }
    .ticket-valid { font-size: 13px; margin-bottom: 20px; opacity: 0.9; }

    .ticket-price-row {
      display: flex; align-items: center; gap: 10px;
      .price { font-size: 24px; font-weight: 800; }
    }
  }

  .ticket-divider {
    position: relative;
    width: 30px;
    background: transparent;
    display: flex;
    flex-direction: column;
    align-items: center;

    .circle {
      width: 20px; height: 20px;
      background: #f5f7fa;
      border-radius: 50%;
      &.top { margin-top: -10px; }
      &.bottom { margin-bottom: -10px; }
    }
    .line {
      flex: 1;
      width: 0;
      border-left: 2px dashed rgba(255, 255, 255, 0.4);
      margin: 6px 0;
    }
  }

  .ticket-right {
    padding: 18px;
    flex: 1;
    display: flex;
    flex-direction: column;
    background: rgba(255, 255, 255, 0.04);

    .ticket-no { font-size: 11px; opacity: 0.75; margin-bottom: 8px; }

    .qr-wrap {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      padding: 8px;
      border-radius: 8px;
      transition: background 0.2s;

      &:hover { background: rgba(255, 255, 255, 0.08); }

      .qr-img { width: 108px; height: 108px; border-radius: 6px; padding: 4px; background: white; }
      .qr-tip { font-size: 11px; margin-top: 6px; opacity: 0.85; }
      .used-time { font-size: 12px; opacity: 0.85; margin-top: 8px; text-align: center; }
    }

    .ticket-actions {
      display: flex;
      gap: 6px;
      justify-content: center;
      margin-top: 8px;
    }
  }
}

.ticket-detail {
  .qr-center {
    width: 260px;
    height: 260px;
    margin: 0 auto 12px;
    padding: 10px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  }
  .big-qr { width: 100%; height: 100%; }
  .code-text { text-align: center; margin-bottom: 4px; font-size: 14px; }
  .tip { text-align: center; color: #909399; font-size: 12px; margin: 0; }
}
</style>
