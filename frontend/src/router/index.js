import { createRouter, createWebHistory } from 'vue-router'

// 新页面 - 招聘流程
import JobList from '../views/JobList.vue'
import JobDetail from '../views/JobDetail.vue'
import JobNew from '../views/JobNew.vue'
import CandidateList from '../views/CandidateList.vue'
import CandidateDetail from '../views/CandidateDetail.vue'
import CandidateNew from '../views/CandidateNew.vue'
import InterviewList from '../views/InterviewList.vue'
import Dashboard from '../views/Dashboard.vue'
import Settings from '../views/Settings.vue'
import ResumeParseRecords from '../views/ResumeParseRecords.vue'

// 旧页面 - 兼容历史
import AnalysisList from '../views/AnalysisList.vue'
import AnalysisNew from '../views/AnalysisNew.vue'
import AnalysisDetail from '../views/AnalysisDetail.vue'

const routes = [
  {
    path: '/',
    redirect: '/screening'
  },

  // ============== 工作台 ==============
  {
    path: '/screening',
    name: 'ScreeningWorkbench',
    component: Dashboard
  },
  {
    path: '/dashboard',
    redirect: '/screening'
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
    path: '/interviews',
    name: 'InterviewManagement',
    component: InterviewList
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

  // ============== 顶部导航功能入口 ==============
  {
    path: '/reports',
    name: 'ReportCenter',
    component: AnalysisList
  },
  {
    path: '/resume-records',
    name: 'ResumeParseRecords',
    component: ResumeParseRecords
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings
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
