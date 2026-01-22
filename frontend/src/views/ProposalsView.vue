<template>
  <div class="proposals-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>Коммерческие предложения</h2>
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            Создать КП
          </el-button>
        </div>
      </template>

      <!-- Фильтры -->
      <div class="filters">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-input
              v-model="searchQuery"
              placeholder="Поиск по названию или номеру КП..."
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
              v-model="filters.client_id"
              placeholder="Клиент"
              clearable
              filterable
              @change="handleFilterChange"
            >
              <el-option
                v-for="client in clients"
                :key="client.client_id"
                :label="client.client_name"
                :value="client.client_id"
              />
            </el-select>
          </el-col>
          <el-col :span="4">
            <el-select
              v-model="filters.proposal_status"
              placeholder="Статус"
              clearable
              @change="handleFilterChange"
            >
              <el-option label="Черновик" value="draft" />
              <el-option label="Отправлено" value="sent" />
              <el-option label="Принято" value="accepted" />
              <el-option label="Отклонено" value="rejected" />
              <el-option label="В переговорах" value="negotiating" />
              <el-option label="Завершено" value="completed" />
            </el-select>
          </el-col>

          <el-col :span="4" style="display: flex; align-items: center;">
             <el-checkbox v-model="includeInactive" label="Показать удаленные" @change="handleFilterChange" />
          </el-col>
        </el-row>
      </div>

      <!-- Таблица КП -->
      <el-table
        v-loading="loading"
        :data="proposalsList"
        stripe
        style="width: 100%; margin-top: 20px"
        :default-sort="{ prop: 'proposal_date', order: 'descending' }"
      >
        <el-table-column prop="proposal_id" label="ID" width="80" sortable />
        <el-table-column prop="outcoming_number" label="Номер КП" width="150" sortable />
        <el-table-column prop="proposal_name" label="Название КП" sortable min-width="200" />
        <el-table-column label="Клиент" width="200">
          <template #default="{ row }">
            {{ row.client?.client_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="proposal_date" label="Дата КП" width="120" sortable>
          <template #default="{ row }">
            {{ formatDate(row.proposal_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="total_price" label="Итоговая цена" width="150" sortable>
          <template #default="{ row }">
            {{ formatPrice(row.total_price, row.currency_ticket) }}
          </template>
        </el-table-column>
        <el-table-column prop="proposal_status" label="Статус" width="130" sortable>
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.proposal_status)">
              {{ getStatusLabel(row.proposal_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="Дата создания" width="180" sortable>
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="Автор (обновил)" width="150" sortable>
          <template #default="{ row }">
             {{ row.updated_by?.user_name || row.user?.user_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="Обновлено" width="180" sortable>
          <template #default="{ row }">
            {{ formatDate(row.updated_at) }}
          </template>
        </el-table-column>

        <el-table-column label="Действия" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              :icon="DocumentCopy"
              @click="handleCopy(row)"
              circle
              title="Создать копию"
            />
            <el-button
              type="warning"
              size="small"
              :icon="DataBoard"
              @click="handleLayout(row)"
              circle
              title="Конструктор (верстка)"
            />
            <el-button
              type="primary"
              size="small"
              :icon="Edit"
              @click="handleEdit(row)"
              circle
              title="Редактировать"
            />
            <el-button
              type="danger"
              size="small"
              :icon="Delete"
              @click="handleDelete(row)"
              circle
              :title="row.is_active === false ? 'Удалено' : 'Архивировать'"
              :disabled="row.is_active === false"
            />
          </template>
        </el-table-column>
      </el-table>

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

    <!-- Модальное окно создания/редактирования КП -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditMode ? 'Редактировать КП' : 'Создать КП'"
      width="1200px"
      @close="handleDialogClose"
      destroy-on-close
    >
      <el-tabs v-model="activeTab" type="border-card" @tab-change="handleTabChange">
        <!-- 1. Основная информация -->
        <el-tab-pane label="Основная информация" name="basic">
          <el-form
            ref="formRef"
            :model="formData"
            :rules="formRules"
            label-width="180px"
            label-position="left"
          >
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="Название КП *" prop="proposal_name">
                  <el-input v-model="formData.proposal_name" placeholder="Введите название КП" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="Номер КП *" prop="outcoming_number">
                  <el-input v-model="formData.outcoming_number" placeholder="Например: Исх. № 123 от 01.01.2025" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="Клиент *" prop="client_id">
                  <el-select
                    v-model="formData.client_id"
                    filterable
                    placeholder="Выберите клиента"
                    style="width: 100%"
                  >
                    <el-option
                      v-for="client in clients"
                      :key="client.client_id"
                      :label="client.client_name"
                      :value="client.client_id"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="Дата КП *" prop="proposal_date">
                  <el-date-picker
                    v-model="formData.proposal_date"
                    type="date"
                    placeholder="Выберите дату"
                    style="width: 100%"
                    format="YYYY-MM-DD"
                    value-format="YYYY-MM-DD"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="Срок действия" prop="valid_until">
                  <el-date-picker
                    v-model="formData.valid_until"
                    type="date"
                    placeholder="Выберите дату"
                    style="width: 100%"
                    format="YYYY-MM-DD"
                    value-format="YYYY-MM-DD"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="Статус *" prop="proposal_status">
                  <el-select v-model="formData.proposal_status" placeholder="Выберите статус" style="width: 100%">
                    <el-option label="Черновик" value="draft" />
                    <el-option label="Отправлено" value="sent" />
                    <el-option label="Принято" value="accepted" />
                    <el-option label="Отклонено" value="rejected" />
                    <el-option label="В переговорах" value="negotiating" />
                    <el-option label="Завершено" value="completed" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="Время доставки" prop="delivery_time">
                  <el-input v-model="formData.delivery_time" placeholder="Например: 30-45 рабочих дней" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="Гарантия" prop="warranty">
                  <el-input v-model="formData.warranty" placeholder="Например: 1 год после поставки" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="Комментарии" prop="comments">
              <el-input
                v-model="formData.comments"
                type="textarea"
                :rows="3"
                placeholder="Введите комментарии"
              />
            </el-form-item>

            <el-form-item label="Ссылка на Битрикс" prop="bitrix_lead_link">
              <el-input v-model="formData.bitrix_lead_link" placeholder="https://..." />
            </el-form-item>
          </el-form>
        </el-tab-pane>


        <!-- 2. Оборудование -->
        <el-tab-pane label="Оборудование" name="equipment">
          <div class="section-header">
            <h3>Оборудование в КП</h3>
            <div style="display: flex; gap: 10px;">
              <el-button type="primary" size="small" @click="showAddEquipmentDialog = true">
                <el-icon><Plus /></el-icon>
                Добавить оборудование
              </el-button>
              <el-button type="default" size="small" @click="refreshEquipmentPrices" :loading="refreshingPrices">
                <el-icon><Refresh /></el-icon>
                Обновить цены из карточек
              </el-button>
            </div>
          </div>

          <el-table 
            :data="selectedEquipment" 
            border 
            style="width: 100%; margin-top: 20px"
            row-key="equipment_id"
          >
            <el-table-column label="Порядок" width="100" align="center">
              <template #default="{ $index }">
                <el-button
                  type="text"
                  size="small"
                  :icon="ArrowUp"
                  :disabled="$index === 0"
                  @click="moveEquipmentUp($index)"
                  circle
                  title="Вверх"
                />
                <el-button
                  type="text"
                  size="small"
                  :icon="ArrowDown"
                  :disabled="$index === selectedEquipment.length - 1"
                  @click="moveEquipmentDown($index)"
                  circle
                  title="Вниз"
                />
              </template>
            </el-table-column>
            <el-table-column prop="equipment_name" label="Оборудование" min-width="200" />
            <el-table-column label="Цена (З) валюта" width="130">
              <template #default="{ row }">
                <span v-if="row.purchase_price_original && row.purchase_price_currency">
                  {{ formatPrice(row.purchase_price_original, row.purchase_price_currency) }}
                </span>
                <span v-else>
                  {{ formatPrice(row.production_price, row.currency) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="Цена (З) KZT" width="130">
              <template #default="{ row }">
                <!-- Always calculate dynamically using internal rate from "Курс валют" tab -->
                {{ formatPrice(calculatePurchasePriceKZT(row), 'KZT') }}
              </template>
            </el-table-column>
            <el-table-column label="Цена продажи KZT" width="140">
              <template #default="{ row }">
                <span v-if="row.sale_price_kzt !== undefined && row.sale_price_kzt !== null">
                  {{ formatPrice(row.sale_price_kzt, 'KZT') }}
                </span>
                <span v-else style="color: #999;">—</span>
              </template>
            </el-table-column>
            <el-table-column label="Кол-во" width="100">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.quantity"
                  :min="1"
                  size="small"
                  style="width: 100%"
                  :controls="false"
                />
              </template>
            </el-table-column>
            <el-table-column label="Размер маржи %" width="130">
              <template #default="{ row }">
                <span v-if="row.margin_percentage !== undefined">
                  {{ formatPrice(row.margin_percentage, 'KZT') }}%
                </span>
                <span v-else-if="row.sale_price_kzt && calculateBaseCostKZT(row) > 0">
                  {{ formatPrice(calculateMarginPercentage(row), 'KZT') }}%
                </span>
                <span v-else style="color: #999;">—</span>
              </template>
            </el-table-column>
            <el-table-column label="Размер маржи (KZT)" width="150">
              <template #default="{ row }">
                <span v-if="row.margin_kzt !== undefined">
                  {{ formatPrice(row.margin_kzt, 'KZT') }}
                </span>
                <span v-else-if="row.sale_price_kzt && calculateBaseCostKZT(row) > 0">
                  {{ formatPrice(calculateMarginKZT(row), 'KZT') }}
                </span>
                <span v-else style="color: #999;">—</span>
              </template>
            </el-table-column>
            <el-table-column label="Сумма расходов (KZT)" width="150">
              <template #default="{ row }">
                {{ formatPrice(calculateTotalExpensesKZT(row), 'KZT') }}
              </template>
            </el-table-column>
            <el-table-column label="Доп. расходы" min-width="200">
              <template #default="{ row }">
                <div v-if="row.row_expenses && row.row_expenses.length">
                  <div v-for="(exp, idx) in row.row_expenses" :key="idx" class="expense-tag-container">
                    <span class="expense-tag">
                      {{ exp.name }}: {{ exp.formattedValue || exp.value }}
                    </span>
                    <el-button
                      type="danger"
                      :icon="Delete"
                      size="small"
                      circle
                      text
                      @click="removeRowExpense(row, idx)"
                      style="margin-left: 5px; padding: 0; width: 20px; height: 20px;"
                    />
                  </div>
                </div>
                <span v-else class="text-gray-400">Нет расходов</span>
              </template>
            </el-table-column>
            <el-table-column label="Действия" width="200" align="center">
              <template #default="{ row, $index }">
                <el-tooltip content="Просмотр карточки оборудования">
                  <el-button
                    type="info"
                    size="small"
                    :icon="View"
                    circle
                    @click="openEquipmentCardDialog(row.equipment_id)"
                  />
                </el-tooltip>
                <el-tooltip content="Добавить расход">
                   <el-button
                    type="primary"
                    size="small"
                    :icon="Plus"
                    circle
                    @click="openRowExpenseDialog(row)"
                  />
                </el-tooltip>
                <el-button
                  type="danger"
                  size="small"
                  :icon="Delete"
                  circle
                  @click="removeEquipment($index)"
                />
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 3. Курс валют -->
        <el-tab-pane label="Курс валют" name="exchange_rates">
          <div class="section-header">
             <h3>Внутренние курсы (для расчета себестоимости)</h3>
             <!-- Кнопка скрыта, т.к. валюты добавляются автоматически по оборудованию -->
             <!-- <el-button size="small" @click="showAddCurrencyDialog = true">
               <el-icon><Plus /></el-icon> Добавить валюту
             </el-button> -->
          </div>
          
          <div v-if="displayedExchangeRates.length === 0" class="text-gray-500 my-4">
             Нет валютного оборудования. Добавьте оборудование с ценой в валюте.
          </div>

          <el-table v-else :data="displayedExchangeRates" border style="width: 100%; margin-top: 20px">
             <el-table-column prop="currency" label="Валюта" width="80" />
             <el-table-column label="Текущий курс НБ" width="120">
               <template #default="{ row }">
                 {{ getLiveRate(row.currency) }}
               </template>
             </el-table-column>
             <el-table-column label="Курс НБ (при созд.)" width="140">
               <template #default="{ row }">
                 {{ row.creation_nb_rate }}
               </template>
             </el-table-column>
             <el-table-column label="Внутренний курс" width="160">
               <template #default="{ row }">
                 <el-input-number 
                    v-model="row.internal_rate" 
                    :min="0" 
                    :step="0.01" 
                    :precision="2"
                    size="small" 
                    style="width: 100%"
                  />
               </template>
             </el-table-column>
             <el-table-column label="Дата установки" width="160">
               <template #default="{ row }">
                 <el-date-picker
                    v-model="row.rate_date"
                    type="date"
                    size="small"
                    placeholder="Дата"
                    style="width: 100%"
                    format="YYYY-MM-DD"
                    value-format="YYYY-MM-DD"
                  />
               </template>
             </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 4. Итоговый расчет КП -->
        <el-tab-pane label="Итоговый расчет КП" name="calculation">
           <!-- Секция 1: Настройка доп. расходов в рамках КП -->
           <div class="calculation-section">
             <h3>1. Общие расходы КП</h3>
             <el-form-item>
                <div style="display: flex; gap: 10px; width: 100%; align-items: center;">
                  <el-select
                    v-model="formData.additional_price_ids"
                    placeholder="Выберите общие расходы (Логистика, Страховка и т.д.)"
                    multiple
                    collapse-tags
                    clearable
                    filterable
                    style="flex: 1"
                  >
                    <el-option
                      v-for="price in additionalPrices"
                      :key="price.price_id"
                      :label="`${price.price_parameter_name} (${price.price_parameter_value} ${price.value_type === 'percentage' ? '%' : price.value_type === 'fixed' ? 'KZT' : ''})`"
                      :value="price.price_id"
                    />
                  </el-select>
                  <el-button type="primary" @click="showAdditionalPriceDialog = true">
                    <el-icon><Setting /></el-icon>
                    Управление
                  </el-button>
                </div>
             </el-form-item>
           </div>
           
           <el-divider />

           <!-- Секция: Дополнительные услуги -->
           <div class="calculation-section">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                 <h3>Дополнительные услуги (фиксированная стоимость)</h3>
                 <el-button type="primary" plain size="small" @click="openAdditionalServicesDialog">
                    <el-icon><Plus /></el-icon> Добавить услугу
                 </el-button>
              </div>
              
              <el-table :data="formData.additional_services" border style="width: 100%; margin-bottom: 20px" v-if="formData.additional_services && formData.additional_services.length > 0">
                 <el-table-column prop="name" label="Название" />
                 <el-table-column prop="price" label="Стоимость (KZT)" width="150">
                    <template #default="{ row }">
                       {{ formatPrice(row.price, 'KZT') }}
                    </template>
                 </el-table-column>
                 <el-table-column prop="description" label="Описание" />
                 <el-table-column label="" width="60" align="center">
                    <template #default="{ $index }">
                       <el-button type="danger" :icon="Delete" circle size="small" @click="removeAdditionalService($index)" />
                    </template>
                 </el-table-column>
              </el-table>
              <div v-else class="text-gray-400" style="margin-bottom: 20px">Нет дополнительных услуг</div>
           </div>

           <el-divider />

           <!-- Секция 2: Итоговый расчет -->
           <div class="calculation-section">
             <h3>2. Калькуляция</h3>
             
             <!-- Инфо-табло внутренних курсов -->
             <div class="rates-summary">
                <span class="label">Примененные курсы:</span>
                <el-tag v-for="rate in internalExchangeRates" :key="rate.currency" class="mx-1" type="warning" effect="plain">
                  1 {{ rate.currency }} = {{ rate.internal_rate }} KZT
                </el-tag>
             </div>

             <div class="calculation-summary-container">
               <el-card shadow="never" class="summary-card">
                  <div class="summary-row">
                    <span>Стоимость оборудования (в тенге):</span>
                    <span>{{ formatPrice(totalEquipmentCostKZT, 'KZT') }}</span>
                  </div>
                  <div class="summary-row" v-if="totalGlobalExpensesKZT > 0">
                    <span>Общие расходы КП (в тенге):</span>
                    <span>+ {{ formatPrice(totalGlobalExpensesKZT, 'KZT') }}</span>
                  </div>
                  <el-divider style="margin: 12px 0"/>
                  <div class="summary-row">
                    <strong>Себестоимость итого (KZT):</strong>
                    <strong>{{ formatPrice(netCostKZT, 'KZT') }}</strong>
                  </div>
               </el-card>

               <div class="margin-block">
                 <h4>Маржа (автоматический расчет)</h4>
                 <div style="margin-bottom: 15px;">
                   <div class="summary-row">
                     <span>Итоговая маржа (KZT):</span>
                     <strong>{{ formatPrice(totalMarginKZT, 'KZT') }}</strong>
                   </div>
                   <div class="summary-row" style="margin-top: 10px;">
                     <span>Итоговая маржа (%):</span>
                     <strong>{{ formatPrice(totalMarginPercentage, 'KZT') }}%</strong>
                   </div>
                 </div>

                  <div class="final-price-display">
                    <span>Итоговая цена КП:</span>
                    <span class="price-value">{{ formatPrice(calculatedTotalPriceKZT, 'KZT') }}</span>
                  </div>
                  <div style="font-size: 0.85em; color: #909399; margin-top: 10px;">
                    Маржа рассчитывается автоматически на основе цен продажи оборудования
                  </div>
               </div>
             </div>
           </div>
        </el-tab-pane>

        <!-- 5. Регистрация платежей -->
        <el-tab-pane label="Регистрация платежей" name="payments">
           <div class="section-header">
             <h3>Платежи</h3>
             <el-button type="primary" size="small" @click="addPayment">
               <el-icon><Plus /></el-icon>
               Добавить платеж
             </el-button>
           </div>

           <el-table :data="tempPayments" border style="width: 100%; margin-top: 20px">
              <el-table-column label="Дата" width="160">
                 <template #default="{ row }">
                    <el-date-picker
                        v-model="row.payment_date"
                        type="date"
                        placeholder="Дата"
                        style="width: 100%"
                        format="YYYY-MM-DD"
                        value-format="YYYY-MM-DD"
                        :clearable="false"
                    />
                 </template>
              </el-table-column>
              <el-table-column label="Название" min-width="150">
                 <template #default="{ row }">
                    <el-input v-model="row.payment_name" placeholder="Например: Аванс" />
                 </template>
              </el-table-column>
              <el-table-column label="Сумма" width="180">
                 <template #default="{ row }">
                    <el-input-number 
                        v-model="row.payment_value" 
                        :min="0" 
                        :precision="2"
                        controls-position="right"
                        style="width: 100%"
                    />
                 </template>
              </el-table-column>
              <el-table-column label="Комментарий" min-width="150">
                 <template #default="{ row }">
                    <el-input v-model="row.comments" placeholder="Комментарий" />
                 </template>
              </el-table-column>
              <el-table-column label="Автор" width="150">
                 <template #default="{ row }">
                    {{ row.user_name || '-' }}
                 </template>
              </el-table-column>
              <el-table-column label="Действия" width="80" align="center">
                 <template #default="{ $index }">
                    <el-button
                        type="danger"
                        size="small"
                        :icon="Delete"
                        circle
                        @click="removePayment($index)"
                    />
                 </template>
              </el-table-column>
           </el-table>

           <div style="margin-top: 20px; text-align: right; font-size: 16px;">
              <div><strong>Итого оплачено: </strong> {{ formatPrice(totalPaid, 'KZT') }}</div>
              <div style="margin-top: 5px;"><strong>Остаток к оплате: </strong> {{ formatPrice(remainingBalance, 'KZT') }}</div>
           </div>
        </el-tab-pane>

      </el-tabs>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">Отмена</el-button>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">
            {{ isEditMode ? 'Сохранить КП' : 'Создать КП' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Модальное окно просмотра карточки оборудования -->
    <el-dialog
      v-model="equipmentCardDialogVisible"
      title="Карточка оборудования"
      width="900px"
      @close="closeEquipmentCardDialog"
    >
      <div v-if="loadingEquipmentCard" style="text-align: center; padding: 40px;">
        <el-icon class="is-loading" style="font-size: 32px;"><Loading /></el-icon>
        <p>Загрузка данных...</p>
      </div>
      <div v-else-if="currentEquipmentCard" class="equipment-card-view">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="Название" :span="2">
            <strong>{{ currentEquipmentCard.equipment_name }}</strong>
          </el-descriptions-item>
          <el-descriptions-item label="Артикул">
            {{ currentEquipmentCard.equipment_articule || '—' }}
          </el-descriptions-item>
          <el-descriptions-item label="Единица измерения">
            {{ currentEquipmentCard.equipment_uom || '—' }}
          </el-descriptions-item>
          <el-descriptions-item label="Краткое описание" :span="2">
            {{ currentEquipmentCard.equipment_short_description || '—' }}
          </el-descriptions-item>
          <el-descriptions-item label="Гарантия">
            {{ currentEquipmentCard.equipment_warranty || '—' }}
          </el-descriptions-item>
          <el-descriptions-item label="Страна производства">
            {{ currentEquipmentCard.equipment_madein_country || '—' }}
          </el-descriptions-item>
          <el-descriptions-item label="Цена закупки">
            {{ currentEquipmentCard.equipment_manufacture_price ? formatPrice(currentEquipmentCard.equipment_manufacture_price, currentEquipmentCard.equipment_price_currency_type || 'KZT') : '—' }}
          </el-descriptions-item>
          <el-descriptions-item label="Цена продажи (KZT)">
            {{ currentEquipmentCard.sale_price_kzt ? formatPrice(currentEquipmentCard.sale_price_kzt, 'KZT') : '—' }}
          </el-descriptions-item>
          <el-descriptions-item label="Опубликовано">
            <el-tag :type="currentEquipmentCard.is_published ? 'success' : 'info'">
              {{ currentEquipmentCard.is_published ? 'Да' : 'Нет' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <!-- Детали оборудования -->
        <div v-if="currentEquipmentCard.details && currentEquipmentCard.details.length > 0" style="margin-top: 20px;">
          <h4>Детали оборудования</h4>
          <el-table :data="currentEquipmentCard.details" border style="margin-top: 10px;">
            <el-table-column prop="detail_parameter_name" label="Параметр" width="200" />
            <el-table-column prop="detail_parameter_value" label="Значение" />
          </el-table>
        </div>

        <!-- Спецификации -->
        <div v-if="currentEquipmentCard.specifications && currentEquipmentCard.specifications.length > 0" style="margin-top: 20px;">
          <h4>Спецификации</h4>
          <el-table :data="currentEquipmentCard.specifications" border style="margin-top: 10px;">
            <el-table-column prop="spec_parameter_name" label="Параметр" width="200" />
            <el-table-column prop="spec_parameter_value" label="Значение" />
          </el-table>
        </div>

        <!-- Техпроцессы -->
        <div v-if="currentEquipmentCard.tech_processes && currentEquipmentCard.tech_processes.length > 0" style="margin-top: 20px;">
          <h4>Технологические процессы</h4>
          <el-table :data="currentEquipmentCard.tech_processes" border style="margin-top: 10px;">
            <el-table-column prop="tech_name" label="Название" width="200" />
            <el-table-column prop="tech_value" label="Значение" />
            <el-table-column prop="tech_desc" label="Описание" />
          </el-table>
        </div>

        <!-- Изображения -->
        <div v-if="currentEquipmentCard.equipment_imagelinks && currentEquipmentCard.equipment_imagelinks.length > 0" style="margin-top: 20px;">
          <h4>Изображения</h4>
          <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px;">
            <div v-for="(img, idx) in currentEquipmentCard.equipment_imagelinks" :key="idx" style="position: relative;">
              <el-image
                :src="typeof img === 'string' ? img : img.url"
                :alt="typeof img === 'object' ? img.name : ''"
                style="width: 150px; height: 150px; object-fit: cover; border-radius: 4px;"
                :preview-src-list="getImagePreviewList()"
                :initial-index="idx"
                fit="cover"
              />
              <div v-if="typeof img === 'object' && img.name" style="text-align: center; margin-top: 5px; font-size: 12px; color: #666;">
                {{ img.name }}
              </div>
            </div>
          </div>
        </div>
      </div>
      <div v-else style="text-align: center; padding: 40px; color: #999;">
        Не удалось загрузить данные оборудования
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="equipmentCardDialogVisible = false">Закрыть</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Диалог добавления валюты -->
    <el-dialog v-model="showAddCurrencyDialog" title="Добавить валюту" width="400px">
       <el-form>
         <el-form-item label="Валюта">
           <el-select v-model="newCurrency" placeholder="Выберите валюту">
             <el-option label="USD" value="USD" :disabled="hasCurrency('USD')"/>
             <el-option label="EUR" value="EUR" :disabled="hasCurrency('EUR')"/>
             <el-option label="RUB" value="RUB" :disabled="hasCurrency('RUB')"/>
             <el-option label="CNY" value="CNY" :disabled="hasCurrency('CNY')"/>
           </el-select>
         </el-form-item>
       </el-form>
       <template #footer>
         <el-button @click="showAddCurrencyDialog = false">Отмена</el-button>
         <el-button type="primary" @click="addCurrency">Добавить</el-button>
       </template>
    </el-dialog>

    <!-- Диалог добавления оборудования (Search) -->
    <el-dialog
      v-model="showAddEquipmentDialog"
      title="Добавить оборудование"
      width="800px"
    >
      <el-input
        v-model="equipmentSearchQuery"
        placeholder="Поиск оборудования..."
        style="margin-bottom: 15px"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <el-table
        :data="filteredEquipment"
        max-height="400"
      >
        <el-table-column prop="equipment_name" label="Название" />
        <el-table-column prop="equipment_articule" label="Артикул" width="120" />
        <el-table-column prop="equipment_manufacture_price" label="Цена" width="120">
            <template #default="{ row }">
               {{ formatPrice(row.equipment_manufacture_price, row.equipment_price_currency_type) }}
            </template>
        </el-table-column>
        <el-table-column label="Действие" width="100">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="selectEquipment(row)">
              Выбрать
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- Диалог управления доп. расходами на строку (Row Expense) -->
    <el-dialog v-model="showRowExpenseDialog" title="Добавить расход на оборудование" width="500px">
      <el-form label-width="120px">
        <el-form-item label="Название">
           <el-input v-model="currentRowExpense.name" placeholder="Например: Упаковка" />
        </el-form-item>
        <el-form-item label="Стоимость (KZT)">
           <el-input-number v-model="currentRowExpense.value" :min="0" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
         <el-button @click="showRowExpenseDialog = false">Отмена</el-button>
         <el-button type="primary" @click="addRowExpense">Добавить</el-button>
      </template>
    </el-dialog>
    
    <!-- Диалог управления общими расходами (Global Additional Price Management from existing code) -->
    <el-dialog
      v-model="showAdditionalPriceDialog"
      title="Управление дополнительными расходами"
      width="900px"
      @opened="loadAdditionalPrices"
    >
      <!-- Reuse existing Logic for managing global additional price types -->
      <div style="margin-bottom: 15px">
        <el-button type="primary" @click="handleCreateAdditionalPrice">
          <el-icon><Plus /></el-icon>
          Создать
        </el-button>
      </div>
      <el-table :data="additionalPrices" border style="width: 100%" v-loading="loadingAdditionalPrices">
         <el-table-column prop="price_parameter_name" label="Название" />
         <el-table-column prop="price_parameter_value" label="Значение" />
         <!-- Minimal columns for brevity -->
         <el-table-column label="Действия">
            <template #default="{ row }">
               <el-button size="small" :icon="Delete" type="danger" @click="handleDeleteAdditionalPrice(row)"/>
            </template>
         </el-table-column>
      </el-table>
       <template #footer>
        <el-button @click="showAdditionalPriceDialog = false">Закрыть</el-button>
      </template>
    </el-dialog>

    <!-- Dialog for creating global additional price type (reused) -->
   <el-dialog
      v-model="showAdditionalPriceFormDialog"
      title="Создать доп. расход"
      width="600px"
    >
       <el-form :model="additionalPriceForm" label-width="150px">
           <el-form-item label="Название">
               <el-input v-model="additionalPriceForm.price_parameter_name"/>
           </el-form-item>
           <el-form-item label="Тип">
              <el-select v-model="additionalPriceForm.value_type">
                  <el-option label="Фиксированная (KZT)" value="fixed"/>
                  <el-option label="Процент (%)" value="percentage"/>
              </el-select>
           </el-form-item>
           <el-form-item label="Значение">
               <el-input-number v-model="additionalPriceForm.price_parameter_value"/>
           </el-form-item>
           <!-- Simplified for brevity, assume full logic exists -->
       </el-form>
       <template #footer>
          <el-button type="primary" @click="handleSubmitAdditionalPrice">Сохранить</el-button>
       </template>
    </el-dialog>

    <!-- Dialog for Additional Services -->
    <el-dialog v-model="showAdditionalServicesDialog" title="Добавить дополнительную услугу" width="500px">
       <el-form label-position="top">
          <el-form-item label="Название услуги *">
             <el-input v-model="currentAdditionalService.name" placeholder="Напр. Монтаж" />
          </el-form-item>
          <el-form-item label="Стоимость (KZT) *">
             <el-input-number v-model="currentAdditionalService.price" :min="0" style="width: 100%" />
          </el-form-item>
          <el-form-item label="Описание">
             <el-input v-model="currentAdditionalService.description" type="textarea" placeholder="Описание услуги..." />
          </el-form-item>
       </el-form>
       <template #footer>
          <el-button @click="showAdditionalServicesDialog = false">Отмена</el-button>
          <el-button type="primary" @click="addAdditionalService">Добавить</el-button>
       </template>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick, inject, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import axios from 'axios'
import Cookies from 'js-cookie'
import { Plus, Edit, Delete, Search, Coin, Setting, DocumentCopy, DataBoard, ArrowUp, ArrowDown, Refresh, View, Loading } from '@element-plus/icons-vue'
import {
  proposalsAPI,
  type CommercialProposal,
  additionalPricesAPI,
  type CommercialProposalCreateData,
  type EquipmentList,
  type AdditionalPrice,
} from '@/api/proposals'
import { exchangeRatesAPI } from '@/api/exchangeRates'
import { equipmentListItemsAPI } from '@/api/proposals'
import { clientsAPI, type Client } from '@/api/clients'
import { equipmentAPI, type Equipment } from '@/api/equipment'
import { formatPrice } from '@/utils/formatters'
import { format } from 'date-fns'
import { useAuthStore } from '@/stores/auth' // Import auth store

// --- Interfaces ---
interface InternalExchangeRate {
  currency: string
  // Display only
  current_nb_rate?: number 
  // Stored
  creation_nb_rate?: number
  internal_rate: number
  rate_date?: string
  // Legacy support
  nb_rate?: number
}

interface RowExpense {
  name: string
  value: number
  formattedValue?: string
}

interface EquipmentRow {
  equipment_id: number
  equipment_name: string
  equipment_manufacture_price: number // Base price from DB
  equipment_price_currency_type: string // Currency from DB
  sale_price_kzt?: number // Sale price in KZT from equipment card
  
  // For calculation
  quantity: number
  production_price: number // Same as manufacture_price
  currency: string // Same as price_currency_type
  
  row_expenses: RowExpense[]
  
  // Calculated fields (from data_package if available)
  purchase_price_original?: number // Purchase price in original currency
  purchase_price_currency?: string // Original currency of purchase price
  purchase_price_kzt?: number // Purchase price converted to KZT
  base_cost_kzt?: number // Base cost (purchase + row expenses) in KZT
  allocated_overhead_per_unit?: number // Distributed overhead per unit
  margin_kzt?: number // Margin per unit in KZT
  margin_percentage?: number // Margin percentage
}

interface PaymentLogItem {
  payment_id?: number
  payment_name: string
  payment_value: number
  payment_date: string
  comments: string
  user_name: string
  user?: number
}

interface AdditionalService {
  name: string
  price: number
  description: string
}

interface AdditionalService {
  name: string
  price: number
  description: string
}

// --- State ---
const loading = ref(false)
const proposalsList = ref<CommercialProposal[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchQuery = ref('')
const filters = reactive({ client_id: null, proposal_status: null })
const includeInactive = ref(false)

const clients = ref<Client[]>([])
const additionalPrices = ref<AdditionalPrice[]>([])
const liveRates = ref<any[]>([]) // Store live rates from API
const equipmentList = ref<Equipment[]>([]) // All available equipment
const internalExchangeRates = ref<InternalExchangeRate[]>([])

const dialogVisible = ref(false)
const isEditMode = ref(false)
const activeTab = ref('basic')
const submitting = ref(false)

// Equipment card dialog state
const equipmentCardDialogVisible = ref(false)
const currentEquipmentCard = ref<Equipment | null>(null)
const loadingEquipmentCard = ref(false)
const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const handleLayout = async (row: CommercialProposal) => {
  const token = Cookies.get('access_token')
  try {
    // First refresh data package from proposal
    await axios.post(`/api/commercial-proposals/${row.proposal_id}/refresh-data-package/`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    })
    ElMessage.success('Данные обновлены')
  } catch (e) {
    console.error(e)
    ElMessage.warning('Не удалось обновить данные, открываю конструктор с текущими данными')
  }
  // Then open constructor
  router.push({ name: 'proposal-constructor', query: { proposal_id: row.proposal_id } })
}
const tempPayments = ref<PaymentLogItem[]>([]) // State for payments

// Form Data
const formRef = ref<FormInstance>()
const formData = reactive<CommercialProposalCreateData>({
  proposal_name: '',
  outcoming_number: '',
  client_id: 0,
  currency_ticket: 'KZT',
  exchange_rate: '1',
  total_price: '0',
  proposal_date: new Date().toISOString().split('T')[0] || '',
  proposal_status: 'draft',
  proposal_version: 1,
  additional_price_ids: [],
  additional_services: [],
  comments: '',
  // ... other fields set defaults
})

// Rules
const formRules: FormRules = {
  proposal_name: [{ required: true, message: 'Обязательное поле', trigger: 'blur' }],
  outcoming_number: [{ required: true, message: 'Обязательное поле', trigger: 'blur' }],
  client_id: [{ required: true, message: 'Выберите клиента', trigger: 'change' }],
}

// Exchange Rates State

const showAddCurrencyDialog = ref(false)
const newCurrency = ref('USD')

// Equipment State
const selectedEquipment = ref<EquipmentRow[]>([])
const showAddEquipmentDialog = ref(false)
const equipmentSearchQuery = ref('')

// Row Expenses State
const showRowExpenseDialog = ref(false)
const currentRowRow = ref<EquipmentRow | null>(null)
const currentRowExpense = reactive({ name: '', value: 0 })

// Payments Methods
const addPayment = () => {
    const userName: string = authStore.userName || ''
    const paymentDate: string = new Date().toISOString().split('T')[0] || ''
    tempPayments.value.push({
        payment_name: '',
        payment_value: 0,
        payment_date: paymentDate,
        comments: '',
        user_name: userName, // Set current user as author
        user: authStore.user?.user_id
    })
}

const removePayment = (index: number) => {
    tempPayments.value.splice(index, 1)
}

const totalPaid = computed(() => {
    return tempPayments.value.reduce((sum, item) => sum + Number(item.payment_value || 0), 0)
})

const remainingBalance = computed(() => {
    const total = Number(formData.total_price || 0)
    return total - totalPaid.value
})

// Global Expenses Management
const showAdditionalPriceDialog = ref(false)
const loadingAdditionalPrices = ref(false)
const showAdditionalPriceFormDialog = ref(false)
const refreshingPrices = ref(false)
const additionalPriceForm = reactive({
    price_parameter_name: '',
    value_type: 'fixed',
    price_parameter_value: 0
}) // simplified

// Additional Services State
const showAdditionalServicesDialog = ref(false)
const currentAdditionalService = reactive<AdditionalService>({ name: '', price: 0, description: '' })


// Calculation State
// marginType и marginValue больше не используются - маржа рассчитывается автоматически

// --- Methods ---

const loadData = async () => {
    loading.value = true
    try {
        const params: any = { page: currentPage.value, search: searchQuery.value }
        if (includeInactive.value) params.include_inactive = true
        
        const propRes = await proposalsAPI.getProposals(params)
        if ('results' in propRes && Array.isArray(propRes.results)) {
            proposalsList.value = propRes.results
            total.value = propRes.count
        } else if (Array.isArray(propRes)) {
            proposalsList.value = propRes
            total.value = propRes.length
        }

        const clientRes = await clientsAPI.getClients()
        if ('results' in clientRes && clientRes.results) {
            clients.value = clientRes.results
        } else if (Array.isArray(clientRes)) {
            clients.value = clientRes
        }

        const equipRes = await equipmentAPI.getEquipment()
        if ('results' in equipRes && equipRes.results) {
            equipmentList.value = equipRes.results
        } else if (Array.isArray(equipRes)) {
            equipmentList.value = equipRes
        }
        
        const addPriceRes = await additionalPricesAPI.getAdditionalPrices()
        additionalPrices.value = addPriceRes
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

const handleFilterChange = () => {
    currentPage.value = 1
    loadData()
}

const handleDialogClose = () => {
    dialogVisible.value = false
}

// Handle tab change - automatically refresh equipment prices when switching to equipment tab
const handleTabChange = async (tabName: string) => {
    // Если переключились на вкладку "Оборудование" и есть оборудование в списке
    if (tabName === 'equipment' && selectedEquipment.value.length > 0 && dialogVisible.value) {
        try {
            // Автоматически обновить цены из карточек оборудования при переключении на вкладку
            // Это обеспечит отображение актуальных данных в таблице
            await refreshEquipmentPricesSilently()
        } catch (e) {
            // Игнорируем ошибки при автоматическом обновлении, чтобы не мешать пользователю
            console.warn('Не удалось автоматически обновить цены из карточек:', e)
        }
    }
}

const handleCreate = async () => {
    isEditMode.value = false
    activeTab.value = 'basic'
    
    // Reset Form completely
    Object.assign(formData, {
        proposal_id: undefined, // Ensure ID is cleared
        proposal_name: '', 
        outcoming_number: '', 
        client_id: undefined,
        proposal_date: new Date().toISOString().split('T')[0] || '',
        valid_until: undefined,
        total_price: '0', 
        proposal_status: 'draft', 
        proposal_version: 1, 
        additional_price_ids: [],
        additional_services: [],
        comments: '', 
        bitrix_lead_link: '', 
        delivery_time: '', 
        warranty: '',
        currency_ticket: 'KZT',
        exchange_rate: '1'
    })

    // Generate unique number
    const now = new Date()
    const uniqueSuffix = `${now.getFullYear()}${(now.getMonth()+1).toString().padStart(2, '0')}${now.getDate().toString().padStart(2, '0')}-${now.getHours().toString().padStart(2, '0')}${now.getMinutes().toString().padStart(2, '0')}${now.getSeconds().toString().padStart(2, '0')}`
    formData.proposal_name = `КП от ${now.toLocaleDateString()}`
    formData.outcoming_number = `KP-${uniqueSuffix}`

    selectedEquipment.value = []
    tempPayments.value = [] 
    
    // Fetch Live Rates before showing dialog
    try {
        const rates = await exchangeRatesAPI.getRates({ latest: true })
        liveRates.value = rates
    } catch (e) {
        console.error('Failed to fetch live rates:', e)
    }

    // Initialize with default major currencies
    internalExchangeRates.value = [
        { 
            currency: 'USD', 
            current_nb_rate: getLiveRate('USD'), 
            creation_nb_rate: getLiveRate('USD'),
            internal_rate: getLiveRate('USD'),
            rate_date: new Date().toISOString().split('T')[0]
        }, 
        { 
            currency: 'EUR', 
            current_nb_rate: getLiveRate('EUR'), 
            creation_nb_rate: getLiveRate('EUR'),
            internal_rate: getLiveRate('EUR'),
            rate_date: new Date().toISOString().split('T')[0]
        },
    ]
    
    dialogVisible.value = true
}



const handleSearch = () => { currentPage.value = 1; loadData() }
const handlePageChange = () => loadData()

// --- Exchange Rate Logic ---
const hasCurrency = (curr: string) => internalExchangeRates.value.some(r => r.currency === curr)

// Computed: Unique currencies used in equipment (excluding KZT)
const activeCurrencies = computed(() => {
    const currencies = new Set<string>()
    selectedEquipment.value.forEach(row => {
        if (row.currency && row.currency !== 'KZT') {
            currencies.add(row.currency)
        }
    })
    return Array.from(currencies)
})

// Computed: Filtered internal rates based on active currencies
const displayedExchangeRates = computed(() => {
    return internalExchangeRates.value.filter(r => activeCurrencies.value.includes(r.currency))
})

// Helper to get live rate
const getLiveRate = (currency: string) => {
   const rateObj = liveRates.value.find(r => r.currency_from === currency && r.currency_to === 'KZT')
   return rateObj ? parseFloat(rateObj.rate_value) : 1
}

// Watcher: Auto-add missing currencies
watch(activeCurrencies, (newCurrencies) => {
    newCurrencies.forEach(currency => {
        if (!hasCurrency(currency)) {
             const rate = getLiveRate(currency)
             internalExchangeRates.value.push({
                currency: currency,
                current_nb_rate: rate, // Live rate for display
                creation_nb_rate: rate, // Snapshot rate at creation
                internal_rate: rate, // Edtiable internal rate
                rate_date: new Date().toISOString().split('T')[0]
            })
        }
    })
}, { deep: true, immediate: true })

const addCurrency = () => {
    if(!hasCurrency(newCurrency.value)) {
        const rate = getLiveRate(newCurrency.value)
        internalExchangeRates.value.push({
            currency: newCurrency.value,
            current_nb_rate: rate, 
            creation_nb_rate: rate,
            internal_rate: rate,
            rate_date: new Date().toISOString().split('T')[0]
        })
    }
    showAddCurrencyDialog.value = false
}
const removeCurrency = (idx: number) => {
    internalExchangeRates.value.splice(idx, 1)
}
const getRate = (curr: string) => {
    if (curr === 'KZT') return 1
    const r = internalExchangeRates.value.find(x => x.currency === curr)
    return r ? r.internal_rate : 1 // fallback
}

// --- Equipment Logic ---
const filteredEquipment = computed(() => {
    if (!equipmentSearchQuery.value) return equipmentList.value
    const q = equipmentSearchQuery.value.toLowerCase()
    return equipmentList.value.filter(e => e.equipment_name.toLowerCase().includes(q) || (e.equipment_articule && e.equipment_articule.toLowerCase().includes(q)))
})

// Флаг для предотвращения двойного вызова
let isSelectingEquipment = false

const selectEquipment = (equip: Equipment) => {
    // Защита от двойного вызова
    if (isSelectingEquipment) {
        return
    }
    isSelectingEquipment = true
    
    try {
        // Проверяем, не добавлено ли уже это оборудование
        const alreadyExists = selectedEquipment.value.some(
            item => item.equipment_id === equip.equipment_id
        )
        
        if (alreadyExists) {
            ElMessage.warning('Это оборудование уже добавлено в список')
            return
        }
        
        selectedEquipment.value.push({
            equipment_id: equip.equipment_id,
            equipment_name: equip.equipment_name,
            equipment_manufacture_price: Number(equip.equipment_manufacture_price) || 0,
            equipment_price_currency_type: equip.equipment_price_currency_type || 'KZT',
            sale_price_kzt: equip.sale_price_kzt ? Number(equip.sale_price_kzt) : undefined,
            production_price: Number(equip.equipment_manufacture_price) || 0,
            currency: equip.equipment_price_currency_type || 'KZT',
            quantity: 1,
            row_expenses: [],
            // Set purchase price fields for correct calculation with internal rate
            purchase_price_original: Number(equip.equipment_manufacture_price) || 0,
            purchase_price_currency: equip.equipment_price_currency_type || 'KZT'
        })
        ElMessage.success('Оборудование добавлено')
    } finally {
        // Сбрасываем флаг через небольшую задержку
        setTimeout(() => {
            isSelectingEquipment = false
        }, 300)
    }
}

const removeEquipment = (idx: number) => {
    selectedEquipment.value.splice(idx, 1)
}

// Internal function to update equipment prices (without messages)
const updateEquipmentPricesFromCards = async (showMessages: boolean = true) => {
    if (selectedEquipment.value.length === 0) {
        if (showMessages) {
            ElMessage.warning('Нет оборудования для обновления')
        }
        return
    }
    
    refreshingPrices.value = true
    try {
        // Load all equipment data from API
        const equipmentIds = selectedEquipment.value.map(row => row.equipment_id)
        const equipmentPromises = equipmentIds.map(id => equipmentAPI.getEquipmentById(id))
        const equipmentDataList = await Promise.all(equipmentPromises)
        
        // Create a map for quick lookup
        const equipmentMap = new Map(equipmentDataList.map(eq => [eq.equipment_id, eq]))
        
        // Update each row with fresh data from equipment cards
        selectedEquipment.value.forEach(row => {
            const equipmentData = equipmentMap.get(row.equipment_id)
            if (equipmentData) {
                // Update sale_price_kzt (priority: from equipment card)
                if (equipmentData.sale_price_kzt) {
                    row.sale_price_kzt = parseFloat(equipmentData.sale_price_kzt as unknown as string)
                } else {
                    row.sale_price_kzt = undefined
                }
                
                // Update manufacture price and currency
                const newManufacturePrice = parseFloat(equipmentData.equipment_manufacture_price as unknown as string) || 0
                const newCurrency = equipmentData.equipment_price_currency_type || 'KZT'
                
                row.equipment_manufacture_price = newManufacturePrice
                row.equipment_price_currency_type = newCurrency
                row.production_price = newManufacturePrice
                row.currency = newCurrency
                
                // Update purchase price fields
                row.purchase_price_original = newManufacturePrice
                row.purchase_price_currency = newCurrency
                
                // IMPORTANT: Clear calculated fields from saved calculated_data to force recalculation
                // This ensures that values are recalculated based on fresh equipment data
                row.purchase_price_kzt = undefined
                row.base_cost_kzt = undefined
                row.margin_kzt = undefined
                row.margin_percentage = undefined
                row.allocated_overhead_per_unit = undefined
            }
        })
        
        if (showMessages) {
            ElMessage.success(`Цены обновлены для ${equipmentDataList.length} единиц оборудования`)
        }
    } catch (error: any) {
        console.error('Failed to refresh equipment prices:', error)
        if (showMessages) {
            ElMessage.error('Ошибка при обновлении цен из карточек оборудования')
        }
    } finally {
        refreshingPrices.value = false
    }
}

// Refresh equipment prices from equipment cards (with messages)
const refreshEquipmentPrices = async () => {
    await updateEquipmentPricesFromCards(true)
}

// Refresh equipment prices silently (without messages) - for automatic updates
const refreshEquipmentPricesSilently = async () => {
    await updateEquipmentPricesFromCards(false)
}

// Перемещение оборудования вверх/вниз
const moveEquipmentUp = (index: number) => {
    if (index > 0) {
        const item = selectedEquipment.value[index]
        if (item) {
            selectedEquipment.value.splice(index, 1)
            selectedEquipment.value.splice(index - 1, 0, item)
        }
    }
}

const moveEquipmentDown = (index: number) => {
    if (index < selectedEquipment.value.length - 1) {
        const item = selectedEquipment.value[index]
        if (item) {
            selectedEquipment.value.splice(index, 1)
            selectedEquipment.value.splice(index + 1, 0, item)
        }
    }
}

// Row Expenses
const openRowExpenseDialog = (row: EquipmentRow) => {
    currentRowRow.value = row
    currentRowExpense.name = ''
    currentRowExpense.value = 0
    showRowExpenseDialog.value = true
}
const addRowExpense = () => {
    if(currentRowRow.value) {
        currentRowRow.value.row_expenses.push({ ...currentRowExpense })
        showRowExpenseDialog.value = false
    }
}

const removeRowExpense = (row: EquipmentRow, index: number) => {
    if (row.row_expenses && row.row_expenses.length > index) {
        row.row_expenses.splice(index, 1)
    }
}

// Per Row Calculation
const calculateRowExpensesSum = (row: EquipmentRow) => {
    return row.row_expenses.reduce((sum, exp) => sum + exp.value, 0)
}

// Calculate purchase price in KZT
// Calculate purchase price in KZT using internal rate from "Курс валют" tab
// Always calculates dynamically using current internal_rate from internalExchangeRates
const calculatePurchasePriceKZT = (row: EquipmentRow): number => {
    // Get purchase price in original currency
    // Use purchase_price_original if available, otherwise use production_price
    const purchasePriceOriginal = row.purchase_price_original !== undefined 
        ? row.purchase_price_original 
        : row.production_price
    
    // Get currency (purchase_price_currency or fallback to currency)
    const currency = row.purchase_price_currency || row.currency
    
    // If currency is KZT, no conversion needed
    if (currency === 'KZT') {
        return purchasePriceOriginal
    }
    
    // Get internal rate from internalExchangeRates (editable rate from "Курс валют" tab)
    // This rate is set by user in the "Курс валют" tab and stored in internalExchangeRates
    // Always use current internal_rate, not saved purchase_price_kzt
    const internalRate = getRate(currency) // This uses internal_rate from internalExchangeRates
    
    // Convert to KZT: purchase_price_original * internal_rate
    return purchasePriceOriginal * internalRate
}

// Calculate base cost (purchase price + row expenses) in KZT
// This is used for margin percentage calculation (denominator)
// Note: allocated_overhead is NOT included in base_cost for percentage calculation
const calculateBaseCostKZT = (row: EquipmentRow): number => {
    // If we have base_cost_kzt from data_package, use it (already calculated with correct rate)
    if (row.base_cost_kzt !== undefined) {
        return row.base_cost_kzt
    }
    
    // Otherwise, calculate: purchase price (converted to KZT using internal rate) + row expenses per unit
    const purchasePriceKZT = calculatePurchasePriceKZT(row)
    const rowExpensesPerUnit = row.quantity > 0 ? calculateRowExpensesSum(row) / row.quantity : 0
    return purchasePriceKZT + rowExpensesPerUnit
}

// Calculate allocated overhead per unit for this row
// Overhead is distributed proportionally to base costs
const calculateAllocatedOverheadPerUnit = (row: EquipmentRow): number => {
    // Calculate total base cost for all equipment (for distribution weight)
    const totalBaseCost = selectedEquipment.value.reduce((sum, r) => {
        const baseCost = calculateBaseCostKZT(r)
        return sum + (baseCost * r.quantity)
    }, 0)
    
    if (totalBaseCost <= 0) return 0
    
    // Calculate this row's base cost
    const rowBaseCost = calculateBaseCostKZT(row)
    const rowBaseTotal = rowBaseCost * row.quantity
    
    // Calculate weight (proportion of this row's base cost to total)
    const weight = rowBaseTotal / totalBaseCost
    
    // Get total global overhead (from additional_price_ids)
    const globalOverhead = totalGlobalExpensesKZT.value
    
    // Allocate overhead proportionally
    const allocatedOverheadTotal = globalOverhead * weight
    const allocatedOverheadPerUnit = row.quantity > 0 ? allocatedOverheadTotal / row.quantity : 0
    
    return allocatedOverheadPerUnit
}

// Calculate total expenses per unit (row expenses + allocated overhead) in KZT
const calculateTotalExpensesKZT = (row: EquipmentRow): number => {
    // Row expenses per unit
    const rowExpensesPerUnit = row.quantity > 0 ? calculateRowExpensesSum(row) / row.quantity : 0
    
    // Calculate allocated overhead dynamically based on current global expenses
    // This ensures margin recalculates when global expenses change
    const allocatedOverhead = calculateAllocatedOverheadPerUnit(row)
    
    return rowExpensesPerUnit + allocatedOverhead
}

// Calculate margin in KZT
// Formula: Margin = Sale Price - (Purchase Price + Total Expenses)
// Where Total Expenses = Row Expenses + Allocated Overhead
// Note: Always recalculates to reflect current global expenses
const calculateMarginKZT = (row: EquipmentRow): number => {
    // Always recalculate to ensure margin updates when global expenses change
    // Don't use saved margin_kzt as it may be outdated
    if (!row.sale_price_kzt) return 0
    
    const purchasePriceKZT = calculatePurchasePriceKZT(row)
    const totalExpensesKZT = calculateTotalExpensesKZT(row)
    
    return row.sale_price_kzt - purchasePriceKZT - totalExpensesKZT
}

// Calculate margin percentage
// Formula: Margin % = (Margin KZT / Base Cost KZT) * 100
// Where Base Cost KZT = Purchase Price KZT + Row Expenses per unit (WITHOUT allocated_overhead)
// This matches backend formula: margin_percentage = (margin_kzt_per_unit / base_unit_cost_kzt) * 100
const calculateMarginPercentage = (row: EquipmentRow): number => {
    // If we have margin_percentage from data_package, use it (already calculated correctly)
    if (row.margin_percentage !== undefined) {
        return row.margin_percentage
    }
    
    // Otherwise, calculate from margin and base cost
    // Base cost should NOT include allocated_overhead for percentage calculation
    const baseCostKZT = calculateBaseCostKZT(row)
    if (baseCostKZT <= 0) return 0
    
    const marginKZT = calculateMarginKZT(row)
    // Formula: (margin_kzt / base_cost_kzt) * 100
    // This matches backend calculation
    return (marginKZT / baseCostKZT) * 100
}

const calculateRowTotal = (row: EquipmentRow) => {
    const rate = getRate(row.currency)
    const baseCostKZT = row.production_price * rate * row.quantity
    const expensesKZT = calculateRowExpensesSum(row) 
    return baseCostKZT + expensesKZT
}

// Overall Calculation
const totalEquipmentCostKZT = computed(() => {
    return selectedEquipment.value.reduce((sum, row) => sum + calculateRowTotal(row), 0)
})

const totalGlobalExpensesKZT = computed(() => {
    if (!formData.additional_price_ids) return 0
    
    let sum = 0
    formData.additional_price_ids.forEach(id => {
        const ap = additionalPrices.value.find(p => p.price_id === id)
        if (ap) {
            const val = Number(ap.price_parameter_value)
            if (ap.value_type === 'percentage') {
                sum += (totalEquipmentCostKZT.value * val / 100)
            } else {
                sum += val
            }
        }
    })
    return sum
})

const netCostKZT = computed(() => totalEquipmentCostKZT.value + totalGlobalExpensesKZT.value)

// Calculate total margin KZT (sum of all equipment margins)
const totalMarginKZT = computed(() => {
    return selectedEquipment.value.reduce((sum, row) => {
        const marginPerUnit = calculateMarginKZT(row)
        return sum + (marginPerUnit * row.quantity)
    }, 0)
})

// Calculate total margin percentage
// Formula: Total Margin % = (Total Margin KZT / Total Sale Price KZT) * 100
// Маржа рассчитывается только от оборудования, без учета дополнительных услуг
const totalMarginPercentage = computed(() => {
    const totalSalePrice = totalSalePriceKZT.value
    
    if (totalSalePrice <= 0) return 0
    return (totalMarginKZT.value / totalSalePrice) * 100
})

// Calculate total sale price (sum of all equipment sale prices)
const totalSalePriceKZT = computed(() => {
    return selectedEquipment.value.reduce((sum, row) => {
        if (row.sale_price_kzt) {
            return sum + (row.sale_price_kzt * row.quantity)
        }
        return sum
    }, 0)
})

// Calculate total additional services price
const totalAdditionalServicesKZT = computed(() => {
    if (!formData.additional_services || !Array.isArray(formData.additional_services)) {
        return 0
    }
    return formData.additional_services.reduce((sum: number, service: any) => {
        return sum + (Number(service.price) || 0)
    }, 0)
})

// Calculate total proposal price
// Formula: Total Price = Sum of Sale Prices + Additional Services
const calculatedTotalPriceKZT = computed(() => {
    const salePrice = totalSalePriceKZT.value || 0
    const servicesPrice = totalAdditionalServicesKZT.value || 0
    const total = salePrice + servicesPrice
    // Ensure we return a valid number (not NaN or Infinity)
    return isNaN(total) || !isFinite(total) ? 0 : Math.max(0, total)
})

const handleEdit = async (row: CommercialProposal) => {
    isEditMode.value = true
    
    // Reset form first
    Object.assign(formData, {
        proposal_name: '', outcoming_number: '', client_id: undefined,
        proposal_date: new Date().toISOString().split('T')[0] || '',
        total_price: '0', proposal_status: 'draft', proposal_version: 1, additional_price_ids: [],
        comments: '', bitrix_lead_link: '', delivery_time: '', warranty: ''
    })
    selectedEquipment.value = []

    try {
        loading.value = true // Or a local loading state for dialog
        
        // Fetch Live Rates
        try {
           const rates = await exchangeRatesAPI.getRates({ latest: true })
           liveRates.value = rates
        } catch(e) { console.error(e) }

        // Fetch full details
        const fullProp = await proposalsAPI.getProposalById(row.proposal_id)
        
        // Populate formData
        formData.proposal_id = fullProp.proposal_id
        formData.proposal_name = fullProp.proposal_name
        formData.outcoming_number = fullProp.outcoming_number
        formData.client_id = fullProp.client?.client_id
        formData.proposal_date = fullProp.proposal_date
        formData.valid_until = fullProp.valid_until
        formData.delivery_time = fullProp.delivery_time
        formData.warranty = fullProp.warranty
        formData.proposal_status = fullProp.proposal_status
        formData.proposal_version = fullProp.proposal_version
        formData.comments = fullProp.comments
        formData.bitrix_lead_link = fullProp.bitrix_lead_link
        formData.exchange_rate = fullProp.exchange_rate
        formData.currency_ticket = fullProp.currency_ticket
        formData.exchange_rate = fullProp.exchange_rate
        formData.currency_ticket = fullProp.currency_ticket
        formData.total_price = fullProp.total_price // Restore total price
        // Restore additional services
        formData.additional_services = (fullProp.additional_services as any) || []
        
        // Маржа теперь рассчитывается автоматически на бэкенде
        // margin_value и margin_percentage будут заполнены автоматически
        
        // Restore internal rates if saved
        if ((fullProp as any).internal_exchange_rates && Array.isArray((fullProp as any).internal_exchange_rates) && (fullProp as any).internal_exchange_rates.length > 0) {
             // Map saved rates, enrich with current live rate
             internalExchangeRates.value = (fullProp as any).internal_exchange_rates.map((saved: any) => ({
                 ...saved,
                 current_nb_rate: getLiveRate(saved.currency),
                 // Fallback for legacy data
                 creation_nb_rate: saved.creation_nb_rate || saved.nb_rate || getLiveRate(saved.currency),
                 rate_date: saved.rate_date || fullProp.created_at?.split('T')[0] || new Date().toISOString().split('T')[0]
             }))
        } else {
            // Default fallback if legacy proposal
            internalExchangeRates.value = [] // Will be populated by watcher based on equipment
        }
        
        // Populate Equipment
        // First, try to get data from data_package (if proposal was saved and calculated)
        const dataPackage = (fullProp as any).data_package
        const equipmentListFromDataPackage = dataPackage?.equipment_list || []
        
        if (fullProp.equipment_lists && fullProp.equipment_lists.length > 0) {
            const list = fullProp.equipment_lists[0]
            if (list && list.equipment_items_data) {
                // Load basic equipment data first (without calculated fields)
                // Calculated fields will be updated from equipment cards
                selectedEquipment.value = list.equipment_items_data.map((item: any) => {
                    // Try to find corresponding item in data_package (fallback)
                    const dataPackageItem = equipmentListFromDataPackage.find(
                        (dpItem: any) => dpItem.equipment_id === item.equipment
                    )
                    
                    // Use saved price_per_unit from EquipmentListItem if available (this is the final calculated price)
                    // Otherwise fall back to data_package price_per_unit
                    const savedPricePerUnit = item.price_per_unit || dataPackageItem?.price_per_unit
                    
                    return {
                        equipment_id: item.equipment,
                        equipment_name: item.equipment_name,
                        quantity: item.quantity,
                        row_expenses: item.row_expenses || [],
                        equipment_manufacture_price: 0,
                        equipment_price_currency_type: 'KZT',
                        production_price: 0,
                        currency: 'KZT',
                        // Will be set from equipment cards
                        purchase_price_original: undefined,
                        purchase_price_currency: undefined,
                        // Calculated fields will be cleared and recalculated after updating from equipment cards
                        purchase_price_kzt: undefined,
                        base_cost_kzt: undefined,
                        allocated_overhead_per_unit: undefined,
                        margin_kzt: undefined,
                        margin_percentage: undefined,
                        // Use saved price_per_unit from EquipmentListItem (final calculated price after overhead distribution)
                        sale_price_kzt: savedPricePerUnit ? parseFloat(savedPricePerUnit) : dataPackageItem?.price_per_unit ? parseFloat(dataPackageItem.price_per_unit) : undefined,
                    }
                })
                
                // Post-process to add equipment details (prices) from global equipment list
                selectedEquipment.value.forEach(row => {
                   const eq = equipmentList.value.find(e => e.equipment_id === row.equipment_id)
                   if (eq) {
                       // Обновляем только базовые поля оборудования
                       row.equipment_manufacture_price = parseFloat(eq.equipment_manufacture_price as unknown as string) || 0
                       row.equipment_price_currency_type = eq.equipment_price_currency_type || 'KZT'
                       row.production_price = parseFloat(eq.equipment_manufacture_price as unknown as string) || 0
                       row.currency = eq.equipment_price_currency_type || 'KZT'
                       
                       // Set purchase price currency and original price
                       row.purchase_price_currency = eq.equipment_price_currency_type || 'KZT'
                       row.purchase_price_original = parseFloat(eq.equipment_manufacture_price as unknown as string) || 0
                       
                       // Use saved price_per_unit if available, otherwise use equipment sale_price_kzt
                       if (row.sale_price_kzt === undefined && eq.sale_price_kzt) {
                           row.sale_price_kzt = parseFloat(eq.sale_price_kzt as unknown as string)
                       }
                   }
                })
            }
            
            // Populate Global Expenses
            if (list && list.additional_prices && Array.isArray(list.additional_prices)) {
                 formData.additional_price_ids = list.additional_prices as any
            }
        }

        // Load payments
        if (fullProp.payment_logs && Array.isArray(fullProp.payment_logs)) {
            tempPayments.value = fullProp.payment_logs.map((p: any) => ({
                payment_id: p.payment_id,
                payment_name: p.payment_name,
                payment_value: Number(p.payment_value),
                payment_date: p.payment_date,
                comments: p.comments || '',
                user_name: p.user_name,
                user: p.user
            }))
        } else {
            tempPayments.value = []
        }
        
        activeTab.value = 'basic'
        dialogVisible.value = true
    } catch (e) {
        console.error(e)
        ElMessage.error('Ошибка при загрузке данных КП')
    } finally {
        loading.value = false
    }
}

// Маржа теперь рассчитывается автоматически на бэкенде
// calculateFinalProposalPrice и marginKZT больше не нужны

// Submit
const handleSubmit = async () => {
    if(!formRef.value) return
    await formRef.value.validate(async (valid, fields) => {
        if(valid) {
            submitting.value = true
            try {
                // Итоговая цена и маржа рассчитываются автоматически на бэкенде
                // на основе sale_price_kzt оборудования
                // Если total_price не указан, бэкенд рассчитает его автоматически

                // Prepare full payload
                const payload = { ...formData }
                
                // Remove margin fields - они теперь рассчитываются автоматически на бэкенде
                delete payload.margin_value
                delete payload.margin_percentage
                
                // Set calculated total price (sum of sale prices + additional services)
                // Ensure it's a valid number
                const totalPrice = calculatedTotalPriceKZT.value
                if (isNaN(totalPrice) || !isFinite(totalPrice) || totalPrice < 0) {
                    ElMessage.error('Некорректная итоговая цена. Проверьте цены оборудования.')
                    submitting.value = false
                    return
                }
                payload.total_price = totalPrice.toFixed(2) // Format to 2 decimal places
                
                // Auto-increment version if editing
                if (isEditMode.value) {
                    payload.proposal_version = (payload.proposal_version || 1) + 1
                }

                // Add internal exchange rates snapshot
                payload.internal_exchange_rates = internalExchangeRates.value

                // Add equipment items with calculated_data
                if (selectedEquipment.value.length > 0) {
                    payload.equipment_items = selectedEquipment.value.map(item => {
                        // Calculate values if not already set
                        const purchasePriceKZT = item.purchase_price_kzt !== undefined 
                            ? item.purchase_price_kzt 
                            : calculatePurchasePriceKZT(item)
                        const baseCostKZT = item.base_cost_kzt !== undefined 
                            ? item.base_cost_kzt 
                            : calculateBaseCostKZT(item)
                        const allocatedOverhead = item.allocated_overhead_per_unit !== undefined 
                            ? item.allocated_overhead_per_unit 
                            : 0
                        const marginKZT = item.margin_kzt !== undefined 
                            ? item.margin_kzt 
                            : calculateMarginKZT(item)
                        const marginPercentage = item.margin_percentage !== undefined 
                            ? item.margin_percentage 
                            : calculateMarginPercentage(item)
                        
                        return {
                            equipment_id: item.equipment_id,
                            quantity: item.quantity,
                            row_expenses: item.row_expenses || [],
                            calculated_data: {
                                purchase_price_kzt: purchasePriceKZT || null,
                                base_cost_kzt: baseCostKZT || null,
                                allocated_overhead_per_unit: allocatedOverhead || null,
                                margin_kzt: marginKZT || null,
                                margin_percentage: marginPercentage || null
                            }
                        }
                    })
                }

                // Add payments
                (payload as any).payment_logs = tempPayments.value.map(p => ({
                    ...p,
                    payment_value: p.payment_value.toString() // Ensure string format for Decimal
                }))

                if (isEditMode.value && formData.proposal_id) { 
                     await proposalsAPI.updateProposal(formData.proposal_id, payload)
                     ElMessage.success('КП успешно обновлено')
                } else {
                     await proposalsAPI.createProposal(payload)
                     ElMessage.success('КП успешно создано')
                }

                dialogVisible.value = false
                loadData()
            } catch(e: any) {
                console.error(e)
                let msg = e.message
                if (e.response?.data) {
                    if (typeof e.response.data === 'object') {
                        msg = Object.entries(e.response.data)
                            .map(([key, val]) => `${key}: ${Array.isArray(val) ? val.join(', ') : val}`)
                            .join('; ')
                    } else {
                        msg = JSON.stringify(e.response.data)
                    }
                }
                ElMessage.error(`Ошибка при сохранении КП: ${msg}`)
            } finally {
                submitting.value = false
            }
        } else {
            console.warn('Validation failed:', fields)
            ElMessage.warning('Пожалуйста, заполните все обязательные поля корректно')
            
            // Switch to basic tab if main fields have errors
            if (fields && (fields.proposal_name || fields.outcoming_number || fields.client_id)) {
                activeTab.value = 'basic'
            }
        }
    })
}

// --- Utils ---
const formatDate = (d: string) => d ? format(new Date(d), 'dd.MM.yyyy') : ''
const getStatusTagType = (status: string) => {
    const map: Record<string, string> = { draft: 'info', sent: 'warning', accepted: 'success', completed: 'success', rejected: 'danger' }
    return map[status] || 'info'
}
const getStatusLabel = (s: string) => s 

// Additional Prices
const loadAdditionalPrices = async () => {
    loadingAdditionalPrices.value = true
    try {
        const res = await additionalPricesAPI.getAdditionalPrices()
        additionalPrices.value = res
    } finally {
        loadingAdditionalPrices.value = false
    }
}
const handleCreateAdditionalPrice = () => {
    // simplified
    showAdditionalPriceFormDialog.value = true
}
const handleSubmitAdditionalPrice = async () => {
    // simplified
    try {
        await additionalPricesAPI.createAdditionalPrice({
            price_parameter_name: additionalPriceForm.price_parameter_name,
            expense_type: 'other', // default
            value_type: additionalPriceForm.value_type as any,
            price_parameter_value: String(additionalPriceForm.price_parameter_value)
        })
        showAdditionalPriceFormDialog.value = false
        loadAdditionalPrices()
    } catch (e) { console.error(e) }
}
const handleDeleteAdditionalPrice = async (row: AdditionalPrice) => {
    await additionalPricesAPI.deleteAdditionalPrice(row.price_id)
    loadAdditionalPrices()
}
const handleCopy = async (row: CommercialProposal) => {
    try {

        await ElMessageBox.confirm(
            `Вы уверены, что хотите создать копию КП "${row.outcoming_number}"?`,
            'Подтверждение копирования',
            {
                confirmButtonText: 'Да',
                cancelButtonText: 'Нет',
                type: 'info',
            }
        )

        await proposalsAPI.copyProposal(row.proposal_id)
        ElMessage.success('Копия коммерческого предложения успешно создана')
        loadData()
    } catch (error) {
        if (error !== 'cancel') {
            console.error('Failed to copy proposal:', error)
            ElMessage.error('Не удалось создать копию коммерческого предложения')
        }
    }
}

// Additional Services Methods
const openAdditionalServicesDialog = () => {
    currentAdditionalService.name = ''
    currentAdditionalService.price = 0
    currentAdditionalService.description = ''
    showAdditionalServicesDialog.value = true
}

const addAdditionalService = () => {
    if (!currentAdditionalService.name) {
        ElMessage.warning('Введите название услуги')
        return
    }
    if (!formData.additional_services) {
        formData.additional_services = []
    }
    // We push a copy
    formData.additional_services.push({ ...currentAdditionalService })
    showAdditionalServicesDialog.value = false
    
    // Auto-update total price if needed (per requirement: real-time update)
    // We can call calculateFinalProposalPrice or a lighter version
    updateTotalPriceWithServices()
}

const removeAdditionalService = (index: number) => {
    if (formData.additional_services) {
        formData.additional_services.splice(index, 1)
        updateTotalPriceWithServices()
    }
}

const updateTotalPriceWithServices = () => {
    // Only update if we already have a valid calculation
    // Base calculation: NetCost + Margin
    // Итоговая цена теперь рассчитывается автоматически на бэкенде
    // на основе sale_price_kzt оборудования
    // Если total_price не указан, бэкенд рассчитает его автоматически
}

const handleDelete = async (row: CommercialProposal) => {
    try {
        await ElMessageBox.confirm(
            'Вы уверены, что хотите архивировать это КП? Оно перестанет отображаться в общем списке.',
            'Подтверждение архивации',
            {
                confirmButtonText: 'Архивировать',
                cancelButtonText: 'Отмена',
                type: 'warning',
            }
        )
        await proposalsAPI.deleteProposal(row.proposal_id)
        ElMessage.success('КП успешно архивировано')
        loadData()
    } catch (e) {
        // cancel
    }
}

// Open equipment card dialog
const openEquipmentCardDialog = async (equipmentId: number) => {
    equipmentCardDialogVisible.value = true
    loadingEquipmentCard.value = true
    currentEquipmentCard.value = null
    
    try {
        const equipment = await equipmentAPI.getEquipmentById(equipmentId)
        currentEquipmentCard.value = equipment
    } catch (error: any) {
        console.error('Failed to load equipment card:', error)
        ElMessage.error('Не удалось загрузить данные оборудования')
        currentEquipmentCard.value = null
    } finally {
        loadingEquipmentCard.value = false
    }
}

// Close equipment card dialog
const closeEquipmentCardDialog = () => {
    equipmentCardDialogVisible.value = false
    currentEquipmentCard.value = null
}

// Get image preview list for el-image component
const getImagePreviewList = (): string[] => {
    if (!currentEquipmentCard.value?.equipment_imagelinks) return []
    return currentEquipmentCard.value.equipment_imagelinks.map((img: any) => 
        typeof img === 'string' ? img : img.url
    ).filter(Boolean)
}

onMounted(async () => {
    await loadData()
    
    // Check if we need to open edit modal from query parameter
    const editId = route.query.edit
    if (editId) {
        const proposalId = parseInt(editId as string)
        if (!isNaN(proposalId)) {
            // Find the proposal in the list
            const proposal = proposalsList.value.find(p => p.proposal_id === proposalId)
            if (proposal) {
                // Wait a bit for the component to be fully mounted
                await nextTick()
                handleEdit(proposal)
                // Remove query parameter from URL
                router.replace({ query: {} })
            }
        }
    }
})
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.filters { margin-bottom: 20px; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
.text-gray-400 { color: #9ca3af; }
.expense-tag-container { display: flex; align-items: center; margin-bottom: 4px; }
.expense-tag { font-size: 0.85em; background: #f3f4f6; padding: 2px 6px; border-radius: 4px; flex: 1; }
.calculation-section h3 { margin-bottom: 15px; color: #303133; }
.rates-summary { margin-bottom: 20px; }
.mx-1 { margin: 0 4px; }
.summary-card { width: 600px; margin-bottom: 20px; }
.summary-row { display: flex; justify-content: space-between; margin-bottom: 8px; }
.margin-block { width: 600px; }
.w-100 { width: 100%; }
.mr-2 { margin-right: 8px; }
.final-price-display { margin-top: 20px; font-size: 1.2em; border-top: 1px solid #eba4a4; padding-top: 10px; display: flex; justify-content: space-between; font-weight: bold; color: #F56C6C; }
</style>
