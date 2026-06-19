<template>
  <div>
    <div class="page-header">
      <div>
        <h2 class="page-title">展位图总览</h2>
        <p class="subtitle">实时查看各展区摊位招商情况</p>
      </div>
      <el-select
        v-if="exhibitions.length"
        v-model="currentExhibitionId"
        style="width: 280px"
        placeholder="选择展会"
        @change="loadZones"
      >
        <el-option
          v-for="e in exhibitions"
          :key="e.id"
          :label="e.name"
          :value="e.id"
        />
      </el-select>
    </div>

    <el-row :gutter="16" class="stats-row">
      <el-col :span="6" v-for="s in summary" :key="s.label">
        <div class="stat-card card-shadow" :style="{ borderTop: `3px solid ${s.color}` }">
          <div class="stat-label">{{ s.label }}</div>
          <div class="stat-value">{{ s.value }}</div>
        </div>
      </el-col>
    </el-row>

    <div v-loading="loading" class="zone-list">
      <div v-for="zone in zones" :key="zone.id" class="zone-container card-shadow">
        <div class="zone-header">
          <div class="zone-title">
            <span class="zone-color" :style="{ background: zone.color }"></span>
            <span class="zone-name">{{ zone.name }}</span>
            <el-tag effect="light" type="info">{{ zone.zone_type_display }}</el-tag>
          </div>
          <div class="zone-stats">
            <el-statistic title="展位总数" :value="zone.booth_count || 0" />
            <el-statistic title="已被申请" :value="zone.stats?.occupied || 0" />
            <el-statistic title="可申请" :value="zone.stats?.available || 0" />
            <el-statistic title="招商率">
              <template #formatter>
                <span style="color: #67c23a; font-weight: 600">
                  {{ zone.stats?.total ? ((zone.stats.occupied / zone.stats.total) * 100).toFixed(1) : 0 }}%
                </span>
              </template>
            </el-statistic>
          </div>
        </div>

        <div
          class="booth-grid"
          :style="{ gridTemplateColumns: `repeat(${getCols(zone)}, 1fr)` }"
        >
          <div
            v-for="b in getSortedBooths(zone)"
            :key="b.id"
            class="booth-cell"
            :class="[b.status, { occupied: b.application }]"
            @click="showBoothDetail(b, zone)"
            :title="b.booth_code + ' - ' + (b.status_display || '')"
          >
            {{ b.booth_code.slice(-2) }}
          </div>
        </div>

        <div class="zone-footer">
          <span class="price">
            <el-icon><Money /></el-icon>
            展位费：¥{{ zone.booth_price }} / 个
          </span>
          <el-button
            type="primary"
            size="small"
            :disabled="!zone.stats?.available"
            @click="goApply(zone)"
          >
            申请此展区展位
          </el-button>
        </div>
      </div>

      <div class="legend card-shadow">
        <h4>图例说明</h4>
        <div class="legend-items">
          <div class="legend-item">
            <span class="color available"></span>可申请
          </div>
          <div class="legend-item">
            <span class="color occupied"></span>已申请/已分配
          </div>
          <div class="legend-item">
            <span class="color reserved"></span>已预留
          </div>
          <div class="legend-item">
            <span class="color maintenance"></span>维护中
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="detailVisible" title="展位详情" width="420px">
      <div v-if="selectedBooth" class="detail-content">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="展位编号">{{ selectedBooth.booth_code }}</el-descriptions-item>
          <el-descriptions-item label="所属展区">{{ currentZone?.name }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusTagType">{{ selectedBooth.status_display }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="供电">
            {{ selectedBooth.has_electricity ? '✓ 有' : '✗ 无' }}
          </el-descriptions-item>
          <el-descriptions-item label="配套桌椅">
            桌：{{ selectedBooth.has_table ? '✓' : '✗' }} / 椅：{{ selectedBooth.has_chair ? '✓' : '✗' }}
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedBooth.application" label="申请社团">
            {{ selectedBooth.application.club_name }}
            <el-tag size="small" style="margin-left: 8px">
              {{ selectedBooth.application.status_display }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button v-if="selectedBooth?.status === 'available' && userStore.isExhibitor" type="primary" @click="goApplyZone">
          申请此展位
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { useExhibitionStore } from '@/stores/exhibition'
import { getActiveExhibitions } from '@/api/exhibitions'
import { getZoneList, getZoneBoothMap } from '@/api/booths'

const router = useRouter()
const userStore = useUserStore()
const exhibitionStore = useExhibitionStore()

const loading = ref(false)
const exhibitions = ref([])
const zones = ref([])
const currentExhibitionId = ref(exhibitionStore.currentId || null)

const detailVisible = ref(false)
const selectedBooth = ref(null)
const currentZone = ref(null)

const statusTagType = computed(() => {
  if (!selectedBooth.value) return 'info'
  const s = selectedBooth.value.status
  if (s === 'available') return 'success'
  if (s === 'occupied' || selectedBooth.value.application) return 'danger'
  if (s === 'reserved') return 'warning'
  return 'info'
})

const summary = computed(() => {
  const total = zones.value.reduce((s, z) => s + (z.stats?.total || 0), 0)
  const occupied = zones.value.reduce((s, z) => s + (z.stats?.occupied || 0), 0)
  const available = zones.value.reduce((s, z) => s + (z.stats?.available || 0), 0)
  const rate = total ? ((occupied / total) * 100).toFixed(1) : 0
  return [
    { label: '展位总数', value: total, color: '#409eff' },
    { label: '已被申请', value: occupied, color: '#f56c6c' },
    { label: '可申请数', value: available, color: '#67c23a' },
    { label: '整体招商率', value: `${rate}%`, color: '#e6a23c' },
  ]
})

function getCols(zone) {
  if (!zone.booths?.length) return 8
  const maxX = Math.max(...zone.booths.map((b) => (b.grid_x || 0) + (b.width_units || 1)))
  return Math.max(6, Math.min(14, maxX + 1))
}

function getSortedBooths(zone) {
  if (!zone.booths) return []
  return [...zone.booths].sort((a, b) => {
    if (a.grid_y !== b.grid_y) return a.grid_y - b.grid_y
    return a.grid_x - b.grid_x
  })
}

async function loadZones() {
  if (!currentExhibitionId.value) return
  loading.value = true
  try {
    const rawZones = await getZoneList({ exhibition_id: currentExhibitionId.value })
    const enriched = []
    for (const z of rawZones) {
      const map = await getZoneBoothMap(z.id)
      enriched.push({ ...z, ...map })
    }
    zones.value = enriched
  } finally {
    loading.value = false
  }
}

async function showBoothDetail(booth, zone) {
  selectedBooth.value = booth
  currentZone.value = zone
  detailVisible.value = true
}

function goApply(zone) {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  if (!userStore.isExhibitor && !userStore.isOrganizer) {
    ElMessage.warning('仅摊主账号可申请摊位')
    return
  }
  router.push({ path: '/apply', query: { zone_id: zone.id, exhibition_id: currentExhibitionId.value } })
}

function goApplyZone() {
  goApply(currentZone.value)
}

onMounted(async () => {
  loading.value = true
  try {
    exhibitions.value = await getActiveExhibitions()
    if (exhibitions.value.length && !currentExhibitionId.value) {
      currentExhibitionId.value = exhibitions.value[0].id
    }
    await loadZones()
  } finally {
    loading.value = false
  }
})
</script>

<style lang="scss" scoped>
.subtitle {
  margin: 6px 0 0;
  color: #909399;
  font-size: 14px;
}

.stats-row {
  margin-bottom: 20px;

  .stat-card {
    padding: 20px;
    border-radius: 10px;

    .stat-label {
      font-size: 13px;
      color: #909399;
    }
    .stat-value {
      font-size: 26px;
      font-weight: 700;
      margin-top: 8px;
      color: #303133;
    }
  }
}

.zone-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.zone-container {
  border-radius: 12px;
  padding: 24px;
  overflow: hidden;

  .zone-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    flex-wrap: wrap;
    gap: 16px;

    .zone-title {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 18px;
      font-weight: 600;

      .zone-color {
        width: 20px;
        height: 20px;
        border-radius: 4px;
      }
    }
    .zone-stats {
      display: flex;
      gap: 32px;

      :deep(.el-statistic__head) {
        font-size: 12px;
      }
    }
  }

  .zone-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px dashed #ebeef5;

    .price {
      display: flex;
      align-items: center;
      gap: 6px;
      color: #f56c6c;
      font-weight: 600;
    }
  }
}

.legend {
  padding: 16px 20px;
  border-radius: 10px;

  h4 {
    margin: 0 0 12px;
    font-size: 14px;
  }

  .legend-items {
    display: flex;
    gap: 24px;
    flex-wrap: wrap;

    .legend-item {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 13px;

      .color {
        width: 16px;
        height: 16px;
        border-radius: 3px;

        &.available { background: #67c23a; }
        &.occupied { background: #f56c6c; }
        &.reserved { background: #e6a23c; }
        &.maintenance { background: #909399; }
      }
    }
  }
}
</style>
