<template>
  <div class="additional-services-table" v-if="services.length > 0">
    <table class="services-table">
      <thead>
        <tr>
          <th :style="{ width: colWidths.description + 'px' }" class="resizable-th">
            Описание
            <div class="resizer" @mousedown="startResizing('description', $event)"></div>
          </th>
          <th class="text-right">Стоимость</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(service, index) in services" :key="index">
          <td>{{ service.description || service.name }}</td>
          <td class="text-right">{{ formatPrice(service.price, currency) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onUnmounted } from 'vue'

const props = defineProps<{
  dataPackage: any,
  columnWidths?: { description: number }
}>()

const emit = defineEmits(['update:columnWidths'])

const services = computed(() => {
  return props.dataPackage?.additional_services || []
})

const currency = computed(() => {
  return props.dataPackage?.proposal?.currency || 'KZT'
})

const colWidths = ref({
  description: props.columnWidths?.description || 400
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
  const newWidth = Math.max(50, startWidth.value + deltaX)
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

const formatPrice = (value: number | string, currency: string) => {
  const num = Number(value)
  return new Intl.NumberFormat('ru-RU', {
    style: 'decimal',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(num) + ' ' + currency
}
</script>

<style scoped>
.additional-services-table {
  margin: 20px 0;
}

.services-table {
  width: 100%;
  border-collapse: collapse;
  font-family: Arial, sans-serif;
  font-size: 10pt;
}

.services-table th,
.services-table td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
  position: relative;
  overflow: hidden;
  text-overflow: ellipsis;
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

.services-table th {
  background-color: #f2f2f2;
  font-weight: bold;
}

.text-right {
  text-align: right;
  width: 150px;
}
</style>
