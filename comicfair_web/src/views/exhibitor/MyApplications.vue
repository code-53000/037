<template>
  <div>
    <div class="page-header">
      <div>
        <h2 class="page-title">我的摊位申请</h2>
        <p class="subtitle">查看申请进度、审核状态和核验凭证</p>
      </div>
      <el-button type="primary" @click="$router.push('/apply')">
        <el-icon><Plus /></el-icon>新建申请
      </el-button>
    </div>

    <el-tabs v-model="tab" class="app-tabs">
      <el-tab-pane label="全部" name="all" />
      <el-tab-pane label="草稿" name="draft" />
      <el-tab-pane label="待审核" name="pending" />
      <el-tab-pane label="已通过/已缴费" name="approved" />
      <el-tab-pane label="已驳回/已取消" name="rejected" />
    </el-tabs>

    <div v-loading="loading" class="app-list">
      <el-empty v-if="!filteredList.length" description="暂无申请记录" />
      <div v-for="app in filteredList" :key="app.id" class="app-card card-shadow">
        <div class="app-head">
          <div>
            <h3 class="club-name">{{ app.club_name }}</h3>
            <p class="app-meta">
              <el-tag effect="light" type="primary">{{ app.exhibition_name }}</el-tag>
              <span class="zone">{{ app.preferred_zone_name }}</span>
              <span class="booth-count">{{ app.booth_count }} 个展位</span>
            </p>
          </div>
          <el-tag :type="statusType(app.status)" size="large" effect="dark">
            {{ app.status_display }}
          </el-tag>
        </div>

        <el-row :gutter="20" class="app-body">
          <el-col :span="8">
            <div class="info-block">
              <div class="label">联系人</div>
              <div class="value">{{ app.contact_name }} · {{ app.contact_phone }}</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="info-block">
              <div class="label">作品类型</div>
              <div class="value">{{ app.works_type || '-' }}</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="info-block">
              <div class="label">分配展位</div>
              <div class="value">
                <el-tag v-if="app.booth_code" type="success" effect="plain">
                  {{ app.booth_code }}
                </el-tag>
                <span v-else style="color: #909399">待分配</span>
              </div>
            </div>
          </el-col>
        </el-row>

        <div class="app-footer">
          <div class="fee-info">
            <template v-if="app.fee_amount > 0">
              <span class="fee-label">费用：</span>
              <span class="fee-amount">¥{{ app.paid_amount }}</span>
              <span class="fee-total"> / ¥{{ app.fee_amount }}</span>
              <el-tag v-if="app.paid_amount >= app.fee_amount" size="small" type="success">
                已缴清
              </el-tag>
              <el-tag v-else size="small" type="warning">待缴费</el-tag>
            </template>
            <span v-else style="color: #909399">费用待审核确定</span>
          </div>

          <div class="actions">
            <el-button v-if="app.status === 'draft'" size="small" @click="goEdit(app)">
              <el-icon><Edit /></el-icon>编辑
            </el-button>
            <el-button
              v-if="app.status === 'draft'"
              type="primary" size="small"
              @click="handleSubmit(app)"
            >
              <el-icon><Promotion /></el-icon>提交审核
            </el-button>
            <el-button
              v-if="app.needs_payment"
              type="success" size="small"
              @click="handlePay(app)"
            >
              <el-icon><Money /></el-icon>立即缴费
            </el-button>
            <el-button
              v-if="app.status === 'paid' || app.status === 'approved'"
              size="small"
              @click="showCode(app)"
            >
              <el-icon><Picture /></el-icon>入场核验码
            </el-button>
            <el-button
              v-if="!['checked_in', 'completed', 'cancelled', 'rejected'].includes(app.status)"
              type="danger" plain size="small"
              @click="handleCancel(app)"
            >
              <el-icon><Close /></el-icon>取消申请
            </el-button>
          </div>
        </div>

        <el-timeline v-if="app.review_notes || app.submitted_at || app.reviewed_at || app.paid_at || app.checked_in_at" class="timeline">
          <el-timeline-item v-if="app.created_at" :timestamp="app.created_at" color="#409eff">
            创建申请
          </el-timeline-item>
          <el-timeline-item v-if="app.submitted_at" :timestamp="app.submitted_at" color="#e6a23c">
            提交审核
          </el-timeline-item>
          <el-timeline-item v-if="app.reviewed_at" :timestamp="app.reviewed_at" :type="app.status === 'rejected' ? 'danger' : 'success'">
            {{ app.status === 'rejected' ? '审核驳回' : '审核通过' }}
            <template v-if="app.review_notes">：{{ app.review_notes }}</template>
            <span v-if="app.reviewed_by_name" class="reviewer">（{{ app.reviewed_by_name }}）</span>
          </el-timeline-item>
          <el-timeline-item v-if="app.paid_at" :timestamp="app.paid_at" color="#67c23a">
            已缴费 ¥{{ app.paid_amount }}（{{ app.payment_method_display || '-' }}）
          </el-timeline-item>
          <el-timeline-item v-if="app.checked_in_at" :timestamp="app.checked_in_at" color="#67c23a" type="success">
            已签到入场
          </el-timeline-item>
        </el-timeline>
      </div>
    </div>

    <el-dialog v-model="payVisible" title="缴费确认" width="420px">
      <div v-if="currentApp" style="padding: 8px 0">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="社团名称">{{ currentApp.club_name }}</el-descriptions-item>
          <el-descriptions-item label="展会">{{ currentApp.exhibition_name }}</el-descriptions-item>
          <el-descriptions-item label="展位">{{ currentApp.booth_code || '展位' }} × {{ currentApp.booth_count }}</el-descriptions-item>
          <el-descriptions-item label="应缴金额">
            <span style="color: #f56c6c; font-size: 20px; font-weight: 700">¥{{ (currentApp.fee_amount - currentApp.paid_amount).toFixed(2) }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="支付方式">
            <el-radio-group v-model="payForm.method">
              <el-radio value="alipay">支付宝</el-radio>
              <el-radio value="wechat">微信支付</el-radio>
              <el-radio value="bank">银行转账</el-radio>
            </el-radio-group>
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="payVisible = false">取消</el-button>
        <el-button type="primary" :loading="paying" @click="confirmPay">确认支付</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="codeVisible" title="摊主入场核验码" width="380px">
      <div v-if="currentApp" class="code-box" style="text-align: center; padding: 20px 0">
        <div class="qrcode-wrap">
          <img :src="qrCodeUrl" alt="核验码" class="qrcode-img" />
        </div>
        <div class="code-text">核验码：<strong style="letter-spacing: 2px">{{ currentApp.check_in_code }}</strong></div>
        <p class="code-tip">开场前凭此码到摊主签到台核验入场</p>
        <el-alert
          v-if="currentApp.status === 'approved'"
          type="warning"
          :closable="false"
          style="margin-top: 12px"
          title="提醒：请先完成缴费后再前往签到"
        />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import QRCode from 'qrcode'
import { getMyApplications, submitApplication, payApplication, cancelApplication } from '@/api/applications'

const router = useRouter()
const loading = ref(false)
const tab = ref('all')
const list = ref([])

const payVisible = ref(false)
const codeVisible = ref(false)
const currentApp = ref(null)
const payForm = reactive({ method: 'wechat' })
const paying = ref(false)
const qrCodeUrl = ref('')

const filteredList = computed(() => {
  const map = {
    draft: ['draft'],
    pending: ['pending'],
    approved: ['approved', 'paid', 'checked_in'],
    rejected: ['rejected', 'cancelled'],
    all: [],
  }
  const allowed = map[tab.value]
  if (!allowed.length) return list.value
  return list.value.filter((a) => allowed.includes(a.status))
})

function statusType(s) {
  return {
    draft: 'info', pending: 'warning', approved: 'primary',
    paid: 'success', rejected: 'danger', cancelled: 'info',
    checked_in: 'success', completed: '',
  }[s] || 'info'
}

async function loadList() {
  loading.value = true
  try {
    const data = await getMyApplications()
    list.value = data.results || data || []
  } finally {
    loading.value = false
  }
}

function goEdit(app) {
  router.push({ path: '/apply', query: { id: app.id } })
}

async function handleSubmit(app) {
  await ElMessageBox.confirm('确定提交此申请吗？提交后将进入审核流程，无法再编辑。', '确认提交', {
    type: 'warning',
  })
  try {
    await submitApplication(app.id)
    ElMessage.success('已提交审核')
    await loadList()
  } catch {}
}

async function handlePay(app) {
  currentApp.value = app
  payForm.method = 'wechat'
  payVisible.value = true
}

async function confirmPay() {
  if (!currentApp.value) return
  paying.value = true
  try {
    const remaining = Number(currentApp.value.fee_amount) - Number(currentApp.value.paid_amount)
    await payApplication(currentApp.value.id, {
      payment_method: payForm.method,
      paid_amount: remaining.toFixed(2),
      payment_transaction_id: 'MOCK_' + Date.now(),
    })
    ElMessage.success('缴费成功')
    payVisible.value = false
    await loadList()
  } finally {
    paying.value = false
  }
}

async function handleCancel(app) {
  await ElMessageBox.confirm('确定取消此申请吗？已缴费用将按退款政策处理。', '确认取消', {
    type: 'warning',
  })
  try {
    await cancelApplication(app.id, { reason: '申请人主动取消' })
    ElMessage.success('申请已取消')
    await loadList()
  } catch {}
}

async function showCode(app) {
  if (!app.check_in_code) {
    ElMessage.warning('核验码尚未生成，请等待审核通过')
    return
  }
  currentApp.value = app
  qrCodeUrl.value = await QRCode.toDataURL(app.check_in_code, { width: 220, margin: 1 })
  codeVisible.value = true
}

onMounted(loadList)
</script>

<style lang="scss" scoped>
.subtitle { margin: 6px 0 0; color: #909399; font-size: 14px; }
.app-tabs { margin-bottom: 20px; }

.app-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.app-card {
  border-radius: 12px;
  padding: 20px 24px;

  .app-head {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 16px;

    .club-name { margin: 0 0 6px; font-size: 18px; }
    .app-meta {
      display: flex; gap: 10px; align-items: center;
      font-size: 13px; color: #606266;

      .zone, .booth-count { color: #909399; }
    }
  }

  .app-body {
    padding: 16px 0;
    border-top: 1px dashed #ebeef5;
    border-bottom: 1px dashed #ebeef5;
    margin-bottom: 16px;

    .info-block {
      .label { font-size: 12px; color: #909399; margin-bottom: 4px; }
      .value { font-weight: 500; }
    }
  }

  .app-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;

    .fee-label { color: #909399; }
    .fee-amount { color: #67c23a; font-weight: 700; font-size: 18px; }
    .fee-total { color: #c0c4cc; }

    .actions { display: flex; gap: 8px; flex-wrap: wrap; }
  }

  .timeline {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px dashed #ebeef5;

    :deep(.el-timeline-item__content) { font-size: 13px; }
    .reviewer { color: #909399; font-size: 12px; }
  }
}

.code-box {
  .qrcode-wrap {
    width: 220px; height: 220px;
    margin: 0 auto 16px;
    padding: 10px; background: #fff;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
    border-radius: 8px;
  }
  .qrcode-img { width: 100%; height: 100%; }
  .code-text { font-size: 14px; margin-bottom: 8px; }
  .code-tip { color: #909399; font-size: 12px; margin: 0; }
}
</style>
