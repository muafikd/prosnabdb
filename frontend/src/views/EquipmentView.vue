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
        <el-table-column label="Актуальная цена (KZT)" width="150" sortable>
          <template #default="{ row }">
            <span v-if="row.sale_price_kzt !== null && row.sale_price_kzt !== undefined">
              {{ formatPrice(row.sale_price_kzt, 'KZT') }}
            </span>
            <span v-else-if="row.actual_price !== null && row.actual_price !== undefined">
              {{ formatPrice(row.actual_price, 'KZT') }}
            </span>
            <span v-else style="color: #999;">—</span>
          </template>
        </el-table-column>
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
            {{ formatPrice(row.equipment_manufacture_price, row.equipment_price_currency_type) }}
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
                <template v-if="getFirstImage(item.equipment_imagelinks)">
                  <div
                    v-show="!cardImageLoaded[item.equipment_id]"
                    class="image-loading"
                  >
                    <el-icon class="is-loading" :size="32"><Loading /></el-icon>
                    <span>Загрузка...</span>
                  </div>
                  <img
                    :src="getImageSrc(getFirstImage(item.equipment_imagelinks))"
                    :alt="item.equipment_name"
                    :class="{ 'image-loaded': cardImageLoaded[item.equipment_id] }"
                    @load="onCardImageLoad(item.equipment_id)"
                    @error="handleImageError"
                  />
                </template>
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
                <div class="card-price">
                  <span class="price-value" v-if="item.sale_price_kzt !== null && item.sale_price_kzt !== undefined && item.sale_price_kzt !== ''">
                    {{ formatPrice(item.sale_price_kzt, 'KZT') }}
                  </span>
                  <span class="price-value price-empty" v-else>—</span>
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
      :title="isEditMode ? 'Редактировать оборудование: ' + (formData.equipment_name || 'без названия') : 'Создать оборудование'"
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
              <div style="display: flex; gap: 10px; width: 100%">
                <el-select
                  v-model="formData.categories"
                  multiple
                  filterable
                  allow-create
                  default-first-option
                  placeholder="Выберите категории или создайте новую"
                  style="flex: 1"
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
                <el-button 
                  type="primary" 
                  :icon="Plus" 
                  @click="handleAddCategoryViaPrompt"
                  title="Добавить новую категорию"
                />
              </div>
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
              <div style="display: flex; gap: 10px; width: 100%">
                <el-select
                  v-model="formData.equipment_types"
                  multiple
                  filterable
                  allow-create
                  default-first-option
                  placeholder="Выберите типы или создайте новый"
                  style="flex: 1"
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
                <el-button 
                  type="primary" 
                  :icon="Plus" 
                  @click="handleAddEquipmentTypeViaPrompt"
                  title="Добавить новый тип оборудования"
                />
              </div>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- Цена -->
        <el-tab-pane label="Цена" name="price">
          <el-form
            :model="formData"
            label-width="200px"
            label-position="left"
          >
            <el-form-item label="Цена продажи (KZT)">
              <el-input-number
                v-model="formData.sale_price_kzt"
                :precision="2"
                :min="0"
                style="width: 100%"
                :formatter="inputFormatter"
                :parser="inputParser"
                placeholder="Фиксированная цена продажи в тенге"
              />
            </el-form-item>

            <el-form-item label="Цена в Валюте">
              <el-input-number
                v-model="formData.equipment_manufacture_price"
                :precision="2"
                :min="0"
                style="width: 100%"
                :formatter="inputFormatter"
                :parser="inputParser"
              />
            </el-form-item>

            <el-form-item label="Валюта">
              <el-select 
                v-model="formData.equipment_price_currency_type" 
                placeholder="Выберите валюту или введите новый тикер" 
                style="width: 100%"
                filterable
                allow-create
                default-first-option
                @change="handleCurrencyChange"
              >
                <el-option 
                  v-for="currency in availableCurrencies" 
                  :key="currency" 
                  :label="currency" 
                  :value="currency" 
                />
              </el-select>
            </el-form-item>

            <el-form-item label="Страна производства">
              <el-select 
                v-model="formData.equipment_madein_country" 
                placeholder="Выберите страну или введите новую" 
                style="width: 100%"
                filterable
                allow-create
                default-first-option
              >
                <el-option 
                  v-for="country in availableCountries" 
                  :key="country" 
                  :label="country" 
                  :value="country" 
                />
              </el-select>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- Документы -->
        <el-tab-pane label="Документы" name="documents">
          <div class="dynamic-list">
            <div class="list-header">
              <h3>Документы оборудования</h3>
              <el-button type="primary" size="small" @click="openDocumentModal()">
                <el-icon><Plus /></el-icon>
                Добавить документ
              </el-button>
            </div>
            <el-table :data="localDocuments" border style="width: 100%">
              <el-table-column prop="document_type" label="Тип документа" width="150">
                <template #default="{ row }">
                  {{ getDocumentTypeLabel(row.document_type) }}
                </template>
              </el-table-column>
              <el-table-column prop="document_name" label="Название" min-width="200" />
              <el-table-column label="Файл/Ссылка" min-width="250">
                <template #default="{ row }">
                  <div v-if="row.file_url" style="display: flex; align-items: center; gap: 8px;">
                    <el-link :href="row.file_url" target="_blank" type="primary">
                      <el-icon><Link /></el-icon>
                      Открыть ссылку
                    </el-link>
                  </div>
                  <div v-else-if="row.file" style="display: flex; align-items: center; gap: 8px;">
                    <el-link :href="getFileUrl(row.file)" target="_blank" type="primary">
                      <el-icon><Document /></el-icon>
                      Открыть файл
                    </el-link>
                    <span v-if="row.file_size" style="color: #909399; font-size: 12px;">
                      ({{ formatFileSize(row.file_size) }})
                    </span>
                  </div>
                  <span v-else style="color: #909399;">—</span>
                </template>
              </el-table-column>
              <el-table-column prop="is_for_client" label="Для клиента" width="120" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.is_for_client ? 'success' : 'info'" size="small">
                    {{ row.is_for_client ? 'Да' : 'Нет' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="is_internal" label="Внутренний" width="120" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.is_internal ? 'warning' : 'info'" size="small">
                    {{ row.is_internal ? 'Да' : 'Нет' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="Дата создания" width="180">
                <template #default="{ row }">
                  {{ formatDate(row.created_at) }}
                </template>
              </el-table-column>
              <el-table-column label="Действия" width="120" align="center">
                <template #default="{ row, $index }">
                  <div style="display: flex; gap: 5px; justify-content: center">
                    <el-button
                      type="primary"
                      :icon="Edit"
                      circle
                      size="small"
                      @click="openDocumentModal($index)"
                    />
                    <el-button
                      type="danger"
                      :icon="Delete"
                      circle
                      size="small"
                      @click="handleDeleteDocument(row.document_id)"
                    />
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <!-- Медиа -->
        <el-tab-pane label="Медиа" name="media">
          <el-form
            :model="formData"
            label-width="200px"
            label-position="left"
          >
            <el-form-item label="Ссылки на изображения">
              <div style="width: 100%">
                <div style="display: flex; justify-content: flex-end; margin-bottom: 10px">
                  <el-button type="primary" @click="openAddImageModal()">
                    + Добавить изображение
                  </el-button>
                </div>
                
                <el-table :data="formData.equipment_imagelinks || []" border style="width: 100%">
                  <el-table-column prop="name" label="Название" min-width="150" />
                  <el-table-column prop="url" label="Ссылка" min-width="250" show-overflow-tooltip />
                  <el-table-column label="Действия" width="120" align="center">
                    <template #default="{ $index }">
                      <div style="display: flex; gap: 5px; justify-content: center">
                        <el-button
                          type="primary"
                          :icon="Edit"
                          circle
                          size="small"
                          @click="openAddImageModal($index)"
                        />
                        <el-button
                          type="danger"
                          :icon="Delete"
                          circle
                          size="small"
                          @click="handleDeleteImage($index)"
                        />
                      </div>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
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
              <div style="display: flex; gap: 8px;">
                <el-button type="primary" size="small" @click="addDetail">
                  <el-icon><Plus /></el-icon>
                  Добавить деталь
                </el-button>
                <el-button size="small" @click="openImportModal('details')">
                  Импорт из буфера (Ctrl+V)
                </el-button>
              </div>
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
              <div style="display: flex; gap: 8px;">
                <el-button type="primary" size="small" @click="addSpecification">
                  <el-icon><Plus /></el-icon>
                  Добавить спецификацию
                </el-button>
                <el-button size="small" @click="openImportModal('specifications')">
                  Импорт из буфера (Ctrl+V)
                </el-button>
              </div>
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
              <div style="display: flex; gap: 8px;">
                <el-button type="primary" size="small" @click="addTechProcess">
                  <el-icon><Plus /></el-icon>
                  Добавить процесс
                </el-button>
                <el-button size="small" @click="openImportModal('tech_processes')">
                  Импорт из буфера (Ctrl+V)
                </el-button>
              </div>
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
                    :formatter="inputFormatter"
                    :parser="inputParser"
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
    <!-- Диалог для добавления/редактирования ссылки на фото -->
    <el-dialog
      v-model="imageModalVisible"
      :title="currentImageForm.index >= 0 ? 'Редактировать изображение' : 'Добавить изображение'"
      width="500px"
      append-to-body
    >
      <el-form :model="currentImageForm" label-width="100px">
        <el-form-item label="Название">
          <el-input v-model="currentImageForm.name" placeholder="Например: Вид сверху" />
        </el-form-item>
        <el-form-item label="Ссылка" required>
          <el-input v-model="currentImageForm.url" placeholder="https://..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="imageModalVisible = false">Отмена</el-button>
        <el-button type="primary" @click="handleSaveLink">Сохранить</el-button>
      </template>
    </el-dialog>

    <!-- Диалог быстрого импорта: вставка из буфера → парсинг по строкам и табуляции → превью → применить -->
    <el-dialog
      v-model="importModalVisible"
      :title="importModalTitle"
      width="720px"
      append-to-body
      @opened="focusImportTextarea"
    >
      <div class="import-paste-area">
        <el-input
          ref="importTextareaRef"
          v-model="importPasteText"
          type="textarea"
          :rows="5"
          :placeholder="importType === 'tech_processes' ? 'Вставьте текст (Ctrl+V). Строки — по Enter, колонки «Название», «Значение», «Описание» — по Tab.' : 'Вставьте текст (Ctrl+V). Строки — по Enter, колонки «Параметр» и «Значение» — по Tab.'"
          @paste="onImportPaste"
        />
        <el-button type="primary" size="small" style="margin-top: 10px" @click="parseImportText">
          Разобрать и показать превью
        </el-button>
      </div>
      <div v-if="parsedImportItems.length > 0" class="import-preview">
        <h4>Превью (можно удалить лишнее)</h4>
        <el-table :data="parsedImportItems" border max-height="280" size="small">
          <template v-if="importType === 'tech_processes'">
            <el-table-column prop="col1" label="Название процесса" min-width="160" />
            <el-table-column prop="col2" label="Значение" min-width="120" show-overflow-tooltip />
            <el-table-column prop="col3" label="Описание" min-width="200" show-overflow-tooltip />
          </template>
          <template v-else>
            <el-table-column prop="col1" label="Параметр" min-width="160" />
            <el-table-column prop="col2" label="Значение" min-width="200" show-overflow-tooltip />
          </template>
          <el-table-column label="" width="60" align="center">
            <template #default="{ $index }">
              <el-button type="danger" size="small" :icon="Delete" circle @click="removeParsedImportItem($index)" />
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="importModalVisible = false">Отмена</el-button>
          <el-button type="primary" :disabled="parsedImportItems.length === 0" @click="applyImport">
            Применить к {{ importApplyLabel }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Диалог для добавления/редактирования документа -->
    <el-dialog
      v-model="documentModalVisible"
      :title="currentDocumentForm.index >= 0 ? 'Редактировать документ' : 'Добавить документ'"
      width="600px"
      append-to-body
    >
      <el-form :model="currentDocumentForm" label-width="150px" ref="documentFormRef">
        <el-form-item label="Тип документа" required>
          <el-select v-model="currentDocumentForm.document_type" placeholder="Выберите тип" style="width: 100%">
            <el-option label="Паспорт" value="passport" />
            <el-option label="Сертификат" value="certificate" />
            <el-option label="Декларация" value="declaration" />
            <el-option label="Смета" value="estimate" />
            <el-option label="Инструкция" value="manual" />
            <el-option label="Прочее" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="Название документа" required>
          <el-input v-model="currentDocumentForm.document_name" placeholder="Введите название документа" />
        </el-form-item>
        <el-form-item label="Загрузить файл">
          <el-upload
            :auto-upload="false"
            :on-change="handleFileChange"
            :file-list="currentDocumentForm.file ? [{ name: currentDocumentForm.file.name }] : []"
            :limit="1"
          >
            <el-button type="primary">Выбрать файл</el-button>
            <template #tip>
              <div class="el-upload__tip">Максимум 1 файл</div>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item label="Или ссылка на файл">
          <el-input v-model="currentDocumentForm.file_url" placeholder="https://..." />
        </el-form-item>
        <el-form-item label="Для клиента">
          <el-switch v-model="currentDocumentForm.is_for_client" />
        </el-form-item>
        <el-form-item label="Внутренний документ">
          <el-switch v-model="currentDocumentForm.is_internal" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="documentModalVisible = false">Отмена</el-button>
        <el-button type="primary" @click="handleSaveDocument" :loading="submitting">Сохранить</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Edit, Delete, Search, List, Grid, Picture, Link, Document, Loading } from '@element-plus/icons-vue'
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
  type EquipmentImage,
  type EquipmentDocument,
  equipmentDocumentsAPI
} from '@/api/equipment'
import { format } from 'date-fns'
import { formatPrice, inputFormatter, inputParser } from '@/utils/formatters'
import { getImageSrc } from '@/utils/imageProxy'
import { useExchangeRateStore } from '@/stores/exchangeRate'
import { exchangeRatesAPI } from '@/api/exchangeRates'

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
// Карточки: картинка загружена (скрываем плейсхолдер)
const cardImageLoaded = ref<Record<number, boolean>>({})

// Exchange rate store
const exchangeRateStore = useExchangeRateStore()

// Popular countries list
const popularCountries = [
  'Казахстан', 'Россия', 'Китай', 'Германия', 'Италия', 'Турция', 
  'США', 'Япония', 'Южная Корея', 'Франция', 'Великобритания', 
  'Польша', 'Чехия', 'Словакия', 'Беларусь', 'Украина', 'Индия',
  'Тайвань', 'Сингапур', 'Малайзия', 'Таиланд', 'Вьетнам'
]

// Available currencies from exchange rates
const availableCurrencies = computed(() => {
  const currencies = new Set<string>(['KZT', 'USD', 'EUR', 'RUB', 'CNY'])
  // Add currencies from exchange rates
  exchangeRateStore.rates.forEach(rate => {
    if (rate.currency_from) currencies.add(rate.currency_from)
    if (rate.currency_to) currencies.add(rate.currency_to)
  })
  return Array.from(currencies).sort()
})

// Available countries (popular + unique from existing equipment + current form value)
const availableCountries = computed(() => {
  const countries = new Set<string>(popularCountries)
  // Add countries from existing equipment
  equipmentList.value.forEach(eq => {
    if (eq.equipment_madein_country) {
      countries.add(eq.equipment_madein_country)
    }
  })
  // Add current form value if it exists (for editing)
  if (formData.equipment_madein_country) {
    countries.add(formData.equipment_madein_country)
  }
  return Array.from(countries).sort()
})

const filters = reactive({
  category: null as number | null,
  manufacturer: null as number | null,
  is_published: null as boolean | null,
})

// Локальные данные для деталей, спецификаций и техпроцессов
const localDetails = ref<(EquipmentDetail & { isNew?: boolean })[]>([])
const localSpecifications = ref<(EquipmentSpecification & { isNew?: boolean })[]>([])
const localTechProcesses = ref<(EquipmentTechProcess & { isNew?: boolean })[]>([])
const localLogistics = ref<(Omit<Logistics, 'cost'> & { cost: number; isNew?: boolean })[]>([])
const localDocuments = ref<EquipmentDocument[]>([])

// State for image link modal
const imageModalVisible = ref(false)
const currentImageForm = reactive({
  name: '',
  url: '',
  index: -1
})

// State for quick import (paste from clipboard)
// Единая структура: col1, col2, col3 (для деталей/спецификаций col3 пустой)
type ParsedImportRow = { col1: string; col2: string; col3: string }
const importModalVisible = ref(false)
const importType = ref<'details' | 'specifications' | 'tech_processes'>('details')
const importPasteText = ref('')
const parsedImportItems = ref<ParsedImportRow[]>([])
const importTextareaRef = ref<{ focus: () => void } | null>(null)

const importModalTitle = computed(() => {
  if (importType.value === 'details') return 'Импорт деталей из буфера'
  if (importType.value === 'specifications') return 'Импорт спецификаций из буфера'
  return 'Импорт техпроцессов из буфера'
})

const importApplyLabel = computed(() => {
  if (importType.value === 'details') return 'детали'
  if (importType.value === 'specifications') return 'спецификациям'
  return 'техпроцессам'
})

function openImportModal(type: 'details' | 'specifications' | 'tech_processes') {
  importType.value = type
  importPasteText.value = ''
  parsedImportItems.value = []
  importModalVisible.value = true
}

function parseImportText() {
  const text = importPasteText.value || ''
  const lines = text.split('\n').map(s => s.trim()).filter(Boolean)
  const items: ParsedImportRow[] = []
  const isTech = importType.value === 'tech_processes'
  for (const line of lines) {
    const parts = line.split('\t').map(s => s.trim())
    const col1 = parts[0] || ''
    if (!col1) continue
    if (isTech) {
      const col2 = parts[1] || ''
      const col3 = parts.slice(2).join('\t').trim() || ''
      items.push({ col1, col2, col3 })
    } else {
      const col2 = parts.slice(1).join('\t').trim() || ''
      items.push({ col1, col2, col3: '' })
    }
  }
  parsedImportItems.value = items
}

function onImportPaste() {
  setTimeout(() => parseImportText(), 0)
}

function removeParsedImportItem(index: number) {
  parsedImportItems.value.splice(index, 1)
}

function applyImport() {
  if (importType.value === 'details') {
    for (const item of parsedImportItems.value) {
      const existing = localDetails.value.find(
        d => (d.detail_parameter_name || '').trim().toLowerCase() === item.col1.trim().toLowerCase()
      )
      if (existing) {
        existing.detail_parameter_value = item.col2
      } else {
        localDetails.value.push({
          detail_id: 0,
          detail_parameter_name: item.col1,
          detail_parameter_value: item.col2,
          isNew: true
        })
      }
    }
  } else if (importType.value === 'specifications') {
    for (const item of parsedImportItems.value) {
      const existing = localSpecifications.value.find(
        s => (s.spec_parameter_name || '').trim().toLowerCase() === item.col1.trim().toLowerCase()
      )
      if (existing) {
        existing.spec_parameter_value = item.col2
      } else {
        localSpecifications.value.push({
          spec_id: 0,
          spec_parameter_name: item.col1,
          spec_parameter_value: item.col2,
          isNew: true
        })
      }
    }
  } else {
    for (const item of parsedImportItems.value) {
      const existing = localTechProcesses.value.find(
        t => (t.tech_name || '').trim().toLowerCase() === item.col1.trim().toLowerCase()
      )
      if (existing) {
        existing.tech_value = item.col2
        existing.tech_desc = item.col3
      } else {
        localTechProcesses.value.push({
          tech_id: 0,
          tech_name: item.col1,
          tech_value: item.col2,
          tech_desc: item.col3,
          isNew: true
        })
      }
    }
  }
  importModalVisible.value = false
  ElMessage.success(`Добавлено записей: ${parsedImportItems.value.length}`)
}

function focusImportTextarea() {
  nextTick(() => importTextareaRef.value?.focus?.())
}

// State for document modal
const documentModalVisible = ref(false)
const documentFormRef = ref<FormInstance>()
const currentDocumentForm = reactive<{
  index: number
  document_type: 'passport' | 'certificate' | 'declaration' | 'estimate' | 'manual' | 'other'
  document_name: string
  file: File | null
  file_url: string
  is_for_client: boolean
  is_internal: boolean
}>({
  index: -1,
  document_type: 'other',
  document_name: '',
  file: null,
  file_url: '',
  is_for_client: false,
  is_internal: false
})

const openAddImageModal = (index = -1) => {
  if (index >= 0) {
    const link = (formData.equipment_imagelinks as EquipmentImage[])?.[index]
    if (link) {
      currentImageForm.name = link.name
      currentImageForm.url = link.url
      currentImageForm.index = index
    }
  } else {
    currentImageForm.name = ''
    currentImageForm.url = ''
    currentImageForm.index = -1
  }
  imageModalVisible.value = true
}

const syncImagesWithBackend = async () => {
  if (!currentEquipmentId.value) return
  
  try {
    const images = (formData.equipment_imagelinks as EquipmentImage[]).filter(l => l && l.url && l.url.trim())
    await equipmentAPI.updateEquipment(currentEquipmentId.value, {
      equipment_imagelinks: images
    })
    ElMessage.success('Медиафайлы синхронизированы')
  } catch (error) {
    console.error('Failed to sync images:', error)
    ElMessage.error('Ошибка синхронизации медиафайлов')
  }
}

const handleSaveLink = async () => {
  if (!currentImageForm.url) {
    ElMessage.warning('Пожалуйста, введите ссылку')
    return
  }
  
  if (!currentImageForm.name) {
    ElMessage.warning('Пожалуйста, введите название изображения')
    return
  }
  
  const newLink: EquipmentImage = { name: currentImageForm.name, url: currentImageForm.url }
  
  if (!Array.isArray(formData.equipment_imagelinks)) {
    formData.equipment_imagelinks = []
  }
  
  if (currentImageForm.index >= 0) {
    (formData.equipment_imagelinks as EquipmentImage[])[currentImageForm.index] = newLink
  } else {
    (formData.equipment_imagelinks as EquipmentImage[]).push(newLink)
  }
  
  imageModalVisible.value = false
  
  // Auto-sync if editing
  await syncImagesWithBackend()
}

const handleDeleteImage = async (index: number) => {
  try {
    await ElMessageBox.confirm('Вы уверены, что хотите удалить это изображение?', 'Подтверждение', {
      confirmButtonText: 'Удалить',
      cancelButtonText: 'Отмена',
      type: 'warning'
    })
    
    if (Array.isArray(formData.equipment_imagelinks)) {
      (formData.equipment_imagelinks as EquipmentImage[]).splice(index, 1)
      await syncImagesWithBackend()
    }
  } catch (error) {
    // User cancelled
  }
}

// Document functions
const openDocumentModal = (index = -1) => {
  if (index >= 0 && localDocuments.value[index]) {
    const doc = localDocuments.value[index]
    currentDocumentForm.index = index
    currentDocumentForm.document_type = doc.document_type
    currentDocumentForm.document_name = doc.document_name
    currentDocumentForm.file = null
    currentDocumentForm.file_url = doc.file_url || ''
    currentDocumentForm.is_for_client = doc.is_for_client
    currentDocumentForm.is_internal = doc.is_internal
  } else {
    currentDocumentForm.index = -1
    currentDocumentForm.document_type = 'other'
    currentDocumentForm.document_name = ''
    currentDocumentForm.file = null
    currentDocumentForm.file_url = ''
    currentDocumentForm.is_for_client = false
    currentDocumentForm.is_internal = false
  }
  documentModalVisible.value = true
}

const handleFileChange = (file: any) => {
  currentDocumentForm.file = file.raw
}

const handleSaveDocument = async () => {
  if (!currentDocumentForm.document_name.trim()) {
    ElMessage.warning('Пожалуйста, введите название документа')
    return
  }
  
  if (!currentDocumentForm.file && !currentDocumentForm.file_url?.trim()) {
    ElMessage.warning('Пожалуйста, загрузите файл или укажите ссылку')
    return
  }
  
  if (!currentEquipmentId.value) {
    ElMessage.error('Оборудование не выбрано')
    return
  }
  
  try {
    submitting.value = true
    
    if (currentDocumentForm.index >= 0) {
      // Редактирование существующего документа
      const doc = localDocuments.value[currentDocumentForm.index]
      await equipmentDocumentsAPI.updateDocument(doc.document_id, {
        document_type: currentDocumentForm.document_type,
        document_name: currentDocumentForm.document_name,
        file: currentDocumentForm.file,
        file_url: currentDocumentForm.file_url || null,
        is_for_client: currentDocumentForm.is_for_client,
        is_internal: currentDocumentForm.is_internal
      })
      ElMessage.success('Документ успешно обновлен')
    } else {
      // Создание нового документа
      await equipmentDocumentsAPI.createDocument({
        equipment: currentEquipmentId.value,
        document_type: currentDocumentForm.document_type,
        document_name: currentDocumentForm.document_name,
        file: currentDocumentForm.file,
        file_url: currentDocumentForm.file_url || null,
        is_for_client: currentDocumentForm.is_for_client,
        is_internal: currentDocumentForm.is_internal
      })
      ElMessage.success('Документ успешно создан')
    }
    
    // Обновляем список документов
    if (currentEquipmentId.value) {
      const documentsData = await equipmentDocumentsAPI.getDocumentsByEquipment(currentEquipmentId.value)
      localDocuments.value = documentsData
    }
    
    documentModalVisible.value = false
  } catch (error: any) {
    console.error('Save document error:', error)
    ElMessage.error(error.response?.data?.message || 'Ошибка сохранения документа')
  } finally {
    submitting.value = false
  }
}

const handleDeleteDocument = async (documentId: number) => {
  try {
    await ElMessageBox.confirm('Вы уверены, что хотите удалить этот документ?', 'Подтверждение', {
      confirmButtonText: 'Удалить',
      cancelButtonText: 'Отмена',
      type: 'warning'
    })
    
    await equipmentDocumentsAPI.deleteDocument(documentId)
    ElMessage.success('Документ успешно удален')
    
    // Обновляем список документов
    if (currentEquipmentId.value) {
      const documentsData = await equipmentDocumentsAPI.getDocumentsByEquipment(currentEquipmentId.value)
      localDocuments.value = documentsData
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Delete document error:', error)
      ElMessage.error(error.response?.data?.message || 'Ошибка удаления документа')
    }
  }
}

const getDocumentTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    passport: 'Паспорт',
    certificate: 'Сертификат',
    declaration: 'Декларация',
    estimate: 'Смета',
    manual: 'Инструкция',
    other: 'Прочее'
  }
  return labels[type] || type
}

const formatFileSize = (bytes: number | null | undefined) => {
  if (!bytes) return '—'
  const sizes = ['Б', 'КБ', 'МБ', 'ГБ']
  if (bytes === 0) return '0 Б'
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
}

const getFileUrl = (filePath: string) => {
  if (!filePath) return ''
  if (filePath.startsWith('http://') || filePath.startsWith('https://')) {
    return filePath
  }
  // Предполагаем, что файлы хранятся в /media/
  // Если путь начинается с /media/, используем его напрямую, иначе добавляем /media/
  if (filePath.startsWith('/media/')) {
    return filePath
  }
  return `/media/${filePath.startsWith('/') ? filePath.slice(1) : filePath}`
}

// Form data
const formData = reactive<EquipmentCreateData & { equipment_manufacture_price?: number | string; sale_price_kzt?: number | string }>({
  equipment_name: '',
  equipment_articule: '',
  equipment_uom: '',
  equipment_short_description: '',
  equipment_warranty: '',
  is_published: false,
  categories: [],
  manufacturers: [],
  equipment_types: [],
  equipment_imagelinks: [],
  equipment_videolinks: '',
  equipment_manufacture_price: undefined,
  sale_price_kzt: undefined,
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
      equipment_imagelinks: Array.isArray(equipmentData.equipment_imagelinks) 
        ? (equipmentData.equipment_imagelinks as any[]).map(img => 
            typeof img === 'string' 
              ? { name: 'Изображение', url: img } 
              : { ...img, name: img.name || 'Изображение' }
          ) 
        : [],
      equipment_videolinks: equipmentData.equipment_videolinks || '',
      equipment_manufacture_price: equipmentData.equipment_manufacture_price 
        ? (typeof equipmentData.equipment_manufacture_price === 'string' 
            ? parseFloat(equipmentData.equipment_manufacture_price) 
            : parseFloat(String(equipmentData.equipment_manufacture_price)))
        : undefined,
      sale_price_kzt: equipmentData.sale_price_kzt 
        ? (typeof equipmentData.sale_price_kzt === 'string' 
            ? parseFloat(equipmentData.sale_price_kzt) 
            : parseFloat(String(equipmentData.sale_price_kzt)))
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
    
    // Загружаем документы
    try {
      const documentsData = await equipmentDocumentsAPI.getDocumentsByEquipment(equipment.equipment_id)
      localDocuments.value = documentsData
    } catch (error) {
      console.error('Load documents error:', error)
      localDocuments.value = []
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
          for (const item of (formData.categories as any[])) {
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
          for (const item of (formData.manufacturers as any[])) {
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
          for (const item of (formData.equipment_types as any[])) {
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
        if (formData.equipment_imagelinks && formData.equipment_imagelinks.length > 0) {
          submitData.equipment_imagelinks = (formData.equipment_imagelinks as any[]).filter(l => l && l.url && l.url.trim())
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
        
        // Цена продажи (KZT)
        if (formData.sale_price_kzt !== undefined && formData.sale_price_kzt !== null && formData.sale_price_kzt !== '') {
          const salePriceValue = typeof formData.sale_price_kzt === 'number' 
            ? formData.sale_price_kzt 
            : parseFloat(String(formData.sale_price_kzt))
          if (!isNaN(salePriceValue) && salePriceValue > 0) {
            submitData.sale_price_kzt = String(salePriceValue)
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
  if (detail && detail.detail_id && !detail.isNew) {
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
  if (spec && spec.spec_id && !spec.isNew) {
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
  if (tech && tech.tech_id && !tech.isNew) {
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
  if (logistics && logistics.logistics_id && !logistics.isNew) {
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
  localDocuments.value = []
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
    equipment_imagelinks: [],
    equipment_videolinks: '',
    equipment_manufacture_price: undefined,
    equipment_madein_country: '',
    equipment_price_currency_type: '',
  })
  localDetails.value = []
  localSpecifications.value = []
  localTechProcesses.value = []
  localLogistics.value = []
  localDocuments.value = []
}

// Обработчики для создания и удаления категорий, производителей и типов

const handleAddCategoryViaPrompt = async () => {
  try {
    const { value } = await ElMessageBox.prompt('Введите название новой категории', 'Новая категория', {
      confirmButtonText: 'Создать',
      cancelButtonText: 'Отмена',
      inputPattern: /^.+$/,
      inputErrorMessage: 'Название не может быть пустым'
    })

    if (value) {
      const newCategory = await categoriesAPI.createCategory({
        category_name: value.trim(),
      })
      categories.value.push(newCategory)
      
      // Добавляем ID созданной категории в выбор
      if (!formData.categories) {
        formData.categories = []
      }
      formData.categories.push(newCategory.category_id)
      
      ElMessage.success(`Категория "${newCategory.category_name}" успешно создана`)
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || 'Ошибка создания категории')
      console.error('Create category error:', error)
    }
  }
}

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

const handleAddEquipmentTypeViaPrompt = async () => {
  try {
    const { value } = await ElMessageBox.prompt('Введите название нового типа оборудования', 'Новый тип оборудования', {
      confirmButtonText: 'Создать',
      cancelButtonText: 'Отмена',
      inputPattern: /^.+$/,
      inputErrorMessage: 'Название не может быть пустым'
    })

    if (value) {
      const newType = await equipmentTypesAPI.createEquipmentType({
        type_name: value.trim(),
      })
      equipmentTypes.value.push(newType)
      
      // Добавляем ID созданного типа в выбор
      if (!formData.equipment_types) {
        formData.equipment_types = []
      }
      formData.equipment_types.push(newType.type_id)
      
      ElMessage.success(`Тип оборудования "${newType.type_name}" успешно создан`)
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || 'Ошибка создания типа оборудования')
      console.error('Create equipment type error:', error)
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
const getFirstImage = (imagelinks?: EquipmentImage[] | string[] | string): string | undefined => {
  if (!imagelinks) return undefined
  if (Array.isArray(imagelinks)) {
    if (imagelinks.length === 0) return undefined
    const first = imagelinks[0]
    if (!first) return undefined
    return typeof first === 'string' ? first : first.url
  }
  // Fallback for legacy string data
  const links = imagelinks.split(',').map(link => link.trim()).filter(link => link)
  return links.length > 0 ? links[0] : undefined
}

const truncateText = (text: string, maxLength: number): string => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

const onCardImageLoad = (equipmentId: number) => {
  cardImageLoaded.value[equipmentId] = true
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
// Handle currency change - add new currency to exchange rates if needed
const handleCurrencyChange = async (value: string) => {
  if (!value) return
  
  // Check if currency exists in available currencies
  const upperValue = value.toUpperCase().trim()
  if (!availableCurrencies.value.includes(upperValue) && upperValue !== 'KZT') {
    try {
      // Try to add new currency via API
      const success = await exchangeRateStore.addCurrency(upperValue)
      if (success) {
        formData.equipment_price_currency_type = upperValue
        ElMessage.success(`Валюта ${upperValue} добавлена`)
      }
    } catch (error: any) {
      console.error('Failed to add currency:', error)
      // Still allow the user to use the currency even if API call fails
    }
  }
}

onMounted(async () => {
  // Load exchange rates first
  await exchangeRateStore.fetchRates()
  
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

.card-image .image-loading {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #909399;
  font-size: 13px;
  background: #f5f7fa;
}

.card-image .image-loading .is-loading {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.card-image img.image-loaded {
  opacity: 1;
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

.price-value.price-empty {
  font-weight: 400;
  color: #909399;
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

.link-url-cell {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
  color: #909399;
  font-size: 13px;
}
</style>
