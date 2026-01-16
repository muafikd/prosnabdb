<template>
  <div class="equipment-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>Каталог оборудования</h2>
          <div class="header-actions">
            <el-radio-group v-model="viewMode" size="default" style="margin-right: 15px">
              <el-radio-button label="table">
                <el-icon><List /></el-icon>
                <span style="margin-left: 5px">Таблица</span>
              </el-radio-button>
              <el-radio-button label="grid">
                <el-icon><Grid /></el-icon>
                <span style="margin-left: 5px">Карточки</span>
              </el-radio-button>
            </el-radio-group>
            <el-button type="primary" @click="handleCreate">
              <el-icon><Plus /></el-icon>
              Добавить оборудование
            </el-button>
          </div>
        </div>
      </template>

      <!-- Фильтры -->
      <div class="filters">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-input
              v-model="searchQuery"
              placeholder="Поиск по названию или артикулу..."
              clearable
              @input="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-col>
          <el-col :span="4">
            <el-select
              v-model="filters.category"
              placeholder="Категория"
              clearable
              filterable
              @change="handleFilterChange"
            >
              <el-option
                v-for="cat in categories"
                :key="cat.category_id"
                :label="cat.category_name"
                :value="cat.category_id"
              />
            </el-select>
          </el-col>
          <el-col :span="4">
            <el-select
              v-model="filters.manufacturer"
              placeholder="Производитель"
              clearable
              filterable
              @change="handleFilterChange"
            >
              <el-option
                v-for="man in manufacturers"
                :key="man.manufacturer_id"
                :label="man.manufacturer_name"
                :value="man.manufacturer_id"
              />
            </el-select>
          </el-col>
          <el-col :span="4">
            <el-select
              v-model="filters.is_published"
              placeholder="Статус публикации"
              clearable
              @change="handleFilterChange"
            >
              <el-option label="Опубликовано" :value="true" />
              <el-option label="Не опубликовано" :value="false" />
            </el-select>
          </el-col>
        </el-row>
      </div>

      <!-- Табличный вид -->
      <el-table
        v-if="viewMode === 'table'"
        v-loading="loading"
        :data="equipmentList"
        stripe
        style="width: 100%; margin-top: 20px"
        :default-sort="{ prop: 'created_at', order: 'descending' }"
      >
        <el-table-column prop="equipment_id" label="ID" width="80" sortable />
        <el-table-column prop="equipment_name" label="Название" sortable min-width="200" />
        <el-table-column prop="equipment_articule" label="Артикул" width="120" />
        <el-table-column prop="equipment_uom" label="Ед. изм." width="100" />
        <el-table-column label="Категории" width="150">
          <template #default="{ row }">
            <el-tag
              v-for="catId in row.categories"
              :key="catId"
              size="small"
              style="margin-right: 5px"
            >
              {{ getCategoryName(catId) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Производители" width="150">
          <template #default="{ row }">
            <el-tag
              v-for="manId in row.manufacturers"
              :key="manId"
              size="small"
              type="success"
              style="margin-right: 5px"
            >
              {{ getManufacturerName(manId) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="equipment_manufacture_price" label="Цена" width="120">
          <template #default="{ row }">
            {{ row.equipment_manufacture_price ? `${row.equipment_manufacture_price} ${row.equipment_price_currency_type || ''}` : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="is_published" label="Опубликовано" width="120" sortable>
          <template #default="{ row }">
            <el-tag :type="row.is_published ? 'success' : 'info'">
              {{ row.is_published ? 'Да' : 'Нет' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="Дата создания" width="180" sortable>
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="Действия" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              :icon="Edit"
              @click="handleEdit(row)"
              circle
            />
            <el-button
              type="danger"
              size="small"
              :icon="Delete"
              @click="handleDelete(row)"
              circle
            />
          </template>
        </el-table-column>
      </el-table>

      <!-- Блочный вид (карточки) -->
      <div v-else-if="viewMode === 'grid'" v-loading="loading" class="equipment-grid">
        <div class="equipment-cards">
          <div
            v-for="item in equipmentList"
            :key="item.equipment_id"
            class="equipment-card"
          >
            <div class="card-image">
              <img
                v-if="getFirstImage(item.equipment_imagelinks)"
                :src="getFirstImage(item.equipment_imagelinks)"
                :alt="item.equipment_name"
                @error="handleImageError"
              />
              <div v-else class="no-image">
                <el-icon :size="48"><Picture /></el-icon>
                <span>Нет изображения</span>
              </div>
              <div class="card-badge" v-if="item.is_published">
                <el-tag type="success" size="small">Опубликовано</el-tag>
              </div>
            </div>
            <div class="card-content">
              <h3 class="card-title" :title="item.equipment_name">
                {{ item.equipment_name }}
              </h3>
              <div class="card-info">
                <div class="card-articule" v-if="item.equipment_articule">
                  <span class="label">Артикул:</span>
                  <span class="value">{{ item.equipment_articule }}</span>
                </div>
                <div class="card-categories" v-if="item.categories && item.categories.length > 0">
                  <el-tag
                    v-for="catId in item.categories.slice(0, 2)"
                    :key="catId"
                    size="small"
                    style="margin-right: 5px; margin-top: 5px"
                  >
                    {{ getCategoryName(catId) }}
                  </el-tag>
                  <el-tag
                    v-if="item.categories.length > 2"
                    size="small"
                    type="info"
                    style="margin-top: 5px"
                  >
                    +{{ item.categories.length - 2 }}
                  </el-tag>
                </div>
                <div class="card-manufacturers" v-if="item.manufacturers && item.manufacturers.length > 0">
                  <span class="label">Производители:</span>
                  <span class="value">
                    {{ item.manufacturers.map(id => getManufacturerName(id)).join(', ') }}
                  </span>
                </div>
                <div class="card-price" v-if="item.equipment_manufacture_price">
                  <span class="price-value">
                    {{ item.equipment_manufacture_price }}
                  </span>
                  <span class="price-currency">
                    {{ item.equipment_price_currency_type || 'KZT' }}
                  </span>
                </div>
                <div class="card-description" v-if="item.equipment_short_description">
                  <p>{{ truncateText(item.equipment_short_description, 100) }}</p>
                </div>
              </div>
            </div>
            <div class="card-actions">
              <el-button
                type="primary"
                size="small"
                :icon="Edit"
                @click="handleEdit(item)"
              >
                Редактировать
              </el-button>
              <el-button
                type="danger"
                size="small"
                :icon="Delete"
                @click="handleDelete(item)"
              >
                Удалить
              </el-button>
            </div>
          </div>
        </div>
        <div v-if="equipmentList.length === 0 && !loading" class="empty-state">
          <el-empty description="Оборудование не найдено" />
        </div>
      </div>

      <!-- Пагинация -->
      <div class="pagination" v-if="total > pageSize">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- Модальное окно создания/редактирования -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditMode ? 'Редактировать оборудование' : 'Создать оборудование'"
      width="900px"
      @close="handleDialogClose"
    >
      <el-tabs v-model="activeTab">
        <!-- Основная информация -->
        <el-tab-pane label="Основная информация" name="basic">
          <el-form
            ref="formRef"
            :model="formData"
            :rules="formRules"
            label-width="200px"
            label-position="left"
          >
            <el-form-item label="Название оборудования *" prop="equipment_name">
              <el-input v-model="formData.equipment_name" placeholder="Введите название" />
            </el-form-item>

            <el-form-item label="Артикул" prop="equipment_articule">
              <el-input v-model="formData.equipment_articule" placeholder="Введите артикул" />
            </el-form-item>

            <el-form-item label="Единица измерения" prop="equipment_uom">
              <el-input v-model="formData.equipment_uom" placeholder="шт, м, кг и т.д." />
            </el-form-item>

            <el-form-item label="Краткое описание" prop="equipment_short_description">
              <el-input
                v-model="formData.equipment_short_description"
                type="textarea"
                :rows="3"
                placeholder="Введите краткое описание"
              />
            </el-form-item>

            <el-form-item label="Гарантия" prop="equipment_warranty">
              <el-input v-model="formData.equipment_warranty" placeholder="Например: 12 месяцев" />
            </el-form-item>

            <el-form-item label="Опубликовано на сайте" prop="is_published">
              <el-switch v-model="formData.is_published" />
            </el-form-item>

            <el-form-item label="Категории" prop="categories">
              <el-select
                v-model="formData.categories"
                multiple
                filterable
                allow-create
                default-first-option
                placeholder="Выберите категории или создайте новую"
                style="width: 100%"
                @create="handleCreateCategory"
              >
                <el-option
                  v-for="cat in categories"
                  :key="cat.category_id"
                  :label="cat.category_name"
                  :value="cat.category_id"
                  class="select-option-with-delete"
                >
                  <div style="display: flex; align-items: center; justify-content: space-between; width: 100%">
                    <span style="flex: 1">{{ cat.category_name }}</span>
                    <el-button
                      type="danger"
                      text
                      size="small"
                      :icon="Delete"
                      @click.stop="handleDeleteCategory(cat.category_id)"
                      style="margin-left: 10px; padding: 0; min-height: auto"
                    />
                  </div>
                </el-option>
              </el-select>
            </el-form-item>

            <el-form-item label="Производители" prop="manufacturers">
              <el-select
                v-model="formData.manufacturers"
                multiple
                filterable
                allow-create
                default-first-option
                placeholder="Выберите производителей или создайте нового"
                style="width: 100%"
                @create="handleCreateManufacturer"
              >
                <el-option
                  v-for="man in manufacturers"
                  :key="man.manufacturer_id"
                  :label="man.manufacturer_name"
                  :value="man.manufacturer_id"
                  class="select-option-with-delete"
                >
                  <div style="display: flex; align-items: center; justify-content: space-between; width: 100%">
                    <span style="flex: 1">{{ man.manufacturer_name }}</span>
                    <el-button
                      type="danger"
                      text
                      size="small"
                      :icon="Delete"
                      @click.stop="handleDeleteManufacturer(man.manufacturer_id)"
                      style="margin-left: 10px; padding: 0; min-height: auto"
                    />
                  </div>
                </el-option>
              </el-select>
            </el-form-item>

            <el-form-item label="Типы оборудования" prop="equipment_types">
              <el-select
                v-model="formData.equipment_types"
                multiple
                filterable
                allow-create
                default-first-option
                placeholder="Выберите типы или создайте новый"
                style="width: 100%"
                @create="handleCreateEquipmentType"
              >
                <el-option
                  v-for="type in equipmentTypes"
                  :key="type.type_id"
                  :label="type.type_name"
                  :value="type.type_id"
                  class="select-option-with-delete"
                >
                  <div style="display: flex; align-items: center; justify-content: space-between; width: 100%">
                    <span style="flex: 1">{{ type.type_name }}</span>
                    <el-button
                      type="danger"
                      text
                      size="small"
                      :icon="Delete"
                      @click.stop="handleDeleteEquipmentType(type.type_id)"
                      style="margin-left: 10px; padding: 0; min-height: auto"
                    />
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- Цена и производство -->
        <el-tab-pane label="Цена и производство" name="price">
          <el-form
            :model="formData"
            label-width="200px"
            label-position="left"
          >
            <el-form-item label="Цена производства">
              <el-input-number
                v-model="formData.equipment_manufacture_price"
                :precision="2"
                :min="0"
                style="width: 100%"
              />
            </el-form-item>

            <el-form-item label="Валюта">
              <el-select v-model="formData.equipment_price_currency_type" placeholder="Выберите валюту" style="width: 100%">
                <el-option label="KZT" value="KZT" />
                <el-option label="USD" value="USD" />
                <el-option label="EUR" value="EUR" />
                <el-option label="RUB" value="RUB" />
                <el-option label="CNY" value="CNY" />
              </el-select>
            </el-form-item>

            <el-form-item label="Страна производства">
              <el-input v-model="formData.equipment_madein_country" placeholder="Введите страну" />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- Медиа -->
        <el-tab-pane label="Медиа" name="media">
          <el-form
            :model="formData"
            label-width="200px"
            label-position="left"
          >
            <el-form-item label="Ссылки на изображения">
              <el-input
                v-model="formData.equipment_imagelinks"
                type="textarea"
                :rows="4"
                placeholder="Введите ссылки на изображения (каждая с новой строки)"
              />
            </el-form-item>

            <el-form-item label="Ссылки на видео">
              <el-input
                v-model="formData.equipment_videolinks"
                type="textarea"
                :rows="4"
                placeholder="Введите ссылки на видео (каждая с новой строки)"
              />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- Детали оборудования -->
        <el-tab-pane label="Детали" name="details">
          <div class="dynamic-list">
            <div class="list-header">
              <h3>Детали оборудования</h3>
              <el-button type="primary" size="small" @click="addDetail">
                <el-icon><Plus /></el-icon>
                Добавить деталь
              </el-button>
            </div>
            <el-table :data="localDetails" border style="width: 100%">
              <el-table-column prop="detail_parameter_name" label="Название параметра" min-width="200">
                <template #default="{ row, $index }">
                  <el-input
                    v-model="row.detail_parameter_name"
                    placeholder="Название параметра"
                  />
                </template>
              </el-table-column>
              <el-table-column prop="detail_parameter_value" label="Значение" min-width="300">
                <template #default="{ row }">
                  <el-input
                    v-model="row.detail_parameter_value"
                    type="textarea"
                    :rows="2"
                    placeholder="Значение параметра"
                  />
                </template>
              </el-table-column>
              <el-table-column label="Действия" width="100">
                <template #default="{ $index }">
                  <el-button
                    type="danger"
                    size="small"
                    :icon="Delete"
                    @click="removeDetail($index)"
                    circle
                  />
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <!-- Спецификации -->
        <el-tab-pane label="Спецификации" name="specifications">
          <div class="dynamic-list">
            <div class="list-header">
              <h3>Спецификации оборудования</h3>
              <el-button type="primary" size="small" @click="addSpecification">
                <el-icon><Plus /></el-icon>
                Добавить спецификацию
              </el-button>
            </div>
            <el-table :data="localSpecifications" border style="width: 100%">
              <el-table-column prop="spec_parameter_name" label="Название параметра" min-width="200">
                <template #default="{ row }">
                  <el-input
                    v-model="row.spec_parameter_name"
                    placeholder="Название параметра"
                  />
                </template>
              </el-table-column>
              <el-table-column prop="spec_parameter_value" label="Значение" min-width="300">
                <template #default="{ row }">
                  <el-input
                    v-model="row.spec_parameter_value"
                    type="textarea"
                    :rows="2"
                    placeholder="Значение параметра"
                  />
                </template>
              </el-table-column>
              <el-table-column label="Действия" width="100">
                <template #default="{ $index }">
                  <el-button
                    type="danger"
                    size="small"
                    :icon="Delete"
                    @click="removeSpecification($index)"
                    circle
                  />
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <!-- Технологические процессы -->
        <el-tab-pane label="Техпроцессы" name="tech_processes">
          <div class="dynamic-list">
            <div class="list-header">
              <h3>Технологические процессы</h3>
              <el-button type="primary" size="small" @click="addTechProcess">
                <el-icon><Plus /></el-icon>
                Добавить процесс
              </el-button>
            </div>
            <el-table :data="localTechProcesses" border style="width: 100%">
              <el-table-column prop="tech_name" label="Название процесса" min-width="200">
                <template #default="{ row }">
                  <el-input
                    v-model="row.tech_name"
                    placeholder="Название процесса"
                  />
                </template>
              </el-table-column>
              <el-table-column prop="tech_value" label="Значение" min-width="150">
                <template #default="{ row }">
                  <el-input
                    v-model="row.tech_value"
                    placeholder="Значение"
                  />
                </template>
              </el-table-column>
              <el-table-column prop="tech_desc" label="Описание" min-width="250">
                <template #default="{ row }">
                  <el-input
                    v-model="row.tech_desc"
                    type="textarea"
                    :rows="2"
                    placeholder="Описание процесса"
                  />
                </template>
              </el-table-column>
              <el-table-column label="Действия" width="100">
                <template #default="{ $index }">
                  <el-button
                    type="danger"
                    size="small"
                    :icon="Delete"
                    @click="removeTechProcess($index)"
                    circle
                  />
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <!-- Логистика -->
        <el-tab-pane label="Логистика" name="logistics">
          <div class="dynamic-list">
            <div class="list-header">
              <h3>Стоимость доставки</h3>
              <el-button type="primary" size="small" @click="addLogistics">
                <el-icon><Plus /></el-icon>
                Добавить маршрут
              </el-button>
            </div>
            <el-table :data="localLogistics" border style="width: 100%">
              <el-table-column prop="route_type" label="Маршрут" min-width="250">
                <template #default="{ row }">
                  <el-select
                    v-model="row.route_type"
                    placeholder="Выберите маршрут"
                    style="width: 100%"
                  >
                    <el-option label="Китай → Казахстан" value="china_kz" />
                    <el-option label="Россия → Казахстан" value="russia_kz" />
                    <el-option label="По Казахстану до нашего склада" value="kz_warehouse" />
                    <el-option label="Другое" value="other" />
                  </el-select>
                </template>
              </el-table-column>
              <el-table-column prop="notes" label="Примечания" min-width="200">
                <template #default="{ row }">
                  <el-input
                    v-model="row.notes"
                    type="textarea"
                    :rows="2"
                    placeholder="Примечания"
                  />
                </template>
              </el-table-column>
              <el-table-column prop="cost" label="Стоимость" min-width="150">
                <template #default="{ row }">
                  <el-input-number
                    v-model="row.cost"
                    :precision="2"
                    :min="0"
                    style="width: 100%"
                    placeholder="Стоимость"
                  />
                </template>
              </el-table-column>
              <el-table-column prop="currency" label="Валюта" width="120">
                <template #default="{ row }">
                  <el-select v-model="row.currency" placeholder="Валюта" style="width: 100%">
                    <el-option label="KZT" value="KZT" />
                    <el-option label="USD" value="USD" />
                    <el-option label="EUR" value="EUR" />
                    <el-option label="RUB" value="RUB" />
                    <el-option label="CNY" value="CNY" />
                  </el-select>
                </template>
              </el-table-column>
              <el-table-column prop="estimated_days" label="Срок (дней)" width="120">
                <template #default="{ row }">
                  <el-input-number
                    v-model="row.estimated_days"
                    :min="0"
                    :precision="0"
                    style="width: 100%"
                    placeholder="Дней"
                  />
                </template>
              </el-table-column>
              <el-table-column prop="is_active" label="Активен" width="100">
                <template #default="{ row }">
                  <el-switch v-model="row.is_active" />
                </template>
              </el-table-column>
              <el-table-column label="Действия" width="100">
                <template #default="{ $index }">
                  <el-button
                    type="danger"
                    size="small"
                    :icon="Delete"
                    @click="removeLogistics($index)"
                    circle
                  />
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">Отмена</el-button>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">
            {{ isEditMode ? 'Сохранить' : 'Создать' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Edit, Delete, Search, List, Grid, Picture } from '@element-plus/icons-vue'
import {
  equipmentAPI,
  categoriesAPI,
  manufacturersAPI,
  equipmentTypesAPI,
  equipmentDetailsAPI,
  equipmentSpecificationsAPI,
  equipmentTechProcessesAPI,
  logisticsAPI,
  type Equipment,
  type EquipmentCreateData,
  type Category,
  type Manufacturer,
  type EquipmentType,
  type EquipmentDetail,
  type EquipmentSpecification,
  type EquipmentTechProcess,
  type Logistics,
} from '@/api/equipment'
import { format } from 'date-fns'

// State
const loading = ref(false)
const submitting = ref(false)
const equipmentList = ref<Equipment[]>([])
const categories = ref<Category[]>([])
const manufacturers = ref<Manufacturer[]>([])
const equipmentTypes = ref<EquipmentType[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchQuery = ref('')
const dialogVisible = ref(false)
const isEditMode = ref(false)
const currentEquipmentId = ref<number | null>(null)
const activeTab = ref('basic')
const formRef = ref<FormInstance>()
const viewMode = ref<'table' | 'grid'>('table')

const filters = reactive({
  category: null as number | null,
  manufacturer: null as number | null,
  is_published: null as boolean | null,
})

// Локальные данные для деталей, спецификаций и техпроцессов
const localDetails = ref<(EquipmentDetail & { isNew?: boolean })[]>([])
const localSpecifications = ref<(EquipmentSpecification & { isNew?: boolean })[]>([])
const localTechProcesses = ref<(EquipmentTechProcess & { isNew?: boolean })[]>([])
const localLogistics = ref<(Logistics & { isNew?: boolean; cost?: number })[]>([])

// Form data
const formData = reactive<EquipmentCreateData & { equipment_manufacture_price?: number | string }>({
  equipment_name: '',
  equipment_articule: '',
  equipment_uom: '',
  equipment_short_description: '',
  equipment_warranty: '',
  is_published: false,
  categories: [],
  manufacturers: [],
  equipment_types: [],
  equipment_imagelinks: '',
  equipment_videolinks: '',
  equipment_manufacture_price: undefined,
  equipment_madein_country: '',
  equipment_price_currency_type: '',
})

// Form validation rules
const formRules: FormRules = {
  equipment_name: [
    { required: true, message: 'Пожалуйста, введите название оборудования', trigger: 'blur' },
    { min: 2, message: 'Название должно содержать минимум 2 символа', trigger: 'blur' },
  ],
}

// Computed
const getCategoryName = computed(() => (id: number) => {
  const cat = categories.value.find(c => c.category_id === id)
  return cat?.category_name || `ID: ${id}`
})

const getManufacturerName = computed(() => (id: number) => {
  const man = manufacturers.value.find(m => m.manufacturer_id === id)
  return man?.manufacturer_name || `ID: ${id}`
})

// Methods
const loadEquipment = async () => {
  try {
    loading.value = true
    const params: any = {
      page: currentPage.value,
    }
    
    if (searchQuery.value) {
      params.search = searchQuery.value
    }
    if (filters.category) {
      params.category_id = filters.category
    }
    if (filters.manufacturer) {
      params.manufacturer_id = filters.manufacturer
    }
    if (filters.is_published !== null) {
      params.is_published = filters.is_published
    }

    const response = await equipmentAPI.getEquipment(params)
    if (Array.isArray(response)) {
      equipmentList.value = response
      total.value = response.length
    } else {
      equipmentList.value = response.results || []
      total.value = response.count || 0
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || 'Ошибка загрузки оборудования')
    console.error('Load equipment error:', error)
  } finally {
    loading.value = false
  }
}

const loadCategories = async () => {
  try {
    categories.value = await categoriesAPI.getCategories()
  } catch (error) {
    console.error('Load categories error:', error)
  }
}

const loadManufacturers = async () => {
  try {
    manufacturers.value = await manufacturersAPI.getManufacturers()
  } catch (error) {
    console.error('Load manufacturers error:', error)
  }
}

const loadEquipmentTypes = async () => {
  try {
    equipmentTypes.value = await equipmentTypesAPI.getEquipmentTypes()
  } catch (error) {
    console.error('Load equipment types error:', error)
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadEquipment()
}

const handleFilterChange = () => {
  currentPage.value = 1
  loadEquipment()
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  loadEquipment()
}

const handleCreate = () => {
  isEditMode.value = false
  currentEquipmentId.value = null
  activeTab.value = 'basic'
  resetForm()
  dialogVisible.value = true
}

const handleEdit = async (equipment: Equipment) => {
  try {
    loading.value = true
    const equipmentData = await equipmentAPI.getEquipmentById(equipment.equipment_id)
    
    isEditMode.value = true
    currentEquipmentId.value = equipment.equipment_id
    activeTab.value = 'basic'
    
    // Заполняем форму данными оборудования
    Object.assign(formData, {
      equipment_name: equipmentData.equipment_name || '',
      equipment_articule: equipmentData.equipment_articule || '',
      equipment_uom: equipmentData.equipment_uom || '',
      equipment_short_description: equipmentData.equipment_short_description || '',
      equipment_warranty: equipmentData.equipment_warranty || '',
      is_published: equipmentData.is_published || false,
      categories: equipmentData.categories || [],
      manufacturers: equipmentData.manufacturers || [],
      equipment_types: equipmentData.equipment_types || [],
      equipment_imagelinks: equipmentData.equipment_imagelinks || '',
      equipment_videolinks: equipmentData.equipment_videolinks || '',
      equipment_manufacture_price: equipmentData.equipment_manufacture_price 
        ? (typeof equipmentData.equipment_manufacture_price === 'string' 
            ? parseFloat(equipmentData.equipment_manufacture_price) 
            : parseFloat(String(equipmentData.equipment_manufacture_price)))
        : undefined,
      equipment_madein_country: equipmentData.equipment_madein_country || '',
      equipment_price_currency_type: equipmentData.equipment_price_currency_type || '',
    })
    
    // Загружаем детали, спецификации и техпроцессы
    localDetails.value = (equipmentData.details || []).map(d => ({ ...d, isNew: false }))
    localSpecifications.value = (equipmentData.specifications || []).map(s => ({ ...s, isNew: false }))
    localTechProcesses.value = (equipmentData.tech_processes || []).map(t => ({ ...t, isNew: false }))
    
    // Загружаем логистику
    try {
      const logisticsData = await logisticsAPI.getLogisticsByEquipment(equipment.equipment_id)
      localLogistics.value = logisticsData.map(l => ({
        ...l,
        isNew: false,
        cost: parseFloat(String(l.cost)) || 0
      }))
    } catch (error) {
      console.error('Load logistics error:', error)
      localLogistics.value = []
    }
    
    dialogVisible.value = true
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || 'Ошибка загрузки данных оборудования')
    console.error('Load equipment error:', error)
  } finally {
    loading.value = false
  }
}

const handleDelete = async (equipment: Equipment) => {
  try {
    if (!equipment.equipment_id) {
      ElMessage.error('Не удалось определить ID оборудования')
      return
    }

    await ElMessageBox.confirm(
      `Вы уверены, что хотите удалить оборудование "${equipment.equipment_name || 'без названия'}"?`,
      'Подтверждение удаления',
      {
        confirmButtonText: 'Удалить',
        cancelButtonText: 'Отмена',
        type: 'warning',
      }
    )

    await equipmentAPI.deleteEquipment(equipment.equipment_id)
    ElMessage.success('Оборудование успешно удалено')
    loadEquipment()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || 'Ошибка удаления оборудования')
      console.error('Delete equipment error:', error)
    }
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        submitting.value = true

        // Преобразуем данные для отправки, убираем пустые значения
        const submitData: any = {}
        
        // Обязательные поля
        submitData.equipment_name = formData.equipment_name?.trim() || ''
        
        // Опциональные поля (только если не пустые)
        if (formData.equipment_articule?.trim()) {
          submitData.equipment_articule = formData.equipment_articule.trim()
        }
        if (formData.equipment_uom?.trim()) {
          submitData.equipment_uom = formData.equipment_uom.trim()
        }
        if (formData.equipment_short_description?.trim()) {
          submitData.equipment_short_description = formData.equipment_short_description.trim()
        }
        if (formData.equipment_warranty?.trim()) {
          submitData.equipment_warranty = formData.equipment_warranty.trim()
        }
        
        submitData.is_published = formData.is_published || false
        
        // Обрабатываем массивы: создаем элементы, если там есть строки, и фильтруем только числа
        if (formData.categories && formData.categories.length > 0) {
          const categoryIds: number[] = []
          for (const item of formData.categories) {
            if (typeof item === 'number') {
              categoryIds.push(item)
            } else if (typeof item === 'string' && item.trim()) {
              // Создаем категорию, если это строка
              try {
                const newCategory = await categoriesAPI.createCategory({
                  category_name: item.trim(),
                })
                categories.value.push(newCategory)
                categoryIds.push(newCategory.category_id)
              } catch (error: any) {
                ElMessage.warning(`Не удалось создать категорию "${item}": ${error.response?.data?.message || 'Ошибка'}`)
              }
            }
          }
          if (categoryIds.length > 0) {
            submitData.categories = categoryIds
          }
        }
        
        if (formData.manufacturers && formData.manufacturers.length > 0) {
          const manufacturerIds: number[] = []
          for (const item of formData.manufacturers) {
            if (typeof item === 'number') {
              manufacturerIds.push(item)
            } else if (typeof item === 'string' && item.trim()) {
              // Создаем производителя, если это строка
              try {
                const newManufacturer = await manufacturersAPI.createManufacturer({
                  manufacturer_name: item.trim(),
                })
                manufacturers.value.push(newManufacturer)
                manufacturerIds.push(newManufacturer.manufacturer_id)
              } catch (error: any) {
                ElMessage.warning(`Не удалось создать производителя "${item}": ${error.response?.data?.message || 'Ошибка'}`)
              }
            }
          }
          if (manufacturerIds.length > 0) {
            submitData.manufacturers = manufacturerIds
          }
        }
        
        if (formData.equipment_types && formData.equipment_types.length > 0) {
          const typeIds: number[] = []
          for (const item of formData.equipment_types) {
            if (typeof item === 'number') {
              typeIds.push(item)
            } else if (typeof item === 'string' && item.trim()) {
              // Создаем тип, если это строка
              try {
                const newType = await equipmentTypesAPI.createEquipmentType({
                  type_name: item.trim(),
                })
                equipmentTypes.value.push(newType)
                typeIds.push(newType.type_id)
              } catch (error: any) {
                ElMessage.warning(`Не удалось создать тип оборудования "${item}": ${error.response?.data?.message || 'Ошибка'}`)
              }
            }
          }
          if (typeIds.length > 0) {
            submitData.equipment_types = typeIds
          }
        }
        
        // Медиа
        if (formData.equipment_imagelinks?.trim()) {
          submitData.equipment_imagelinks = formData.equipment_imagelinks.trim()
        }
        if (formData.equipment_videolinks?.trim()) {
          submitData.equipment_videolinks = formData.equipment_videolinks.trim()
        }
        
        // Цена производства
        if (formData.equipment_manufacture_price !== undefined && formData.equipment_manufacture_price !== null && formData.equipment_manufacture_price !== '') {
          const priceValue = typeof formData.equipment_manufacture_price === 'number' 
            ? formData.equipment_manufacture_price 
            : parseFloat(String(formData.equipment_manufacture_price))
          if (!isNaN(priceValue) && priceValue > 0) {
            submitData.equipment_manufacture_price = String(priceValue)
          }
        }
        
        if (formData.equipment_madein_country?.trim()) {
          submitData.equipment_madein_country = formData.equipment_madein_country.trim()
        }
        if (formData.equipment_price_currency_type?.trim()) {
          submitData.equipment_price_currency_type = formData.equipment_price_currency_type.trim()
        }
        
        // Логируем для отладки
        console.log('Отправляемые данные:', submitData)

        let equipmentId: number

        if (isEditMode.value && currentEquipmentId.value) {
          await equipmentAPI.updateEquipment(currentEquipmentId.value, submitData)
          equipmentId = currentEquipmentId.value
          ElMessage.success('Оборудование успешно обновлено')
        } else {
          const created = await equipmentAPI.createEquipment(submitData)
          console.log('Созданное оборудование (полный ответ):', created)
          console.log('Equipment ID:', created?.equipment_id)
          
          if (!created) {
            throw new Error('Оборудование не было создано. Сервер не вернул данные.')
          }
          
          if (!created.equipment_id) {
            console.error('Ответ сервера без equipment_id:', created)
            throw new Error('Оборудование не было создано. Ответ сервера: ' + JSON.stringify(created))
          }
          
          equipmentId = created.equipment_id
          console.log('Используемый equipment_id для деталей:', equipmentId)
          ElMessage.success('Оборудование успешно создано')
        }

        // Сохраняем детали, спецификации и техпроцессы только если оборудование создано
        if (equipmentId) {
          await saveDetails(equipmentId)
          await saveSpecifications(equipmentId)
          await saveTechProcesses(equipmentId)
          await saveLogistics(equipmentId)
        } else {
          throw new Error('Не удалось получить ID созданного оборудования')
        }

        dialogVisible.value = false
        loadEquipment()
      } catch (error: any) {
        const errorMessage = error.response?.data?.message || 
                           (error.response?.data ? JSON.stringify(error.response.data) : '') ||
                           'Ошибка сохранения оборудования'
        ElMessage.error(errorMessage)
        console.error('Submit error:', error)
      } finally {
        submitting.value = false
      }
    } else {
      ElMessage.warning('Пожалуйста, заполните все обязательные поля')
    }
  })
}

// Методы для работы с деталями
const addDetail = () => {
  localDetails.value.push({
    detail_id: 0,
    detail_parameter_name: '',
    detail_parameter_value: '',
    isNew: true,
  })
}

const removeDetail = async (index: number) => {
  const detail = localDetails.value[index]
  if (detail.detail_id && !detail.isNew) {
    try {
      await equipmentDetailsAPI.deleteDetail(detail.detail_id)
      ElMessage.success('Деталь удалена')
    } catch (error) {
      ElMessage.error('Ошибка удаления детали')
      return
    }
  }
  localDetails.value.splice(index, 1)
}

const saveDetails = async (equipmentId: number) => {
  for (const detail of localDetails.value) {
    // Пропускаем пустые записи
    if (!detail.detail_parameter_name?.trim()) {
      continue
    }

    if (detail.isNew) {
      // Создаем новую деталь
      await equipmentDetailsAPI.createDetail({
        equipment: equipmentId,
        detail_parameter_name: detail.detail_parameter_name.trim(),
        detail_parameter_value: detail.detail_parameter_value?.trim() || undefined,
      })
    } else if (detail.detail_id) {
      // Обновляем существующую деталь
      await equipmentDetailsAPI.updateDetail(detail.detail_id, {
        detail_parameter_name: detail.detail_parameter_name.trim(),
        detail_parameter_value: detail.detail_parameter_value?.trim() || undefined,
      })
    }
  }
}

// Методы для работы со спецификациями
const addSpecification = () => {
  localSpecifications.value.push({
    spec_id: 0,
    spec_parameter_name: '',
    spec_parameter_value: '',
    isNew: true,
  })
}

const removeSpecification = async (index: number) => {
  const spec = localSpecifications.value[index]
  if (spec.spec_id && !spec.isNew) {
    try {
      await equipmentSpecificationsAPI.deleteSpecification(spec.spec_id)
      ElMessage.success('Спецификация удалена')
    } catch (error) {
      ElMessage.error('Ошибка удаления спецификации')
      return
    }
  }
  localSpecifications.value.splice(index, 1)
}

const saveSpecifications = async (equipmentId: number) => {
  for (const spec of localSpecifications.value) {
    // Пропускаем пустые записи
    if (!spec.spec_parameter_name?.trim()) {
      continue
    }

    if (spec.isNew) {
      await equipmentSpecificationsAPI.createSpecification({
        equipment: equipmentId,
        spec_parameter_name: spec.spec_parameter_name.trim(),
        spec_parameter_value: spec.spec_parameter_value?.trim() || undefined,
      })
    } else if (spec.spec_id) {
      await equipmentSpecificationsAPI.updateSpecification(spec.spec_id, {
        spec_parameter_name: spec.spec_parameter_name.trim(),
        spec_parameter_value: spec.spec_parameter_value?.trim() || undefined,
      })
    }
  }
}

// Методы для работы с техпроцессами
const addTechProcess = () => {
  localTechProcesses.value.push({
    tech_id: 0,
    tech_name: '',
    tech_value: '',
    tech_desc: '',
    isNew: true,
  })
}

const removeTechProcess = async (index: number) => {
  const tech = localTechProcesses.value[index]
  if (tech.tech_id && !tech.isNew) {
    try {
      await equipmentTechProcessesAPI.deleteTechProcess(tech.tech_id)
      ElMessage.success('Техпроцесс удален')
    } catch (error) {
      ElMessage.error('Ошибка удаления техпроцесса')
      return
    }
  }
  localTechProcesses.value.splice(index, 1)
}

const saveTechProcesses = async (equipmentId: number) => {
  for (const tech of localTechProcesses.value) {
    // Пропускаем пустые записи
    if (!tech.tech_name?.trim()) {
      continue
    }

    if (tech.isNew) {
      await equipmentTechProcessesAPI.createTechProcess({
        equipment: equipmentId,
        tech_name: tech.tech_name.trim(),
        tech_value: tech.tech_value?.trim() || undefined,
        tech_desc: tech.tech_desc?.trim() || undefined,
      })
    } else if (tech.tech_id) {
      await equipmentTechProcessesAPI.updateTechProcess(tech.tech_id, {
        tech_name: tech.tech_name.trim(),
        tech_value: tech.tech_value?.trim() || undefined,
        tech_desc: tech.tech_desc?.trim() || undefined,
      })
    }
  }
}

// Методы для работы с логистикой
const addLogistics = () => {
  localLogistics.value.push({
    logistics_id: 0,
    equipment: currentEquipmentId.value || 0,
    route_type: 'china_kz',
    cost: 0,
    currency: 'KZT',
    estimated_days: undefined,
    is_active: true,
    notes: '',
    created_at: '',
    updated_at: '',
    isNew: true,
  })
}

const removeLogistics = async (index: number) => {
  const logistics = localLogistics.value[index]
  if (logistics.logistics_id && !logistics.isNew) {
    try {
      await logisticsAPI.deleteLogistics(logistics.logistics_id)
      ElMessage.success('Логистика удалена')
    } catch (error) {
      ElMessage.error('Ошибка удаления логистики')
      return
    }
  }
  localLogistics.value.splice(index, 1)
}

const saveLogistics = async (equipmentId: number) => {
  for (const logistics of localLogistics.value) {
    // Пропускаем записи без маршрута или стоимости
    if (!logistics.route_type || !logistics.cost || logistics.cost <= 0) {
      continue
    }

    if (logistics.isNew) {
      await logisticsAPI.createLogistics({
        equipment: equipmentId,
        route_type: logistics.route_type,
        cost: String(logistics.cost),
        currency: logistics.currency || 'KZT',
        estimated_days: logistics.estimated_days || undefined,
        is_active: logistics.is_active !== false,
        notes: logistics.notes || undefined,
      })
    } else if (logistics.logistics_id) {
      await logisticsAPI.updateLogistics(logistics.logistics_id, {
        route_type: logistics.route_type,
        cost: String(logistics.cost),
        currency: logistics.currency || 'KZT',
        estimated_days: logistics.estimated_days || undefined,
        is_active: logistics.is_active !== false,
        notes: logistics.notes || undefined,
      })
    }
  }
}

const handleDialogClose = () => {
  resetForm()
  formRef.value?.clearValidate()
  activeTab.value = 'basic'
  localDetails.value = []
  localSpecifications.value = []
  localTechProcesses.value = []
  localLogistics.value = []
}

const resetForm = () => {
  Object.assign(formData, {
    equipment_name: '',
    equipment_articule: '',
    equipment_uom: '',
    equipment_short_description: '',
    equipment_warranty: '',
    is_published: false,
    categories: [],
    manufacturers: [],
    equipment_types: [],
    equipment_imagelinks: '',
    equipment_videolinks: '',
    equipment_manufacture_price: undefined,
    equipment_madein_country: '',
    equipment_price_currency_type: '',
  })
  localDetails.value = []
  localSpecifications.value = []
  localTechProcesses.value = []
  localLogistics.value = []
}

// Обработчики для создания и удаления категорий, производителей и типов
const handleCreateCategory = async (newCategoryName: string) => {
  try {
    const newCategory = await categoriesAPI.createCategory({
      category_name: newCategoryName.trim(),
    })
    categories.value.push(newCategory)
    // Заменяем строку на ID в массиве выбранных
    if (!formData.categories) {
      formData.categories = []
    }
    // Находим индекс строки и заменяем на ID
    const stringIndex = formData.categories.findIndex((item: any) => typeof item === 'string' && item === newCategoryName.trim())
    if (stringIndex !== -1) {
      formData.categories[stringIndex] = newCategory.category_id
    } else {
      // Если строка не найдена, просто добавляем ID
      formData.categories.push(newCategory.category_id)
    }
    ElMessage.success(`Категория "${newCategoryName}" создана`)
  } catch (error: any) {
    // Удаляем строку из массива при ошибке
    if (formData.categories) {
      formData.categories = formData.categories.filter((item: any) => item !== newCategoryName.trim() || typeof item === 'number')
    }
    ElMessage.error(error.response?.data?.message || 'Ошибка создания категории')
    console.error('Create category error:', error)
  }
}

const handleDeleteCategory = async (categoryId: number) => {
  try {
    await ElMessageBox.confirm(
      'Вы уверены, что хотите удалить эту категорию? Это действие нельзя отменить.',
      'Подтверждение удаления',
      {
        confirmButtonText: 'Удалить',
        cancelButtonText: 'Отмена',
        type: 'warning',
      }
    )
    
    await categoriesAPI.deleteCategory(categoryId)
    categories.value = categories.value.filter(cat => cat.category_id !== categoryId)
    // Удаляем из выбранных, если была выбрана
    if (formData.categories) {
      formData.categories = formData.categories.filter(id => id !== categoryId)
    }
    ElMessage.success('Категория удалена')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || 'Ошибка удаления категории')
      console.error('Delete category error:', error)
    }
  }
}

const handleCreateManufacturer = async (newManufacturerName: string) => {
  try {
    const newManufacturer = await manufacturersAPI.createManufacturer({
      manufacturer_name: newManufacturerName.trim(),
    })
    manufacturers.value.push(newManufacturer)
    // Заменяем строку на ID в массиве выбранных
    if (!formData.manufacturers) {
      formData.manufacturers = []
    }
    // Находим индекс строки и заменяем на ID
    const stringIndex = formData.manufacturers.findIndex((item: any) => typeof item === 'string' && item === newManufacturerName.trim())
    if (stringIndex !== -1) {
      formData.manufacturers[stringIndex] = newManufacturer.manufacturer_id
    } else {
      // Если строка не найдена, просто добавляем ID
      formData.manufacturers.push(newManufacturer.manufacturer_id)
    }
    ElMessage.success(`Производитель "${newManufacturerName}" создан`)
  } catch (error: any) {
    // Удаляем строку из массива при ошибке
    if (formData.manufacturers) {
      formData.manufacturers = formData.manufacturers.filter((item: any) => item !== newManufacturerName.trim() || typeof item === 'number')
    }
    ElMessage.error(error.response?.data?.message || 'Ошибка создания производителя')
    console.error('Create manufacturer error:', error)
  }
}

const handleDeleteManufacturer = async (manufacturerId: number) => {
  try {
    await ElMessageBox.confirm(
      'Вы уверены, что хотите удалить этого производителя? Это действие нельзя отменить.',
      'Подтверждение удаления',
      {
        confirmButtonText: 'Удалить',
        cancelButtonText: 'Отмена',
        type: 'warning',
      }
    )
    
    await manufacturersAPI.deleteManufacturer(manufacturerId)
    manufacturers.value = manufacturers.value.filter(man => man.manufacturer_id !== manufacturerId)
    // Удаляем из выбранных, если был выбран
    if (formData.manufacturers) {
      formData.manufacturers = formData.manufacturers.filter(id => id !== manufacturerId)
    }
    ElMessage.success('Производитель удален')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || 'Ошибка удаления производителя')
      console.error('Delete manufacturer error:', error)
    }
  }
}

const handleCreateEquipmentType = async (newTypeName: string) => {
  try {
    const newType = await equipmentTypesAPI.createEquipmentType({
      type_name: newTypeName.trim(),
    })
    equipmentTypes.value.push(newType)
    // Заменяем строку на ID в массиве выбранных
    if (!formData.equipment_types) {
      formData.equipment_types = []
    }
    // Находим индекс строки и заменяем на ID
    const stringIndex = formData.equipment_types.findIndex((item: any) => typeof item === 'string' && item === newTypeName.trim())
    if (stringIndex !== -1) {
      formData.equipment_types[stringIndex] = newType.type_id
    } else {
      // Если строка не найдена, просто добавляем ID
      formData.equipment_types.push(newType.type_id)
    }
    ElMessage.success(`Тип оборудования "${newTypeName}" создан`)
  } catch (error: any) {
    // Удаляем строку из массива при ошибке
    if (formData.equipment_types) {
      formData.equipment_types = formData.equipment_types.filter((item: any) => item !== newTypeName.trim() || typeof item === 'number')
    }
    ElMessage.error(error.response?.data?.message || 'Ошибка создания типа оборудования')
    console.error('Create equipment type error:', error)
  }
}

const handleDeleteEquipmentType = async (typeId: number) => {
  try {
    await ElMessageBox.confirm(
      'Вы уверены, что хотите удалить этот тип оборудования? Это действие нельзя отменить.',
      'Подтверждение удаления',
      {
        confirmButtonText: 'Удалить',
        cancelButtonText: 'Отмена',
        type: 'warning',
      }
    )
    
    await equipmentTypesAPI.deleteEquipmentType(typeId)
    equipmentTypes.value = equipmentTypes.value.filter(type => type.type_id !== typeId)
    // Удаляем из выбранных, если был выбран
    if (formData.equipment_types) {
      formData.equipment_types = formData.equipment_types.filter(id => id !== typeId)
    }
    ElMessage.success('Тип оборудования удален')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || 'Ошибка удаления типа оборудования')
      console.error('Delete equipment type error:', error)
    }
  }
}

const formatDate = (dateString: string) => {
  try {
    return format(new Date(dateString), 'dd.MM.yyyy HH:mm')
  } catch {
    return dateString
  }
}

// Вспомогательные функции для карточного вида
const getFirstImage = (imagelinks?: string): string | null => {
  if (!imagelinks) return null
  const links = imagelinks.split(',').map(link => link.trim()).filter(link => link)
  return links.length > 0 ? links[0] : null
}

const truncateText = (text: string, maxLength: number): string => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

const handleImageError = (event: Event) => {
  const target = event.target as HTMLImageElement
  target.style.display = 'none'
  const parent = target.parentElement
  if (parent && !parent.querySelector('.no-image')) {
    const noImageDiv = document.createElement('div')
    noImageDiv.className = 'no-image'
    noImageDiv.innerHTML = '<span>Ошибка загрузки изображения</span>'
    parent.appendChild(noImageDiv)
  }
}

// Lifecycle
onMounted(async () => {
  await Promise.all([
    loadEquipment(),
    loadCategories(),
    loadManufacturers(),
    loadEquipmentTypes(),
  ])
})
</script>

<style scoped>
.equipment-view {
  max-width: 1600px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
}

.card-header h2 {
  margin: 0;
}

.filters {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.dynamic-list {
  padding: 20px 0;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.list-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

/* Стили для карточного вида */
.equipment-grid {
  margin-top: 20px;
}

.equipment-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  padding: 0;
}

.equipment-card {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.equipment-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.card-image {
  position: relative;
  width: 100%;
  height: 200px;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.card-image .no-image {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #909399;
  width: 100%;
  height: 100%;
}

.card-image .no-image span {
  margin-top: 10px;
  font-size: 14px;
}

.card-badge {
  position: absolute;
  top: 10px;
  right: 10px;
}

.card-content {
  padding: 16px;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 12px 0;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.4;
  min-height: 50px;
}

.card-info {
  flex-grow: 1;
}

.card-articule {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.card-articule .label {
  font-weight: 500;
  margin-right: 5px;
}

.card-articule .value {
  color: #909399;
}

.card-categories {
  margin-bottom: 8px;
}

.card-manufacturers {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.card-manufacturers .label {
  font-weight: 500;
  margin-right: 5px;
}

.card-manufacturers .value {
  color: #909399;
}

.card-price {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e4e7ed;
  display: flex;
  align-items: baseline;
  gap: 5px;
}

.price-value {
  font-size: 20px;
  font-weight: 700;
  color: #409eff;
}

.price-currency {
  font-size: 14px;
  color: #909399;
}

.card-description {
  margin-top: 12px;
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
}

.card-description p {
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.card-actions {
  padding: 12px 16px;
  border-top: 1px solid #e4e7ed;
  display: flex;
  gap: 8px;
  justify-content: space-between;
}

.card-actions .el-button {
  flex: 1;
}

.empty-state {
  padding: 40px 0;
  text-align: center;
}

/* Адаптивность для карточек */
@media (max-width: 768px) {
  .equipment-cards {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 15px;
  }
}

@media (max-width: 480px) {
  .equipment-cards {
    grid-template-columns: 1fr;
  }
  
  .header-actions {
    flex-direction: column;
    gap: 10px;
    align-items: stretch;
  }
  
  .header-actions .el-radio-group {
    width: 100%;
  }
  
  .header-actions .el-radio-button {
    flex: 1;
  }
}

/* Стили для селектов с кнопками удаления */
.select-option-with-delete {
  padding-right: 10px;
}

.select-option-with-delete .el-button {
  opacity: 0;
  transition: opacity 0.2s;
  flex-shrink: 0;
}

.select-option-with-delete:hover .el-button {
  opacity: 1;
}
</style>
