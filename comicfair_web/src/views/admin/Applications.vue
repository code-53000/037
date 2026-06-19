<template>
  <div>
    <div class="page-bar">
      <h2>摊位申请审核</h2>
      <div class="filter-bar">
        <el-select
          v-if="exhibitions.length"
          v-model="filters.exhibition"
          placeholder="选择展会"
          clearable
          style="width: 200px; margin-right: 8px"
          @change="loadList"
        >
          <el-option v-for="e in exhibitions" :key="e.id" :label="e.name" :value="e.id" />
        </el-select>
        <el-select
          v-model="filters.status"
          placeholder="状态"
          clearable
          style="width: 140px; margin-right: 8px"
          @change="loadList"
        >
          <el-option label="草稿" value="draft" />
          <el-option label="待审核" value="pending" />
          <el-option label="已通过" value="approved" />
          <el-option label="已驳回" value="rejected" />
          <el-option label="已缴费" value="paid" />
          <el-option label="已取消" value="cancelled" />
          <el-option label="已签到" value="checked_in" />
        </el-select>
        <el-input
          v-model="filters.club_name"
          placeholder="搜索社团名称"
          clearable
          style="width: 200px; margin-right: 8px"
          @keyup.enter="loadList"
        />
        <el-button type="primary" @click="loadList">
          <el-icon><Search /></el-icon>查询
        </el-button>
      </div>
    </div>

    <div class="data-card">
      <el-table v-loading="loading" :data="list" stripe>
        <el-table-column label="社团信息" min-width="220">
          <template #default="{ row }">
            <div class="club-info">
              <strong>{{ row.club_name }}</strong>
              <div class="meta">
                <el-tag size="small" effect="light" type="primary">{{ row.exhibition_name }}</el-tag>
                <span>{{ row.preferred_zone_name }}</span>
              </div>
              <div class="works" v-if="row.works_type">{{ row.works_type }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="联系方式" width="180">
          <template #default="{ row }">
            <div>{{ row.contact_name }}</div>
            <div style="color: #909399; font-size: 12px">{{ row.contact_phone }}</div>
            <div v-if="row.contact_email" style="color: #909399; font-size: 12px">{{ row.contact_email }}</div>
          </template>
        </el-table-column>
        <el-table-column label="分配展位" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.booth_code" type="success" size="small">{{ row.booth_code }}</el-tag>
            <span v-else style="color: #c0c4cc">未分配</span>
          </template>
        </el-table-column>
        <el-table-column label="费用" width="120">
          <template #default="{ row }">
            <template v-if="row.fee_amount > 0">
              <div style="color: #f56c6c; font-weight: 600">¥{{ row.paid_amount }}</div>
              <div style="color: #909399; font-size: 12px">/ ¥{{ row.fee_amount }}</div>
            </template>
            <span v-else style="color: #c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ row.status_display }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="申请时间" width="160" prop="created_at" />
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">详情</el-button>
            <el-button
              v-if="row.status === 'pending'"
              link type="success"
              @click="openReview(row, true)"
            >通过</el-button>
            <el-button
              v-if="row.status === 'pending'"
              link type="danger"
              @click="openReview(row, false)"
            >驳回</el-button>
            <el-button
              v-if="row.needs_payment"
              link type="warning"
              @click="markPaid(row)"
            >标记缴费</el-button>
            <el-button
              v-if="row.check_in_code && ['approved', 'paid'].includes(row.status)"
              link
              @click="showCheckinCode(row)"
            >核验码</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top: 16px; text-align: right">
        <el-pagination
          v-model:current-page="page.page"
          v-model:page-size="page.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="page.total"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="loadList"
          @size-change="loadList"
        />
      </div>
    </div>

    <el-dialog v-model="detailVisible" title="摊位申请详情" width="640px">
      <div v-if="detail">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="社团名称" :span="2">{{ detail.club_name }}</el-descriptions-item>
          <el-descriptions-item label="所属展会">{{ detail.exhibition_name }}</el-descriptions-item>
          <el-descriptions-item label="意向展区">{{ detail.preferred_zone_name }}</el-descriptions-item>
          <el-descriptions-item label="分配展位">
            <el-tag v-if="detail.booth_code" type="success">{{ detail.booth_code }}</el-tag>
            <span v-else>未分配</span>
          </el-descriptions-item>
          <el-descriptions-item label="申请状态">
            <el-tag :type="statusType(detail.status)">{{ detail.status_display }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="联系人">{{ detail.contact_name }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ detail.contact_phone }}</el-descriptions-item>
          <el-descriptions-item label="联系邮箱">{{ detail.contact_email || '-' }}</el-descriptions-item>
          <el-descriptions-item label="社团简介" :span="2">{{ detail.club_introduction || '-' }}</el-descriptions-item>
          <el-descriptions-item label="作品类型">{{ detail.works_type || '-' }}</el-descriptions-item>
          <el-descriptions-item label="展位数量">{{ detail.booth_count }} 个</el-descriptions-item>
          <el-descriptions-item label="主要作品" :span="2">{{ detail.main_works || '-' }}</el-descriptions-item>
          <el-descriptions-item label="用电需求">
            {{ detail.has_power ? (detail.power_description || '需要供电') : '无' }}
          </el-descriptions-item>
          <el-descriptions-item label="应缴费用">
            <span v-if="detail.fee_amount > 0" style="color: #f56c6c; font-weight: 600">
              ¥{{ detail.fee_amount }}（已缴 ¥{{ detail.paid_amount }}）
            </span>
            <span v-else>待审核确定</span>
          </el-descriptions-item>
          <el-descriptions-item label="特殊需求" :span="2">{{ detail.special_requirements || '-' }}</el-descriptions-item>
          <el-descriptions-item label="审核备注" :span="2">{{ detail.review_notes || '-' }}</el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <template v-if="detail?.status === 'pending'">
          <el-button type="success" @click="openReview(detail, true)">审核通过</el-button>
          <el-button type="danger" @click="openReview(detail, false)">审核驳回</el-button>
        </template>
      </template>
    </el-dialog>

    <el-dialog v-model="reviewVisible" :title="isApprove ? '审核通过 - 分配展位' : '审核驳回'" width="520px">
      <div v-if="reviewApp">
        <template v-if="isApprove">
          <el-alert
            type="info"
            :closable="false"
            :title="`社团：${reviewApp.club_name} | 意向展区：${reviewApp.preferred_zone_name}`"
            style="margin-bottom: 16px"
          />
          <el-form label-width="100px">
            <el-form-item label="分配展区">
              <el-select
                v-model="reviewForm.zone_id"
                placeholder="选择展区"
                filterable
                style="width: 100%"
                @change="loadBooths"
              >
                <el-option
                  v-for="z in zones"
                  :key="z.id"
                  :label="`${z.name} (¥${z.booth_price})`"
                  :value="z.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="分配展位" required>
              <el-select
                v-model="reviewForm.booth_id"
                placeholder="选择具体展位"
                filterable
                style="width: 100%"
              >
                <el-option
                  v-for="b in availableBooths"
                  :key="b.id"
                  :label="`${b.booth_code} (${b.status_display})`"
                  :value="b.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="费用">
              <el-input-number
                v-model="reviewForm.fee_amount"
                :min="0"
                :precision="2"
                :step="100"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="审核备注">
              <el-input v-model="reviewForm.review_notes" type="textarea" :rows="2" />
            </el-form-item>
          </el-form>
        </template>
        <template v-else>
          <el-form label-width="100px">
            <el-form-item label="驳回原因">
              <el-input v-model="reviewForm.review_notes" type="textarea" :rows="4" placeholder="请填写驳回原因" />
            </el-form-item>
          </el-form>
        </template>
      </div>
      <template #footer>
        <el-button @click="reviewVisible = false">取消</el-button>
        <el-button
          :type="isApprove ? 'success' : 'danger'"
          :loading="reviewing"
          @click="confirmReview"
        >确认</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="codeVisible" title="摊主核验码" width="360px">
      <div v-if="codeApp" style="text-align: center; padding: 16px 0">
        <div style="width: 220px; height: 220px; margin: 0 auto 12px; padding: 8px; background: white; border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,0.08)">
          <img :src="codeQr" alt="核验码" style="width: 100%; height: 100%" />
        </div>
        <div>核验码：<strong style="letter-spacing: 2px">{{ codeApp.check_in_code }}</strong></div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import QRCode from 'qrcode'
import { getActiveExhibitions } from '@/api/exhibitions'
import { getZoneList, getAvailableBooths } from '@/api/booths'
import {
  getApplicationList, getApplicationDetail,
  reviewApplication, payApplication,
} from '@/api/applications'

const route = useRoute()
const loading = ref(false)
const reviewing = ref(false)
const exhibitions = ref([])
const zones = ref([])
const availableBooths = ref([])
const list = ref([])
const page = reactive({ page: 1, pageSize: 20, total: 0 })
const filters = reactive({
  exhibition: route.query.exhibition ? parseInt(route.query.exhibition) : null,
  status: route.query.status || null,
  club_name: route.query.club_name || '',
})

const detailVisible = ref(false)
const detail = ref(null)

const reviewVisible = ref(false)
const reviewApp = ref(null)
const isApprove = ref(true)
const reviewForm = reactive({
  zone_id: null, booth_id: null, fee_amount: 0, review_notes: '',
})

const codeVisible = ref(false)
const codeApp = ref(null)
const codeQr = ref('')

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
    const params = {
      page: page.page, page_size: page.pageSize,
      ...(filters.exhibition ? { exhibition: filters.exhibition } : {}),
      ...(filters.status ? { status: filters.status } : {}),
      ...(filters.club_name ? { club_name: filters.club_name } : {}),
      ordering: '-created_at',
    }
    const data = await getApplicationList(params)
    list.value = data.results || []
    page.total = data.count || 0
  } finally {
    loading.value = false
  }
}

async function loadZones() {
  if (!filters.exhibition) return
  zones.value = await getZoneList({ exhibition_id: filters.exhibition })
}

async function loadBooths(zoneId) {
  reviewForm.booth_id = null
  if (!zoneId) {
    availableBooths.value = []
    return
  }
  availableBooths.value = await getAvailableBooths(zoneId)
}

async function openDetail(row) {
  detail.value = await getApplicationDetail(row.id)
  detailVisible.value = true
}

function openReview(row, approve) {
  reviewApp.value = row
  isApprove.value = approve
  reviewForm.zone_id = row.preferred_zone
  reviewForm.booth_id = null
  reviewForm.fee_amount = row.preferred_zone ? (zones.value.find((z) => z.id === row.preferred_zone)?.booth_price || 0) : 0
  reviewForm.review_notes = ''
  if (approve && row.preferred_zone) {
    loadBooths(row.preferred_zone)
  }
  reviewVisible.value = true
}

async function confirmReview() {
  if (isApprove.value && !reviewForm.booth_id) {
    ElMessage.warning('请选择分配的展位')
    return
  }
  if (!isApprove.value && !reviewForm.review_notes) {
    ElMessage.warning('请填写驳回原因')
    return
  }
  reviewing.value = true
  try {
    await reviewApplication(reviewApp.value.id, {
      action: isApprove.value ? 'approve' : 'reject',
      booth_id: isApprove.value ? reviewForm.booth_id : null,
      review_notes: reviewForm.review_notes,
      fee_amount: reviewForm.fee_amount,
    })
    ElMessage.success(isApprove.value ? '审核通过，已分配展位' : '已驳回')
    reviewVisible.value = false
    if (detailVisible.value) detail.value = await getApplicationDetail(reviewApp.value.id)
    await loadList()
  } finally {
    reviewing.value = false
  }
}

async function markPaid(row) {
  const remaining = Number(row.fee_amount) - Number(row.paid_amount)
  try {
    const { value } = await ElMessageBox.prompt(
      `输入缴费金额（应缴：¥${remaining.toFixed(2)}）`,
      '标记缴费',
      {
        inputPattern: /^\d+(\.\d{1,2})?$/,
        inputValue: remaining.toFixed(2),
      },
    )
    await payApplication(row.id, {
      payment_method: 'cash',
      paid_amount: value,
      payment_transaction_id: 'MANUAL_' + Date.now(),
    })
    ElMessage.success('已标记缴费')
    await loadList()
  } catch {}
}

async function showCheckinCode(row) {
  codeApp.value = row
  codeQr.value = await QRCode.toDataURL(row.check_in_code, { width: 220, margin: 1 })
  codeVisible.value = true
}

onMounted(async () => {
  exhibitions.value = await getActiveExhibitions()
  if (filters.exhibition) await loadZones()
  await loadList()
  const origLoad = loadZones
  loadZones = async () => {
    if (filters.exhibition) zones.value = await getZoneList({ exhibition_id: filters.exhibition })
  }
})
</script>

<style lang="scss" scoped>
.page-bar {
  display: flex; justify-content: space-between; align-items: flex-end;
  margin-bottom: 12px; flex-wrap: wrap; gap: 10px;
  h2 { margin: 0; font-size: 22px; }
  .filter-bar { display: flex; align-items: center; flex-wrap: wrap; }
}
.data-card {
  background: #fff; border-radius: 10px; padding: 16px;
}
.club-info {
  .meta { font-size: 12px; color: #909399; margin: 4px 0; display: flex; gap: 8px; }
  .works { font-size: 12px; color: #606266; }
}
</style>
