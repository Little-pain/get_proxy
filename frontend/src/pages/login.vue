<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="4">
        <v-card elevation="12">
          <v-toolbar color="primary" dark flat>
            <v-toolbar-title>Вход в систему</v-toolbar-title>
          </v-toolbar>
          <v-card-text>
            <v-alert
              v-if="errorMessage"
              type="error"
              variant="tonal"
              class="mb-4"
              density="compact"
            >
              {{ errorMessage }}
            </v-alert>

            <v-form @submit.prevent="handleLogin" ref="form">
              <v-text-field 
                label="Email" 
                v-model="email" 
                prepend-icon="mdi-account" 
                type="email" 
                required
              ></v-text-field>

              <v-text-field 
                label="Пароль" 
                v-model="password" 
                prepend-icon="mdi-lock" 
                type="password" 
                required
              ></v-text-field>
              
              <v-btn 
                type="submit" 
                block 
                color="primary" 
                :loading="loading" 
                class="mb-4"
              >
                Войти
              </v-btn>
            </v-form>

            <v-row justify="center" class="mt-2">
              <div class="text-subtitle-2">
                Нет аккаунта? 
                <router-link to="/register" class="text-primary font-weight-bold">Регистрация</router-link>
              </div>
            </v-row>
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
const loading = ref(false)
const errorMessage = ref('')
const router = useRouter()

const handleLogin = async () => {
  loading.value = true
  errorMessage.value = ''
  
  try {
    const response = await authApi.login(email.value, password.value)
    const authToken = response.data?.access;
    
    if (authToken) {
      localStorage.setItem('access_token', authToken);
      await router.push('/dashboard');
    } else {
      errorMessage.value = 'Ошибка авторизации. Попробуйте снова.';
    }
    
  } catch (error: any) {
    if (error.response) {
      if (error.response.status === 400 || error.response.status === 401) {
        errorMessage.value = 'Неверный email или пароль.';
      } else {
        errorMessage.value = 'Ошибка на сервере. Попробуйте позже.';
      }
    } else if (error.request) {
      errorMessage.value = 'Сервер недоступен. Проверьте подключение к интернету.';
    } else {
      errorMessage.value = 'Произошла непредвиденная ошибка.';
    }
  } finally {
    loading.value = false
  }
}
</script>