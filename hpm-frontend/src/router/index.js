import { createRouter, createWebHistory } from 'vue-router'

// 导入你的页面组件
import Home from '../views/Home.vue'
import CstSweep from '../views/CstSweep.vue'
import CstOpt from '../views/CstOpt.vue'
import NeuralNet from '../views/NeuralNet.vue'
import DataCenter from '../views/DataCenter.vue'
import LiteratureAssistant from '../views/LiteratureAssistant.vue'

const routes = [
  { path: '/', redirect: '/home' }, // 默认重定向到主页
  { path: '/home', component: Home, name: 'Home' },
  { path: '/cst-sweep', component: CstSweep, name: 'CstSweep' },
  { path: '/cst-opt', component: CstOpt, name: 'CstOpt' },
  { path: '/nn', component: NeuralNet, name: 'NeuralNet' },
  { path: '/literature', component: LiteratureAssistant, name: 'LiteratureAssistant' },
  { path: '/data-center', component: DataCenter, name: 'DataCenter' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router