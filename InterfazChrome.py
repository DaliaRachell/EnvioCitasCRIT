import pandas as pd
from selenium import webdriver
# Se cambian las opciones de Edge por las de Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.parse
import time
import os
import random
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import ctypes

# =========================
# CONFIGURACIÓN DE PANTALLA
# =========================
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

COLOR_PRIMARIO = "#681A73"
COLOR_ACENTO = "#F2CB05"
COLOR_TEXTO = "#FFFFFF"
FUENTE_TIERNA = ("Comic Sans MS", 11, "bold")


# =========================
# FUNCIÓN DE ENVÍO
# =========================
def iniciar_envio(df_filtrado):
    if df_filtrado.empty:
        messagebox.showwarning("Sin datos", "No hay registros en el bloque seleccionado.")
        return

    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_ladas = os.path.join(directorio_actual, 'ladas_mexico.csv')

    try:
        df_ladas = pd.read_csv(ruta_ladas, dtype=str)
        lista_ladas_mex = df_ladas.iloc[:, 0].tolist()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo cargar ladas_mexico.csv: {e}")
        return

    df_agrupado = df_filtrado.groupby(['NUMERO', 'NOMBRE', 'FECHA DE CITA']).agg({
        'CARNET': lambda x: ', '.join(map(str, x.unique())),
        'HORA': lambda x: ' y '.join(map(str, x.unique()))
    }).reset_index()

    # --- CONFIGURACIÓN DE CHROME ---
    chrome_options = Options()
    # Usamos una carpeta específica para la sesión de Chrome
    ruta_sesion = os.path.join(directorio_actual, "sesion_whatsapp_chrome")
    chrome_options.add_argument(f"user-data-dir={ruta_sesion}")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    try:
        # Se inicializa el driver de Chrome
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        messagebox.showerror("Error", f"Cierra otras ventanas de Chrome que usen este perfil.\n{e}")
        return

    driver.get("https://web.whatsapp.com")
    messagebox.showinfo("WhatsApp Web", "Espera a que carguen tus chats y presiona Aceptar.")

    enviados = 0
    fallidos = []

    for index, fila in df_agrupado.iterrows():
        nombre = str(fila['NOMBRE']).strip()
        carnets = str(fila['CARNET']).strip()
        num_limpio = "".join(filter(str.isdigit, str(fila['NUMERO'])))

        if num_limpio.startswith("52"):
            numero = num_limpio
        elif num_limpio.startswith("1") and len(num_limpio) > 10:
            numero = num_limpio
        else:
            es_mexico = any(num_limpio.startswith(lada) for lada in lista_ladas_mex)
            numero = ("52" + num_limpio) if es_mexico else ("1" + num_limpio)

        saludo = random.choice(["Buen día", "Hola", "Le saludamos del CRIT"])
        mensaje_completo = (
            f"{saludo}, le recordamos la cita de {nombre} con carnet {carnets} "
            f"programada para el día {fila['FECHA DE CITA']} a las {fila['HORA']} en CRIT Tijuana. "
            f"En caso de no poder asistir, favor de comunicarse al 664 900 9900. ¡Gracias!"
        )

        url = f"https://web.whatsapp.com/send?phone={numero}&text={urllib.parse.quote(mensaje_completo)}"
        driver.get(url)

        try:
            wait = WebDriverWait(driver, 25)

            # --- DETECTOR DE ESTADO ---
            intentos_deteccion = 0
            while intentos_deteccion < 6:
                # 1. ¿Número inexistente?
                error_buttons = driver.find_elements(By.XPATH,
                                                     '//div[@role="button"][contains(., "OK") or contains(., "Aceptar") or contains(., "Cerrar")]')
                if error_buttons:
                    print(f"⚠️ Detectado número inexistente: {nombre}")
                    error_buttons[0].click()
                    fallidos.append(f"{nombre} ({numero}) - No existe")
                    time.sleep(2)
                    break

                # 2. ¿Caja de mensaje lista?
                caja = driver.find_elements(By.CSS_SELECTOR, 'div[contenteditable="true"][data-tab="10"]')
                if caja:
                    time.sleep(3)
                    caja[0].send_keys(Keys.ENTER)
                    enviados += 1
                    print(f"✅ {enviados}. Enviado: {nombre}")
                    break

                time.sleep(2)
                intentos_deteccion += 1

            if intentos_deteccion == 6:
                raise Exception("Tiempo de espera agotado para este mensaje")

        except Exception as e:
            fallidos.append(f"{nombre} ({numero}) - Error de carga")
            print(f"❌ Error en {nombre}: {e}")

        # --- PAUSAS ANTI-BLOQUEO ---
        time.sleep(random.randint(20, 35))

        if enviados > 0 and enviados % 15 == 0:
            print("☕ Pausa de 2 min...")
            time.sleep(120)

        if enviados > 0 and enviados % 40 == 0:
            print("⏳ PAUSA CRÍTICA (10 min)...")
            time.sleep(600)

    driver.quit()
    resumen = f"✅ Proceso finalizado\n\nEnviados: {enviados}"
    if fallidos:
        resumen += "\n\n❌ No enviados:\n" + "\n".join(fallidos)
    messagebox.showinfo("Resumen", resumen)

# =========================
# FILTRADO POR HORARIO
# =========================
def procesar_seleccion(opcion):
    try:
        directorio_actual = os.path.dirname(os.path.abspath(__file__))
        ruta_csv = os.path.join(directorio_actual, 'Book.csv')

        df = pd.read_csv(
            ruta_csv,
            sep=None,
            engine='python',
            dtype={"CARNET": str}
        )

        df.columns = df.columns.str.strip()
        df['Hora_DT'] = pd.to_datetime(df['HORA'], errors='coerce').dt.time

        from datetime import time as dt_time

        if opcion == 1:
            df_filtrado = df[(df['Hora_DT'] >= dt_time(7, 0)) & (df['Hora_DT'] <= dt_time(11, 0))]
        elif opcion == 2:
            df_filtrado = df[(df['Hora_DT'] >= dt_time(11, 1)) & (df['Hora_DT'] <= dt_time(14, 0))]
        elif opcion == 3:
            df_filtrado = df[(df['Hora_DT'] >= dt_time(14, 1)) & (df['Hora_DT'] <= dt_time(18, 0))]

        root.withdraw()
        iniciar_envio(df_filtrado)
        root.deiconify()

    except Exception as e:
        messagebox.showerror("Error", f"Detalle: {e}")

# =========================
# INTERFAZ GRÁFICA
# =========================
root = tk.Tk()
root.title("Notificador CRIT (Chrome Version)")
root.geometry("450x650")
root.resizable(False, False)
root.configure(bg=COLOR_PRIMARIO)

try:
    ruta_script = os.path.dirname(os.path.abspath(__file__))
    ruta_icono = os.path.join(ruta_script, "icono.ico")
    root.iconbitmap(ruta_icono)
except Exception:
    pass

try:
    img_path = os.path.join(ruta_script, "logo.png")
    img = Image.open(img_path)
    img = img.resize((200, 160), Image.LANCZOS)
    photo = ImageTk.PhotoImage(img)
    tk.Label(root, image=photo, bg=COLOR_PRIMARIO).pack(pady=20)
except Exception:
    tk.Label(root, text="✨", font=("Arial", 30), bg=COLOR_PRIMARIO, fg=COLOR_ACENTO).pack(pady=20)

tk.Label(root, text="¡Hola! Selecciona un bloque:", font=FUENTE_TIERNA, bg=COLOR_PRIMARIO, fg=COLOR_TEXTO,
         pady=10).pack()

estilo_boton = {"font": FUENTE_TIERNA, "fg": COLOR_PRIMARIO, "bg": COLOR_ACENTO, "width": 25, "pady": 2,
                "relief": "flat", "cursor": "hand2", "activebackground": "#d9b504"}

tk.Button(root, text="Bloque 1 (07:00 - 11:00)", command=lambda: procesar_seleccion(1), **estilo_boton).pack(pady=10)
tk.Button(root, text="Bloque 2 (11:01 - 14:00)", command=lambda: procesar_seleccion(2), **estilo_boton).pack(pady=10)
tk.Button(root, text="Bloque 3 (14:01 - 18:00)", command=lambda: procesar_seleccion(3), **estilo_boton).pack(pady=10)
tk.Button(root, text="❌ SALIR", command=root.destroy, font=FUENTE_TIERNA, fg="white", bg="#B22222", relief="flat",
          width=25, pady=5).pack(pady=(30, 0))

root.mainloop()