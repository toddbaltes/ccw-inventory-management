<template>
  <div class="app" @keydown.esc="sidebarOpen = false">
    <div
      v-if="sidebarOpen"
      class="sidebar-backdrop"
      aria-hidden="true"
      @click="sidebarOpen = false"
    ></div>

    <aside id="app-sidebar" class="sidebar" :class="{ open: sidebarOpen }">
      <div class="logo">
        <span class="logo-mark" aria-hidden="true"></span>
        <div class="logo-text">
          <h1>{{ t('nav.companyName') }}</h1>
          <span class="subtitle">{{ t('nav.subtitle') }}</span>
        </div>
      </div>
      <nav class="nav-tabs" @click="sidebarOpen = false">
        <router-link to="/" :class="{ active: $route.path === '/' }">
          {{ t('nav.overview') }}
        </router-link>
        <router-link to="/inventory" :class="{ active: $route.path === '/inventory' }">
          {{ t('nav.inventory') }}
        </router-link>
        <router-link to="/orders" :class="{ active: $route.path === '/orders' }">
          {{ t('nav.orders') }}
        </router-link>
        <router-link to="/spending" :class="{ active: $route.path === '/spending' }">
          {{ t('nav.finance') }}
        </router-link>
        <router-link to="/demand" :class="{ active: $route.path === '/demand' }">
          {{ t('nav.demandForecast') }}
        </router-link>
        <router-link to="/reports" :class="{ active: $route.path === '/reports' }">
          Reports
        </router-link>
      </nav>
    </aside>

    <div class="app-main">
      <header class="top-bar">
        <button
          class="menu-button"
          type="button"
          aria-controls="app-sidebar"
          :aria-label="t('nav.toggleNavigation')"
          :aria-expanded="sidebarOpen"
          @click="sidebarOpen = !sidebarOpen"
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M3 5H17M3 10H17M3 15H17" stroke="currentColor" stroke-width="1.75" stroke-linecap="round"/>
          </svg>
        </button>
        <FilterBar />
        <div class="top-bar-actions">
          <LanguageSwitcher />
          <ProfileMenu
            @show-profile-details="showProfileDetails = true"
            @show-tasks="showTasks = true"
          />
        </div>
      </header>
      <main class="main-content">
        <router-view />
      </main>
    </div>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])
    const sidebarOpen = ref(false)

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(loadTasks)

    return {
      t,
      showProfileDetails,
      showTasks,
      sidebarOpen,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style>
.app {
  min-height: 100vh;
}

.sidebar {
  position: fixed;
  top: 0;
  bottom: 0;
  left: 0;
  width: var(--sidebar-width);
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
  padding: var(--space-4) var(--space-4);
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  z-index: var(--z-sidebar);
  overflow-y: auto;
}

.logo {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: calc(var(--topbar-height) - var(--space-4));
  padding: 0 var(--space-2);
  flex-shrink: 0;
}

.logo-mark {
  width: 6px;
  height: 28px;
  border-radius: var(--radius-full);
  background: var(--brand);
  flex-shrink: 0;
}

.logo-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.logo h1 {
  font-size: var(--text-md);
  font-weight: var(--weight-bold);
  color: var(--color-text-strong);
  letter-spacing: var(--tracking-tight);
  line-height: 1.2;
  white-space: nowrap;
}

.subtitle {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.nav-tabs {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.nav-tabs a {
  display: flex;
  align-items: center;
  min-height: 40px;
  padding: 0 var(--space-3);
  color: var(--color-text-muted);
  text-decoration: none;
  font-weight: var(--weight-medium);
  font-size: var(--text-md);
  border-radius: var(--radius-md);
  border-left: 3px solid transparent;
  transition: background-color var(--transition), color var(--transition);
}

.nav-tabs a:hover {
  color: var(--color-text-strong);
  background: var(--color-surface-hover);
}

.nav-tabs a.active {
  color: var(--brand);
  background: var(--brand-tint);
  border-left-color: var(--brand);
  font-weight: var(--weight-semibold);
}

.nav-tabs a:focus-visible {
  box-shadow: var(--focus-ring);
}

.sidebar-backdrop {
  display: none;
}

.app-main {
  margin-left: var(--sidebar-width);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.top-bar {
  position: sticky;
  top: 0;
  z-index: var(--z-topbar);
  display: flex;
  align-items: center;
  gap: var(--space-4);
  min-height: var(--topbar-height);
  padding: var(--space-2) var(--space-6);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.top-bar > .filters-bar {
  flex: 1;
  min-width: 0;
}

.top-bar-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-left: auto;
  flex-shrink: 0;
}

.menu-button {
  display: none;
  align-items: center;
  justify-content: center;
  width: var(--control-height);
  height: var(--control-height);
  background: var(--color-surface);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  color: var(--slate-700);
  cursor: pointer;
  flex-shrink: 0;
  transition: background-color var(--transition);
}

.menu-button:hover {
  background: var(--color-surface-hover);
}

.main-content {
  flex: 1;
  width: 100%;
  max-width: var(--content-max);
  margin: 0 auto;
  padding: var(--space-6) var(--space-8);
  min-width: 0;
}

@media (max-width: 1024px) {
  .sidebar {
    transform: translateX(-100%);
    visibility: hidden;
    transition: transform 0.2s ease, visibility 0s linear 0.2s;
    box-shadow: none;
  }

  .sidebar.open {
    transform: translateX(0);
    visibility: visible;
    transition: transform 0.2s ease, visibility 0s;
    box-shadow: var(--shadow-modal);
  }

  .sidebar-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    background: var(--color-overlay);
    z-index: calc(var(--z-sidebar) - 1);
  }

  .app-main {
    margin-left: 0;
  }

  .menu-button {
    display: inline-flex;
  }

  .top-bar {
    padding: var(--space-2) var(--space-4);
  }

  .main-content {
    padding: var(--space-5) var(--space-4);
  }
}

@media (max-width: 639px) {
  .top-bar {
    position: static;
    flex-wrap: wrap;
  }

  .top-bar > .filters-bar {
    order: 3;
    flex: 1 1 100%;
  }

  .top-bar-actions {
    flex: 1;
    justify-content: flex-end;
  }
}
</style>
