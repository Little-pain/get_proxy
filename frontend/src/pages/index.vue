<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="4" class="text-center">
        <v-card class="pa-6" elevation="2">
          <v-card-title class="text-h4 mb-4">Get Proxy Service</v-card-title>
          
          <v-card-text class="text-body-1">
            Добро пожаловать в панель управления. <br>
            Для работы с системой необходимо авторизоваться.
          </v-card-text>

          <v-divider class="my-6"></v-divider>

          <v-card-actions class="flex-column ga-3">
            <v-btn 
              block 
              color="primary" 
              size="large" 
              variant="elevated" 
              :to="hasToken ? '/dashboard' : '/login'"
            >
              {{ hasToken ? 'Перейти в кабинет' : 'Войти в аккаунт' }}
            </v-btn>

            <v-btn 
              v-if="!hasToken"
              block 
              color="secondary" 
              variant="tonal" 
              to="/register"
            >
              Регистрация
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const hasToken = ref(false)

onMounted(() => {
  hasToken.value = !!localStorage.getItem('access_token')
})
</script>