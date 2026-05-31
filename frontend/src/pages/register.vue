<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="4">
        <v-card elevation="12">
          <v-toolbar color="secondary" dark flat>
            <v-toolbar-title>Регистрация</v-toolbar-title>
          </v-toolbar>
          <v-card-text>
            <v-form @submit.prevent="handleRegister" ref="form">
              <v-text-field
                label="Email"
                v-model="email"
                prepend-icon="mdi-email"
                type="email"
                :rules="[v => !!v || 'Email обязателен']"
                required
              ></v-text-field>

              <v-text-field
                label="Пароль"
                v-model="password"
                prepend-icon="mdi-lock"
                type="password"
                :rules="[v => !!v || 'Пароль обязателен']"
                required
              ></v-text-field>

              <v-text-field
                label="Подтверждение пароля"
                v-model="confirmPassword"
                prepend-icon="mdi-lock-check"
                type="password"
                :rules="[v => v === password || 'Пароли не совпадают']"
                required
              ></v-text-field>
              
              <v-btn 
                type="submit" 
                color="secondary" 
                block 
                class="mt-4" 
                :loading="loading"
              >
                Создать аккаунт
              </v-btn>
              
              <div class="text-center mt-4">
                <router-link to="/login">Уже есть аккаунт? Войти</router-link>
              </div>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '@/api'

const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const router = useRouter()

const handleRegister = async () => {

  
  if (password.value !== confirmPassword.value) {
    alert('Пароли не совпадают!')
    return
  }

  loading.value = true
  try {
    await authApi.register({
      email: email.value,
      password: password.value,
      password_confirm: confirmPassword.value
    })
    
    alert('Регистрация успешна!')
    router.push('/login')
  } catch (error: any) {
    const errors = error.response?.data
    let errorMessage = 'Ошибка регистрации: '
    
    if (typeof errors === 'object' && errors !== null) {
      errorMessage += Object.entries(errors)
        .map(([field, messages]) => `${field}: ${messages}`)
        .join(', ')
    } else {
      errorMessage = 'Ошибка сервера. Попробуйте позже.'
    }

    console.error("Полный ответ ошибки:", errors)
    alert(errorMessage)
  } finally {
    loading.value = false
  }
}
</script>