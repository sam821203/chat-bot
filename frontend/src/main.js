import './assets/main.css'

import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'

import App from './App.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/chat' },
    { path: '/chat/:threadId?', name: 'Chat', component: App },
  ],
})

const app = createApp(App)
app.use(router)
app.mount('#app')
