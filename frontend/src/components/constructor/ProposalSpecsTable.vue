<template>
  <div class="proposal-specs-container">
    <div v-for="item in items" :key="item.equipment_id" class="spec-block">
      <div v-if="hasSpecs(item.equipment_id)">
        <h3>{{ item.name }}</h3>
        
        <!-- Table -->
        <table class="specs-table">
          <thead>
             <tr>
               <th :style="{ width: colWidths.param + 'px' }" class="resizable-th">
                 Параметр
                 <div class="resizer" @mousedown="startResizing('param', $event)"></div>
               </th>
               <th>Значение</th>
             </tr>
          </thead>
          <tbody>
            <tr v-for="(spec, idx) in getSpecs(item.equipment_id)" :key="idx">
              <td>{{ spec.name }}</td>
              <td>{{ spec.value }}</td>
            </tr>
          </tbody>
        </table>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onUnmounted } from 'vue'

const props = defineProps<{
  dataPackage: any,
  columnWidths?: { param: number }
}>()

const emit = defineEmits(['update:columnWidths'])

const items = computed(() => props.dataPackage?.equipment_list || [])
const specsMap = computed(() => props.dataPackage?.equipment_specifications || {})

const hasSpecs = (id: number) => {
  return specsMap.value[id] && specsMap.value[id].length > 0
}

const getSpecs = (id: number) => {
  return specsMap.value[id] || []
}

const colWidths = ref({
  param: props.columnWidths?.param || 200
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
</script>

<style scoped>
.proposal-specs-container {
  font-family: Arial, sans-serif;
  font-size: 10pt;
}
.spec-block {
  margin-bottom: 25px;
  page-break-inside: avoid;
}
h3 {
  margin-bottom: 10px;
  font-size: 1.1em;
  color: #000;
}
.specs-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 15px;
}
.specs-table th, .specs-table td {
  border: 1px solid #ddd;
  padding: 6px;
  text-align: left;
  position: relative;
  overflow: hidden;
  text-overflow: ellipsis;
}
.specs-table th {
  background-color: #f9f9f9;
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
</style>
