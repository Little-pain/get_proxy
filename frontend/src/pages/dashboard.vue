<template>
  <v-container>
    <v-row justify="center">
      <v-col cols="12" md="8">
        
        <v-card v-if="!pageLoading && !isLoggedIn" class="mt-5 text-center pa-10" elevation="2">
          <v-card-title class="text-h5 text-error justify-center">Вы не вошли в аккаунт</v-card-title>
          <v-card-text class="text-body-1">
            Для доступа к личному кабинету и вашим ключам необходимо авторизоваться в системе.
          </v-card-text>
          <v-card-actions class="justify-center mt-4">
            <v-btn color="primary" variant="elevated" size="large" to="/login">Войти в аккаунт</v-btn>
          </v-card-actions>
        </v-card>

        <v-card v-else-if="pageLoading" class="mt-5 d-flex align-center justify-center" min-height="200" elevation="0">
          <v-progress-circular indeterminate color="primary"></v-progress-circular>
        </v-card>

        <v-card v-else class="mt-5" elevation="2">
          <v-card-title class="text-h4 d-flex justify-space-between align-center">
            <span>Личный кабинет</span>
            <v-btn color="error" variant="text" @click="showLogoutDialog = true">Выйти</v-btn>
          </v-card-title>
          
          <v-divider></v-divider>

          <v-card-text class="pt-4">
            <div class="mb-6 d-flex align-center">
              <span class="text-subtitle-1 mr-3">Статус вашего аккаунта:</span>
              <v-chip :color="user.is_active ? 'success' : 'warning'">
                {{ user.is_active ? 'Активен' : 'Неактивен' }}
              </v-chip>
            </div>

            <v-text-field
              label="Ваш персональный ключ (64 символа)"
              v-model="user.activation_key"
              readonly
              hint="Используйте этот ключ для авторизации в десктопном приложении"
              persistent-hint
              variant="outlined"
              append-inner-icon="mdi-content-copy"
              @click:append-inner="copyKeyToClipboard"
            ></v-text-field>
          </v-card-text>

          <v-card-actions class="pa-4">
            <v-btn 
              color="primary" 
              variant="elevated" 
              @click="refreshKey" 
              :loading="btnLoading"
            >
              Обновить ключ
            </v-btn>
          </v-card-actions>

          <v-divider class="my-6"></v-divider>

          <v-card-text>
            <h3 class="text-h6 mb-4">Безопасность</h3>
            <v-row>
              <v-col cols="12" md="6">
                <v-text-field 
                  v-model="passData.old_password" 
                  label="Старый пароль" 
                  type="password" 
                  variant="outlined"
                  density="compact"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field 
                  v-model="passData.new_password" 
                  label="Новый пароль" 
                  type="password" 
                  variant="outlined"
                  density="compact"
                ></v-text-field>
              </v-col>
            </v-row>
            <v-btn 
              color="secondary" 
              variant="tonal" 
              :loading="passLoading" 
              @click="handleChangePassword"
            >
              Сменить пароль
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-dialog v-model="showLogoutDialog" max-width="400">
      <v-card>
        <v-card-title class="text-h5">Точно выйти?</v-card-title>
        <v-card-text>Сессия будет завершена.</v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey-darken-1" variant="text" @click="showLogoutDialog = false">Отмена</v-btn>
          <v-btn color="error" variant="elevated" :loading="logoutLoading" @click="handleLogout">Да, выйти</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '@/api'

interface UserProfile {
  is_active: boolean;
  activation_key: string;
}

const user = ref<UserProfile>({ is_active: false, activation_key: '' })
const isLoggedIn = ref(false)
const pageLoading = ref(true)
const btnLoading = ref(false)
const logoutLoading = ref(false)
const passLoading = ref(false)
const showLogoutDialog = ref(false)
const passData = ref({ old_password: '', new_password: '' })
const router = useRouter()

const fetchProfile = async () => {
  const token = localStorage.getItem('access_token')
  if (!token) {
    isLoggedIn.value = false
    pageLoading.value = false
    return
  }

  pageLoading.value = true
  try {
    const res = await authApi.getProfile() 
    user.value = res.data
    isLoggedIn.value = true
  } catch (error) {
    console.error("Ошибка загрузки профиля:", error)
    isLoggedIn.value = false
  } finally {
    pageLoading.value = false
  }
}

const refreshKey = async () => {
  btnLoading.value = true
  try {
    const res = await authApi.refreshKey()
    user.value.activation_key = res.data.new_key
    alert('Ключ успешно обновлен!')
  } catch (error) {
    alert('Не удалось обновить ключ.')
  } finally {
    btnLoading.value = false
  }
}

const copyKeyToClipboard = () => {
  if (user.value.activation_key) {
    navigator.clipboard.writeText(user.value.activation_key)
    alert('Ключ скопирован!')
  }
}

const handleLogout = async () => {
  logoutLoading.value = true
  try {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) await authApi.logout(refreshToken);
  } catch (error) {
    console.warn("Чистим локально.");
  } finally {
    localStorage.clear();
    logoutLoading.value = false;
    showLogoutDialog.value = false;
    await router.replace('/');
  }
}

const handleChangePassword = async () => {
  passLoading.value = true
  try {
    await authApi.changePassword(passData.value)
    alert('Пароль изменен!')
    await handleLogout()
  } catch (error: any) {
    alert(error.response?.data?.old_password?.[0] || 'Ошибка')
  } finally {
    passLoading.value = false
  }
}

onMounted(fetchProfile)
</script>