<template>
  <div class="photo-grids-container">
    <div v-for="item in itemsWithImages" :key="item.equipment_id" class="photo-grid-module">
      <table class="photo-grid-table">
        <thead>
          <tr>
            <th colspan="2" class="equipment-title-cell">{{ item.name }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in chunkImages(item.images)" :key="row.map(img => img.url).join('')">
            <td v-for="(img, imgIndex) in row" :key="imgIndex" class="photo-cell">
              <div v-if="img && img.url" class="photo-wrapper">
                <img :src="getImageSrc(img.url)" class="equipment-photo" @error="handleImageError" />
                <div v-if="img.name" class="photo-caption">{{ img.name }}</div>
              </div>
            </td>
            <!-- Fill empty cell if row is not full -->
            <td v-if="row.length === 1" class="photo-cell"></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { getImageSrc } from '@/utils/imageProxy'

const props = defineProps<{
  dataPackage: any
}>()

const itemsWithImages = computed(() => {
  return (props.dataPackage?.equipment_list || []).filter((item: any) => item.images && item.images.length > 0)
})

const chunkImages = (images: {name: string, url: string}[]) => {
  const chunks = []
  for (let i = 0; i < images.length; i += 2) {
    chunks.push(images.slice(i, i + 2))
  }
  return chunks
}

const handleImageError = (e: Event) => {
  const target = e.target as HTMLImageElement
  target.style.display = 'none'
}
</script>

<style scoped>
.photo-grids-container {
  width: 100%;
}

.photo-grid-module {
  margin-bottom: 30px;
  page-break-inside: avoid;
}

.photo-grid-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.equipment-title-cell {
  background-color: #f9f9f9;
  border: 1px solid #eee;
  padding: 10px;
  text-align: left;
  font-weight: bold;
  font-size: 11pt;
}

.photo-cell {
  width: 50%;
  height: 70mm; /* Mandatory 70mm height */
  border: 1px solid #eee;
  overflow: hidden;
  text-align: center;
  padding: 5px;
  vertical-align: middle;
}

.photo-wrapper {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.equipment-photo {
  max-width: 100%;
  max-height: 85%; /* Leave space for caption */
  object-fit: contain; /* Maintain proportions */
  display: block;
}

.photo-caption {
  margin-top: 4px;
  font-size: 9pt;
  color: #666;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

@media print {
  .photo-cell {
    height: 70mm !important;
  }
}
</style>
