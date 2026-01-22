<template>
  <div class="proposal-table-container">
    <table class="proposal-table">
      <thead>
        <tr>
          <th style="width: 40px">№</th>
          <th :style="{ width: colWidths.name + 'px' }" class="resizable-th">
            Наименование
            <div class="resizer" @mousedown="startResizing('name', $event)"></div>
          </th>
          <th style="width: 60px">Кол-во</th>
          <th style="width: 60px">Ед.</th>
          <th style="width: 100px">Цена за ед.</th>
          <th style="width: 100px">Сумма</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(item, index) in items" :key="item.equipment_id">
          <td>{{ Number(index) + 1 }}</td>
          <td>
            <div class="item-name">{{ item.name }}</div>
            <div class="item-desc" v-if="item.description">{{ item.description }}</div>
            <div class="item-article" v-if="item.article">Арт: {{ item.article }}</div>
          </td>
          <td class="text-center">{{ item.quantity }}</td>
          <td class="text-center">{{ item.unit }}</td>
          <td class="text-right whitespace-nowrap">{{ formatPrice(item.price_per_unit) }} {{ currency }}</td>
          <td class="text-right whitespace-nowrap">{{ formatPrice(item.total_price) }} {{ currency }}</td>
        </tr>
        <!-- Итого строка -->
        <tr class="total-row">
          <td colspan="5" style="text-align: right; font-weight: bold; padding: 8px; background-color: #f5f5f5;">Итого:</td>
          <td class="text-right whitespace-nowrap" style="font-weight: bold; padding: 8px; background-color: #f5f5f5;">
            {{ formatPrice(totalEquipmentSum) }} {{ currency }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onUnmounted } from 'vue'

const props = defineProps<{
  dataPackage: any,
  columnWidths?: { name: number }
}>()

const emit = defineEmits(['update:columnWidths'])

const items = computed(() => props.dataPackage?.equipment_list || [])
const currency = computed(() => props.dataPackage?.proposal?.currency || '')

// Calculate total sum for equipment only
const totalEquipmentSum = computed(() => {
  return items.value.reduce((sum, item) => {
    return sum + (parseFloat(item.total_price) || 0)
  }, 0)
})

const formatPrice = (value: number) => {
  return new Intl.NumberFormat('ru-RU', {
    style: 'decimal',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value)
}

const colWidths = ref({
  name: props.columnWidths?.name || 300
})

const isResizing = ref(false)
const currentResizer = ref<string | null>(null)
const startX = ref(0)
const startWidth = ref(0)

const startResizing = (col: string, event: MouseEvent) => {
  isResizing.value = true
  currentResizer.value = col
  startX.value = event.clientX
  startWidth.value = (colWidths.value as any)[col]
  
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', stopResizing)
  event.preventDefault()
}

const handleMouseMove = (event: MouseEvent) => {
  if (!isResizing.value || !currentResizer.value) return
  const deltaX = event.clientX - startX.value
  const newWidth = Math.max(100, startWidth.value + deltaX)
  ;(colWidths.value as any)[currentResizer.value] = newWidth
}

const stopResizing = () => {
  isResizing.value = false
  currentResizer.value = null
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', stopResizing)
  emit('update:columnWidths', { ...colWidths.value })
}

onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', stopResizing)
})
</script>

<style scoped>
.proposal-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 20px;
  font-family: Arial, sans-serif;
  font-size: 10pt;
}

.proposal-table th, .proposal-table td {
  border: 1px solid #ddd;
  padding: 8px;
  vertical-align: top;
  position: relative;
  overflow: hidden;
  text-overflow: ellipsis;
}

.proposal-table th {
  background-color: #f2f2f2;
  text-align: left;
  font-weight: bold;
}

.resizable-th {
  position: relative;
}

.resizer {
  position: absolute;
  right: 0;
  top: 0;
  width: 5px;
  cursor: col-resize;
  user-select: none;
  height: 100%;
  z-index: 1;
}

.resizer:hover {
  background: #409eff;
}

.text-center { text-align: center; }
.text-right { text-align: right; }
.whitespace-nowrap { white-space: nowrap; }

.item-name { font-weight: bold; }
.item-desc { font-size: 0.9em; color: #000; margin-top: 4px; }
.item-article { font-size: 0.8em; color: #000; margin-top: 2px; }

.total-row {
  background-color: #f5f5f5;
  border-top: 2px solid #333;
}

.total-row td {
  border-top: 2px solid #333;
}
</style>
