<template>
  <div class="proposal-tech-container">
    <div v-for="item in items" :key="item.equipment_id" class="tech-block">
      <div v-if="hasTech(item.equipment_id)">
        <h3>{{ item.name }} - Технологический процесс</h3>
        
        <div v-for="(proc, idx) in getTech(item.equipment_id)" :key="idx" class="tech-item">
           <h4>{{ proc.title }}</h4>
           <p v-if="proc.value"><strong>Значение:</strong> {{ proc.value }}</p>
           <p v-if="proc.desc">{{ proc.desc }}</p>
        </div>
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
const techMap = computed(() => props.dataPackage?.tech_processes || {})

const hasTech = (id: number) => {
  return techMap.value[id] && techMap.value[id].length > 0
}

const getTech = (id: number) => {
  return techMap.value[id] || []
}
</script>

<style scoped>
.proposal-tech-container {
  font-family: Arial, sans-serif;
  font-size: 10pt;
}
.tech-block {
  margin-bottom: 20px;
}
h3 {
  border-bottom: 1px solid #ddd;
  padding-bottom: 5px;
  margin-bottom: 15px;
}
.tech-item {
  background: #f9f9f9;
  padding: 10px;
  margin-bottom: 10px;
  border-radius: 4px;
}
.tech-item h4 {
  margin-top: 0;
  margin-bottom: 5px;
  color: #000;
}
.tech-item p {
  margin: 5px 0;
}
</style>
