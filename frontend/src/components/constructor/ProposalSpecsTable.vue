<template>
  <div class="proposal-specs-container">
    <div v-for="item in items" :key="item.equipment_id" class="spec-block">
      <div v-if="hasSpecs(item.equipment_id)">
        <h3>{{ item.name }}</h3>
        
        <!-- Table: Параметр 35%, Значение 20%, Изображение 45% -->
        <table class="specs-table">
          <thead>
             <tr>
               <th class="col-param">Параметр</th>
               <th class="col-value">Значение</th>
               <th class="col-image">Изображение</th>
             </tr>
          </thead>
          <tbody>
            <tr v-for="(spec, rowIndex) in getSpecs(item.equipment_id)" :key="rowIndex">
              <td class="col-param">{{ spec.name }}</td>
              <td class="col-value">{{ spec.value }}</td>
              <td
                v-if="getImageCellAt(item.equipment_id, rowIndex)"
                v-bind="getImageCellAt(item.equipment_id, rowIndex)!.attrs"
                class="col-image cell-image"
              >
                <div v-if="getImageCellAt(item.equipment_id, rowIndex)!.photo.url" class="image-cell-inner">
                  <img
                    :src="getImageSrc(getImageCellAt(item.equipment_id, rowIndex)!.photo.url)"
                    class="spec-photo"
                    @error="handleImageError"
                  />
                  <span v-if="getImageCellAt(item.equipment_id, rowIndex)!.photo.name" class="spec-photo-caption">
                    {{ getImageCellAt(item.equipment_id, rowIndex)!.photo.name }}
                  </span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { getImageSrc } from '@/utils/imageProxy'

const props = defineProps<{
  dataPackage: any
  /** Не используется: ширина столбцов фиксирована 35% / 20% / 45%. Оставлено для совместимости с конструктором. */
  columnWidths?: Record<string, number>
}>()

const items = computed(() => props.dataPackage?.equipment_list || [])
const specsMap = computed(() => props.dataPackage?.equipment_specifications || {})

const hasSpecs = (id: number) => {
  return specsMap.value[id] && specsMap.value[id].length > 0
}

const getSpecs = (id: number) => {
  return specsMap.value[id] || []
}

/** Фото оборудования по equipment_id (из equipment_list[].images) */
const getImages = (equipmentId: number): { name: string; url: string }[] => {
  const item = items.value.find((i: any) => i.equipment_id === equipmentId)
  return (item?.images && Array.isArray(item.images)) ? item.images : []
}

/**
 * Равномерное распределение фото по строкам третьего столбца.
 * Возвращает для данной строки ячейку с rowspan и фото, если в этой строке начинается новая ячейка; иначе null.
 */
interface ImageCellInfo {
  attrs: { rowspan: number }
  photo: { name: string; url: string }
}
const getImageCellAt = (equipmentId: number, rowIndex: number): ImageCellInfo | null => {
  const specs = getSpecs(equipmentId)
  const images = getImages(equipmentId)
  const totalRows = specs.length
  if (totalRows === 0) return null

  if (images.length === 0) {
    // Одна пустая ячейка на всю высоту — показываем только в первой строке
    return rowIndex === 0 ? { attrs: { rowspan: totalRows }, photo: { name: '', url: '' } } : null
  }

  const numPhotos = images.length
  const baseRowspan = Math.floor(totalRows / numPhotos)
  const remainder = totalRows % numPhotos
  let startRow = 0
  for (let i = 0; i < numPhotos; i++) {
    const rowspan = i < remainder ? baseRowspan + 1 : baseRowspan
    if (rowIndex === startRow) {
      return { attrs: { rowspan }, photo: images[i] }
    }
    startRow += rowspan
  }
  return null
}

const handleImageError = (e: Event) => {
  const target = e.target as HTMLImageElement
  target.style.display = 'none'
}
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
  table-layout: fixed;
}
.specs-table th,
.specs-table td {
  border: 1px solid #ddd;
  padding: 6px;
  text-align: left;
  vertical-align: top;
  overflow: hidden;
  text-overflow: ellipsis;
}
.specs-table th {
  background-color: #f9f9f9;
}
.col-param {
  width: 35%;
}
.col-value {
  width: 20%;
}
.col-image {
  width: 45%;
}
.cell-image {
  vertical-align: middle;
  text-align: center;
}
.image-cell-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60px;
  padding: 4px;
}
.spec-photo {
  width: 95%;
  height: auto;
  object-fit: contain;
  display: block;
}
.spec-photo-caption {
  margin-top: 4px;
  font-size: 8pt;
  color: #666;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}
</style>
