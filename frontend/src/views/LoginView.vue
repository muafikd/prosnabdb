<template>
  <div class="login-container">
    <div class="login-card">
      <h1 class="login-title">Вход в систему</h1>
      
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        label-width="120px"
        class="login-form"
      >
        <el-form-item label="Логин" prop="user_login">
          <el-input
            v-model="loginForm.user_login"
            placeholder="Введите логин"
            :prefix-icon="User"
            size="large"
            clearable
          />
        </el-form-item>

        <el-form-item label="Пароль" prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="Введите пароль"
            :prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-alert
          v-if="authStore.error"
          :title="authStore.error"
          type="error"
          :closable="true"
          @close="authStore.clearError()"
          style="margin-bottom: 20px"
        />

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="authStore.isLoading"
            @click="handleLogin"
            style="width: 100%"
          >
            Войти
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <p>Нет аккаунта? <router-link to="/register">Зарегистрироваться</router-link></p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const loginFormRef = ref<FormInstance>()

const loginForm = reactive({
  user_login: '',
  password: '',
})

const loginRules: FormRules = {
  user_login: [
    { required: true, message: 'Пожалуйста, введите логин', trigger: 'blur' },
    { min: 3, message: 'Логин должен содержать минимум 3 символа', trigger: 'blur' },
  ],
  password: [
    { required: true, message: 'Пожалуйста, введите пароль', trigger: 'blur' },
    { min: 6, message: 'Пароль должен содержать минимум 6 символов', trigger: 'blur' },
  ],
}

const handleLogin = async () => {
  if (!loginFormRef.value) return

  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        await authStore.login({
          user_login: loginForm.user_login,
          password: loginForm.password,
        })

        ElMessage.success('Успешный вход!')
        
        // Перенаправляем на главную страницу
        router.push('/')
      } catch (error) {
        // Ошибка уже обработана в store
        console.error('Login error:', error)
      }
    } else {
      ElMessage.warning('Пожалуйста, заполните все поля корректно')
    }
  })
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 450px;
}

.login-title {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
  font-size: 28px;
  font-weight: 600;
}

.login-form {
  margin-top: 20px;
}

.login-footer {
  text-align: center;
  margin-top: 20px;
  color: #666;
}

.login-footer a {
  color: #409eff;
  text-decoration: none;
}

.login-footer a:hover {
  text-decoration: underline;
}
</style>

