import customtkinter as ctk
from tkinter import messagebox
import threading
import json
import websocket
import winreg
import ctypes

WS_URL_BASE = "ws://127.0.0.1:8000/ws/desktop/" 

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

class ProxyClientApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Proxy Access Client")
        self.geometry("400x300")
        self.resizable(False, False)
        
        self.ws = None
        self.current_key = None

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- UI ЭЛЕМЕНТЫ ---
        self.title_label = ctk.CTkLabel(self, text="Подключение к Proxy", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(pady=(20, 10))

        self.key_entry = ctk.CTkEntry(self, placeholder_text="Вставьте ваш ключ активации...", width=300, height=40)
        self.key_entry.pack(pady=10)

        self.connect_btn = ctk.CTkButton(self, text="Подключиться", command=self.start_connection, font=ctk.CTkFont(size=15), height=40)
        self.connect_btn.pack(pady=15)

        self.status_label = ctk.CTkLabel(self, text="Статус: Ожидание", text_color="gray", font=ctk.CTkFont(size=14))
        self.status_label.pack(pady=(5, 0))

        self.proxy_info_label = ctk.CTkLabel(self, text="", text_color="#1f6aa5", font=ctk.CTkFont(size=14))
        self.proxy_info_label.pack(pady=5)

    # ================= ЛОГИКА СИСТЕМНОГО ПРОКСИ =================

    def set_windows_proxy(self, host, port):
        """Включает системный прокси в Windows"""
        try:
            internet_settings = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r'Software\Microsoft\Windows\CurrentVersion\Internet Settings',
                0, winreg.KEY_ALL_ACCESS)
            
            winreg.SetValueEx(internet_settings, 'ProxyEnable', 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(internet_settings, 'ProxyServer', 0, winreg.REG_SZ, f"{host}:{port}")
            winreg.CloseKey(internet_settings)

            INTERNET_OPTION_REFRESH = 37
            INTERNET_OPTION_SETTINGS_CHANGED = 39
            ctypes.windll.wininet.InternetSetOptionW(0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)
            ctypes.windll.wininet.InternetSetOptionW(0, INTERNET_OPTION_REFRESH, 0, 0)
        except Exception as e:
            print(f"Ошибка при установке прокси: {e}")

    def disable_windows_proxy(self):
        """Выключает системный прокси в Windows"""
        try:
            internet_settings = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r'Software\Microsoft\Windows\CurrentVersion\Internet Settings',
                0, winreg.KEY_ALL_ACCESS)
            
            winreg.SetValueEx(internet_settings, 'ProxyEnable', 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(internet_settings)
            
            INTERNET_OPTION_REFRESH = 37
            INTERNET_OPTION_SETTINGS_CHANGED = 39
            ctypes.windll.wininet.InternetSetOptionW(0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)
            ctypes.windll.wininet.InternetSetOptionW(0, INTERNET_OPTION_REFRESH, 0, 0)
        except Exception as e:
            print(f"Ошибка при отключении прокси: {e}")

    # ==========================================================

    def start_connection(self):
        key = self.key_entry.get().strip()
        if not key:
            messagebox.showwarning("Ошибка", "Введите ключ!")
            return

        self.current_key = key
        self.update_status("Статус: Подключение...", "orange")
        self.connect_btn.configure(state="disabled")

        threading.Thread(target=self.run_ws, daemon=True).start()

    def run_ws(self):
        def on_open(ws):
            auth_message = {"action": "activate_key", "code": self.current_key}
            ws.send(json.dumps(auth_message))

        def on_message(ws, message):
            data = json.loads(message)
            
            if data.get("type") == "activation_result":
                if data.get("success"):
                    proxy = data.get("proxy_data", {})
                    host = proxy.get("host")
                    port = proxy.get("port")
                    protocol = proxy.get("protocol")

                    self.set_windows_proxy(host, port)

                    proxy_text = f"{protocol}://{host}:{port}"
                    self.after(0, self.update_status, "Статус: Подключено", "#2cc985")
                    self.after(0, self.update_proxy_info, proxy_text)
                else:
                    error_msg = data.get("error", "Ошибка активации")
                    self.after(0, self.update_status, "Статус: Ошибка", "#fa5c5c")
                    self.after(0, self.show_error, error_msg)
                    ws.close()

            elif data.get("type") == "status_change":
                new_status = data.get("data", {}).get("status")
                if new_status == "disconnected":
                    self.disable_windows_proxy()

                    self.after(0, self.update_status, "Статус: Отключено (Выбило)", "#fa5c5c")
                    self.after(0, self.update_proxy_info, "")
                elif new_status == "connected":
                    self.after(0, self.update_status, "Статус: Подключено", "#2cc985")

        def on_error(ws, error):
            self.disable_windows_proxy()
            self.after(0, self.update_status, "Статус: Ошибка сети", "#fa5c5c")
            self.after(0, lambda: self.connect_btn.configure(state="normal"))

        def on_close(ws, close_status_code, close_msg):
            self.disable_windows_proxy()
            self.after(0, self.update_status, "Статус: Отключено", "gray")
            self.after(0, lambda: self.connect_btn.configure(state="normal"))

        self.ws = websocket.WebSocketApp(
            WS_URL_BASE,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        self.ws.run_forever()

    def on_closing(self):
        """Вызывается при нажатии на крестик окна"""
        # Сначала выключаем системный прокси
        self.disable_windows_proxy()
        # Потом закрываем сокет
        if self.ws:
            self.ws.close()
        # Убиваем само окно
        self.destroy()

    def update_status(self, text, color):
        self.status_label.configure(text=text, text_color=color)

    def update_proxy_info(self, text):
        self.proxy_info_label.configure(text=text)

    def show_error(self, message):
        messagebox.showerror("Ошибка", message)

if __name__ == "__main__":
    app = ProxyClientApp()
    app.mainloop()