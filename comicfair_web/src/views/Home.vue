<template>
  <div>
    <section class="hero-section card-shadow">
      <div class="hero-inner">
        <div class="hero-text">
          <h1>同人漫展管理平台</h1>
          <p class="hero-desc">
            一站式解决同人漫展摊位招商、票务销售、入场核验问题
            <br />让漫展运营更高效、更有秩序
          </p>
          <div class="hero-actions">
            <el-button type="primary" size="large" @click="$router.push('/tickets')">
              <el-icon><Ticket /></el-icon>立即购票
            </el-button>
            <el-button size="large" @click="$router.push('/apply')">
              <el-icon><Shop /></el-icon>申请摊位
            </el-button>
          </div>
        </div>
        <div class="hero-stats">
          <div class="stat-item">
            <div class="stat-num">{{ exhibitionCount }}</div>
            <div class="stat-label">展会数</div>
          </div>
          <div class="stat-item">
            <div class="stat-num">{{ boothCount }}</div>
            <div class="stat-label">展位总数</div>
          </div>
          <div class="stat-item">
            <div class="stat-num">{{ ticketCount }}</div>
            <div class="stat-label">已售门票</div>
          </div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="section-header">
        <h2 class="section-title">当前展会</h2>
        <el-button link type="primary" @click="$router.push('/booth-map')">查看展位图 →</el-button>
      </div>
      <div v-loading="loading" class="exhibition-grid">
        <div
          v-for="e in exhibitions"
          :key="e.id"
          class="exhibition-card card-shadow"
          @click="$router.push(`/exhibition/${e.id}`)"
        >
          <div class="exhibition-tag" :class="e.status">{{ e.status_display }}</div>
          <div class="exhibition-emoji">🎨</div>
          <h3 class="exhibition-name">{{ e.name }}</h3>
          <p class="exhibition-subtitle">{{ e.subtitle }}</p>
          <div class="exhibition-info">
            <div class="info-row">
              <el-icon><Calendar /></el-icon>
              <span>{{ e.start_date }} ~ {{ e.end_date }}</span>
            </div>
            <div class="info-row">
              <el-icon><Location /></el-icon>
              <span>{{ e.venue }}</span>
            </div>
            <div class="info-row">
              <el-icon><Clock /></el-icon>
              <span>{{ e.open_time }} - {{ e.close_time }}</span>
            </div>
          </div>
          <div class="exhibition-footer">
            <el-tag type="success">共 {{ e.duration_days }} 天</el-tag>
            <el-button type="primary" size="small" link>查看详情 →</el-button>
          </div>
        </div>
      </div>
    </section>

    <section class="section features-section">
      <h2 class="section-title center">为什么选择我们</h2>
      <div class="features-grid">
        <div class="feature-card card-shadow">
          <el-icon :size="40" color="#409eff"><Grid /></el-icon>
          <h3>可视化展位图</h3>
          <p>实时查看各展区摊位招商情况，支持选择展位区域</p>
        </div>
        <div class="feature-card card-shadow">
          <el-icon :size="40" color="#67c23a"><CircleCheckFilled /></el-icon>
          <h3>电子核验</h3>
          <p>扫码核验摊主与观众入场凭证，告别名单翻找</p>
        </div>
        <div class="feature-card card-shadow">
          <el-icon :size="40" color="#e6a23c"><DataLine /></el-icon>
          <h3>数据看板</h3>
          <p>实时掌握各展区招商进度和当日入场人数</p>
        </div>
        <div class="feature-card card-shadow">
          <el-icon :size="40" color="#f56c6c"><WarningFilled /></el-icon>
          <h3>冲突检测</h3>
          <p>独立的展位分配服务，自动避免展位重复分配</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useExhibitionStore } from '@/stores/exhibition'
import { getActiveExhibitions } from '@/api/exhibitions'
import { getZoneList } from '@/api/booths'
import { getTicketTierList } from '@/api/tickets'

const exhibitionStore = useExhibitionStore()
const loading = ref(false)
const exhibitions = ref([])
const exhibitionCount = ref(0)
const boothCount = ref(0)
const ticketCount = ref(0)

onMounted(async () => {
  loading.value = true
  try {
    const data = await getActiveExhibitions()
    exhibitions.value = data
    exhibitionCount.value = data.length

    if (data.length) {
      exhibitionStore.setCurrent(data[0])
      const zones = await getZoneList({ exhibition_id: data[0].id })
      boothCount.value = zones.reduce((s, z) => s + (z.booth_count || 0), 0)

      const tiers = await getTicketTierList({ exhibition_id: data[0].id })
      ticketCount.value = tiers.reduce((s, t) => s + (t.sold_count || 0), 0)
    }
  } finally {
    loading.value = false
  }
})
</script>

<style lang="scss" scoped>
.hero-section {
  border-radius: 16px;
  padding: 48px;
  margin-bottom: 32px;
  background: linear-gradient(135deg, #eef2ff 0%, #e0f2fe 100%);

  .hero-inner {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 40px;
    max-width: 1200px;
    margin: 0 auto;
  }

  .hero-text h1 {
    font-size: 36px;
    margin: 0 0 16px;
    color: #1e40af;
  }
  .hero-desc {
    font-size: 16px;
    color: #475569;
    line-height: 1.8;
    margin-bottom: 32px;
  }
  .hero-actions {
    display: flex;
    gap: 12px;
  }

  .hero-stats {
    display: flex;
    flex-direction: column;
    gap: 20px;
    min-width: 200px;

    .stat-item {
      text-align: center;
      background: rgba(255, 255, 255, 0.7);
      border-radius: 12px;
      padding: 16px 24px;
    }
    .stat-num {
      font-size: 28px;
      font-weight: 700;
      color: #1e40af;
    }
    .stat-label {
      font-size: 13px;
      color: #64748b;
      margin-top: 4px;
    }
  }
}

.section {
  margin-bottom: 40px;
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.section-title {
  font-size: 22px;
  margin: 0;
  font-weight: 600;
  &.center {
    text-align: center;
    margin-bottom: 24px;
  }
}

.exhibition-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.exhibition-card {
  border-radius: 12px;
  padding: 24px;
  position: relative;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  }

  .exhibition-tag {
    position: absolute;
    top: 16px;
    right: 16px;
    padding: 2px 10px;
    border-radius: 10px;
    font-size: 12px;
    color: white;
    &.published, &.ongoing { background: #67c23a; }
    &.draft { background: #909399; }
    &.ended { background: #f56c6c; }
  }
  .exhibition-emoji {
    font-size: 48px;
    text-align: center;
    margin: 16px 0;
  }
  .exhibition-name {
    font-size: 18px;
    margin: 0 0 6px;
    text-align: center;
  }
  .exhibition-subtitle {
    text-align: center;
    color: #909399;
    font-size: 13px;
    margin: 0 0 16px;
    min-height: 20px;
  }
  .exhibition-info {
    border-top: 1px solid #f0f0f0;
    padding-top: 16px;
    .info-row {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 13px;
      color: #606266;
      margin-bottom: 6px;
    }
  }
  .exhibition-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 16px;
    padding-top: 12px;
    border-top: 1px solid #f0f0f0;
  }
}

.features-section {
  padding: 20px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
  max-width: 1200px;
  margin: 0 auto;

  .feature-card {
    padding: 32px 24px;
    border-radius: 12px;
    text-align: center;
    h3 {
      font-size: 18px;
      margin: 16px 0 8px;
    }
    p {
      color: #909399;
      font-size: 14px;
      margin: 0;
      line-height: 1.6;
    }
  }
}
</style>
