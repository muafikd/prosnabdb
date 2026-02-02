<template>
  <div class="deals-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <div class="card-header-top">
            <div>
              <h2>Сделки Bitrix</h2>
              <span class="card-subtitle">Импортированные сделки из Bitrix24 (привязка к КП)</span>
            </div>
            <el-button type="primary" @click="openBitrixSearch">
              <el-icon><Search /></el-icon>
              Импорт из Bitrix24
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="deals"
        stripe
        style="width: 100%; margin-top: 20px"
        :default-sort="{ prop: 'created_at', order: 'descending' }"
      >
        <el-table-column prop="title" label="Название сделки" min-width="220" sortable />
        <el-table-column prop="stage_title" label="Статус" width="180" sortable>
          <template #default="{ row }">
            {{ row.stage_title || row.stage_id || '—' }}
          </template>
        </el-table-column>
        <el-table-column label="Компания" width="200">
          <template #default="{ row }">
            <template v-if="row.client">
              <span>{{ row.client.client_company_name || row.client.client_name || '—' }}</span>
            </template>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="contact_name" label="Контактное лицо" width="180">
          <template #default="{ row }">
            {{ row.contact_name || '—' }}
          </template>
        </el-table-column>
        <el-table-column prop="contact_phone" label="Телефон контакта" width="150">
          <template #default="{ row }">
            {{ row.contact_phone || '—' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="Дата создания" width="140" sortable>
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="КП" width="140">
          <template #default="{ row }">
            <template v-if="row.commercial_proposal_ids && row.commercial_proposal_ids.length">
              <router-link
                v-for="pid in row.commercial_proposal_ids"
                :key="pid"
                :to="{ name: 'proposals' }"
                class="kp-link"
              >
                #{{ pid }}
              </router-link>
            </template>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="Bitrix24" width="100" align="center">
          <template #default="{ row }">
            <el-link
              v-if="row.bitrix_deal_url"
              :href="row.bitrix_deal_url"
              target="_blank"
              type="primary"
              :underline="false"
              title="Открыть сделку в Bitrix24"
            >
              <el-icon><Link /></el-icon>
            </el-link>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && deals.length === 0" class="empty-state">
        <p>Нет импортированных сделок.</p>
        <p class="text-muted">Нажмите «Импорт из Bitrix24» или выберите сделку при создании КП.</p>
      </div>
    </el-card>

    <BitrixSearchModal
      v-model="bitrixSearchVisible"
      default-tab="deal"
      @select-deal="onDealSelected"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Link, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import BitrixSearchModal from '@/components/BitrixSearchModal.vue'
import { dealsAPI, type CrmDeal } from '@/api/deals'
import { format } from 'date-fns'

const loading = ref(false)
const deals = ref<CrmDeal[]>([])
const bitrixSearchVisible = ref(false)

const loadData = async () => {
  loading.value = true
  try {
    deals.value = await dealsAPI.getList()
  } catch (e) {
    console.error(e)
    deals.value = []
  } finally {
    loading.value = false
  }
}

const formatDate = (d: string) => (d ? format(new Date(d), 'dd.MM.yyyy') : '')

const openBitrixSearch = () => {
  bitrixSearchVisible.value = true
}

const onDealSelected = async (payload: { deal_id: number; client_id: number | null; deal_title: string }) => {
  try {
    await loadData()
    ElMessage.success('Сделка выгружена в локальную БД' + (payload.client_id ? ', компания подтянута' : ''))
  } catch (e) {
    console.error('Failed to refresh deals:', e)
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.card-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.card-header-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}
.card-header h2 {
  margin: 0;
}
.card-subtitle {
  font-size: 13px;
  color: #909399;
}
.kp-link {
  margin-right: 8px;
}
.text-muted {
  color: #909399;
}
.empty-state {
  padding: 40px 20px;
  text-align: center;
  color: #606266;
}
.empty-state .text-muted {
  font-size: 13px;
  margin-top: 8px;
}
</style>
