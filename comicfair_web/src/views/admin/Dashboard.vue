<template>
  <div>
    <div class="dash-header">
      <h2>数据总览</h2>
      <el-select
        v-if="exhibitions.length"
        v-model="currentId"
        placeholder="选择展会"
        style="width: 240px; margin-left: 16px"
        @change="loadAll"
      >
        <el-option v-for="e in exhibitions" :key="e.id" :label="e.name" :value="e.id" />
      </el-select>
    </div>

    <el-row :gutter="16" class="stat-row">
      <el-col :span="6" v-for="s in topStats" :key="s.label">
        <div class="stat-card" :style="{ borderLeft: `4px solid ${s.color}` }">
          <div class="stat-label">{{ s.label }}</div>
          <div class="stat-value">{{ s.value }}</div>
          <div class="stat-icon" :style="{ background: s.color + '22', color: s.color }">
            <el-icon :size="26"><component :is="s.icon" /></el-icon>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="12">
        <div class="chart-card">
          <h3 class="card-title">展区招商情况</h3>
          <v-chart class="chart" :option="zoneChartOption" autoresize />
        </div>
      </el-col>
      <el-col :span="12">
        <div class="chart-card">
          <h3 class="card-title">今日签到趋势</h3>
          <v-chart class="chart" :option="hourlyChartOption" autoresize />
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="12">
        <div class="panel-card">
          <div class="panel-head">
            <h3 class="card-title">摊位申请进度</h3>
            <el-button link type="primary" @click="$router.push('/admin/applications')">查看全部</el-button>
          </div>
          <el-table :data="recentApps" stripe size="small">
            <el-table-column prop="club_name" label="社团名称" min-width="140" />
            <el-table-column prop="preferred_zone_name" label="意向展区" width="120" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag size="small" :type="statusType(row.status)">{{ row.status_display }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="160" />
          </el-table>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="panel-card">
          <div class="panel-head">
            <h3 class="card-title">最近签到</h3>
            <el-button link type="primary" @click="$router.push('/admin/checkin-records')">查看全部</el-button>
          </div>
          <el-table :data="recentCheckins" stripe size="small">
            <el-table-column label="类型" width="90">
              <template #default="{ row }">
                <el-tag size="small">{{ row.type_display }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="person_name" label="人员" min-width="120" />
            <el-table-column label="结果" width="90">
              <template #default="{ row }">
                <el-tag size="small" :type="row.status === 'success' ? 'success' : 'warning'">
                  {{ row.status_display }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="checkin_time" label="时间" width="160" />
          </el-table>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import {
  TitleComponent, TooltipComponent, LegendComponent,
  GridComponent, DatasetComponent, TransformComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'
import { useExhibitionStore } from '@/stores/exhibition'
import { getActiveExhibitions, getExhibitionStats } from '@/api/exhibitions'
import { getApplicationList } from '@/api/applications'
import { getCheckinRecords, getCheckinStats } from '@/api/checkins'

use([
  CanvasRenderer, BarChart, LineChart, PieChart,
  TitleComponent, TooltipComponent, LegendComponent,
  GridComponent, DatasetComponent, TransformComponent,
])

const exhibitionStore = useExhibitionStore()
const exhibitions = ref([])
const currentId = ref(exhibitionStore.currentId || null)
const stats = ref({})
const checkinStats = ref({})
const recentApps = ref([])
const recentCheckins = ref([])

const topStats = computed(() => [
  { label: '展位总数', value: stats.value.total_booths || 0, icon: 'Grid', color: '#409eff' },
  { label: '摊位申请', value: stats.value.total_applications || 0, icon: 'Document', color: '#e6a23c' },
  { label: '售票总数', value: stats.value.total_tickets || 0, icon: 'Ticket', color: '#67c23a' },
  { label: '签到总数', value: stats.value.total_checkins || 0, icon: 'CircleCheck', color: '#f56c6c' },
])

const zoneChartOption = computed(() => {
  const zones = stats.value.zone_stats || []
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['已分配', '可申请'] },
    grid: { left: 60, right: 20, top: 40, bottom: 40 },
    xAxis: {
      type: 'category',
      data: zones.map((z) => z.name),
      axisLabel: { interval: 0, rotate: 20, fontSize: 11 },
    },
    yAxis: { type: 'value' },
    series: [
      { name: '已分配', type: 'bar', stack: 'total', data: zones.map((z) => z.occupied), itemStyle: { color: '#f56c6c' } },
      { name: '可申请', type: 'bar', stack: 'total', data: zones.map((z) => z.total_booths - z.occupied), itemStyle: { color: '#67c23a' } },
    ],
  }
})

const hourlyChartOption = computed(() => {
  const hourly = checkinStats.value.hourly || Array(24).fill(0).map((_, i) => ({ hour: i, count: 0 }))
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: hourly.map((h) => `${h.hour}:00`), axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value' },
    series: [{
      type: 'line',
      smooth: true,
      data: hourly.map((h) => h.count || 0),
      areaStyle: { color: 'rgba(64, 158, 255, 0.2)' },
      lineStyle: { color: '#409eff' },
      itemStyle: { color: '#409eff' },
    }],
  }
})

function statusType(s) {
  return {
    draft: 'info', pending: 'warning', approved: 'primary',
    paid: 'success', rejected: 'danger', cancelled: 'info', checked_in: 'success',
  }[s] || 'info'
}

async function loadAll() {
  if (!currentId.value) return
  exhibitionStore.currentId = currentId.value
  try {
    const [exhiStats, apps, records, ciStats] = await Promise.all([
      getExhibitionStats(currentId.value),
      getApplicationList({ exhibition: currentId.value, page_size: 5, ordering: '-created_at' }),
      getCheckinRecords({ exhibition_id: currentId.value, today: 'true', page_size: 5, ordering: '-checkin_time' }),
      getCheckinStats(currentId.value),
    ])
    stats.value = exhiStats
    recentApps.value = apps.results || apps || []
    recentCheckins.value = records.results || records || []
    checkinStats.value = ciStats
  } catch {}
}

onMounted(async () => {
  exhibitions.value = await getActiveExhibitions()
  if (!currentId.value && exhibitions.value.length) currentId.value = exhibitions.value[0].id
  await loadAll()
})
</script>

<style lang="scss" scoped>
.dash-header {
  display: flex; align-items: center; margin-bottom: 16px;
  h2 { margin: 0; font-size: 22px; }
}
.stat-row { margin-bottom: 4px; }
.stat-card {
  background: #fff; border-radius: 10px; padding: 20px;
  position: relative; min-height: 110px;
  .stat-label { font-size: 13px; color: #909399; }
  .stat-value { font-size: 30px; font-weight: 700; margin-top: 8px; }
  .stat-icon {
    position: absolute; right: 18px; top: 20px;
    width: 50px; height: 50px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
  }
}
.chart-card, .panel-card {
  background: #fff; border-radius: 10px; padding: 20px;
  min-height: 340px;
  .card-title { margin: 0 0 12px; font-size: 16px; }
  .chart { height: 280px; }
  .panel-head {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 12px;
    .card-title { margin: 0; }
  }
}
</style>
