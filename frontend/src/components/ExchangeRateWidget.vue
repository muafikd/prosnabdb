<template>
  <div class="exchange-rate-widget">
    <div class="rate-display">
      <span class="rate-date">
        На {{ formatDate(new Date()) }}
        <span v-if="lastUpdatedDisplay"> (обновлено {{ lastUpdatedDisplay }})</span>:
      </span>
      
      <el-select 
        v-model="selectedCurrency" 
        placeholder="Валюта" 
        size="small" 
        style="width: 100px; margin: 0 10px;"
      >
        <el-option
          v-for="code in uniqueCurrencies"
          :key="code"
          :label="code"
          :value="code"
        >
          <span style="float: left">{{ code }}</span>
          <span style="float: right; color: #8492a6; font-size: 13px">
            {{ getFlag(code) }}
          </span>
        </el-option>
      </el-select>

      <span class="rate-value" v-if="currentRate">
        1 {{ selectedCurrency }} = {{ formatPrice(currentRate.rate_value) }} KZT
      </span>
      <span class="rate-value" v-else>
        -
      </span>
    </div>

    <div class="actions">
      <el-tooltip content="Обновить курсы (НБ РК)" placement="bottom">
        <el-button 
          circle 
          size="small" 
          :loading="store.loading" 
          @click="handleSync"
        >
          <el-icon><Refresh /></el-icon>
        </el-button>
      </el-tooltip>

      <el-tooltip content="Добавить валюту" placement="bottom">
        <el-button 
          circle 
          size="small" 
          @click="dialogVisible = true"
        >
          <el-icon><Plus /></el-icon>
        </el-button>
      </el-tooltip>
    </div>

    <!-- Manage Currencies Dialog -->
    <el-dialog
      v-model="dialogVisible"
      title="Управление валютами"
      width="500px"
      append-to-body
    >
      <div style="margin-bottom: 20px;">
        <p style="margin-bottom: 10px;">Добавить валюту:</p>
        <div style="display: flex; gap: 10px;">
          <el-input 
            v-model="newCurrencyCode" 
            placeholder="Код (USD, EUR...)" 
            @keyup.enter="handleAdd" 
            uppercase
          >
            <template #prefix>
              <el-icon><Money /></el-icon>
            </template>
          </el-input>
          <el-button type="primary" :loading="store.loading" @click="handleAdd">
            Добавить
          </el-button>
        </div>
      </div>

      <el-divider>Отслеживаемые валюты</el-divider>

      <div class="currency-list">
        <el-table :data="store.rates" stripe style="width: 100%" max-height="300">
          <el-table-column label="Валюта" width="100">
            <template #default="{ row }">
              <span style="font-size: 16px; margin-right: 5px">{{ getFlag(row.currency_from) }}</span>
              <span>{{ row.currency_from }}</span>
            </template>
          </el-table-column>
          <el-table-column label="Курс (KZT)">
            <template #default="{ row }">
              {{ formatPrice(row.rate_value) }}
            </template>
          </el-table-column>
          <el-table-column label="" width="60" align="center">
            <template #default="{ row }">
              <el-button 
                type="danger" 
                circle 
                size="small" 
                text
                @click="handleDelete(row.rate_id, row.currency_from)"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">Закрыть</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useExchangeRateStore } from '@/stores/exchangeRate'
import { Refresh, Plus, Money, Delete } from '@element-plus/icons-vue'
import { format } from 'date-fns'
import { ElMessageBox } from 'element-plus'
import { formatPrice } from '@/utils/formatters'

const store = useExchangeRateStore()
const selectedCurrency = ref('USD')
const dialogVisible = ref(false)
const newCurrencyCode = ref('')
const lastUpdatedDisplay = computed(() => {
  if (!store.lastUpdated) return ''
  return format(new Date(store.lastUpdated), 'dd.MM.yyyy HH:mm')
})

const uniqueCurrencies = computed(() => {
  const set = new Set<string>()
  store.rates.forEach((r) => set.add(r.currency_from))
  return Array.from(set)
})

const currentRate = computed(() => {
  return store.getRate(selectedCurrency.value)
})

const formatDate = (date: Date) => {
  return format(date, 'dd.MM.yyyy')
}

const getFlag = (code: string) => {
  const flags: Record<string, string> = {
    'USD': '🇺🇸', 'EUR': '🇪🇺', 'RUB': '🇷🇺', 'CNY': '🇨🇳', 'KZT': '🇰🇿',
    'GBP': '🇬🇧', 'TRY': '🇹🇷', 'AED': '🇦🇪', 'JPY': '🇯🇵', 'KRW': '🇰🇷',
    'CHF': '🇨🇭', 'CAD': '🇨🇦', 'AUD': '🇦🇺', 'NZD': '🇳🇿', 'SGD': '🇸🇬',
    'HKD': '🇭🇰', 'SEK': '🇸🇪', 'NOK': '🇳🇴', 'DKK': '🇩🇰', 'PLN': '🇵🇱',
    'CZK': '🇨🇿', 'HUF': '🇭🇺', 'RON': '🇷🇴', 'BGN': '🇧🇬', 'HRK': '🇭🇷',
    'ISK': '🇮🇸', 'UAH': '🇺🇦', 'BYN': '🇧🇾', 'AZN': '🇦🇿', 'AMD': '🇦🇲',
    'GEL': '🇬🇪', 'KGS': '🇰🇬', 'TJS': '🇹🇯', 'UZS': '🇺🇿', 'MDL': '🇲🇩',
    'INR': '🇮🇳', 'BRL': '🇧🇷', 'ZAR': '🇿🇦', 'SAR': '🇸🇦', 'MXN': '🇲🇽',
    'THB': '🇹🇭', 'IDR': '🇮🇩', 'MYR': '🇲🇾', 'VND': '🇻🇳', 'PHP': '🇵🇭'
  }
  return flags[code] || '🌐'
}

const handleSync = async () => {
  await store.syncRates()
}

const handleAdd = async () => {
  if (!newCurrencyCode.value) return
  
  const success = await store.addCurrency(newCurrencyCode.value.toUpperCase())
  if (success) {
    newCurrencyCode.value = ''
    // Не закрываем диалог, чтобы пользователь видел результат в списке
  }
}

const handleDelete = async (rateId: number, currency: string) => {
  try {
    await ElMessageBox.confirm(
      `Вы уверены, что хотите удалить ${currency} из списка отслеживаемых?`,
      'Подтверждение удаления',
      {
        confirmButtonText: 'Удалить',
        cancelButtonText: 'Отмена',
        type: 'warning',
      }
    )
    await store.deleteRate(rateId)
    // Если удалили выбранную валюту, переключаем на другую
    if (selectedCurrency.value === currency) {
       if (store.rates.length > 0) {
         selectedCurrency.value = store.rates[0].currency_from
       } else {
         selectedCurrency.value = ''
       }
    }
  } catch (e) {
    // Cancelled
  }
}

// Initial load
onMounted(async () => {
  if (store.rates.length === 0) {
    await store.fetchRates()
  }
  // Default to USD if available, else first unique
  if (!store.getRate('USD') && uniqueCurrencies.value.length > 0) {
    selectedCurrency.value = uniqueCurrencies.value[0]
  }
})
</script>

<style scoped>
.exchange-rate-widget {
  display: flex;
  align-items: center;
  gap: 15px;
  background: #f5f7fa;
  padding: 5px 15px;
  border-radius: 20px;
  border: 1px solid #e4e7ed;
  margin-right: 20px;
}

.rate-display {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: #606266;
}

.rate-date {
  color: #909399;
  font-size: 12px;
  margin-right: 5px;
}

.rate-value {
  font-weight: 600;
  color: #303133;
  margin-left: 5px;
  min-width: 100px;
}

.actions {
  display: flex;
  gap: 5px;
}
</style>
