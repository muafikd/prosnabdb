<template>
  <div class="not-found">
    <h1>404</h1>
    <p>Страница не найдена</p>
    <el-button type="primary" @click="$router.push('/')">Вернуться на главную</el-button>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
.not-found {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  text-align: center;
}

.not-found h1 {
  font-size: 72px;
  margin-bottom: 20px;
  color: #409eff;
}
</style>

