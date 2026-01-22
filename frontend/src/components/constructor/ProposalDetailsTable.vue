<template>
  <div class="proposal-details-container">
    <div v-for="item in items" :key="item.equipment_id" class="detail-block">
      <div v-if="hasDetails(item.equipment_id)">
        <h3>{{ item.name }}</h3>
        <ul>
          <li v-for="(detail, idx) in getDetails(item.equipment_id)" :key="idx">
            <strong>{{ detail.name }}:</strong> {{ detail.value }}
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  dataPackage: any
}>()

const items = computed(() => props.dataPackage?.equipment_list || [])
const detailsMap = computed(() => props.dataPackage?.equipment_details || {})

const hasDetails = (id: number) => {
  return detailsMap.value[id] && detailsMap.value[id].length > 0
}

const getDetails = (id: number) => {
  return detailsMap.value[id] || []
}
</script>

<style scoped>
.proposal-details-container {
  font-family: Arial, sans-serif;
  font-size: 10pt;
}
.detail-block {
  margin-bottom: 15px;
}
h3 {
  margin-bottom: 8px;
  font-size: 1.1em;
}
ul {
  list-style-type: disc;
  padding-left: 20px;
  margin: 0;
}
li {
  margin-bottom: 4px;
}
</style>
