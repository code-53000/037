<template>
  <div class="login-page">
    <div class="login-card card-shadow">
      <div class="login-logo">
        <el-icon :size="48" color="#409eff"><Reading /></el-icon>
      </div>
      <h2 class="login-title">同人漫展平台</h2>
      <p class="login-subtitle">欢迎回来，请登录您的账号</p>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @submit.prevent="handleLogin"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" :prefix-icon="User" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-button
          type="primary"
          class="login-btn"
          :loading="loading"
          @click="handleLogin"
        >
          登 录
        </el-button>
      </el-form>

      <div class="quick-login">
        <div class="quick-label">快速体验（点击填充）</div>
        <div class="quick-btns">
          <el-tag
            v-for="acc in quickAccounts"
            :key="acc.username"
            type="primary"
            effect="plain"
            class="quick-tag"
            @click="fillAccount(acc)"
          >
            {{ acc.label }}
          </el-tag>
        </div>
      </div>

      <div class="login-footer">
        还没有账号？
        <router-link to="/register">立即注册</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const quickAccounts = [
  { username: 'organizer', password: 'comicfair2024', label: '主办方' },
  { username: 'exhibitor1', password: 'comicfair2024', label: '摊主1' },
  { username: 'exhibitor2', password: 'comicfair2024', label: '摊主2' },
  { username: 'visitor1', password: 'comicfair2024', label: '观众1' },
]

function fillAccount(acc) {
  form.username = acc.username
  form.password = acc.password
}

async function handleLogin() {
  await formRef.value?.validate()
  try {
    loading.value = true
    await userStore.login({ username: form.username, password: form.password })
    ElMessage.success('登录成功')
    const redirect = route.query.redirect
    router.push(redirect || '/')
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.login-card {
  width: 100%;
  max-width: 420px;
  padding: 40px;
  border-radius: 12px;
}

.login-logo {
  text-align: center;
  margin-bottom: 16px;
}

.login-title {
  text-align: center;
  margin: 0 0 8px;
  font-size: 24px;
  color: #303133;
}

.login-subtitle {
  text-align: center;
  margin: 0 0 32px;
  color: #909399;
  font-size: 14px;
}

.login-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
  margin-top: 8px;
}

.quick-login {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px dashed #ebeef5;

  .quick-label {
    font-size: 12px;
    color: #909399;
    margin-bottom: 10px;
    text-align: center;
  }

  .quick-btns {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;

    .quick-tag {
      cursor: pointer;
      padding: 6px 12px;
    }
  }
}

.login-footer {
  margin-top: 24px;
  text-align: center;
  font-size: 14px;
  color: #606266;

  a {
    color: #409eff;
  }
}
</style>
