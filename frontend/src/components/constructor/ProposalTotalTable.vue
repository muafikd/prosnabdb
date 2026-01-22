<template>
  <div class="proposal-total-container">
    <div class="total-box">
       <div class="total-row">
          <h3>Итого: {{ formattedTotal }} {{ currency }}</h3>
       </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  dataPackage: any
}>()

const additionalServices = computed(() => props.dataPackage?.additional_services || [])

const total = computed(() => {
    // Prefer total_price from proposal if available as it includes everything including services
    if (props.dataPackage?.proposal?.total_price) {
        return Number(props.dataPackage.proposal.total_price)
    }
    // Fallback calculation (might be inaccurate if services are not added)
    const items = props.dataPackage?.equipment_list || []
    const eqTotal = items.reduce((sum: number, item: any) => sum + (item.total_price || 0), 0)
    const svcTotal = additionalServices.value.reduce((sum: number, svc: any) => sum + Number(svc.price || 0), 0)
    return eqTotal + svcTotal
})


const currency = computed(() => props.dataPackage?.proposal?.currency || '')




const formatPrice = (value: number | string, currency: string) => {
  const num = Number(value)
  return new Intl.NumberFormat('ru-RU', {
    style: 'decimal',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(num)
}

const formattedTotal = computed(() => formatPrice(total.value, ''))
</script>

<style scoped>
.proposal-total-container {
  margin-top: 20px;
  text-align: right;
}
.total-box {
  display: inline-block;
  padding: 10px 20px;
  background-color: #f5f7fa;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}
h3 {
  margin: 0;
  font-size: 1.2em;
  color: #000;
}
.service-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 5px;
    font-size: 0.9em;
    color: #606266;
    border-bottom: 1px dashed #e4e7ed;
    padding-bottom: 2px;
}
.total-row {
    margin-top: 10px;
    border-top: 2px solid #000;
    padding-top: 5px;
}
</style>
