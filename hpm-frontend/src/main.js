import { createApp } from 'vue'
import App from './App.vue'
import './assets/naive-theme-overrides.css'
import router from './router' // 引入路由
import naive from 'naive-ui' // 引入整个 naive-ui 库

const app = createApp(App)
app.use(router) // 挂载路由
app.use(naive)
app.mount('#app')