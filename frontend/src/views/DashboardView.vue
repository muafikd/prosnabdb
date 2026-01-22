<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h2>Dashboard</h2>
    </div>

    <!-- Stats Cards -->
    <el-row :gutter="20" class="stats-row">
      <!-- Equipment Card -->
      <el-col :span="8">
        <el-card class="stats-card">
          <div class="card-content">
            <div class="card-icon equipment-icon">
              <el-icon :size="40"><Box /></el-icon>
            </div>
            <div class="card-info">
              <h3>Оборудование</h3>
              <p class="card-value">{{ stats.equipment_total }}</p>
              <p class="card-label">Всего позиций в базе</p>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- Proposals Card -->
      <el-col :span="8">
        <el-card class="stats-card">
          <div class="card-content">
            <div class="card-icon proposals-icon">
              <el-icon :size="40"><Document /></el-icon>
            </div>
            <div class="card-info">
              <h3>Коммерческие предложения</h3>
              <p class="card-value">{{ totalProposals }}</p>
              <p class="card-label">Всего создано КП</p>
              <div class="status-indicators">
                <el-tag
                  v-for="stat in stats.proposals_stats"
                  :key="stat.status"
                  :type="getStatusType(stat.status)"
                  size="small"
                  style="margin-right: 5px; margin-top: 5px;"
                >
                  {{ stat.label }}: {{ stat.count }}
                </el-tag>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- Exchange Rates Card -->
      <el-col :span="8">
        <el-card class="stats-card">
          <div class="card-content">
            <div class="card-icon rates-icon">
              <el-icon :size="40"><Money /></el-icon>
            </div>
            <div class="card-info">
              <h3>Мониторинг валют</h3>
              <p class="card-label">Актуальные курсы к KZT</p>
              <div class="rates-list">
                <div
                  v-for="rate in stats.active_rates"
                  :key="rate.currency_from"
                  class="rate-item"
                >
                  <span class="rate-ticker">{{ rate.currency_from }}</span>
                  <span class="rate-value">{{ formatRate(rate.rate_value) }}</span>
                  <span class="rate-time">{{ formatTime(rate.updated_at) }}</span>
                </div>
                <p v-if="stats.active_rates.length === 0" class="no-rates">Нет активных курсов</p>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Chart Row -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="6">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>КП по статусам</span>
            </div>
          </template>
          <div class="chart-container">
            <Pie
              v-if="chartData"
              :data="chartData"
              :options="chartOptions"
            />
            <el-empty v-else description="Нет данных для отображения" />
          </div>
        </el-card>
      </el-col>
      <el-col :span="18">
        <el-card>
          <template #header>
            <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
              <span>Открытые КП с оплатами</span>
              <el-date-picker
                v-model="dateRange"
                type="monthrange"
                range-separator="—"
                start-placeholder="Начало"
                end-placeholder="Конец"
                format="YYYY-MM"
                value-format="YYYY-MM-DD"
                @change="handleDateRangeChange"
                style="width: 240px;"
              />
            </div>
          </template>
          <el-table
            v-loading="loadingProposals"
            :data="activeProposals"
            stripe
            style="width: 100%"
            max-height="400"
          >
            <el-table-column prop="outcoming_number" label="Номер КП" width="150">
              <template #default="{ row }">
                <el-link
                  type="primary"
                  :underline="false"
                  @click="handleProposalClick(row.proposal_id)"
                  style="cursor: pointer;"
                >
                  {{ row.outcoming_number }}
                </el-link>
              </template>
            </el-table-column>
            <el-table-column label="Компания клиента" min-width="200">
              <template #default="{ row }">
                {{ row.client.client_company_name || row.client.client_name || '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="proposal_status" label="Статус" width="130">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.proposal_status)">
                  {{ row.proposal_status_label }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="Сумма и Оплата" width="300">
              <template #default="{ row }">
                <div class="payment-progress-container">
                  <div class="payment-progress-bar">
                    <!-- Gray bar if no payments -->
                    <div
                      v-if="parseFloat(row.paid_amount) === 0"
                      class="payment-progress-no-payment"
                      style="width: 100%;"
                    ></div>
                    <!-- Green bar for paid amount -->
                    <div
                      v-else-if="row.payment_percentage > 0"
                      class="payment-progress-paid"
                      :style="{ width: `${row.payment_percentage}%` }"
                    ></div>
                    <!-- Orange bar for remaining amount -->
                    <div
                      v-if="row.payment_percentage < 100 && parseFloat(row.paid_amount) > 0"
                      class="payment-progress-remaining"
                      :style="{ width: `${100 - row.payment_percentage}%` }"
                    ></div>
                  </div>
                  <div class="payment-progress-text">
                    {{ formatPrice(row.total_sum, 'KZT') }}
                  </div>
                </div>
              </template>
            </el-table-column>
          </el-table>
          <el-empty
            v-if="!loadingProposals && activeProposals.length === 0"
            description="Нет открытых КП за выбранный период"
            style="padding: 40px 0;"
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Box, Document, Money } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { Pie } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from 'chart.js'
import { dashboardAPI, type DashboardStats, type ActiveProposal } from '@/api/dashboard'
import { formatPrice } from '@/utils/formatters'

ChartJS.register(ArcElement, Tooltip, Legend)

const router = useRouter()
const authStore = useAuthStore()
const stats = ref<DashboardStats>({
  equipment_total: 0,
  proposals_stats: [],
  active_rates: [],
})
const loading = ref(false)
const loadingProposals = ref(false)
const activeProposals = ref<ActiveProposal[]>([])

// Date range for filtering proposals (default to current month)
const getCurrentMonthRange = (): [string, string] => {
  const now = new Date()
  const year = now.getFullYear()
  const month = now.getMonth()
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  return [
    firstDay.toISOString().split('T')[0],
    lastDay.toISOString().split('T')[0]
  ]
}

const dateRange = ref<[string, string] | null>(getCurrentMonthRange())

const totalProposals = computed(() => {
  return stats.value.proposals_stats.reduce((sum, stat) => sum + stat.count, 0)
})

const chartData = computed(() => {
  if (!stats.value.proposals_stats || stats.value.proposals_stats.length === 0) {
    return null
  }

  // Status color mapping
  const statusColors: Record<string, string> = {
    draft: '#909399',      // Gray for Черновик
    sent: '#409eff',        // Blue for Отправлено
    accepted: '#67c23a',    // Green for Принято
    rejected: '#f56c6c',    // Red for Отклонено
    negotiating: '#e6a23c', // Orange for В переговорах
    completed: '#606266',   // Dark gray for Завершено
  }

  return {
    labels: stats.value.proposals_stats.map(s => s.label),
    datasets: [
      {
        data: stats.value.proposals_stats.map(s => s.count),
        backgroundColor: stats.value.proposals_stats.map(s => statusColors[s.status] || '#909399'),
        borderWidth: 2,
        borderColor: '#fff',
      },
    ],
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '60%', // Makes it a doughnut chart
  plugins: {
    legend: {
      position: 'bottom' as const,
    },
    tooltip: {
      callbacks: {
        label: function(context: any) {
          const label = context.label || ''
          const value = context.parsed || 0
          const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0)
          const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0
          return `${label}: ${value} (${percentage}%)`
        },
      },
    },
  },
}

const getStatusType = (status: string): string => {
  const typeMap: Record<string, string> = {
    draft: 'info',
    sent: '',
    accepted: 'success',
    rejected: 'danger',
    negotiating: 'warning',
    completed: '',
  }
  return typeMap[status] || ''
}

const formatRate = (value: string): string => {
  const num = parseFloat(value)
  return num.toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const formatTime = (timeStr: string): string => {
  try {
    const date = new Date(timeStr)
    return date.toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return timeStr
  }
}

const fetchStats = async () => {
  loading.value = true
  try {
    const data = await dashboardAPI.getStats()
    stats.value = data
  } catch (error) {
    console.error('Failed to fetch dashboard stats:', error)
    ElMessage.error('Не удалось загрузить статистику')
  } finally {
    loading.value = false
  }
}

const fetchActiveProposals = async () => {
  loadingProposals.value = true
  try {
    const range = dateRange.value || getCurrentMonthRange()
    const [dateFrom, dateTo] = range
    const data = await dashboardAPI.getActiveProposals(dateFrom, dateTo)
    activeProposals.value = data
  } catch (error) {
    console.error('Failed to fetch active proposals:', error)
    ElMessage.error('Не удалось загрузить список КП')
  } finally {
    loadingProposals.value = false
  }
}

const handleDateRangeChange = () => {
  fetchActiveProposals()
}

const handleProposalClick = (proposalId: number) => {
  // Navigate to proposals page with query parameter to open modal
  router.push({
    name: 'proposals',
    query: { edit: proposalId.toString() }
  })
}

onMounted(async () => {
  await Promise.all([fetchStats(), fetchActiveProposals()])
})
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.stats-card {
  height: 100%;
}

.card-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.card-icon {
  width: 80px;
  height: 80px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.equipment-icon {
  background-color: #e3f2fd;
  color: #1976d2;
}

.proposals-icon {
  background-color: #f3e5f5;
  color: #7b1fa2;
}

.rates-icon {
  background-color: #fff3e0;
  color: #e65100;
}

.card-info {
  flex: 1;
}

.card-info h3 {
  margin: 0 0 10px 0;
  color: #303133;
  font-size: 18px;
}

.card-value {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  margin: 5px 0;
}

.card-label {
  color: #909399;
  font-size: 14px;
  margin: 5px 0;
}

.status-indicators {
  margin-top: 10px;
}

.rates-list {
  margin-top: 10px;
  max-height: 200px;
  overflow-y: auto;
}

.rate-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #ebeef5;
}

.rate-item:last-child {
  border-bottom: none;
}

.rate-ticker {
  font-weight: bold;
  color: #303133;
  min-width: 50px;
}

.rate-value {
  color: #409eff;
  font-weight: 500;
  flex: 1;
  text-align: center;
}

.rate-time {
  color: #909399;
  font-size: 12px;
  min-width: 80px;
  text-align: right;
}

.no-rates {
  color: #909399;
  text-align: center;
  padding: 20px;
}

.chart-row {
  margin-top: 20px;
}

.chart-container {
  height: 300px;
  position: relative;
}

.card-header {
  font-weight: 600;
  font-size: 16px;
}

.payment-progress-container {
  position: relative;
  width: 100%;
}

.payment-progress-bar {
  display: flex;
  height: 24px;
  border-radius: 4px;
  overflow: hidden;
  background-color: #f0f0f0;
  position: relative;
}

.payment-progress-paid {
  background-color: #67C23A;
  height: 100%;
  transition: width 0.3s ease;
}

.payment-progress-remaining {
  background-color: #E6A23C;
  height: 100%;
  transition: width 0.3s ease;
}

.payment-progress-no-payment {
  background-color: #909399;
  height: 100%;
}

.payment-progress-text {
  margin-top: 4px;
  font-size: 12px;
  color: #303133;
  font-weight: 500;
}
</style>
