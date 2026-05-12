import pandas as pd
from selenium import webdriver
from selenium.webdriver.edge.options import Options
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

    # Se ajustaron los nombres a MAYÚSCULAS
    df_agrupado = df_filtrado.groupby(['NUMERO', 'NOMBRE', 'FECHA DE CITA']).agg({
        'CARNET': lambda x: ', '.join(map(str, x.unique())),
        'HORA': lambda x: ' y '.join(map(str, x.unique()))
    }).reset_index()

    edge_options = Options()
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_sesion = os.path.join(directorio_actual, "sesion_whatsapp")

    edge_options.add_argument(f"user-data-dir={ruta_sesion}")
    edge_options.add_argument("--disable-blink-features=AutomationControlled")
    edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])

    try:
        driver = webdriver.Edge(options=edge_options)
    except Exception as e:
        messagebox.showerror("Error", f"Cierra otras ventanas de Edge.\n{e}")
        return

    driver.get("https://web.whatsapp.com")
    messagebox.showinfo("WhatsApp Web", "Espera a que carguen tus chats y presiona Aceptar.")

    enviados = 0
    fallidos = []

    for index, fila in df_agrupado.iterrows():
        nombre = str(fila['NOMBRE']).strip()
        carnets = str(fila['CARNET']).strip()

        # Limpieza de número
        num_limpio = "".join(filter(str.isdigit, str(fila['NUMERO'])))
        # Definir ladas de USA
        ladas_usa = ("213", "310", "323", "415", "619", "818", "916")

        if num_limpio.startswith(ladas_usa):
            numero = "1" + num_limpio
        elif num_limpio.startswith("1") and len(num_limpio) > 10 and num_limpio[1:4] in ladas_usa:
            numero = num_limpio
        else:
            numero = "52" + num_limpio if not num_limpio.startswith("52") else num_limpio

        mensaje_completo = (
            f"Buen día {nombre}, le recordamos la cita del paciente con carnet {carnets} "
            f"programada para el día {fila['FECHA DE CITA']} a las {fila['HORA']} en CRIT Tijuana. "
            f"En caso de no poder asistir, favor de comunicarse al número 664 900 9900. ¡Gracias!"
        )

        url = f"https://web.whatsapp.com/send?phone={numero}&text={urllib.parse.quote(mensaje_completo)}"
        driver.get(url)

        try:
            wait = WebDriverWait(driver, 30)
            caja_texto = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[contenteditable="true"][data-tab="10"]')))

            time.sleep(2)
            error_popup = driver.find_elements(By.XPATH,
                                               '//div[contains(text(), "inválido") or contains(text(), "no existe")]')

            if error_popup:
                fallidos.append(f"{nombre} ({numero}) - No existe")
                continue

            time.sleep(1)
            caja_texto.send_keys(Keys.ENTER)
            enviados += 1
            print(f"✅ Enviado: {nombre}")

        except Exception:
            fallidos.append(f"{nombre} ({numero}) - No existe el número")
            print(f"❌ Falló: {nombre}")

        time.sleep(random.randint(4, 7))

        if (index + 1) % 15 == 0:
            time.sleep(random.randint(40, 60))

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
        #Aquí se le cambia el nombre
        ruta_csv = os.path.join(directorio_actual, 'Book.csv')

        df = pd.read_csv(
            ruta_csv,
            sep=None,
            engine='python',
            dtype={"CARNET": str}
        )

        df.columns = df.columns.str.strip()

        # Convertir usando la columna HORA en mayúsculas
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
# INTERFAZ GRÁFICA (Sin cambios en lógica, solo visual)
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
tk.Button(root, text="❌ SALIR", command=root.destroy, font=FUENTE_TIERNA, fg="white", bg="#B22222", relief="flat",
          width=25, pady=5).pack(pady=(30, 0))

root.mainloop()