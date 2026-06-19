<template>
  <div>
    <div class="page-header">
      <div>
        <h2 class="page-title">摊位申请</h2>
        <p class="subtitle">填写社团资料，选择意向展区，提交申请</p>
      </div>
      <el-button @click="$router.push('/my-applications')">
        <el-icon><List /></el-icon>查看我的申请
      </el-button>
    </div>

    <el-steps :active="step" finish-status="success" align-center class="apply-steps">
      <el-step title="选择展会" description="选择您要参加的漫展" />
      <el-step title="选择展区" description="挑选意向展位区域" />
      <el-step title="填写资料" description="社团信息和联系方式" />
      <el-step title="确认提交" description="确认并提交申请" />
    </el-steps>

    <div class="form-card card-shadow">
      <template v-if="step === 0">
        <h3 class="step-title">第一步：选择展会</h3>
        <el-radio-group v-model="form.exhibition" class="exhibition-list">
          <el-radio
            v-for="e in exhibitions"
            :key="e.id"
            :label="e.id"
            border
            class="exhibition-option"
          >
            <div class="option-content">
              <div class="option-emoji">🎨</div>
              <div>
                <div class="option-name">{{ e.name }}</div>
                <div class="option-meta">{{ e.start_date }} ~ {{ e.end_date }} · {{ e.venue }}</div>
                <el-tag size="small" type="success">{{ e.status_display }}</el-tag>
              </div>
            </div>
          </el-radio>
        </el-radio-group>
      </template>

      <template v-if="step === 1">
        <h3 class="step-title">第二步：选择意向展区</h3>
        <p class="step-desc">点击下方展区卡片选择意向区域，后续主办方会根据审核情况分配具体展位</p>
        <div class="zone-grid">
          <div
            v-for="z in zones"
            :key="z.id"
            class="zone-card"
            :class="{ active: form.preferred_zone === z.id }"
            @click="form.preferred_zone = z.id; loadZoneBooths(z)"
          >
            <div class="zone-head" :style="{ background: z.color }">
              <span class="zone-name">{{ z.name }}</span>
              <el-tag size="small" effect="dark">{{ z.zone_type_display }}</el-tag>
            </div>
            <div class="zone-body">
              <p class="zone-desc">{{ z.description }}</p>
              <div class="zone-info-row">
                <span><el-icon><Grid /></el-icon>共 {{ z.booth_count }} 个展位</span>
                <span><el-icon><Money /></el-icon>¥{{ z.booth_price }}/展位</span>
              </div>
              <div class="zone-availability">
                <el-progress
                  :percentage="z.booth_count ? (100 - Math.round((z.stats?.available || 0) / z.booth_count * 100)) : 0"
                  :color="z.color"
                  :stroke-width="8"
                />
                <div class="avail-text">
                  剩余可申请：<strong>{{ z.stats?.available || 0 }}</strong> 个
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <template v-if="step === 2">
        <h3 class="step-title">第三步：填写社团资料</h3>
        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-width="130px"
          class="detail-form"
        >
          <el-divider content-position="left">社团信息</el-divider>
          <el-form-item label="社团/摊位名称" prop="club_name">
            <el-input v-model="form.club_name" placeholder="请输入您的社团或摊位名称" maxlength="200" />
          </el-form-item>
          <el-form-item label="社团简介" prop="club_introduction">
            <el-input v-model="form.club_introduction" type="textarea" :rows="3" placeholder="介绍一下您的社团（可不填）" />
          </el-form-item>
          <el-form-item label="作品类型" prop="works_type">
            <el-input v-model="form.works_type" placeholder="如：同人本/周边/原创插画等" />
          </el-form-item>
          <el-form-item label="主要作品">
            <el-input v-model="form.main_works" type="textarea" :rows="3" placeholder="简单介绍本次参展作品（可不填）" />
          </el-form-item>
          <el-form-item label="申请展位数量" prop="booth_count">
            <el-input-number v-model="form.booth_count" :min="1" :max="6" />
          </el-form-item>

          <el-divider content-position="left">联系方式</el-divider>
          <el-form-item label="联系人姓名" prop="contact_name">
            <el-input v-model="form.contact_name" placeholder="请输入联系人真实姓名" />
          </el-form-item>
          <el-form-item label="联系电话" prop="contact_phone">
            <el-input v-model="form.contact_phone" placeholder="用于紧急联络" />
          </el-form-item>
          <el-form-item label="联系邮箱" prop="contact_email">
            <el-input v-model="form.contact_email" placeholder="用于发送审核通知" />
          </el-form-item>
          <el-form-item label="社交账号">
            <el-input v-model="form.social_media" placeholder="微博/LOFTER/B站等，可不填" />
          </el-form-item>

          <el-divider content-position="left">特殊需求</el-divider>
          <el-form-item label="额外用电需求">
            <el-switch v-model="form.has_power" />
            <el-input
              v-if="form.has_power"
              v-model="form.power_description"
              placeholder="请说明用电设备和功率（如：笔记本电脑2台）"
              style="margin-top: 8px"
            />
          </el-form-item>
          <el-form-item label="其他特殊需求">
            <el-input v-model="form.special_requirements" type="textarea" :rows="2" placeholder="其他需要主办方配合的事项（可不填）" />
          </el-form-item>
        </el-form>
      </template>

      <template v-if="step === 3">
        <h3 class="step-title">第四步：确认信息</h3>
        <el-descriptions :column="2" border class="preview-desc">
          <el-descriptions-item label="展会" :span="2">{{ currentExhibition?.name }}</el-descriptions-item>
          <el-descriptions-item label="意向展区">{{ currentZone?.name }}</el-descriptions-item>
          <el-descriptions-item label="展位数量">{{ form.booth_count }} 个</el-descriptions-item>
          <el-descriptions-item label="社团名称" :span="2">{{ form.club_name }}</el-descriptions-item>
          <el-descriptions-item label="作品类型">{{ form.works_type || '-' }}</el-descriptions-item>
          <el-descriptions-item label="联系人">{{ form.contact_name }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ form.contact_phone }}</el-descriptions-item>
          <el-descriptions-item label="联系邮箱">{{ form.contact_email || '-' }}</el-descriptions-item>
          <el-descriptions-item label="用电需求">{{ form.has_power ? (form.power_description || '需要供电') : '无' }}</el-descriptions-item>
          <el-descriptions-item label="预估费用">
            <span style="color: #f56c6c; font-weight: 600; font-size: 16px">
              ¥{{ estimatedFee }}
            </span>
            <span style="color: #909399; font-size: 12px; margin-left: 8px">实际费用以审核为准</span>
          </el-descriptions-item>
        </el-descriptions>
        <el-alert
          type="info"
          :closable="false"
          style="margin-top: 16px"
          title="温馨提示：提交后请耐心等待主办方审核，审核通过后将收到通知并可在线缴费"
        />
      </template>

      <div class="step-actions">
        <el-button v-if="step > 0" @click="step--">
          <el-icon><ArrowLeft /></el-icon>上一步
        </el-button>
        <el-button v-if="step < 3" type="primary" @click="nextStep">
          下一步<el-icon><ArrowRight /></el-icon>
        </el-button>
        <el-button v-if="step === 3" type="success" :loading="submitting" @click="submitForm">
          <el-icon><Check /></el-icon>确认提交申请
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useExhibitionStore } from '@/stores/exhibition'
import { getActiveExhibitions } from '@/api/exhibitions'
import { getZoneList, getZoneBoothMap } from '@/api/booths'
import { createApplication, submitApplication } from '@/api/applications'

const route = useRoute()
const router = useRouter()
const exhibitionStore = useExhibitionStore()
const formRef = ref(null)

const step = ref(0)
const submitting = ref(false)
const exhibitions = ref([])
const zones = ref([])

const form = reactive({
  exhibition: route.query.exhibition_id ? parseInt(route.query.exhibition_id) : null,
  preferred_zone: route.query.zone_id ? parseInt(route.query.zone_id) : null,
  club_name: '',
  club_introduction: '',
  works_type: '',
  main_works: '',
  booth_count: 1,
  contact_name: '',
  contact_phone: '',
  contact_email: '',
  social_media: '',
  has_power: false,
  power_description: '',
  special_requirements: '',
})

const rules = {
  club_name: [{ required: true, message: '请输入社团名称', trigger: 'blur' }],
  works_type: [{ required: true, message: '请填写作品类型', trigger: 'blur' }],
  booth_count: [{ required: true, message: '请选择展位数量', trigger: 'change' }],
  contact_name: [{ required: true, message: '请输入联系人姓名', trigger: 'blur' }],
  contact_phone: [
    { required: true, message: '请输入联系电话', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' },
  ],
  contact_email: [{ type: 'email', message: '请输入正确邮箱', trigger: 'blur' }],
}

const currentExhibition = computed(() =>
  exhibitions.value.find((e) => e.id === form.exhibition)
)
const currentZone = computed(() => zones.value.find((z) => z.id === form.preferred_zone))
const estimatedFee = computed(() => {
  const zone = currentZone.value
  if (!zone) return 0
  return (Number(zone.booth_price) * form.booth_count).toFixed(2)
})

async function loadZones() {
  if (!form.exhibition) {
    zones.value = []
    return
  }
  const list = await getZoneList({ exhibition_id: form.exhibition })
  const enriched = []
  for (const z of list) {
    try {
      const map = await getZoneBoothMap(z.id)
      enriched.push({ ...z, ...map })
    } catch {
      enriched.push({ ...z, stats: { total: z.booth_count || 0, available: z.booth_count || 0 } })
    }
  }
  zones.value = enriched
}

function loadZoneBooths(z) {
  if (!z.stats) {
    getZoneBoothMap(z.id).then((map) => {
      const idx = zones.value.findIndex((item) => item.id === z.id)
      if (idx > -1) zones.value[idx] = { ...zones.value[idx], ...map }
    })
  }
}

async function nextStep() {
  if (step.value === 0 && !form.exhibition) {
    ElMessage.warning('请选择展会')
    return
  }
  if (step.value === 1 && !form.preferred_zone) {
    ElMessage.warning('请选择意向展区')
    return
  }
  if (step.value === 2) {
    await formRef.value?.validate()
  }
  step.value++
}

async function submitForm() {
  submitting.value = true
  try {
    const data = {
      exhibition: form.exhibition,
      preferred_zone: form.preferred_zone,
      club_name: form.club_name,
      club_introduction: form.club_introduction,
      works_type: form.works_type,
      main_works: form.main_works,
      booth_count: form.booth_count,
      contact_name: form.contact_name,
      contact_phone: form.contact_phone,
      contact_email: form.contact_email,
      social_media: form.social_media,
      has_power: form.has_power,
      power_description: form.has_power ? form.power_description : '',
      special_requirements: form.special_requirements,
    }
    const created = await createApplication(data)
    await submitApplication(created.id)
    ElMessage.success('申请提交成功！请等待主办方审核')
    router.push('/my-applications')
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  exhibitions.value = await getActiveExhibitions()
  if (!form.exhibition && exhibitions.value.length) {
    form.exhibition = exhibitions.value[0].id
  }
  if (exhibitions.value.length) {
    exhibitionStore.setCurrent(exhibitions.value[0])
  }
  if (form.exhibition) await loadZones()
})
</script>

<style lang="scss" scoped>
.subtitle { margin: 6px 0 0; color: #909399; font-size: 14px; }
.apply-steps { margin-bottom: 32px; }

.form-card {
  padding: 32px;
  border-radius: 12px;

  .step-title { margin: 0 0 20px; font-size: 18px; }
  .step-desc { color: #909399; margin: -10px 0 20px; }

  .exhibition-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 12px;

    .exhibition-option {
      padding: 4px;

      .option-content {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 4px;

        .option-emoji { font-size: 36px; }
        .option-name { font-weight: 600; margin-bottom: 4px; }
        .option-meta { font-size: 12px; color: #909399; margin-bottom: 6px; }
      }
    }
  }

  .zone-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;

    .zone-card {
      border-radius: 10px;
      overflow: hidden;
      border: 2px solid #ebeef5;
      cursor: pointer;
      transition: all 0.2s;

      &:hover { border-color: #b3d8ff; }
      &.active { border-color: #409eff; box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2); }

      .zone-head {
        padding: 12px 16px;
        color: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-weight: 600;
      }

      .zone-body { padding: 16px; }
      .zone-desc { min-height: 40px; color: #606266; margin: 0 0 10px; font-size: 13px; }
      .zone-info-row {
        display: flex; justify-content: space-between; font-size: 13px;
        color: #606266; margin-bottom: 12px;
      }
      .avail-text {
        text-align: center; font-size: 12px;
        color: #909399; margin-top: 6px;
        strong { color: #67c23a; font-size: 14px; }
      }
    }
  }

  .detail-form {
    max-width: 720px;
  }

  .preview-desc {
    margin-top: 8px;
  }

  .step-actions {
    margin-top: 32px;
    padding-top: 20px;
    border-top: 1px solid #ebeef5;
    display: flex;
    justify-content: flex-end;
    gap: 12px;
  }
}
</style>
