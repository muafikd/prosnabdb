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
  margin-top: 15px;
  text-align: right;
  font-family: 'Times New Roman', Times, serif;
  font-size: 13.3px; /* 10pt */
}
.total-box {
  display: inline-block;
  padding: 5px 0;
  border-top: 2px solid #333;
}
h3 {
  margin: 0;
  font-size: 10pt;
  font-weight: bold;
  color: #000;
}
</style>
