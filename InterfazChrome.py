# =========================
# IMPORTACIÓN DE LIBRERÍAS
# =========================
import pandas as pd  # Para manejo de datos (CSV)
from selenium import webdriver  # Para automatizar el navegador
# --- CAMBIO AQUÍ: Importamos Chrome en lugar de Edge ---
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
# ------------------------------------------------------
from selenium.webdriver.common.keys import Keys
import urllib.parse
import time
import os
import random
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import ctypes

# =========================
# CONFIGURACIÓN DE PANTALLA (DPI)
# =========================
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

COLOR_PRIMARIO = "#681A73"
COLOR_ACENTO = "#F2CB05"
COLOR_TEXTO = "#FFFFFF"
FUENTE_TIERNA = ("Comic Sans MS", 11, "bold")


# =========================
# FUNCIÓN PRINCIPAL DE ENVÍO
# =========================
def iniciar_envio(df_filtrado):
    if df_filtrado.empty:
        messagebox.showwarning("Sin datos", "No hay registros en el bloque seleccionado.")
        return

    # --- CAMBIO AQUÍ: Configuración para Google Chrome ---
    chrome_options = Options()

    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    # Cambiamos el nombre de la carpeta de sesión para que no choque con la de Edge
    ruta_sesion = os.path.join(directorio_actual, "sesion_chrome_whatsapp")

    chrome_options.add_argument(f"user-data-dir={ruta_sesion}")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    try:
        # Inicializamos Chrome
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        messagebox.showerror("Error de Sesión",
                             f"No se pudo abrir Chrome.\n\nDetalle: {e}\n\nAsegúrate de tener Chrome instalado.")
        return
    # ------------------------------------------------------

    driver.get("https://web.whatsapp.com")
    messagebox.showinfo("WhatsApp Web", "Espera a que carguen tus chats y presiona Aceptar.")

    for index, (idx_original, fila) in enumerate(df_filtrado.iterrows()):
        nombre = str(fila['Nombre']).strip()
        carnet = str(fila['Carnet']).strip()
        numero_crudo = str(fila['Numero']).replace(".0", "").strip()

        if not numero_crudo.startswith("52"):
            numero = "52" + numero_crudo
        else:
            numero = numero_crudo

        hora_cita = str(fila['Hora']).strip()
        fecha_cita = str(fila['Fecha de cita']).strip()

        mensaje_completo = (
            f"Buen día {nombre}, le recordamos la cita del paciente con carnet {carnet} "
            f"programada para el día {fecha_cita} a las {hora_cita} en CRIT Tijuana. "
            f"Le pedimos confirmar de recibido respondiendo con la palabra 'Recibido'. ¡Gracias!"
        )

        mensaje_url = urllib.parse.quote(mensaje_completo)
        url = f"https://web.whatsapp.com/send?phone={numero}&text={mensaje_url}"

        driver.get(url)
        time.sleep(random.randint(15, 20))

        try:
            acciones = webdriver.ActionChains(driver)
            acciones.send_keys(Keys.ENTER)
            acciones.perform()
        except Exception as e:
            print(f"Error con {nombre}: {e}")

        time.sleep(random.randint(5, 8))

        if (index + 1) % 15 == 0 and (index + 1) < len(df_filtrado):
            time.sleep(random.randint(60, 90))

    messagebox.showinfo("Finalizado", "Proceso completado.")
    driver.quit()


# El resto del código (procesar_seleccion e interfaz) se mantiene igual...
# =========================
# FILTRADO POR HORARIO
# =========================
def procesar_seleccion(opcion):
    try:
        directorio_actual = os.path.dirname(os.path.abspath(__file__))
        ruta_csv = os.path.join(directorio_actual, 'datos - Numeros.csv')

        df = pd.read_csv(ruta_csv, sep=None, engine='python', dtype={"Carnet": str})
        df.columns = df.columns.str.strip()
        df['Hora_DT'] = pd.to_datetime(df['Hora'], errors='coerce').dt.time

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
root.title("Notificador CRIT")
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
tk.Button(root, text="❌ CERRAR PROGRAMA", command=root.destroy, **estilo_boton).pack(pady=(20, 20))

root.mainloop()