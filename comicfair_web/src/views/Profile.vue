<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">个人中心</h2>
    </div>

    <el-row :gutter="20">
      <el-col :span="8">
        <div class="profile-card card-shadow">
          <div class="avatar-wrap">
            <el-avatar :size="80">
              {{ userStore.userInfo?.real_name?.[0] || userStore.userInfo?.username?.[0] }}
            </el-avatar>
          </div>
          <h3 class="name">{{ userStore.userInfo?.real_name || userStore.userInfo?.username }}</h3>
          <div class="role-wrap">
            <el-tag size="large" type="primary" effect="light">
              {{ userStore.userInfo?.role_display }}
            </el-tag>
            <el-tag v-if="userStore.userInfo?.organization" size="large" effect="plain">
              {{ userStore.userInfo.organization }}
            </el-tag>
          </div>
          <p class="username">@{{ userStore.userInfo?.username }}</p>
          <p class="join-time">加入时间：{{ userStore.userInfo?.date_joined?.slice(0, 10) }}</p>
        </div>
      </el-col>

      <el-col :span="16">
        <div class="form-card card-shadow">
          <h3 class="card-title">修改个人信息</h3>
          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            label-width="100px"
            style="max-width: 500px"
          >
            <el-form-item label="用户名">
              <el-input v-model="form.username" disabled />
            </el-form-item>
            <el-form-item label="真实姓名" prop="real_name">
              <el-input v-model="form.real_name" />
            </el-form-item>
            <el-form-item v-if="userStore.isExhibitor" label="社团/组织" prop="organization">
              <el-input v-model="form.organization" />
            </el-form-item>
            <el-form-item label="手机号" prop="phone">
              <el-input v-model="form.phone" />
            </el-form-item>
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="form.email" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="saving" @click="handleSave">保存修改</el-button>
            </el-form-item>
          </el-form>
        </div>

        <div v-if="quickLinks.length" class="form-card card-shadow" style="margin-top: 20px">
          <h3 class="card-title">快捷入口</h3>
          <div class="links">
            <router-link v-for="l in quickLinks" :key="l.path" :to="l.path" class="link-item">
              <el-icon :size="22" :color="l.color">
                <component :is="l.icon" />
              </el-icon>
              <div>
                <div class="link-name">{{ l.name }}</div>
                <div class="link-desc">{{ l.desc }}</div>
              </div>
              <el-icon><ArrowRight /></el-icon>
            </router-link>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { updateProfile } from '@/api/auth'

const userStore = useUserStore()
const formRef = ref(null)
const saving = ref(false)

const form = reactive({
  username: '',
  real_name: '',
  organization: '',
  phone: '',
  email: '',
})

const rules = {
  real_name: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  phone: [{ pattern: /^1[3-9]\d{9}$/, message: '请输入正确手机号', trigger: 'blur' }],
  email: [{ type: 'email', message: '请输入正确邮箱', trigger: 'blur' }],
}

const quickLinks = computed(() => {
  const links = []
  if (userStore.isExhibitor) {
    links.push({
      path: '/apply', name: '摊位申请',
      desc: '申请展会摊位，提交社团资料',
      icon: 'Shop', color: '#409eff',
    })
    links.push({
      path: '/my-applications', name: '我的申请',
      desc: '查看摊位申请进度和核验码',
      icon: 'Tickets', color: '#e6a23c',
    })
  }
  links.push({
    path: '/tickets', name: '门票购买',
    desc: '购买漫展入场门票',
    icon: 'Ticket', color: '#67c23a',
  })
  links.push({
    path: '/my-tickets', name: '我的门票',
    desc: '查看已购门票和入场凭证',
    icon: 'Document', color: '#f56c6c',
  })
  if (userStore.isOrganizer) {
    links.push({
      path: '/admin', name: '主办方后台',
      desc: '管理展会、摊位、票务、签到',
      icon: 'Management', color: '#909399',
    })
  }
  return links
})

onMounted(() => {
  if (userStore.userInfo) {
    Object.assign(form, {
      username: userStore.userInfo.username,
      real_name: userStore.userInfo.real_name || '',
      organization: userStore.userInfo.organization || '',
      phone: userStore.userInfo.phone || '',
      email: userStore.userInfo.email || '',
    })
  }
})

async function handleSave() {
  await formRef.value?.validate()
  try {
    saving.value = true
    const updated = await updateProfile({ ...form })
    userStore.setUser({ ...userStore.userInfo, ...updated })
    ElMessage.success('保存成功')
  } finally {
    saving.value = false
  }
}
</script>

<style lang="scss" scoped>
.profile-card {
  padding: 32px;
  text-align: center;
  border-radius: 12px;

  .avatar-wrap {
    margin-bottom: 16px;
    :deep(.el-avatar) {
      background: linear-gradient(135deg, #667eea, #764ba2);
      font-size: 30px;
      font-weight: 700;
    }
  }
  .name {
    margin: 0 0 10px;
    font-size: 20px;
  }
  .role-wrap {
    display: flex;
    justify-content: center;
    gap: 8px;
    margin-bottom: 8px;
    flex-wrap: wrap;
  }
  .username {
    color: #909399;
    margin: 4px 0;
  }
  .join-time {
    color: #c0c4cc;
    font-size: 12px;
  }
}

.form-card {
  padding: 24px;
  border-radius: 12px;

  .card-title {
    margin: 0 0 20px;
    font-size: 18px;
    padding-bottom: 12px;
    border-bottom: 2px solid #f0f0f0;
  }

  .links {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;

    .link-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 16px;
      border-radius: 10px;
      background: #fafafa;
      transition: all 0.2s;

      &:hover {
        background: #ecf5ff;
        transform: translateX(2px);
      }

      .link-name {
        font-weight: 600;
        font-size: 14px;
        flex: 1;
      }
      .link-desc {
        font-size: 12px;
        color: #909399;
      }
    }
  }
}
</style>
