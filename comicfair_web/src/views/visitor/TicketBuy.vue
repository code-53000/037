<template>
  <div>
    <div class="page-header">
      <div>
        <h2 class="page-title">漫展购票</h2>
        <p class="subtitle">在线购买漫展门票，获取电子入场凭证</p>
      </div>
      <el-select
        v-if="exhibitions.length"
        v-model="currentExhibitionId"
        style="width: 280px"
        placeholder="选择展会"
        @change="loadTiers"
      >
        <el-option v-for="e in exhibitions" :key="e.id" :label="e.name" :value="e.id" />
      </el-select>
    </div>

    <div v-if="currentExhibition" class="exhibition-info card-shadow">
      <div class="exhi-emoji">🎪</div>
      <div class="exhi-detail">
        <h2>{{ currentExhibition.name }}</h2>
        <p>{{ currentExhibition.venue }} · {{ currentExhibition.start_date }} 至 {{ currentExhibition.end_date }}</p>
      </div>
    </div>

    <h3 class="section-title">选择票种</h3>

    <div v-loading="loading" class="tier-grid">
      <div v-for="tier in tiers" :key="tier.id" class="tier-card card-shadow" :class="{ vip: tier.ticket_type === 'vip' }">
        <div class="tier-badge" v-if="tier.ticket_type === 'vip'">VIP</div>
        <div class="tier-head">
          <h4 class="tier-name">{{ tier.name }}</h4>
          <el-tag size="small" effect="light">{{ tier.ticket_type_display }}</el-tag>
        </div>
        <p class="tier-desc">{{ tier.description || '标准入场门票' }}</p>
        <div class="tier-meta">
          <span v-if="tier.valid_date">有效期：{{ tier.valid_date }}</span>
          <span v-else>{{ currentExhibition?.start_date }} ~ {{ currentExhibition?.end_date }}</span>
        </div>
        <div class="tier-price-row">
          <div class="price-wrap">
            <span class="currency">¥</span>
            <span class="price">{{ tier.price }}</span>
          </div>
          <div class="stock">
            <template v-if="tier.quantity === 0">不限量</template>
            <template v-else>
              <span v-if="tier.remaining > 0">剩余 {{ tier.remaining }} 张</span>
              <el-tag v-else type="danger" size="small">已售罄</el-tag>
            </template>
          </div>
        </div>
        <el-progress
          v-if="tier.quantity > 0"
          :percentage="Math.round(tier.sold_count / tier.quantity * 100)"
          :stroke-width="4"
          style="margin-bottom: 16px"
        />
        <div class="purchase-row">
          <span class="refund-policy">{{ {
            no_refund: '不退不换', full_refund: '可全额退款', partial_refund: '部分退款'
          }[tier.refund_policy] }}</span>
          <div class="buy-wrap">
            <el-input-number
              v-model="buyMap[tier.id]"
              :min="1"
              :max="tier.max_per_order"
              :disabled="!tier.is_available || !tier.remaining"
              size="small"
              controls-position="right"
            />
            <el-button
              type="primary"
              size="small"
              :disabled="!tier.is_available || !tier.remaining"
              @click="handleBuy(tier)"
            >
              立即购买
            </el-button>
          </div>
        </div>
      </div>

      <el-empty v-if="!tiers.length" description="当前展会暂无可售票种" />
    </div>

    <el-dialog v-model="checkoutVisible" title="确认订单" width="460px">
      <div v-if="checkoutTier" style="padding: 8px 0">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="展会">{{ currentExhibition?.name }}</el-descriptions-item>
          <el-descriptions-item label="票种">{{ checkoutTier.name }}</el-descriptions-item>
          <el-descriptions-item label="张数">{{ checkoutQty }} 张</el-descriptions-item>
          <el-descriptions-item label="单张票价">¥{{ checkoutTier.price }}</el-descriptions-item>
          <el-descriptions-item label="应付金额">
            <span style="color: #f56c6c; font-size: 22px; font-weight: 700">¥{{ checkoutTotal }}</span>
          </el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">持票人信息（可选）</el-divider>
        <el-form label-width="80px">
          <el-form-item label="姓名">
            <el-input v-model="checkoutForm.holder_name" placeholder="持票人姓名，可不填" />
          </el-form-item>
          <el-form-item label="手机号">
            <el-input v-model="checkoutForm.holder_phone" placeholder="接收入场短信，可不填" />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="checkoutVisible = false">取消</el-button>
        <el-button type="primary" :loading="buying" @click="confirmBuy">确认支付</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useExhibitionStore } from '@/stores/exhibition'
import { getActiveExhibitions } from '@/api/exhibitions'
import { getAvailableTiers, purchaseTickets } from '@/api/tickets'

const router = useRouter()
const exhibitionStore = useExhibitionStore()
const loading = ref(false)
const buying = ref(false)

const exhibitions = ref([])
const tiers = ref([])
const currentExhibitionId = ref(exhibitionStore.currentId || null)
const currentExhibition = computed(() =>
  exhibitions.value.find((e) => e.id === currentExhibitionId.value)
)

const buyMap = reactive({})
tiers.value.forEach((t) => { buyMap[t.id] = 1 })

watch(tiers, (newTiers) => {
  newTiers.forEach((t) => { if (!buyMap[t.id]) buyMap[t.id] = 1 })
}, { immediate: true })

const checkoutVisible = ref(false)
const checkoutTier = ref(null)
const checkoutQty = ref(1)
const checkoutForm = reactive({ holder_name: '', holder_phone: '' })

const checkoutTotal = computed(() =>
  checkoutTier.value ? (Number(checkoutTier.value.price) * checkoutQty.value).toFixed(2) : 0
)

async function loadTiers() {
  if (!currentExhibitionId.value) return
  loading.value = true
  try {
    tiers.value = await getAvailableTiers(currentExhibitionId.value)
  } finally {
    loading.value = false
  }
}

function handleBuy(tier) {
  checkoutTier.value = tier
  checkoutQty.value = buyMap[tier.id] || 1
  checkoutForm.holder_name = ''
  checkoutForm.holder_phone = ''
  checkoutVisible.value = true
}

async function confirmBuy() {
  buying.value = true
  try {
    const res = await purchaseTickets({
      tier_id: checkoutTier.value.id,
      quantity: checkoutQty.value,
      holder_name: checkoutForm.holder_name || undefined,
      holder_phone: checkoutForm.holder_phone || undefined,
      payment_method: 'wechat',
    })
    ElMessage.success(`购买成功！共 ${res.tickets.length} 张门票`)
    checkoutVisible.value = false
    await loadTiers()
    router.push('/my-tickets')
  } finally {
    buying.value = false
  }
}

onMounted(async () => {
  loading.value = true
  try {
    exhibitions.value = await getActiveExhibitions()
    if (!currentExhibitionId.value && exhibitions.value.length) {
      currentExhibitionId.value = exhibitions.value[0].id
      exhibitionStore.setCurrent(exhibitions.value[0])
    }
    await loadTiers()
  } finally {
    loading.value = false
  }
})
</script>

<style lang="scss" scoped>
.subtitle { margin: 6px 0 0; color: #909399; font-size: 14px; }

.section-title {
  font-size: 18px;
  margin: 24px 0 16px;
  padding-left: 10px;
  border-left: 4px solid #409eff;
}

.exhibition-info {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  border-radius: 12px;
  background: linear-gradient(135deg, #e0f2fe, #ecfdf5);

  .exhi-emoji { font-size: 48px; }
  h2 { margin: 0 0 6px; font-size: 20px; }
  p { margin: 0; color: #606266; }
}

.tier-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.tier-card {
  position: relative;
  border-radius: 12px;
  padding: 20px;
  border: 2px solid transparent;
  transition: all 0.2s;

  &:hover { border-color: #b3d8ff; transform: translateY(-2px); }
  &.vip {
    background: linear-gradient(135deg, #fef3c7 0%, #fce7f3 100%);
    border-color: #fbbf24;
  }

  .tier-badge {
    position: absolute; top: -10px; right: 16px;
    background: linear-gradient(135deg, #f59e0b, #ef4444);
    color: white; padding: 2px 10px;
    border-radius: 10px; font-size: 12px; font-weight: 700;
  }

  .tier-head {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 6px;

    .tier-name { margin: 0; font-size: 17px; }
  }
  .tier-desc { color: #606266; font-size: 13px; margin: 0 0 8px; min-height: 20px; }
  .tier-meta { color: #909399; font-size: 12px; margin-bottom: 12px; }

  .tier-price-row {
    display: flex; justify-content: space-between; align-items: flex-end;
    margin-bottom: 8px;

    .currency { font-size: 14px; color: #f56c6c; font-weight: 600; }
    .price { font-size: 32px; font-weight: 800; color: #f56c6c; line-height: 1; }
    .stock { font-size: 13px; color: #606266; }
  }

  .purchase-row {
    display: flex; justify-content: space-between; align-items: center;

    .refund-policy { font-size: 12px; color: #909399; }
    .buy-wrap { display: flex; gap: 8px; align-items: center; }
  }
}
</style>
