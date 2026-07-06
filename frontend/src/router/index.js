import { createRouter, createWebHistory } from 'vue-router'

// 新页面 - 招聘流程
import JobList from '../views/JobList.vue'
import JobDetail from '../views/JobDetail.vue'
import JobNew from '../views/JobNew.vue'
import CandidateList from '../views/CandidateList.vue'
import CandidateDetail from '../views/CandidateDetail.vue'
import CandidateNew from '../views/CandidateNew.vue'
import Dashboard from '../views/Dashboard.vue'

// 旧页面 - 兼容历史
import AnalysisList from '../views/AnalysisList.vue'
import AnalysisNew from '../views/AnalysisNew.vue'
import AnalysisDetail from '../views/AnalysisDetail.vue'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },

  // ============== 工作台 ==============
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard
  },

  // ============== 新路由：招聘流程 ==============
  {
    path: '/jobs',
    name: 'JobList',
    component: JobList
  },
  {
    path: '/jobs/new',
    name: 'JobNew',
    component: JobNew
  },
  {
    path: '/jobs/:id',
    name: 'JobDetail',
    component: JobDetail
  },
  {
    path: '/candidates',
    name: 'CandidateList',
    component: CandidateList
  },
  {
    path: '/candidates/new',
    name: 'CandidateNew',
    component: CandidateNew
  },
  {
    path: '/candidates/:id',
    name: 'CandidateDetail',
    component: CandidateDetail
  },

  // ============== 旧路由：保留兼容 ==============
  {
    path: '/analysis/list',
    name: 'AnalysisList',
    component: AnalysisList
  },
  {
    path: '/analysis/new',
    name: 'AnalysisNew',
    component: AnalysisNew
  },
  {
    path: '/analysis/:id',
    name: 'AnalysisDetail',
    component: AnalysisDetail
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
