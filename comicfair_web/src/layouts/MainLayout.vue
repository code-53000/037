<template>
  <div class="page-container">
    <el-header class="app-header">
      <div class="header-inner">
        <div class="logo-area" @click="$router.push('/')">
          <el-icon :size="28" color="#409eff"><Reading /></el-icon>
          <span class="logo-text">同人漫展平台</span>
        </div>
        <el-menu
          mode="horizontal"
          :default-active="activeMenu"
          class="app-menu"
          router
        >
          <el-menu-item index="/">首页</el-menu-item>
          <el-menu-item index="/booth-map">展位图</el-menu-item>
          <el-menu-item index="/tickets">购票</el-menu-item>
          <el-menu-item v-if="userStore.isExhibitor || userStore.isOrganizer" index="/apply">
            摊位申请
          </el-menu-item>
          <el-menu-item v-if="userStore.isOrganizer" index="/admin">
            主办方后台
          </el-menu-item>
        </el-menu>
        <div class="user-area">
          <template v-if="userStore.isLoggedIn">
            <el-dropdown @command="handleCommand">
              <span class="user-info">
                <el-avatar :size="32">
                  {{ userStore.userInfo?.real_name?.[0] || userStore.userInfo?.username?.[0] }}
                </el-avatar>
                <span class="username">{{ userStore.userInfo?.real_name || userStore.userInfo?.username }}</span>
                <el-tag size="small" type="primary" effect="light">
                  {{ userStore.userInfo?.role_display }}
                </el-tag>
                <el-icon><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">
                    <el-icon><User /></el-icon>个人中心
                  </el-dropdown-item>
                  <el-dropdown-item v-if="userStore.isExhibitor" command="my-applications">
                    <el-icon><Tickets /></el-icon>我的申请
                  </el-dropdown-item>
                  <el-dropdown-item command="my-tickets">
                    <el-icon><Ticket /></el-icon>我的门票
                  </el-dropdown-item>
                  <el-dropdown-item v-if="userStore.isOrganizer" command="admin">
                    <el-icon><Setting /></el-icon>管理后台
                  </el-dropdown-item>
                  <el-dropdown-item divided command="logout">
                    <el-icon><SwitchButton /></el-icon>退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
          <template v-else>
            <el-button type="primary" @click="$router.push('/login')">登录</el-button>
            <el-button @click="$router.push('/register')">注册</el-button>
          </template>
        </div>
      </div>
    </el-header>

    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <el-footer class="app-footer">
      <div class="footer-inner">
        <p>© 2026 同人漫展管理平台 · ComicFair</p>
        <p class="muted">让漫展更简单、更有序</p>
      </div>
    </el-footer>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)

function handleCommand(command) {
  if (command === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }).then(() => {
      userStore.logout()
      ElMessage.success('已退出登录')
      router.push('/')
    }).catch(() => {})
    return
  }
  const routeMap = {
    'profile': '/profile',
    'my-applications': '/my-applications',
    'my-tickets': '/my-tickets',
    'admin': '/admin',
  }
  if (routeMap[command]) router.push(routeMap[command])
}
</script>

<style lang="scss" scoped>
.app-header {
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  padding: 0;
  height: 64px;

  .header-inner {
    max-width: 1440px;
    margin: 0 auto;
    height: 100%;
    display: flex;
    align-items: center;
    padding: 0 24px;
    gap: 32px;
  }

  .logo-area {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    font-weight: 700;
    font-size: 18px;
    color: #303133;
  }

  .app-menu {
    flex: 1;
    border-bottom: none;
  }

  .user-area {
    display: flex;
    align-items: center;
    gap: 12px;

    .user-info {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      padding: 8px 12px;
      border-radius: 6px;
      transition: background 0.2s;

      &:hover {
        background: #f5f7fa;
      }

      .username {
        font-weight: 500;
      }
    }
  }
}

.app-footer {
  background: #fff;
  border-top: 1px solid #ebeef5;
  padding: 24px;
  text-align: center;
  color: #909399;
  font-size: 13px;
  margin-top: 48px;

  .footer-inner {
    max-width: 1440px;
    margin: 0 auto;

    p {
      margin: 4px 0;
    }
    .muted {
      color: #c0c4cc;
      font-size: 12px;
    }
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
