<template>
  <div class="proposal-specs-container">
    <div v-for="item in items" :key="item.equipment_id" class="spec-block">
      <div v-if="hasSpecs(item.equipment_id)">
        <h3>{{ item.name }}</h3>
        
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
              <!-- Combined row for video link -->
              <template v-if="spec.is_video_link">
                <td colspan="2" class="col-combined">
                  <span v-html="formatVideoLink(spec.name)"></span>
                </td>
              </template>
              <template v-else>
                <td class="col-param">{{ spec.name }}</td>
                <td class="col-value">
                  <template v-if="String(spec.value).startsWith('http')">
                    <a :href="spec.value" target="_blank" class="clickable-link">{{ spec.value }}</a>
                  </template>
                  <template v-else>
                    {{ spec.value }}
                  </template>
                </td>
              </template>

              <!-- Image Cell (handles rowspan) -->
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

const formatVideoLink = (text: string) => {
  if (!text) return ''
  const urlRegex = /(https?:\/\/[^\s]+)/g
  return text.replace(urlRegex, (url) => `<a href="${url}" target="_blank" class="clickable-link">${url}</a>`)
}

const getImages = (equipmentId: number): { name: string; url: string }[] => {
  const item = items.value.find((i: any) => i.equipment_id === equipmentId)
  return (item?.images && Array.isArray(item.images)) ? item.images : []
}

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
  font-family: 'Times New Roman', Times, serif;
  font-size: 13.3px; /* 10pt */
}
.clickable-link {
  color: blue;
  text-decoration: underline;
  word-break: break-all;
}
.spec-block {
  margin-bottom: 20px;
}
h3 {
  margin-bottom: 5px;
  font-size: 10pt;
  font-weight: bold;
  border-bottom: 1px solid #eee;
}
.specs-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 10px;
  table-layout: fixed;
}
.specs-table th,
.specs-table td {
  border: 1px solid #333;
  padding: 4px;
  text-align: left;
  vertical-align: top;
  font-size: 10pt;
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
.col-combined {
  width: 55%; /* Sum of 35% and 20% */
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
  padding: 2px;
}
.spec-photo {
  max-width: 95%;
  height: auto;
  object-fit: contain;
}
.spec-photo-caption {
  margin-top: 4px;
  font-size: 8pt;
  color: #666;
}
</style>
