import pandas as pd
from selenium import webdriver
# Importaciones para Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
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
# CONFIGURACIÓN DE PANTALLA (DPI)
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

    # Agrupar por paciente para no enviar varios mensajes a la misma persona
    df_agrupado = df_filtrado.groupby(['Numero', 'Nombre', 'Fecha de cita']).agg({
        'Carnet': lambda x: ', '.join(map(str, x.unique())),
        'Hora': lambda x: ' y '.join(map(str, x.unique()))
    }).reset_index()

    # Configuración de opciones para Chrome
    chrome_options = Options()
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_sesion = os.path.join(directorio_actual, "sesion_whatsapp_chrome")

    chrome_options.add_argument(f"user-data-dir={ruta_sesion}")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    # Iniciar el navegador Chrome
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        messagebox.showerror("Error",
                             f"Asegúrate de cerrar todas las ventanas de Chrome que usen la sesión automática.\nDetalle: {e}")
        return

    driver.get("https://web.whatsapp.com")
    messagebox.showinfo("WhatsApp Web",
                        "Por favor, inicia sesión si es necesario y espera a que carguen tus chats. Luego presiona Aceptar aquí.")

    enviados = 0
    fallidos = []

    for index, fila in df_agrupado.iterrows():
        nombre = str(fila['Nombre']).strip()
        carnets = str(fila['Carnet']).strip()

        # Limpiar y formatear número (Lada 52 para México)
        num_limpio = "".join(filter(str.isdigit, str(fila['Numero'])))
        if not num_limpio.startswith("52"):
            numero = "52" + num_limpio
        else:
            numero = num_limpio

        mensaje_completo = (
            f"Buen día {nombre}, le recordamos la cita del paciente con carnet {carnets} "
            f"programada para el día {fila['Fecha de cita']} a las {fila['Hora']} en CRIT Tijuana. "
            f"Confirme respondiendo 'Recibido'. ¡Gracias!"
        )

        # Cargar URL de envío directo
        url = f"https://web.whatsapp.com/send?phone={numero}&text={urllib.parse.quote(mensaje_completo)}"
        driver.get(url)

        try:
            # Esperar a que la caja de texto esté disponible
            wait = WebDriverWait(driver, 35)
            caja_texto = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[contenteditable="true"][data-tab="10"]')))

            time.sleep(2)  # Respiro para carga de interfaz

            # Verificar si aparece cartel de número inválido
            error_popup = driver.find_elements(By.XPATH,
                                               '//div[contains(text(), "inválido") or contains(text(), "no existe")]')

            if error_popup:
                fallidos.append(f"{nombre} ({numero}) - Número no registrado")
                continue

            # Presionar Enter para enviar
            caja_texto.send_keys(Keys.ENTER)
            enviados += 1
            print(f"✅ Enviado a: {nombre}")

        except Exception:
            fallidos.append(f"{nombre} ({numero}) - No existe")
            print(f"❌ No se pudo enviar a: {nombre}")

        # Pausa aleatoria para evitar detección de bot
        time.sleep(random.randint(5, 9))

        # Pausa extendida cada 15 mensajes
        if (index + 1) % 15 == 0:
            time.sleep(random.randint(30, 50))

    driver.quit()

    resumen = f"✅ Proceso finalizado\n\nTotal Enviados: {enviados}"
    if fallidos:
        resumen += "\n\n❌ Errores en:\n" + "\n".join(fallidos)
    messagebox.showinfo("Resumen de Envío", resumen)


# =========================
# LÓGICA DE FILTRADO
# =========================
def procesar_seleccion(opcion):
    try:
        directorio_actual = os.path.dirname(os.path.abspath(__file__))
        ruta_csv = os.path.join(directorio_actual, 'datos - Numeros.csv')

        if not os.path.exists(ruta_csv):
            messagebox.showerror("Error", f"No se encontró el archivo: datos - Numeros.csv")
            return

        df = pd.read_csv(ruta_csv, sep=None, engine='python', dtype={"Carnet": str, "Numero": str})
        df.columns = df.columns.str.strip()

        # Convertir columna Hora a objeto de tiempo para filtrar
        df['Hora_DT'] = pd.to_datetime(df['Hora'], errors='coerce').dt.time
        from datetime import time as dt_time

        if opcion == 1:
            df_filtrado = df[(df['Hora_DT'] >= dt_time(7, 0)) & (df['Hora_DT'] <= dt_time(11, 0))]
        elif opcion == 2:
            df_filtrado = df[(df['Hora_DT'] >= dt_time(11, 1)) & (df['Hora_DT'] <= dt_time(14, 0))]
        elif opcion == 3:
            df_filtrado = df[(df['Hora_DT'] >= dt_time(14, 1)) & (df['Hora_DT'] <= dt_time(18, 0))]

        root.withdraw()  # Ocultar menú principal
        iniciar_envio(df_filtrado)
        root.deiconify()  # Mostrar menú al terminar

    except Exception as e:
        messagebox.showerror("Error Crítico", f"Ocurrió un error: {e}")


# =========================
# INTERFAZ GRÁFICA (GUI)
# =========================
root = tk.Tk()
root.title("Notificador CRIT - Versión Chrome")
root.geometry("450x650")
root.resizable(False, False)
root.configure(bg=COLOR_PRIMARIO)

# Icono
try:
    ruta_script = os.path.dirname(os.path.abspath(__file__))
    root.iconbitmap(os.path.join(ruta_script, "icono.ico"))
except:
    pass

# Logo
try:
    img = Image.open(os.path.join(ruta_script, "logo.png"))
    img = img.resize((200, 160), Image.LANCZOS)
    photo = ImageTk.PhotoImage(img)
    tk.Label(root, image=photo, bg=COLOR_PRIMARIO).pack(pady=20)
except:
    tk.Label(root, text="💜", font=("Arial", 40), bg=COLOR_PRIMARIO, fg=COLOR_ACENTO).pack(pady=20)

tk.Label(root, text="Sistema de Recordatorios", font=("Arial", 14, "bold"), bg=COLOR_PRIMARIO, fg=COLOR_TEXTO).pack()
tk.Label(root, text="Selecciona el bloque de citas:", font=FUENTE_TIERNA, bg=COLOR_PRIMARIO, fg=COLOR_TEXTO,
         pady=10).pack()

estilo_boton = {
    "font": FUENTE_TIERNA,
    "fg": COLOR_PRIMARIO,
    "bg": COLOR_ACENTO,
    "width": 28,
    "pady": 5,
    "relief": "flat",
    "cursor": "hand2",
    "activebackground": "#d9b504"
}

tk.Button(root, text="Bloque 1 (07:00 - 11:00)", command=lambda: procesar_seleccion(1), **estilo_boton).pack(pady=10)
tk.Button(root, text="Bloque 2 (11:01 - 14:00)", command=lambda: procesar_seleccion(2), **estilo_boton).pack(pady=10)
tk.Button(root, text="Bloque 3 (14:01 - 18:00)", command=lambda: procesar_seleccion(3), **estilo_boton).pack(pady=10)

tk.Button(root, text="❌ SALIR", command=root.destroy, font=FUENTE_TIERNA, fg="white", bg="#B22222", relief="flat",
          width=28, pady=5).pack(pady=(30, 0))

root.mainloop()