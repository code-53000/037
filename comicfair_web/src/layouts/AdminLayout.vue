<template>
  <el-container class="admin-container">
    <el-aside width="220px" class="admin-aside">
      <div class="aside-header">
        <el-icon :size="24" color="#fff"><Management /></el-icon>
        <span>主办方后台</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#001529"
        text-color="#c0c4cc"
        active-text-color="#ffd04b"
        class="admin-menu"
      >
        <el-menu-item index="/admin">
          <el-icon><DataAnalysis /></el-icon>
          <span>数据总览</span>
        </el-menu-item>
        <el-menu-item index="/admin/exhibitions">
          <el-icon><Calendar /></el-icon>
          <span>展会管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/booths">
          <el-icon><Grid /></el-icon>
          <span>展位管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/applications">
          <el-icon><DocumentChecked /></el-icon>
          <span>摊位申请审核</span>
        </el-menu-item>
        <el-menu-item index="/admin/tickets">
          <el-icon><Money /></el-icon>
          <span>票务管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/checkin">
          <el-icon><CircleCheckFilled /></el-icon>
          <span>入场核验</span>
        </el-menu-item>
        <el-menu-item index="/admin/checkin-records">
          <el-icon><List /></el-icon>
          <span>签到记录</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="admin-header">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
          <el-breadcrumb-item>主办方后台</el-breadcrumb-item>
          <el-breadcrumb-item>{{ route.meta?.title }}</el-breadcrumb-item>
        </el-breadcrumb>
        <div class="header-right">
          <el-tag type="success">{{ currentExhibition?.name || '请选择展会' }}</el-tag>
          <el-select
            v-if="exhibitionStore.list.length"
            v-model="exhibitionStore.currentId"
            size="small"
            style="width: 200px; margin-left: 12px"
            @change="handleExhibitionChange"
          >
            <el-option
              v-for="e in exhibitionStore.list"
              :key="e.id"
              :label="e.name"
              :value="e.id"
            />
          </el-select>
          <el-divider direction="vertical" />
          <span class="user-label">{{ userStore.userInfo?.real_name || userStore.userInfo?.username }}</span>
          <el-button type="danger" link @click="handleLogout">
            <el-icon><SwitchButton /></el-icon>退出
          </el-button>
        </div>
      </el-header>

      <el-main class="admin-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { useExhibitionStore } from '@/stores/exhibition'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const exhibitionStore = useExhibitionStore()

const activeMenu = computed(() => route.path)
const currentExhibition = computed(() => exhibitionStore.getCurrent())

onMounted(async () => {
  if (!exhibitionStore.list.length) {
    await exhibitionStore.loadList()
  }
})

function handleExhibitionChange(id) {
  const found = exhibitionStore.list.find((e) => e.id === id)
  if (found) {
    exhibitionStore.setCurrent(found)
    ElMessage.success(`已切换至 ${found.name}`)
  }
}

function handleLogout() {
  userStore.logout()
  router.push('/')
}
</script>

<style lang="scss" scoped>
.admin-container {
  min-height: 100vh;
}

.admin-aside {
  background: #001529;
  color: #fff;

  .aside-header {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    font-size: 16px;
    font-weight: 600;
    color: #fff;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }

  .admin-menu {
    border-right: none;

    :deep(.el-menu-item) {
      height: 50px;
      line-height: 50px;

      &:hover {
        background: rgba(255, 255, 255, 0.05);
      }

      &.is-active {
        background: rgba(255, 208, 75, 0.15);
      }
    }
  }
}

.admin-header {
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  align-items: center;
  justify-content: space-between;

  .header-right {
    display: flex;
    align-items: center;
    gap: 8px;

    .user-label {
      color: #606266;
    }
  }
}

.admin-main {
  background: #f0f2f5;
  padding: 24px;
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
