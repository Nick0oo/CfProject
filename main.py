import tkinter as tk
from tkinter import filedialog, messagebox
from ttkbootstrap import Style, ttk
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import json
import time
import random
import threading

# Variables globales
drivers = {}
bot_running = {}
stop_bot_signal = {}
accounts_data = {}

class InstagramBot:
    def __init__(self, card_index):
        self.card_index = card_index
        self.driver = None
        self.wait = None

    def start_driver(self):
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, 10)  # Aumentado a 10 segundos

    def login(self, username, password):
        self.driver.get("https://www.instagram.com/accounts/login/")
        username_field = self.wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_field = self.wait.until(EC.presence_of_element_located((By.NAME, "password")))
        username_field.send_keys(username)
        password_field.send_keys(password)
        password_field.send_keys(Keys.RETURN)
        time.sleep(5)

    def add_to_close_friends(self, username):
        self.driver.get("https://www.instagram.com/accounts/close_friends/")
        time.sleep(3)

        try:
            search_input = self.wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Buscar']")))
            search_input.clear()
            search_input.send_keys(username)
            time.sleep(2)

            print(f"Buscando a {username}...")

            # Intenta encontrar el primer usuario coincidente
            user_element = self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'x9f619') or contains(@class, '_aae-') or contains(@role, 'button')]//span[contains(text(), '" + username + "')]")))

            if user_element:
                actions = ActionChains(self.driver)
                actions.move_to_element(user_element).click().perform()
                print(f"Se hizo clic en el resultado de búsqueda para {username}")
                time.sleep(2)
            else:
                print(f"No se pudo encontrar el resultado de búsqueda para {username}")
                return False

            # Busca el botón de agregar
            add_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, '_acan') and contains(@class, '_acap')]")))

            if add_button:
                actions.move_to_element(add_button).click().perform()
                print(f"Se hizo clic en el botón para agregar a {username}")
                time.sleep(1)
            else:
                print(f"No se pudo encontrar el botón para agregar a {username}")
                return False

            confirmation_texts = ["Agregado", "Added", "En la lista", "In list", "Setting saved", "Configuración guardada", ""]
            for text in confirmation_texts:
                if len(self.driver.find_elements(By.XPATH, f"//div[contains(text(), '{text}')]")) > 0:
                    print(f"{username} ha sido agregado a Mejores Amigos")
                    return True

            print(f"No se pudo confirmar si {username} fue agregado a Mejores Amigos")
            return False

        except Exception as e:
            print(f"Error al agregar {username} a Mejores Amigos: {str(e)}")
            return False

    def close(self):
        if self.driver:
            self.driver.quit()

def start_bot(card_index, username, password, accounts):
    global bot_running, stop_bot_signal
    bot_running[card_index] = True
    stop_bot_signal[card_index] = False
    bot = InstagramBot(card_index)

    try:
        bot.start_driver()
        bot.login(username, password)

        for account in accounts:
            if stop_bot_signal[card_index]:
                break
            for _ in range(1):  # Intenta hasta 1 vez para cada usuario
                if bot.add_to_close_friends(account):
                    break
                time.sleep(random.uniform(2, 4))
            time.sleep(random.uniform(1, 2))  # Pausa entre cada usuario

        messagebox.showinfo("Completado", "El bot ha terminado de agregar a los Mejores Amigos")

    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error en la tarjeta {card_index + 1}: {e}")
    finally:
        bot.close()
        bot_running[card_index] = False

def stop_bot(card_index):
    global stop_bot_signal
    stop_bot_signal[card_index] = True

def validate_account(card_index, username, password):
    if username.get() and password.get() and accounts_data.get(card_index):
        threading.Thread(target=start_bot, args=(card_index, username.get(), password.get(), accounts_data[card_index])).start()
    else:
        messagebox.showwarning("Error", "Por favor, ingresa todos los datos y carga un archivo JSON")

def load_json(card_index):
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if file_path:
        with open(file_path, 'r') as file:
            accounts_data[card_index] = [user["string_list_data"][0]["value"] for user in json.load(file) if user["string_list_data"]]
        messagebox.showinfo("JSON cargado", f"Archivo JSON cargado para la tarjeta {card_index + 1}")
    else:
        messagebox.showwarning("Advertencia", "No se seleccionó ningún archivo JSON")

def logout_card(card_frame, card_index):
    stop_bot(card_index)
    for widget in card_frame.winfo_children():
        if isinstance(widget, tk.Entry):
            widget.delete(0, tk.END)
    accounts_data[card_index] = []
    enable_card(card_frame)

def enable_card(card_frame):
    for widget in card_frame.winfo_children():
        if isinstance(widget, (tk.Entry, ttk.Button)):
            widget.config(state="normal")

def disable_card(card_frame):
    for widget in card_frame.winfo_children():
        if isinstance(widget, (tk.Entry, ttk.Button)):
            widget.config(state="disabled")

def toggle_mode():
    current_mode = style.theme_use()
    if current_mode == "cosmo":
        style.theme_use("darkly")
        toggle_button.config(text="Modo Claro")
        background_frame.config(bg="#333")
    else:
        style.theme_use("cosmo")
        toggle_button.config(text="Modo Oscuro")
        background_frame.config(bg="#D6EAF8")

# Configuración de la interfaz
style = Style(theme='darkly')
root = style.master
root.title("Boosting.Lab - Instagram Bot")
root.geometry("1000x600")

background_frame = tk.Frame(root, bg="#333")
background_frame.pack(fill=tk.BOTH, expand=True)

title_label = ttk.Label(root, text="Boosting.Lab", font=("Helvetica", 24, "bold"), bootstyle="primary")
title_label.pack(pady=20)

toggle_button = ttk.Checkbutton(root, text="Modo Claro", bootstyle="round-toggle", command=toggle_mode)
toggle_button.pack(pady=10)

main_frame = tk.Frame(root, bg="#333")
main_frame.pack(expand=True, pady=20)

accounts_data = {i: [] for i in range(5)}
cards = []

for i in range(5):
    card_frame = tk.Frame(main_frame, bd=2, relief="groove", padx=20, pady=20, bg="#444", highlightbackground="blue", highlightthickness=1)
    card_frame.grid(row=0, column=i, padx=10)

    tk.Label(card_frame, text=f"Ingresar cuenta {i + 1}", font=("Helvetica", 10, "bold"), bg="#444", fg="white").pack(pady=5)

    username = tk.Entry(card_frame, font=("Helvetica", 10), width=20)
    username.pack(pady=5)

    password = tk.Entry(card_frame, show="*", font=("Helvetica", 10), width=20)
    password.pack(pady=5)

    load_button = ttk.Button(card_frame, text="Cargar JSON", command=lambda idx=i: load_json(idx))
    load_button.pack(pady=5)

    start_button = ttk.Button(card_frame, text="Iniciar Bot", command=lambda idx=i, u=username, p=password: validate_account(idx, u, p))
    start_button.pack(pady=5)

    stop_button = ttk.Button(card_frame, text="Detener Bot", command=lambda idx=i: stop_bot(idx))
    stop_button.pack(pady=5)

    logout_button = ttk.Button(card_frame, text="Cerrar Sesión", command=lambda cf=card_frame, idx=i: logout_card(cf, idx))
    logout_button.pack(pady=5)

    cards.append(card_frame)

root.mainloop() 
