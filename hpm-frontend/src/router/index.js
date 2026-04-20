import { createRouter, createWebHistory } from 'vue-router'

// 导入你的页面组件
import Home from '../views/Home.vue'
import CstSweep from '../views/CstSweep.vue' // ✨ 新增：导入扫参组件
import CstOpt from '../views/CstOpt.vue'
import NeuralNet from '../views/NeuralNet.vue'
import DataCenter from '../views/DataCenter.vue'

const routes = [
  { path: '/', redirect: '/home' }, // 默认重定向到主页
  { path: '/home', component: Home, name: 'Home' },
  { path: '/cst-sweep', component: CstSweep, name: 'CstSweep' }, // ✨ 新增：扫参路由
  { path: '/cst-opt', component: CstOpt, name: 'CstOpt' },       // 💡 调整：优化路由
  { path: '/nn', component: NeuralNet, name: 'NeuralNet' },
  { path: '/data-center', component: DataCenter, name: 'DataCenter' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router