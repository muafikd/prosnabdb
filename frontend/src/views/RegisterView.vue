<template>
  <div class="register-container">
    <div class="register-card">
      <h1 class="register-title">Регистрация</h1>
      
      <el-form
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        label-width="150px"
        class="register-form"
      >
        <el-form-item label="Логин" prop="user_login">
          <el-input
            v-model="registerForm.user_login"
            placeholder="Введите логин"
            :prefix-icon="User"
            size="large"
            clearable
          />
        </el-form-item>

        <el-form-item label="Имя" prop="user_name">
          <el-input
            v-model="registerForm.user_name"
            placeholder="Введите ваше имя"
            :prefix-icon="User"
            size="large"
            clearable
          />
        </el-form-item>

        <el-form-item label="Email" prop="user_email">
          <el-input
            v-model="registerForm.user_email"
            type="email"
            placeholder="Введите email"
            :prefix-icon="Message"
            size="large"
            clearable
          />
        </el-form-item>

        <el-form-item label="Телефон" prop="user_phone">
          <el-input
            v-model="registerForm.user_phone"
            placeholder="Введите телефон (необязательно)"
            :prefix-icon="Phone"
            size="large"
            clearable
          />
        </el-form-item>

        <el-form-item label="Пароль" prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="Введите пароль"
            :prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>

        <el-form-item label="Подтверждение" prop="password_confirm">
          <el-input
            v-model="registerForm.password_confirm"
            type="password"
            placeholder="Подтвердите пароль"
            :prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="handleRegister"
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
            @click="handleRegister"
            style="width: 100%"
          >
            Зарегистрироваться
          </el-button>
        </el-form-item>
      </el-form>

      <div class="register-footer">
        <p>Уже есть аккаунт? <router-link to="/login">Войти</router-link></p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock, Message, Phone } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const registerFormRef = ref<FormInstance>()

const registerForm = reactive({
  user_login: '',
  user_name: '',
  user_email: '',
  user_phone: '',
  password: '',
  password_confirm: '',
})

const validatePasswordConfirm = (rule: any, value: string, callback: any) => {
  if (value !== registerForm.password) {
    callback(new Error('Пароли не совпадают'))
  } else {
    callback()
  }
}

const registerRules: FormRules = {
  user_login: [
    { required: true, message: 'Пожалуйста, введите логин', trigger: 'blur' },
    { min: 3, message: 'Логин должен содержать минимум 3 символа', trigger: 'blur' },
  ],
  user_name: [
    { required: true, message: 'Пожалуйста, введите имя', trigger: 'blur' },
  ],
  user_email: [
    { required: true, message: 'Пожалуйста, введите email', trigger: 'blur' },
    { type: 'email', message: 'Введите корректный email', trigger: 'blur' },
  ],
  user_phone: [
    { required: false },
  ],
  password: [
    { required: true, message: 'Пожалуйста, введите пароль', trigger: 'blur' },
    { min: 8, message: 'Пароль должен содержать минимум 8 символов', trigger: 'blur' },
  ],
  password_confirm: [
    { required: true, message: 'Пожалуйста, подтвердите пароль', trigger: 'blur' },
    { validator: validatePasswordConfirm, trigger: 'blur' },
  ],
}

const handleRegister = async () => {
  if (!registerFormRef.value) return

  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        await authStore.register({
          user_login: registerForm.user_login,
          user_name: registerForm.user_name,
          user_email: registerForm.user_email,
          user_phone: registerForm.user_phone || undefined,
          password: registerForm.password,
          password_confirm: registerForm.password_confirm,
        })

        ElMessage.success(
          'Регистрация прошла успешно. Ваша учетная запись скоро активируется вашим руководителем.'
        )

        // Перенаправляем на страницу логина
        router.push('/login')
      } catch (error) {
        console.error('Register error:', error)
        const data = (error as any)?.response?.data
        let msg: string

        if (typeof data === 'string') {
          msg = data
        } else if (data && typeof data === 'object') {
          // Собираем ошибки вида {field: ["err1", "err2"], ...}
          msg = Object.entries(data)
            .map(([k, v]) => {
              if (Array.isArray(v)) return `${k}: ${v.join(', ')}`
              if (typeof v === 'object') return `${k}: ${JSON.stringify(v)}`
              return `${k}: ${v}`
            })
            .join('; ')
        } else {
          msg =
            (error as any)?.response?.data?.detail ||
            (error as any)?.response?.data?.message ||
            (error as any)?.message ||
            'Ошибка регистрации'
        }

        ElMessage.error(msg)
      }
    } else {
      ElMessage.warning('Пожалуйста, заполните все поля корректно')
    }
  })
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.register-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 500px;
}

.register-title {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
  font-size: 28px;
  font-weight: 600;
}

.register-form {
  margin-top: 20px;
}

.register-footer {
  text-align: center;
  margin-top: 20px;
  color: #666;
}

.register-footer a {
  color: #409eff;
  text-decoration: none;
}

.register-footer a:hover {
  text-decoration: underline;
}
</style>

