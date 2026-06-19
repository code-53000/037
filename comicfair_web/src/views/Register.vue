<template>
  <div class="login-page">
    <div class="login-card card-shadow">
      <h2 class="login-title">创建账号</h2>
      <p class="login-subtitle">注册后享受完整功能</p>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @submit.prevent="handleRegister"
      >
        <el-form-item label="用户角色" prop="role">
          <el-radio-group v-model="form.role">
            <el-radio value="visitor">
              <el-icon><User /></el-icon>观众
            </el-radio>
            <el-radio value="exhibitor">
              <el-icon><Shop /></el-icon>参展摊主
            </el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名（4-20位）" />
        </el-form-item>
        <el-form-item label="真实姓名" prop="real_name">
          <el-input v-model="form.real_name" placeholder="请输入真实姓名" />
        </el-form-item>
        <el-form-item v-if="form.role === 'exhibitor'" label="社团/组织名称" prop="organization">
          <el-input v-model="form.organization" placeholder="请输入社团或组织名称" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="至少6位" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input v-model="form.confirm_password" type="password" placeholder="再次输入密码" show-password />
        </el-form-item>
        <el-button
          type="primary"
          class="login-btn"
          :loading="loading"
          @click="handleRegister"
        >
          注 册
        </el-button>
      </el-form>

      <div class="login-footer">
        已有账号？
        <router-link to="/login">去登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  role: 'visitor',
  username: '',
  real_name: '',
  organization: '',
  phone: '',
  email: '',
  password: '',
  confirm_password: '',
})

const rules = {
  role: [{ required: true, message: '请选择用户角色', trigger: 'change' }],
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 4, max: 20, message: '长度在 4 到 20 个字符', trigger: 'blur' },
  ],
  real_name: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  organization: [],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' },
  ],
  email: [{ type: 'email', message: '请输入正确的邮箱', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (_, val, cb) => {
        if (val !== form.password) cb(new Error('两次密码不一致'))
        else cb()
      },
      trigger: 'blur',
    },
  ],
}

async function handleRegister() {
  await formRef.value?.validate()
  try {
    loading.value = true
    const data = { ...form }
    if (data.role !== 'exhibitor') delete data.organization
    await userStore.register(data)
    ElMessage.success('注册成功，请登录')
    router.push('/login')
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
  padding: 40px 24px;
}
.login-card {
  width: 100%;
  max-width: 500px;
  padding: 40px;
  border-radius: 12px;
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
