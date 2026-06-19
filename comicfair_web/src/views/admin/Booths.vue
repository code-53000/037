<template>
  <div>
    <div class="page-bar">
      <h2>展位管理</h2>
      <div>
        <el-select
          v-if="exhibitions.length"
          v-model="currentId"
          placeholder="选择展会"
          style="width: 220px; margin-right: 10px"
          @change="loadZones"
        >
          <el-option v-for="e in exhibitions" :key="e.id" :label="e.name" :value="e.id" />
        </el-select>
        <el-button type="primary" @click="openZoneDialog()">
          <el-icon><Plus /></el-icon>新建展区
        </el-button>
      </div>
    </div>

    <el-row :gutter="16" style="margin-top: 10px">
      <el-col :span="8">
        <div class="zone-card card-shadow">
          <h3 class="panel-title">展区列表</h3>
          <div v-loading="zonesLoading" class="zone-list">
            <div
              v-for="z in zones"
              :key="z.id"
              class="zone-item"
              :class="{ active: selectedZoneId === z.id }"
              @click="selectZone(z)"
            >
              <div class="z-left">
                <span class="z-color" :style="{ background: z.color }"></span>
                <div>
                  <div class="z-name">{{ z.name }}</div>
                  <div class="z-meta">{{ z.booth_count || 0 }} 展位 · ¥{{ z.booth_price }}</div>
                </div>
              </div>
              <div>
                <el-button link size="small" type="primary" @click.stop="openZoneDialog(z)">
                  编辑
                </el-button>
              </div>
            </div>
            <el-empty v-if="!zones.length" description="暂无展区" />
          </div>
        </div>
      </el-col>

      <el-col :span="16">
        <div class="zone-card card-shadow">
          <div class="panel-head">
            <h3 class="panel-title">
              {{ selectedZone?.name || '展位详情' }}
            </h3>
            <div v-if="selectedZone">
              <el-button type="primary" size="small" @click="openBoothDialog()">
                <el-icon><Plus /></el-icon>新增展位
              </el-button>
              <el-button size="small" @click="generateBooths">批量生成</el-button>
            </div>
          </div>
          <div v-if="selectedZone" v-loading="boothsLoading" class="booth-area">
            <div class="zone-stats-row">
              <el-tag type="success">可申请：{{ zoneMap.stats?.available || 0 }}</el-tag>
              <el-tag type="danger">已分配：{{ zoneMap.stats?.occupied || 0 }}</el-tag>
              <el-tag type="warning">已预留：{{ zoneMap.stats?.reserved || 0 }}</el-tag>
              <el-tag type="info">维护中：{{ zoneMap.stats?.maintenance || 0 }}</el-tag>
            </div>
            <div
              class="booth-grid"
              :style="{ gridTemplateColumns: `repeat(${getCols()}, minmax(0,1fr))` }"
            >
              <div
                v-for="b in sortedBooths"
                :key="b.id"
                class="booth-cell"
                :class="[b.status, { occupied: b.application, selected: selectedBoothId === b.id }]"
                @click="selectBooth(b)"
              >
                {{ b.booth_code.slice(-2) }}
              </div>
            </div>

            <div v-if="selectedBooth" class="booth-detail">
              <el-divider />
              <div class="detail-head">
                <strong>展位：{{ selectedBooth.booth_code }}</strong>
                <div>
                  <el-button size="small" type="primary" link @click="openBoothDialog(selectedBooth)">
                    编辑
                  </el-button>
                  <el-button
                    v-if="selectedBooth.status === 'available'"
                    size="small" link
                    type="warning"
                    @click="handleReserve"
                  >预留</el-button>
                  <el-button
                    v-if="['reserved', 'occupied'].includes(selectedBooth.status) || selectedBooth.application"
                    size="small" link
                    type="success"
                    @click="handleRelease"
                  >释放</el-button>
                </div>
              </div>
              <el-descriptions :column="3" size="small" border style="margin-top: 8px">
                <el-descriptions-item label="状态">
                  <el-tag :type="boothStatusType(selectedBooth.status)" size="small">
                    {{ selectedBooth.status_display }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="坐标">
                  ({{ selectedBooth.grid_x }}, {{ selectedBooth.grid_y }})
                </el-descriptions-item>
                <el-descriptions-item label="尺寸">
                  {{ selectedBooth.width_units }} × {{ selectedBooth.height_units }} 格
                </el-descriptions-item>
                <el-descriptions-item label="供电">{{ selectedBooth.has_electricity ? '✓' : '✗' }}</el-descriptions-item>
                <el-descriptions-item label="桌子">{{ selectedBooth.has_table ? '✓' : '✗' }}</el-descriptions-item>
                <el-descriptions-item label="椅子">{{ selectedBooth.has_chair ? '✓' : '✗' }}</el-descriptions-item>
              </el-descriptions>
              <el-descriptions v-if="selectedBooth.application" :column="1" size="small" border style="margin-top: 10px">
                <el-descriptions-item label="关联申请">
                  <router-link
                    :to="`/admin/applications?club_name=${selectedBooth.application.club_name}`"
                    style="color: #409eff"
                  >
                    {{ selectedBooth.application.club_name }}
                  </router-link>
                  （{{ selectedBooth.application.status_display }}）
                  · 申请人：{{ selectedBooth.application.applicant }}
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </div>
          <el-empty v-else description="请在左侧选择展区" />
        </div>
      </el-col>
    </el-row>

    <el-dialog v-model="zoneDialogVisible" :title="zoneForm.id ? '编辑展区' : '新建展区'" width="520px">
      <el-form ref="zoneFormRef" :model="zoneForm" :rules="zoneRules" label-width="100px">
        <el-form-item label="展区名称" prop="name">
          <el-input v-model="zoneForm.name" />
        </el-form-item>
        <el-form-item label="展区类型">
          <el-select v-model="zoneForm.zone_type" style="width: 100%">
            <el-option label="普通展区" value="general" />
            <el-option label="精品展区" value="premium" />
            <el-option label="Cosplay专区" value="cosplay" />
            <el-option label="餐饮区" value="food" />
            <el-option label="活动舞台" value="activity" />
          </el-select>
        </el-form-item>
        <el-form-item label="展区说明">
          <el-input v-model="zoneForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="标识颜色">
          <el-color-picker v-model="zoneForm.color" show-alpha />
        </el-form-item>
        <el-row :gutter="10">
          <el-col :span="12"><el-form-item label="X坐标"><el-input-number v-model="zoneForm.position_x" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="Y坐标"><el-input-number v-model="zoneForm.position_y" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="宽度"><el-input-number v-model="zoneForm.width" :min="50" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="高度"><el-input-number v-model="zoneForm.height" :min="50" style="width: 100%" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="单个展位价格" prop="booth_price">
          <el-input-number v-model="zoneForm.booth_price" :min="0" :precision="2" :step="100" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="zoneDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="zoneSaving" @click="saveZone">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="boothDialogVisible" :title="boothForm.id ? '编辑展位' : '新增展位'" width="480px">
      <el-form ref="boothFormRef" :model="boothForm" :rules="boothRules" label-width="100px">
        <el-form-item label="展位编号" prop="booth_code">
          <el-input v-model="boothForm.booth_code" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="boothForm.status" style="width: 100%">
            <el-option label="可申请" value="available" />
            <el-option label="已预留" value="reserved" />
            <el-option label="维护中" value="maintenance" />
          </el-select>
        </el-form-item>
        <el-row :gutter="10">
          <el-col :span="12"><el-form-item label="X网格"><el-input-number v-model="boothForm.grid_x" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="Y网格"><el-input-number v-model="boothForm.grid_y" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="宽度格"><el-input-number v-model="boothForm.width_units" :min="1" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="高度格"><el-input-number v-model="boothForm.height_units" :min="1" style="width: 100%" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="配套设施">
          <el-checkbox-group>
            <el-checkbox v-model="boothForm.has_electricity">供电</el-checkbox>
            <el-checkbox v-model="boothForm.has_table">桌子</el-checkbox>
            <el-checkbox v-model="boothForm.has_chair">椅子</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="boothForm.notes" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="boothDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="boothSaving" @click="saveBooth">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useExhibitionStore } from '@/stores/exhibition'
import { getActiveExhibitions } from '@/api/exhibitions'
import {
  getZoneList, createZone, updateZone, getZoneDetail,
  getBoothList, createBooth, updateBooth, getZoneBoothMap,
  reserveBooth, releaseBooth, getBoothDetail,
} from '@/api/booths'

const exhibitionStore = useExhibitionStore()
const exhibitions = ref([])
const currentId = ref(exhibitionStore.currentId || null)

const zonesLoading = ref(false)
const boothsLoading = ref(false)
const zones = ref([])
const selectedZoneId = ref(null)
const selectedZone = computed(() => zones.value.find((z) => z.id === selectedZoneId.value))
const zoneMap = ref({ booths: [], stats: {} })

const selectedBoothId = ref(null)
const sortedBooths = computed(() => {
  const list = zoneMap.value.booths || []
  return [...list].sort((a, b) => a.grid_y - b.grid_y || a.grid_x - b.grid_x)
})
const selectedBooth = computed(() =>
  sortedBooths.value.find((b) => b.id === selectedBoothId.value)
)

const zoneDialogVisible = ref(false)
const zoneSaving = ref(false)
const zoneFormRef = ref(null)
const zoneForm = reactive({
  id: null, exhibition: null, name: '', zone_type: 'general',
  description: '', color: '#409EFF',
  position_x: 0, position_y: 0, width: 420, height: 300,
  booth_price: 0,
})
const zoneRules = {
  name: [{ required: true, message: '请输入展区名称', trigger: 'blur' }],
  booth_price: [{ required: true, message: '请输入展位价格', trigger: 'blur' }],
}

const boothDialogVisible = ref(false)
const boothSaving = ref(false)
const boothFormRef = ref(null)
const boothForm = reactive({
  id: null, zone: null, booth_code: '', status: 'available',
  grid_x: 0, grid_y: 0, width_units: 1, height_units: 1,
  has_electricity: true, has_table: true, has_chair: true,
  notes: '',
})
const boothRules = {
  booth_code: [{ required: true, message: '请输入展位编号', trigger: 'blur' }],
}

function boothStatusType(s) {
  return { available: 'success', reserved: 'warning', occupied: 'danger', maintenance: 'info' }[s] || 'info'
}

function getCols() {
  const maxX = Math.max(...(zoneMap.value.booths || []).map((b) => (b.grid_x || 0) + (b.width_units || 1)), 0)
  return Math.max(6, Math.min(16, maxX + 1))
}

async function loadZones() {
  if (!currentId.value) return
  exhibitionStore.currentId = currentId.value
  zonesLoading.value = true
  try {
    zones.value = await getZoneList({ exhibition_id: currentId.value })
    if (zones.value.length && !selectedZoneId.value) selectZone(zones.value[0])
  } finally {
    zonesLoading.value = false
  }
}

async function selectZone(z) {
  selectedZoneId.value = z.id
  selectedBoothId.value = null
  boothsLoading.value = true
  try {
    zoneMap.value = await getZoneBoothMap(z.id)
  } finally {
    boothsLoading.value = false
  }
}

function selectBooth(b) {
  selectedBoothId.value = b.id
}

function openZoneDialog(row) {
  if (row) {
    Object.assign(zoneForm, row)
  } else {
    Object.assign(zoneForm, {
      id: null, exhibition: currentId.value, name: '', zone_type: 'general',
      description: '', color: '#409EFF',
      position_x: 0, position_y: 0, width: 420, height: 300,
      booth_price: 800,
    })
  }
  zoneDialogVisible.value = true
}

async function saveZone() {
  await zoneFormRef.value?.validate()
  zoneSaving.value = true
  try {
    const payload = { ...zoneForm, exhibition: currentId.value }
    if (zoneForm.id) {
      await updateZone(zoneForm.id, payload)
    } else {
      await createZone(payload)
    }
    ElMessage.success('保存成功')
    zoneDialogVisible.value = false
    await loadZones()
  } finally {
    zoneSaving.value = false
  }
}

function openBoothDialog(b) {
  if (b) {
    Object.assign(boothForm, b)
  } else {
    Object.assign(boothForm, {
      id: null, zone: selectedZoneId.value,
      booth_code: '', status: 'available',
      grid_x: 0, grid_y: 0, width_units: 1, height_units: 1,
      has_electricity: true, has_table: true, has_chair: true, notes: '',
    })
  }
  boothDialogVisible.value = true
}

async function saveBooth() {
  await boothFormRef.value?.validate()
  boothSaving.value = true
  try {
    if (boothForm.id) {
      await updateBooth(boothForm.id, { ...boothForm, zone: selectedZoneId.value })
    } else {
      await createBooth({ ...boothForm, zone: selectedZoneId.value })
    }
    ElMessage.success('保存成功')
    boothDialogVisible.value = false
    await selectZone(selectedZone.value)
  } finally {
    boothSaving.value = false
  }
}

async function generateBooths() {
  try {
    const { value } = await ElMessageBox.prompt('生成展位的行数（1-20）：', '批量生成展位', {
      inputPattern: /^\d+$/,
      inputValue: '5',
      inputPlaceholder: '请输入行数',
    })
    const rows = parseInt(value, 10)
    const cols = Math.max(5, Math.floor((selectedZone.value?.width || 400) / 50))
    const prefix = selectedZone.value.name.match(/([A-Z])/i)?.[1]?.toUpperCase() || 'Z'
    const existing = await getBoothList({ zone_id: selectedZoneId.value })
    const existingCodes = new Set((existing.results || existing || []).map((b) => b.booth_code))

    for (let r = 1; r <= rows; r++) {
      for (let c = 1; c <= cols; c++) {
        const code = `${prefix}${String(r).padStart(2, '0')}${String(c).padStart(2, '0')}`
        if (existingCodes.has(code)) continue
        await createBooth({
          zone: selectedZoneId.value,
          booth_code: code,
          status: 'available',
          grid_x: c - 1, grid_y: r - 1,
          width_units: 1, height_units: 1,
          has_electricity: true, has_table: true, has_chair: true,
        })
      }
    }
    ElMessage.success('批量生成完成')
    await selectZone(selectedZone.value)
  } catch {}
}

async function handleReserve() {
  if (!selectedBooth.value) return
  try {
    await reserveBooth(selectedBooth.value.id)
    ElMessage.success('已预留')
    await selectZone(selectedZone.value)
  } catch {}
}

async function handleRelease() {
  if (!selectedBooth.value) return
  await ElMessageBox.confirm('确定释放此展位？如果有分配的申请将解除关联。', '确认释放', { type: 'warning' })
  try {
    await releaseBooth(selectedBooth.value.id)
    ElMessage.success('已释放')
    await selectZone(selectedZone.value)
  } catch {}
}

onMounted(async () => {
  exhibitions.value = await getActiveExhibitions()
  if (!currentId.value && exhibitions.value.length) currentId.value = exhibitions.value[0].id
  await loadZones()
})
</script>

<style lang="scss" scoped>
.page-bar {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 8px;
  h2 { margin: 0; font-size: 22px; }
}
.zone-card { padding: 20px; border-radius: 10px; min-height: 600px; }
.panel-title { margin: 0 0 16px; font-size: 16px; border-left: 3px solid #409eff; padding-left: 10px; }
.panel-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.zone-list { display: flex; flex-direction: column; gap: 10px; }
.zone-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 14px; border-radius: 8px; cursor: pointer;
  border: 1px solid #ebeef5; transition: all 0.2s;
  &:hover { background: #ecf5ff; }
  &.active { background: #ecf5ff; border-color: #409eff; }

  .z-left { display: flex; align-items: center; gap: 12px; }
  .z-color { width: 18px; height: 18px; border-radius: 4px; }
  .z-name { font-weight: 600; margin-bottom: 2px; }
  .z-meta { font-size: 12px; color: #909399; }
}

.zone-stats-row { display: flex; gap: 12px; margin-bottom: 16px; }

.booth-grid {
  display: grid; gap: 4px;
  padding: 14px; background: #fafafa; border-radius: 10px;
  margin-bottom: 14px;
}

.booth-detail {
  margin-top: 12px;
  .detail-head { display: flex; justify-content: space-between; align-items: center; }
}
</style>
