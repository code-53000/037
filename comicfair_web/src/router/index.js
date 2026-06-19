import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false, title: '登录' },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { requiresAuth: false, title: '注册' },
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('@/views/Home.vue'),
        meta: { requiresAuth: false, title: '首页' },
      },
      {
        path: 'exhibition/:id',
        name: 'ExhibitionDetail',
        component: () => import('@/views/ExhibitionDetail.vue'),
        meta: { requiresAuth: false, title: '展会详情' },
      },
      {
        path: 'booth-map',
        name: 'BoothMap',
        component: () => import('@/views/BoothMap.vue'),
        meta: { requiresAuth: false, title: '展位图' },
      },
      {
        path: 'apply',
        name: 'BoothApply',
        component: () => import('@/views/exhibitor/BoothApply.vue'),
        meta: { requiresAuth: true, role: 'exhibitor', title: '摊位申请' },
      },
      {
        path: 'my-applications',
        name: 'MyApplications',
        component: () => import('@/views/exhibitor/MyApplications.vue'),
        meta: { requiresAuth: true, role: 'exhibitor', title: '我的申请' },
      },
      {
        path: 'tickets',
        name: 'TicketBuy',
        component: () => import('@/views/visitor/TicketBuy.vue'),
        meta: { requiresAuth: false, title: '购票' },
      },
      {
        path: 'my-tickets',
        name: 'MyTickets',
        component: () => import('@/views/visitor/MyTickets.vue'),
        meta: { requiresAuth: true, title: '我的门票' },
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/Profile.vue'),
        meta: { requiresAuth: true, title: '个人中心' },
      },
    ],
  },
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresAuth: true, role: 'organizer' },
    children: [
      {
        path: '',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/Dashboard.vue'),
        meta: { title: '数据总览' },
      },
      {
        path: 'exhibitions',
        name: 'AdminExhibitions',
        component: () => import('@/views/admin/Exhibitions.vue'),
        meta: { title: '展会管理' },
      },
      {
        path: 'booths',
        name: 'AdminBooths',
        component: () => import('@/views/admin/Booths.vue'),
        meta: { title: '展位管理' },
      },
      {
        path: 'applications',
        name: 'AdminApplications',
        component: () => import('@/views/admin/Applications.vue'),
        meta: { title: '摊位申请审核' },
      },
      {
        path: 'tickets',
        name: 'AdminTickets',
        component: () => import('@/views/admin/Tickets.vue'),
        meta: { title: '票务管理' },
      },
      {
        path: 'checkin',
        name: 'AdminCheckin',
        component: () => import('@/views/admin/Checkin.vue'),
        meta: { title: '入场核验' },
      },
      {
        path: 'checkin-records',
        name: 'AdminCheckinRecords',
        component: () => import('@/views/admin/CheckinRecords.vue'),
        meta: { title: '签到记录' },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { title: '页面不存在' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  document.title = to.meta?.title ? `${to.meta.title} - 同人漫展平台` : '同人漫展平台'

  if (to.meta?.requiresAuth && !userStore.isLoggedIn) {
    return next({ path: '/login', query: { redirect: to.fullPath } })
  }

  if (to.meta?.role && userStore.role && userStore.role !== to.meta.role) {
    if (to.meta.role === 'organizer' && !userStore.isOrganizer) {
      return next('/')
    }
    if (to.meta.role === 'exhibitor' && !(userStore.isExhibitor || userStore.isOrganizer)) {
      return next('/')
    }
  }

  if ((to.path === '/login' || to.path === '/register') && userStore.isLoggedIn) {
    return next('/')
  }

  if (userStore.token && !userStore.userInfo) {
    try {
      await userStore.fetchUser()
    } catch (e) {
      userStore.logout()
      return next('/login')
    }
  }

  next()
})

export default router
