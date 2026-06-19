<template>
  <div v-loading="loading" class="exhibition-detail">
    <el-button link @click="$router.back()">
      <el-icon><ArrowLeft /></el-icon>返回
    </el-button>

    <div v-if="exhibition" class="detail-hero card-shadow">
      <div class="hero-emoji">🎪</div>
      <h1 class="exhibition-title">{{ exhibition.name }}</h1>
      <p class="exhibition-subtitle">{{ exhibition.subtitle }}</p>
      <el-tag size="large" :type="statusType">{{ exhibition.status_display }}</el-tag>

      <div class="hero-info-grid">
        <div class="info-block">
          <el-icon :size="24" color="#409eff"><Calendar /></el-icon>
          <div>
            <div class="label">举办时间</div>
            <div class="value">{{ exhibition.start_date }} 至 {{ exhibition.end_date }}</div>
          </div>
        </div>
        <div class="info-block">
          <el-icon :size="24" color="#e6a23c"><Location /></el-icon>
          <div>
            <div class="label">举办地点</div>
            <div class="value">{{ exhibition.venue }}</div>
          </div>
        </div>
        <div class="info-block">
          <el-icon :size="24" color="#67c23a"><Clock /></el-icon>
          <div>
            <div class="label">开放时间</div>
            <div class="value">{{ exhibition.open_time }} - {{ exhibition.close_time }}</div>
          </div>
        </div>
        <div class="info-block">
          <el-icon :size="24" color="#f56c6c"><User /></el-icon>
          <div>
            <div class="label">预计观众</div>
            <div class="value">{{ exhibition.max_visitors }} 人</div>
          </div>
        </div>
      </div>

      <div class="hero-actions">
        <el-button type="primary" size="large" @click="$router.push('/tickets')">
          <el-icon><Ticket /></el-icon>购买门票
        </el-button>
        <el-button size="large" @click="$router.push('/apply')">
          <el-icon><Shop /></el-icon>申请摊位
        </el-button>
        <el-button size="large" @click="$router.push('/booth-map')">
          <el-icon><Grid /></el-icon>查看展位图
        </el-button>
      </div>
    </div>

    <el-row :gutter="20" class="detail-content">
      <el-col :span="16">
        <div class="card-shadow content-card">
          <h3 class="card-title">展会介绍</h3>
          <p class="description">{{ exhibition?.description || '暂无介绍' }}</p>

          <h3 class="card-title">展区导览</h3>
          <div v-for="z in zones" :key="z.id" class="zone-item">
            <span class="zone-color" :style="{ background: z.color }"></span>
            <div class="zone-info">
              <div class="zone-name">
                {{ z.name }}
                <el-tag size="small" effect="light" type="info">{{ z.zone_type_display }}</el-tag>
              </div>
              <div class="zone-desc">{{ z.description }}</div>
            </div>
            <div class="zone-price">
              <div class="amount">¥{{ z.booth_price }}</div>
              <div class="per">/ 展位</div>
            </div>
          </div>
        </div>
      </el-col>

      <el-col :span="8">
        <div class="card-shadow content-card">
          <h3 class="card-title">联系方式</h3>
          <p style="white-space: pre-line">{{ exhibition?.organizer_contact || '暂无' }}</p>
        </div>

        <div v-if="userStore.isOrganizer && exhibition" class="card-shadow content-card" style="margin-top: 20px">
          <h3 class="card-title">数据统计</h3>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="展位总数">{{ stats.total_booths || '-' }}</el-descriptions-item>
            <el-descriptions-item label="申请总数">{{ stats.total_applications || '-' }}</el-descriptions-item>
            <el-descriptions-item label="通过审核">{{ stats.approved_applications || '-' }}</el-descriptions-item>
            <el-descriptions-item label="已缴费">{{ stats.paid_applications || '-' }}</el-descriptions-item>
            <el-descriptions-item label="售票总数">{{ stats.total_tickets || '-' }}</el-descriptions-item>
            <el-descriptions-item label="签到总数">{{ stats.total_checkins || '-' }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { getExhibitionDetail, getExhibitionStats } from '@/api/exhibitions'
import { getZoneList } from '@/api/booths'

const route = useRoute()
const userStore = useUserStore()

const loading = ref(false)
const exhibition = ref(null)
const zones = ref([])
const stats = ref({})

const statusType = computed(() => {
  const map = { published: 'success', ongoing: 'success', draft: 'info', ended: 'danger', cancelled: 'danger' }
  return map[exhibition.value?.status] || 'info'
})

onMounted(async () => {
  loading.value = true
  try {
    const id = route.params.id
    exhibition.value = await getExhibitionDetail(id)
    zones.value = await getZoneList({ exhibition_id: id })

    if (userStore.isOrganizer) {
      stats.value = await getExhibitionStats(id)
    }
  } finally {
    loading.value = false
  }
})
</script>

<style lang="scss" scoped>
.detail-hero {
  padding: 40px;
  border-radius: 16px;
  margin: 16px 0 24px;
  text-align: center;
  background: linear-gradient(135deg, #fef3c7 0%, #fce7f3 100%);

  .hero-emoji {
    font-size: 64px;
  }
  .exhibition-title {
    font-size: 32px;
    margin: 12px 0 8px;
  }
  .exhibition-subtitle {
    color: #78716c;
    margin: 0 0 16px;
  }

  .hero-info-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin: 32px auto;
    max-width: 900px;
    text-align: left;

    .info-block {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      background: rgba(255, 255, 255, 0.6);
      padding: 16px;
      border-radius: 10px;

      .label {
        font-size: 12px;
        color: #909399;
        margin-bottom: 4px;
      }
      .value {
        font-weight: 600;
        color: #303133;
      }
    }
  }

  .hero-actions {
    display: flex;
    gap: 12px;
    justify-content: center;
  }
}

.detail-content {
  margin-top: 24px;
}

.content-card {
  padding: 24px;
  border-radius: 12px;

  .card-title {
    font-size: 18px;
    margin: 0 0 16px;
    padding-bottom: 12px;
    border-bottom: 2px solid #f0f0f0;
  }

  .description {
    line-height: 1.8;
    color: #606266;
  }
}

.zone-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  margin-bottom: 12px;
  border-radius: 8px;
  background: #fafafa;

  .zone-color {
    width: 32px;
    height: 32px;
    border-radius: 6px;
    flex-shrink: 0;
  }
  .zone-info {
    flex: 1;
    .zone-name {
      font-weight: 600;
      margin-bottom: 4px;
    }
    .zone-desc {
      font-size: 13px;
      color: #909399;
    }
  }
  .zone-price {
    text-align: right;
    .amount {
      font-size: 20px;
      font-weight: 700;
      color: #f56c6c;
    }
    .per {
      font-size: 12px;
      color: #909399;
    }
  }
}
</style>
