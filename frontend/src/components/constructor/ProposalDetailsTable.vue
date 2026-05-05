<template>
  <div class="proposal-details-container">
    <div v-for="item in items" :key="item.equipment_id" class="detail-block">
      <div v-if="hasDetails(item.equipment_id)">
        <h3>{{ item.name }}</h3>
        <table class="details-table">
          <tbody>
            <tr v-for="(detail, idx) in getDetails(item.equipment_id)" :key="idx">
              <td class="col-param"><strong>{{ detail.name }}</strong></td>
              <td class="col-value">{{ detail.value }}</td>
            </tr>
          </tbody>
        </table>
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
  const details = detailsMap.value[id] || detailsMap.value[String(id)]
  return details && details.length > 0
}

const getDetails = (id: number) => {
  return detailsMap.value[id] || detailsMap.value[String(id)] || []
}
</script>

<style scoped>
.proposal-details-container {
  font-family: 'Times New Roman', Times, serif;
  font-size: 13.3px; /* 10pt */
}
.detail-block {
  margin-bottom: 15px;
}
h3 {
  margin-bottom: 5px;
  font-size: 10pt;
  font-weight: bold;
  border-bottom: 1px solid #eee;
}
.details-table {
  width: 100%;
  border-collapse: collapse;
}
.details-table td {
  border: 1px solid #333;
  padding: 4px;
  font-size: 10pt;
}
.col-param {
  width: 35%;
}
</style>
