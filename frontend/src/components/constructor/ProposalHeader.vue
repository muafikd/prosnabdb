<template>
  <div class="proposal-header">
    <div class="logo-section">
      <img :src="headerData?.logo || '/assets/prosnab_logo.png'" alt="PROSNAB Service" class="logo-img" />
    </div>
    
    <div class="info-section">
      <div class="info-column kz">
        <div 
          class="editable-info" 
          contenteditable="true" 
          @blur="updateContent('kz_info', $event)"
          v-html="headerData?.kz_info || defaultKZInfo"
        ></div>
      </div>
      
      <div class="vertical-divider"></div>
      
      <div class="info-column ru">
        <div 
          class="editable-info" 
          contenteditable="true" 
          @blur="updateContent('ru_info', $event)"
          v-html="headerData?.ru_info || defaultRUInfo"
        ></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  headerData?: {
    logo?: string;
    kz_info?: string;
    ru_info?: string;
  }
}>()

const emit = defineEmits(['update:headerData'])

const defaultKZInfo = `
  <p class="company-name">ЖШС «PROSNABservice»</p>
  <p>Мекен жай: 050065, Алматы қ.,</p>
  <p>Төле би көшесі 286/4, 403 каб.</p>
  <p>БИН 170940001112</p>
  <p>ИИК KZ796017131000018253</p>
  <p>АҚ «Қазақстан халық банкі»</p>
  <p>БИК «HSBKKZKX»</p>
  <p>e-mail: prosnabservice@mail.ru</p>
`

const defaultRUInfo = `
  <p class="company-name">ТОО «PROSNAB service»</p>
  <p>Адрес: 050065, г. Алматы,</p>
  <p>ул. Толе би 286/4, 403 каб.</p>
  <p>БИН 170940001112</p>
  <p>ИИК KZ796017131000018253</p>
  <p>АО «Народный банк Казахстана»</p>
  <p>БИК «HSBKKZKX»</p>
  <p>e-mail: prosnabservice@mail.ru</p>
`

const updateContent = (field: string, event: FocusEvent) => {
  const target = event.target as HTMLElement
  const newData = { ...props.headerData }
  if (field === 'kz_info') newData.kz_info = target.innerHTML
  if (field === 'ru_info') newData.ru_info = target.innerHTML
  emit('update:headerData', newData)
}
</script>

<style scoped>
.proposal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding-bottom: 20px;
  border-bottom: 2px solid #000;
  margin-bottom: 20px;
  font-family: "Times New Roman", Times, serif;
}

.logo-section {
  flex: 0 0 30%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-img {
  max-width: 100%;
  max-height: 100px;
  object-fit: contain;
}

.info-section {
  flex: 0 0 65%;
  display: flex;
  justify-content: space-between;
  font-size: 9pt; /* Adjust size to match dense text */
  line-height: 1.2;
}

.info-column {
  flex: 1;
}

.vertical-divider {
  width: 1px;
  background-color: #000;
  margin: 0 10px;
  align-self: stretch; /* Make it full height */
}

.company-name {
  font-weight: bold;
  margin-bottom: 4px;
}

p {
  margin: 0;
  padding: 0;
}
</style>
