<template>
  <div class="proposal-constructor-view">
    <div v-if="!selectedProposal" class="list-mode">
      <el-card>
        <template #header>
          <div class="card-header">
            <h2>Конструктор коммерческих предложений</h2>
            <el-button type="primary" @click="openCreateModal">
              <el-icon><Plus /></el-icon>
              Создать верстку
            </el-button>
            <el-button @click="openSectionLibrary">
              <el-icon><List /></el-icon>
              Библиотека разделов
            </el-button>
          </div>
        </template>

        <div class="search-bar">
          <el-input
            v-model="searchQuery"
            placeholder="Поиск по номеру или названию КП"
            clearable
            @input="handleSearch"
            style="width: 300px"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>

        <el-table
          v-loading="loading"
          :data="proposals"
          style="width: 100%; margin-top: 20px"
          border
        >
          <el-table-column prop="outcoming_number" label="Номер КП" width="180" />
          <el-table-column prop="proposal_date" label="Дата" width="120" />
          <el-table-column prop="client_name" label="Клиент" min-width="200">
            <template #default="scope">
              {{ scope.row.client?.client_name }}
            </template>
          </el-table-column>
          <el-table-column prop="total_price" label="Сумма" width="150">
             <template #default="scope">
               {{ scope.row.total_price }} {{ scope.row.currency_ticket }}
             </template>
          </el-table-column>
          <el-table-column prop="template_status" label="Статус верстки" width="150" align="center">
            <template #default="scope">
              <el-tag :type="getStatusType(scope.row.template_status)">
                {{ getStatusLabel(scope.row.template_status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="Действия" width="150" align="center">
            <template #default="scope">
              <el-button 
                type="primary" 
                size="small" 
                @click="selectProposal(scope.row)"
                :disabled="scope.row.template_status === 'Not Created'"
              >
                <el-icon><Edit /></el-icon>
                Редактировать
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- Initialize Modal -->
      <el-dialog
        v-model="dialogVisible"
        title="Создание верстки КП"
        width="600px"
        align-center
      >
        <div class="dialog-content">
          <p style="margin-bottom: 10px;">Выберите коммерческое предложение для создания макета:</p>
          <el-select
            v-model="selectedProposalId"
            filterable
            remote
            reserve-keyword
            placeholder="Введите номер КП или клиента"
            :remote-method="searchProposalsForSelect"
            :loading="selectLoading"
            style="width: 100%"
            value-key="proposal_id"
          >
            <el-option
              v-for="item in selectOptions"
              :key="item.proposal_id"
              :label="item.outcoming_number ? `${item.outcoming_number} - ${item.client?.client_name || 'Без клиента'}` : `КП без номера (${item.client?.client_name || 'Без клиента'})`"
              :value="item.proposal_id"
            >
              <div class="option-row">
                <span class="option-number">{{ item.outcoming_number || 'Нет номера' }}</span>
                <span class="option-client">{{ item.client?.client_name || 'Без клиента' }}</span>
                <span class="option-date">{{ formatDate(item.proposal_date) }}</span>
              </div>
            </el-option>
          </el-select>
        </div>
        <template #footer>
          <div class="dialog-footer">
            <el-button @click="dialogVisible = false">Отмена</el-button>
            <el-button type="primary" @click="createTemplateAndGo" :disabled="!selectedProposalId">
              Перейти к верстке
            </el-button>
          </div>
        </template>
      </el-dialog>

    </div>

    <!-- Editor Mode -->
    <div v-else class="editor-mode">
       <div class="editor-header">
         <el-button @click="clearSelection" text circle class="back-button">
           <el-icon><ArrowLeft /></el-icon>
         </el-button>
         <div class="header-content">
           <div class="header-top-row">
             <div class="header-left-group">
               <el-button @click="refreshDataPackage" type="warning" :loading="refreshingData">Обновить данные из КП</el-button>
               <el-button @click="forceSave" type="primary" :loading="saving">Сохранить</el-button>
               <el-checkbox v-model="isFinal" label="Готово к отправке" @change="debouncedSave"/>
               <span v-if="saving" class="saving-indicator">Сохранение...</span>
             </div>
             <div class="header-right-group">
               <el-dropdown @command="handleExport">
                 <el-button>Скачать <el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
                 <template #dropdown>
                   <el-dropdown-menu>
                     <el-dropdown-item command="pdf">Скачать PDF</el-dropdown-item>
                     <el-dropdown-item command="docx">Скачать DOCX</el-dropdown-item>
                   </el-dropdown-menu>
                 </template>
               </el-dropdown>
             </div>
           </div>
           <div class="header-title-row">
             <span class="text-large font-600 mr-3">
               Редактор макета КП: {{ selectedProposal.outcoming_number }}
             </span>
             <el-tag :type="templateData?.is_final ? 'success' : 'warning'" class="ml-2">
                {{ templateData?.is_final ? 'Готово' : 'Черновик' }}
             </el-tag>
           </div>
         </div>
       </div>

       <div class="workspace-container">
          <!-- A4 Page Simulation -->
          <div class="a4-page" ref="a4Page">
              <ProposalHeader 
                :header-data="templateData?.header_data" 
                @update:headerData="updateHeaderData"
              />
              
              <!-- Proposal Number and Date - Right Aligned -->
              <div class="proposal-meta-info" style="text-align: right; margin-bottom: 20px;">
                  <span class="meta-text" style="font-weight: bold; font-size: 11pt;">Исх. № {{ proposalDataPackage?.proposal?.number }} от {{ formatDate(proposalDataPackage?.proposal?.date) }}</span>
              </div>

              <div class="page-header" style="text-align: left; border-bottom: none;">
                 <!-- Editable Proposal Title -->
                  <div class="title-container">
                    <div 
                      class="editable-title" 
                      contenteditable="true" 
                      style="font-size: 18pt; font-weight: bold; white-space: pre-wrap; outline: none; border: 1px dashed transparent; transition: border 0.3s;"
                      @input="updateProposalHeader($event)"
                      @focus="($event.target as HTMLElement).style.borderColor = '#dcdfe6'"
                      @blur="($event.target as HTMLElement).style.borderColor = 'transparent'"
                    >
                      {{ proposalDataPackage?.proposal?.header || 'Коммерческое предложение' }}
                    </div>
                    <!-- Simple font size control could go here if needed, but per request just editing text/layout is focus -->
                  </div>
              </div>

              <div class="blocks-area">
                  <div 
                    v-for="(block, index) in templateBlocks" 
                    :key="index" 
                    class="block-wrapper"
                    :style="{ marginBottom: (block.spacing !== undefined ? block.spacing : 15) + 'mm' }"
                  >
                      <!-- Block Controls (Hover) -->
                      <div class="block-controls">
                          <el-button size="small" circle text @click="moveBlock(index, -1)" :disabled="index === 0"><el-icon><ArrowUp /></el-icon></el-button>
                          <el-button size="small" circle text @click="moveBlock(index, 1)" :disabled="index === templateBlocks.length - 1"><el-icon><ArrowDown /></el-icon></el-button>
                          <el-divider style="margin: 4px 0" />
                          <el-popover placement="left" :width="160" trigger="hover">
                            <template #reference>
                              <el-button size="small" circle text><el-icon><Sort /></el-icon></el-button>
                            </template>
                            <div class="spacing-presets">
                              <p style="margin: 0 0 8px 0; font-size: 12px; font-weight: bold;">Отступ:</p>
                              <el-radio-group v-model="block.spacing" size="small" @change="debouncedSave">
                                <el-radio-button :label="5">5мм</el-radio-button>
                                <el-radio-button :label="15">15мм</el-radio-button>
                                <el-radio-button :label="30">30мм</el-radio-button>
                              </el-radio-group>
                            </div>
                          </el-popover>
                          <el-button size="small" circle text type="danger" @click="removeBlock(index)"><el-icon><Delete /></el-icon></el-button>
                      </div>

                      <!-- Block Title - Hide for total_price_table placeholder -->
                      <div class="block-title-edit" v-if="block.content !== '{total_price_table}'">
                          <input v-model="block.title" class="title-input" placeholder="Заголовок раздела (опционально)" @input="debouncedSave" />
                      </div>

                      <!-- Dynamic Content -->
                      <div class="block-content">
                          <!-- If Placeholder detected, render component -->
                          <div v-if="isPlaceholder(block.content)" class="component-renderer">
                              <component 
                                :is="getComponentForPlaceholder(block.content)"
                                  :data-package="proposalDataPackage"
                                  :column-widths="block.columnWidths"
                                  @update:columnWidths="updateBlockColumnWidths(index, $event)"
                                />
                          </div>
                          <!-- Else render Editable Text Area -->
                          <div v-else-if="block.content !== undefined">
                              <!-- Simple textarea with auto-grow replacement or contenteditable -->
                               <div 
                                  class="editable-text"
                                  contenteditable="true"
                                  @input="updateBlockContent(index, $event)"
                               >
                                  {{ block.content }}
                               </div>
                               <!-- Helper buttons to insert placeholders -->
                               <div class="text-controls" v-if="!block.content || block.content === '' || block.content === 'Текст...'" >
                                  <el-tag 
                                    v-for="ph in placeholders" 
                                    :key="ph.tag" 
                                    class="placeholder-tag"
                                    @click="replaceBlockContent(index, ph.tag)"
                                  >
                                    {{ ph.label }}
                                  </el-tag>
                               </div>
                          </div>
                      </div>
                  </div>

                  <!-- Empty State / Add Block -->
                  <div class="add-section-area">
                      <el-button type="primary" plain style="width: 100%" @click="addBlock">
                         <el-icon><Plus /></el-icon> Добавить раздел
                      </el-button>
                      <el-button plain style="width: 100%; margin: 10px 0 0 0;" @click="openSelectTemplateModal">
                         <el-icon><List /></el-icon> Добавить из библиотеки
                      </el-button>
                  </div>
              </div>
          </div>
       </div>
    </div>

    <!-- Modals (Global) -->
    <!-- Section Library Modal -->
    <el-dialog
      v-model="libraryVisible"
      title="Библиотека разделов"
      width="800px"
      align-center
    >
      <div class="library-header" style="margin-bottom: 20px; text-align: right;">
         <el-button type="primary" @click="openCreateTemplateModal">
            <el-icon><Plus /></el-icon> Создать шаблон
         </el-button>
      </div>
      
      <el-table :data="sectionTemplates" border v-loading="libraryLoading">
         <el-table-column prop="title" label="Заголовок" width="200" />
         <el-table-column prop="name" label="Тех. название" width="200" />
         <el-table-column prop="text" label="Контент" show-overflow-tooltip />
         <el-table-column label="Действия" width="100" align="center">
            <template #default="scope">
               <el-button size="small" type="danger" circle @click="deleteSectionTemplate(scope.row.id)">
                  <el-icon><Delete /></el-icon>
               </el-button>
            </template>
         </el-table-column>
      </el-table>
    </el-dialog>

    <!-- Create/Edit Section Template Modal -->
    <el-dialog
      v-model="templateModalVisible"
      title="Создание шаблона раздела"
      width="600px"
      align-center
    >
       <el-form label-position="top">
          <el-form-item label="Техническое название (например, warranty_v1)">
             <el-input v-model="newTemplate.name" placeholder="Уникальное имя" />
          </el-form-item>
          <el-form-item label="Заголовок раздела (для КП)">
             <el-input v-model="newTemplate.title" placeholder="Пример: Гарантийные обязательства" />
          </el-form-item>
          <el-form-item label="Текст раздела">
             <el-input 
               v-model="newTemplate.text" 
               type="textarea" 
               :rows="5" 
               placeholder="Введите текст раздела..." 
             />
          </el-form-item>
       </el-form>
       <template #footer>
          <div class="dialog-footer">
             <el-button @click="templateModalVisible = false">Отмена</el-button>
             <el-button type="primary" @click="saveSectionTemplate" :loading="savingTemplate">
                Сохранить
             </el-button>
          </div>
       </template>
    </el-dialog>
    
    <!-- Select Template for Insertion Modal -->
    <el-dialog
      v-model="selectTemplateVisible"
      title="Выберите шаблон для вставки"
      width="600px"
      align-center
    >
      <el-table :data="sectionTemplates" border highlight-current-row @current-change="handleTemplateSelection" style="cursor: pointer">
         <el-table-column prop="title" label="Заголовок" />
         <el-table-column prop="text" label="Текст (превью)" width="300" show-overflow-tooltip />
      </el-table>
      <template #footer>
         <div class="dialog-footer">
            <el-button @click="selectTemplateVisible = false">Отмена</el-button>
            <el-button type="primary" @click="insertSelectedTemplate" :disabled="!templateToInsert">
               Вставить
            </el-button>
         </div>
      </template>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, defineAsyncComponent } from 'vue'
import { useRoute } from 'vue-router'
import { Search, Edit, Delete, ArrowUp, ArrowDown, Plus, List, Sort, ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus'
import axios from 'axios'
import Cookies from 'js-cookie'

// Async components
const ProposalHeader = defineAsyncComponent(() => import('@/components/constructor/ProposalHeader.vue'))
const ProposalPricesTable = defineAsyncComponent(() => import('@/components/constructor/ProposalPricesTable.vue'))
const ProposalDetailsTable = defineAsyncComponent(() => import('@/components/constructor/ProposalDetailsTable.vue'))
const ProposalSpecsTable = defineAsyncComponent(() => import('@/components/constructor/ProposalSpecsTable.vue'))
const ProposalTechProcess = defineAsyncComponent(() => import('@/components/constructor/ProposalTechProcess.vue'))
const ProposalTotalTable = defineAsyncComponent(() => import('@/components/constructor/ProposalTotalTable.vue'))
const AdditionalServicesTable = defineAsyncComponent(() => import('@/components/constructor/AdditionalServicesTable.vue'))
const ProposalPhotoGrid = defineAsyncComponent(() => import('@/components/constructor/ProposalPhotoGrid.vue'))

// --- State ---
const proposals = ref([])
const loading = ref(false)
const searchQuery = ref('')
const selectedProposal = ref<any>(null)
const templateData = ref<any>(null) 
const templateBlocks = ref<any[]>([])
const proposalDataPackage = ref<any>(null)
const saving = ref(false)
const refreshingData = ref(false)
const isFinal = ref(false)

// Section Library State
const libraryVisible = ref(false)
const libraryLoading = ref(false)
const sectionTemplates = ref<any[]>([])
const templateModalVisible = ref(false)
const savingTemplate = ref(false)
const newTemplate = ref({ name: '', title: '', text: '' })
const logoInput = ref<HTMLInputElement | null>(null)

// Insert Template State
const selectTemplateVisible = ref(false)
const templateToInsert = ref<any>(null)

// Modal State
const dialogVisible = ref(false)
const selectedProposalId = ref(null)
const selectOptions = ref<any[]>([])
const selectLoading = ref(false)
const route = useRoute()

const createTemplate = async (proposalId: number) => {
   const token = Cookies.get('access_token')
   return await axios.post('/api/proposal-templates/', {
       proposal: proposalId,
       layout_data: [
          { title: 'Введение', content: 'Уважаемые партнеры! Предлагаем вам ознакомиться с нашим предложением.' },
          { title: 'Список оборудования', content: '{equipment_list}' },
          { title: 'Характеристики', content: '{equipment_specs}' },
          { title: 'Итого', content: '{total_price_table}' }
       ]
    }, { headers: { Authorization: `Bearer ${token}` } })
}

const placeholders = [
    { tag: '{equipment_list}', label: 'Таблица цен', component: ProposalPricesTable },
    { tag: '{equipment_details}', label: 'Детали', component: ProposalDetailsTable },
    { tag: '{equipment_specs}', label: 'Спецификация', component: ProposalSpecsTable },
    { tag: '{equipment_tech_process}', label: 'Техпроцесс', component: ProposalTechProcess },
    { tag: '{additional_services_table}', label: 'Доп. услуги', component: AdditionalServicesTable },
    { tag: '{equipment_photo_grid}', label: 'Фотогалерея', component: ProposalPhotoGrid },
    { tag: '{total_price_table}', label: 'Итого', component: ProposalTotalTable },
]

// --- Helper Methods ---
const getStatusLabel = (status: string) => {
   const map: Record<string, string> = { 'Ready': 'Готово', 'Draft': 'Черновик', 'Not Created': 'Не создано' }
   return map[status] || status
}

const getStatusType = (status: string) => {
   const map: Record<string, string> = { 'Ready': 'success', 'Draft': 'warning', 'Not Created': 'info' }
   return map[status] || 'info'
}

const formatDate = (dateStr: string) => {
    if (!dateStr) return ''
    return new Date(dateStr).toLocaleDateString('ru-RU')
}

// --- Methods for List ---
const openCreateModal = () => {
   dialogVisible.value = true
   searchProposalsForSelect('')
}

const searchProposalsForSelect = async (query: string) => {
   selectLoading.value = true
   const token = Cookies.get('access_token')
   try {
      const response = await axios.get('/api/commercial-proposals/', {
         headers: { Authorization: `Bearer ${token}` },
         params: { search: query }
      })
      if (response.data.results) selectOptions.value = response.data.results
      else selectOptions.value = response.data
   } catch (e) { console.error(e) } finally { selectLoading.value = false }
}

const createTemplateAndGo = async () => {
   if (!selectedProposalId.value) return
   loading.value = true
   const token = Cookies.get('access_token')
   try {
        const foundOption = selectOptions.value.find(o => o.proposal_id === selectedProposalId.value)
        if (foundOption && foundOption.template_status !== 'Not Created') {
            await selectProposal(foundOption)
            dialogVisible.value = false
            return
        }

        const createResp = await axios.post('/api/proposal-templates/', {
           proposal: selectedProposalId.value,
           layout_data: [
              { title: 'Введение', content: 'Уважаемые партнеры! Предлагаем вам ознакомиться с нашим предложением.' },
              { title: 'Список оборудования', content: '{equipment_list}' },
              { title: 'Характеристики', content: '{equipment_specs}' },
              { title: 'Итого', content: '{total_price_table}' }
           ]
        }, { headers: { Authorization: `Bearer ${token}` } })
        
        selectedProposal.value = selectOptions.value.find(o => o.proposal_id === selectedProposalId.value)
        templateData.value = createResp.data
        templateBlocks.value = createResp.data.layout_data || []
        proposalDataPackage.value = createResp.data.data_package
        isFinal.value = createResp.data.is_final
        dialogVisible.value = false

   } catch(e) {
       console.error(e)
       ElMessage.error('Ошибка создания верстки')
   } finally { loading.value = false }
}

const fetchProposals = async () => {
  loading.value = true
  const token = Cookies.get('access_token')
  try {
     const response = await axios.get('/api/commercial-proposals/', {
        headers: { Authorization: `Bearer ${token}` },
        params: { search: searchQuery.value }
     })
     if (response.data.results) proposals.value = response.data.results
     else proposals.value = response.data
  } catch (e) {
     console.error(e)
     ElMessage.error('Ошибка загрузки КП')
  } finally { loading.value = false }
}

const handleSearch = () => { fetchProposals() }

// --- Section Library Methods ---
const fetchSectionTemplates = async () => {
    libraryLoading.value = true
    const token = Cookies.get('access_token')
    try {
        const response = await axios.get('/api/section-templates/', {
            headers: { Authorization: `Bearer ${token}` }
        })
        if (response.data.results) sectionTemplates.value = response.data.results
        else sectionTemplates.value = response.data
    } catch (e) {
        console.error(e)
        ElMessage.error('Ошибка загрузки шаблонов')
    } finally {
        libraryLoading.value = false
    }
}

const openSectionLibrary = () => {
    libraryVisible.value = true
    fetchSectionTemplates()
}

const deleteSectionTemplate = async (id: number) => {
    try {
        await ElMessageBox.confirm('Вы уверены, что хотите удалить этот шаблон?', 'Внимание', {
            confirmButtonText: 'Удалить',
            cancelButtonText: 'Отмена',
            type: 'warning'
        })
        
        const token = Cookies.get('access_token')
        await axios.delete(`/api/section-templates/${id}/`, {
            headers: { Authorization: `Bearer ${token}` }
        })
        ElMessage.success('Шаблон удален')
        fetchSectionTemplates()
    } catch (e) {
        if (e !== 'cancel') {
             console.error(e)
             ElMessage.error('Ошибка удаления')
        }
    }
}

const openCreateTemplateModal = () => {
    newTemplate.value = { name: '', title: '', text: '' }
    templateModalVisible.value = true
}

const saveSectionTemplate = async () => {
    if (!newTemplate.value.name || !newTemplate.value.title) {
        ElMessage.warning('Заполните обязательные поля')
        return
    }
    savingTemplate.value = true
    const token = Cookies.get('access_token')
    try {
        await axios.post('/api/section-templates/', newTemplate.value, {
            headers: { Authorization: `Bearer ${token}` }
        })
        ElMessage.success('Шаблон создан')
        templateModalVisible.value = false
        fetchSectionTemplates()
    } catch (e) {
        console.error(e)
        ElMessage.error('Ошибка создания шаблона')
    } finally {
        savingTemplate.value = false
    }
}

const openSelectTemplateModal = () => {
    selectTemplateVisible.value = true
    fetchSectionTemplates() // Refresh list
    templateToInsert.value = null
}

const handleTemplateSelection = (val: any) => {
    templateToInsert.value = val
}

const insertSelectedTemplate = () => {
    if (!templateToInsert.value) return
    
    // Add new block with template content
    templateBlocks.value.push({
        title: templateToInsert.value.title,
        content: templateToInsert.value.text
    })
    
    selectTemplateVisible.value = false
    debouncedSave()
    ElMessage.success('Раздел добавлен')
}

// --- Methods for Editor ---
const selectProposal = async (proposal: any) => {
   selectedProposal.value = proposal
   loading.value = true
   const token = Cookies.get('access_token')
   
   try {
     const response = await axios.get('/api/proposal-templates/', {
        headers: { Authorization: `Bearer ${token}` },
        params: { proposal: proposal.proposal_id }
     })
     
     let found = null
     if (response.data.results && response.data.results.length > 0) {
         found = response.data.results[0]
     } else if (Array.isArray(response.data) && response.data.length > 0) {
         found = response.data[0]
     }

     if (found) {
        templateData.value = found
        templateBlocks.value = found.layout_data || []
        proposalDataPackage.value = found.data_package
        isFinal.value = found.is_final
        
        // Enforce centralized logo from system settings (via data package)
        if (found.data_package?.company_logo_url) {
            if (!templateData.value.header_data) templateData.value.header_data = {}
            templateData.value.header_data.logo = found.data_package.company_logo_url + '?t=' + Date.now()
        }
     } else {
        ElMessage.warning('Шаблон не найден.')
        clearSelection()
     }

   } catch (e) {
      console.error(e)
      ElMessage.error('Ошибка загрузки шаблона')
   } finally { loading.value = false }
}

const clearSelection = () => {
   selectedProposal.value = null
   templateData.value = null
   templateBlocks.value = []
   proposalDataPackage.value = null
   isFinal.value = false
   fetchProposals()
}

// --- Block Management ---
const addBlock = () => {
   templateBlocks.value.push({ title: 'Новый раздел', content: 'Текст...', spacing: 15 })
   debouncedSave()
}

const removeBlock = (index: number) => {
   templateBlocks.value.splice(index, 1)
   debouncedSave()
}

const moveBlock = (index: number, direction: number) => {
   const newIndex = index + direction
   if (newIndex >= 0 && newIndex < templateBlocks.value.length) {
      const item = templateBlocks.value.splice(index, 1)[0]
      templateBlocks.value.splice(newIndex, 0, item)
      debouncedSave()
   }
}

const isPlaceholder = (content: string) => {
    return placeholders.some(p => p.tag === content)
}

const getComponentForPlaceholder = (content: string) => {
    const p = placeholders.find(p => p.tag === content)
    return p ? p.component : null
}

const updateBlockContent = (index: number, event: Event) => {
    const target = event.target as HTMLElement
    templateBlocks.value[index].content = target.innerText
    debouncedSave()
}

const replaceBlockContent = (index: number, content: string) => {
    templateBlocks.value[index].content = content
    // Clear title for total_price_table placeholder to save space
    if (content === '{total_price_table}') {
        templateBlocks.value[index].title = ''
    }
    debouncedSave()
}

const updateProposalHeader = (event: Event) => {
    const target = event.target as HTMLElement
    if (proposalDataPackage.value && proposalDataPackage.value.proposal) {
        proposalDataPackage.value.proposal.header = target.innerText
        debouncedSave()
    }
}

// --- Saving ---
const saveFn = async () => {
   if (!templateData.value) return
   saving.value = true
   const token = Cookies.get('access_token')
   try {
      await axios.patch(`/api/proposal-templates/${templateData.value.template_id}/`, {
         layout_data: templateBlocks.value,
         header_data: templateData.value.header_data,
         is_final: isFinal.value,
         data_package_to_save: proposalDataPackage.value // Save current data_package from constructor
      }, {
         headers: { Authorization: `Bearer ${token}` }
      })
   } catch (e) {
      console.error(e)
   } finally {
      saving.value = false
   }
}

// Simple debounce implementation
let timeout: any = null
const debouncedSave = () => {
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(() => {
        saveFn()
    }, 1000)
}

const forceSave = async () => {
    if (timeout) clearTimeout(timeout)
    await saveFn()
    ElMessage.success('Сохранено')
}

const refreshDataPackage = async () => {
    if (!templateData.value || !selectedProposal.value) return
    refreshingData.value = true
    const token = Cookies.get('access_token')
    try {
        // Refresh data package from proposal
        const response = await axios.post(`/api/proposal-templates/${templateData.value.template_id}/refresh-data-package/`, {}, {
            headers: { Authorization: `Bearer ${token}` }
        })
        
        // Update local data package
        proposalDataPackage.value = response.data.data_package
        
        // Also refresh template data to get updated data_package
        const templateResp = await axios.get(`/api/proposal-templates/${templateData.value.template_id}/`, {
            headers: { Authorization: `Bearer ${token}` }
        })
        templateData.value = templateResp.data
        proposalDataPackage.value = templateResp.data.data_package
        
        ElMessage.success('Данные обновлены из КП')
    } catch (e) {
        console.error(e)
        ElMessage.error('Ошибка обновления данных')
    } finally {
        refreshingData.value = false
    }
}

const updateHeaderData = (newData: any) => {
    if (templateData.value) {
        templateData.value.header_data = newData
        debouncedSave()
    }
}

const updateBlockColumnWidths = (index: number, widths: any) => {
    if (!templateBlocks.value[index].columnWidths) {
         templateBlocks.value[index].columnWidths = {}
    }
    templateBlocks.value[index].columnWidths = { ...templateBlocks.value[index].columnWidths, ...widths }
    debouncedSave()
}

// --- Export ---
const handleExport = async (command: string) => {
    if (!templateData.value) return
    const loading = ElLoading.service({ text: command === 'pdf' ? 'Генерация PDF...' : 'Подготовка файла...', background: 'rgba(0, 0, 0, 0.7)' })
    
    try {
        await forceSave()
        const id = templateData.value.template_id
        const token = Cookies.get('access_token')
        
        const endpoint = command === 'pdf' ? 'export-pdf' : 'export-docx'
        const ext = command === 'pdf' ? '.pdf' : '.docx'
        
        // PDF uses async mode by default (slow), DOCX uses sync mode (fast)
        if (command === 'pdf') {
            // PDF: Use async mode (default)
            try {
                const asyncResponse = await axios.get(`/api/proposal-templates/${id}/${endpoint}/`, {
                    headers: { Authorization: `Bearer ${token}` }
                })
                if (asyncResponse.data.task_id) {
                    pollExportTask(asyncResponse.data.task_id, loading, ext)
                    return
                }
            } catch (asyncError: any) {
                // If async fails, try sync mode as fallback
                console.warn('Async PDF export failed, trying sync:', asyncError)
                try {
                    const syncResponse = await axios.get(`/api/proposal-templates/${id}/${endpoint}/?sync=true`, {
                        responseType: 'blob',
                        headers: { Authorization: `Bearer ${token}` }
                    })
                    loading.close()
                    const url = window.URL.createObjectURL(new Blob([syncResponse.data], { type: 'application/pdf' }))
                    const link = document.createElement('a')
                    link.href = url
                    link.setAttribute('download', `proposal_${selectedProposal.value.outcoming_number}${ext}`)
                    document.body.appendChild(link)
                    link.click()
                    document.body.removeChild(link)
                    window.URL.revokeObjectURL(url)
                    ElMessage.success('Файл успешно скачан')
                    return
                } catch (syncError: any) {
                    console.error('Sync PDF export also failed:', syncError)
                    loading.close()
                    ElMessage.error('Ошибка экспорта PDF: ' + (syncError.response?.data?.error || syncError.message || 'Неизвестная ошибка'))
                    return
                }
            }
        } else {
            // DOCX: Use sync mode (fast, default)
            try {
                const response = await axios.get(`/api/proposal-templates/${id}/${endpoint}/`, {
                    responseType: 'blob',
                    headers: { Authorization: `Bearer ${token}` }
                })
                
                loading.close()
                const url = window.URL.createObjectURL(new Blob([response.data], { 
                    type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' 
                }))
                const link = document.createElement('a')
                link.href = url
                link.setAttribute('download', `proposal_${selectedProposal.value.outcoming_number}${ext}`)
                document.body.appendChild(link)
                link.click()
                document.body.removeChild(link)
                window.URL.revokeObjectURL(url)
                ElMessage.success('Файл успешно скачан')
                return
            } catch (docxError: any) {
                console.error('DOCX export error:', docxError)
                loading.close()
                ElMessage.error('Ошибка экспорта DOCX: ' + (docxError.response?.data?.error || docxError.message || 'Неизвестная ошибка'))
                return
            }
        }
        
    } catch (e: any) {
        console.error(e)
        loading.close()
        ElMessage.error('Ошибка запуска экспорта: ' + (e.message || 'Неизвестная ошибка'))
    }
}

const pollExportTask = async (taskId: string, loadingInstance: any, ext: string) => {
    const token = Cookies.get('access_token')
    const checkTask = async () => {
        try {
            const resp = await axios.get(`/api/celery-task-status/${taskId}/`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            
            if (resp.data.status === 'SUCCESS') {
                const result = resp.data.result
                if (result && result.status === 'SUCCESS') {
                    loadingInstance.close()
                    ElMessage.success('Файл готов!')
                    
                    // Trigger download
                    const fileUrl = result.url
                    const link = document.createElement('a')
                    link.href = fileUrl
                    link.setAttribute('download', `proposal_${selectedProposal.value.outcoming_number}${ext}`)
                    document.body.appendChild(link)
                    link.click()
                    document.body.removeChild(link)
                } else if (result && result.status === 'FAILURE') {
                    loadingInstance.close()
                    ElMessage.error('Ошибка генерации: ' + (result.error || 'Неизвестная ошибка'))
                } else {
                    // Fallback for direct success results
                    loadingInstance.close()
                    ElMessage.success('Файл готов!')
                }
                
            } else if (resp.data.status === 'FAILURE') {
                loadingInstance.close()
                const err = resp.data.result?.error || resp.data.result || 'Ошибка на сервере'
                ElMessage.error('Ошибка генерации файла: ' + err)
            } else {
                // Pending, Started, etc. - continue polling
                setTimeout(checkTask, 2000)
            }
        } catch (e) {
            loadingInstance.close()
            ElMessage.error('Ошибка проверки статуса задачи')
        }
    }
    checkTask()
}

const exportPdf = () => {
   if (!templateData.value) return
   forceSave() // Ensure latest state is saved
   const id = templateData.value.template_id
   const token = Cookies.get('access_token')
   axios.get(`/api/proposal-templates/${id}/export-pdf/`, {
      responseType: 'blob',
      headers: { Authorization: `Bearer ${token}` }
   }).then(response => {
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `proposal_${selectedProposal.value.outcoming_number}.pdf`)
      document.body.appendChild(link)
      link.click()
   }).catch(e => ElMessage.error('Ошибка экспорта PDF'))
}

const exportDocx = () => {
   if (!templateData.value) return
   forceSave()
   const id = templateData.value.template_id
   const token = Cookies.get('access_token')
   axios.get(`/api/proposal-templates/${id}/export-docx/`, {
      responseType: 'blob',
      headers: { Authorization: `Bearer ${token}` }
   }).then(response => {
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `proposal_${selectedProposal.value.outcoming_number}.docx`)
      document.body.appendChild(link)
      link.click()
   }).catch(e => ElMessage.error('Ошибка экспорта DOCX'))
}

onMounted(async () => {
   const proposalId = route.query.proposal_id
   if (proposalId) {
       // We have a direct link to editor
       loading.value = true
       const token = Cookies.get('access_token')
       try {
           // 1. Fetch Proposal Info first to populate header
           // We can get it from the `selectOptions` logic or a direct call.
           // Let's do a direct call to get proposal details
           const propResp = await axios.get(`/api/commercial-proposals/${proposalId}/`, {
               headers: { Authorization: `Bearer ${token}` }
           })
           selectedProposal.value = propResp.data
           
           // 2. Check for existing template
           const response = await axios.get('/api/proposal-templates/', {
                headers: { Authorization: `Bearer ${token}` },
                params: { proposal: proposalId }
           })
           
           let found = null
           if (response.data.results && response.data.results.length > 0) {
                found = response.data.results[0]
           } else if (Array.isArray(response.data) && response.data.length > 0) {
                found = response.data[0]
           }

           if (found) {
                templateData.value = found
                templateBlocks.value = found.layout_data || []
                proposalDataPackage.value = found.data_package
                isFinal.value = found.is_final
                
                // Enforce centralized logo from system settings (via data package)
                if (found.data_package?.company_logo_url) {
                    if (!templateData.value.header_data) templateData.value.header_data = {}
                    templateData.value.header_data.logo = found.data_package.company_logo_url + '?t=' + Date.now()
                }
           } else {
                // Auto-create if not exists
                const createResp = await createTemplate(Number(proposalId))
                templateData.value = createResp.data
                templateBlocks.value = createResp.data.layout_data || []
                proposalDataPackage.value = createResp.data.data_package
                isFinal.value = createResp.data.is_final
                
                // Enforce centralized logo from system settings (via data package)
                if (createResp.data.data_package?.company_logo_url) {
                    if (!templateData.value.header_data) templateData.value.header_data = {}
                    templateData.value.header_data.logo = createResp.data.data_package.company_logo_url + '?t=' + Date.now()
                }
           }

       } catch (e) {
           console.error(e)
           ElMessage.error('Ошибка загрузки конструктора')
       } finally {
           loading.value = false
       }
   } else {
       // Fallback to List Mode
       fetchProposals()
   }
})
</script>

<style scoped>
.proposal-constructor-view {
  padding: 20px;
  background-color: #f0f2f5; /* Grey bg for workspace */
  min-height: 100vh;
}
/* List mode styles */

.editor-header {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 20px;
    padding: 16px;
    background: white;
    border-radius: 4px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.back-button {
    margin-top: 4px;
}

.header-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.header-top-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
}

.header-left-group {
    display: flex;
    align-items: center;
    gap: 12px;
}

.header-right-group {
    display: flex;
    align-items: center;
}

.header-title-row {
    display: flex;
    align-items: center;
}

.saving-indicator {
    margin-right: 10px;
    color: #409eff;
    font-size: 12px;
}
.a4-container {
  background-color: #f0f2f5;
  padding: 20px;
  display: flex;
  justify-content: center;
}
.a4-page {
    width: 210mm;
    min-height: 297mm;
    background: white;
    box-shadow: 0 0 15px rgba(0,0,0,0.1);
    padding: 20mm; /* A4 margins */
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    color: #000; /* Ensure black text */
    position: relative;
    /* Visual Page Dividers */
    background-image: linear-gradient(to bottom, transparent 296.8mm, #dcdfe6 296.8mm, #dcdfe6 297mm, transparent 297mm);
    background-size: 100% 297mm;
}

.page-header {
    margin-bottom: 30px;
    text-align: center;
    border-bottom: 2px solid #333;
    padding-bottom: 10px;
}
.page-header h1 {
    font-size: 20pt;
    margin: 0 0 10px 0;
}
.page-header .subtitle {
    font-size: 12pt;
    color: #000;
    margin: 0;
}

.blocks-area {
    flex: 1;
}

.block-wrapper {
    position: relative;
    margin-bottom: 20px;
    border: 1px dashed transparent;
    transition: all 0.2s;
}
.block-wrapper:hover {
    border-color: #dcdfe6;
}
.block-controls {
    position: absolute;
    right: -40px;
    top: 0;
    display: flex;
    flex-direction: column;
    gap: 4px;
    opacity: 0;
    transition: opacity 0.2s;
    background: white;
    padding: 4px;
    border-radius: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.block-wrapper:hover .block-controls {
    opacity: 1;
}
.spacing-presets {
    padding: 8px;
}
.dialog-content {
    display: flex;
    flex-direction: column;
    gap: 10px;
}
.dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-top: 10px;
}
.option-row {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
}
.option-number {
    font-weight: bold;
    min-width: 80px;
}
.option-client {
    flex: 1;
    color: #606266;
    font-size: 13px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.option-date {
    font-size: 12px;
    color: #909399;
}

.block-title-edit {
    margin-bottom: 10px;
}
.title-input {
    width: 100%;
    border: none;
    font-size: 14pt;
    font-weight: bold;
    color: #000;
    outline: none;
    background: transparent;
}
.title-input:focus {
    background: #fdf6ec;
}

.editable-text {
    min-height: 50px;
    outline: none;
    padding: 8px;
    font-size: 11pt; /* Document font size */
    line-height: 1.5;
    border-radius: 4px;
}
.editable-text:focus {
    background: #fdf6ec;
}
.editable-text:empty:before {
    content: "Введите текст раздела...";
    color: #aaa;
}

.text-controls {
    margin-top: 5px;
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    opacity: 0.5;
}
.block-wrapper:hover .text-controls {
    opacity: 1;
}
.placeholder-tag {
    cursor: pointer;
}

.add-section-area {
    margin-top: 30px;
    border: 2px dashed #e4e7ed;
    padding: 20px;
    text-align: center;
    border-radius: 8px;
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.saving-indicator {
    margin-right: 15px;
    font-size: 12px;
    color: #909399;
}
.ml-2 { margin-left: 8px; }
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.card-header h2 {
    color: #000;
    margin: 0;
}
</style>
