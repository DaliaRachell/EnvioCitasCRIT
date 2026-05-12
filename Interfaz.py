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

    df_agrupado = df_filtrado.groupby(['Numero', 'Nombre', 'Fecha de cita']).agg({
        'Carnet': lambda x: ', '.join(map(str, x.unique())),
        'Hora': lambda x: ' y '.join(map(str, x.unique()))
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
        nombre = str(fila['Nombre']).strip()
        carnets = str(fila['Carnet']).strip()
        # Limpieza profunda del número
        num_limpio = "".join(filter(str.isdigit, str(fila['Numero'])))
        numero = "52" + num_limpio if not num_limpio.startswith("52") else num_limpio

        mensaje_completo = (
            f"Buen día {nombre}, le recordamos la cita del paciente con carnet {carnets} "
            f"programada para el día {fila['Fecha de cita']} a las {fila['Hora']} en CRIT Tijuana. "
            f"Confirme respondiendo 'Recibido'. "
            f"En caso de no poder asistir, favor de comunicarse al número 664 999 00. ¡Gracias!"
        )

        url = f"https://web.whatsapp.com/send?phone={numero}&text={urllib.parse.quote(mensaje_completo)}"
        driver.get(url)

        try:
            # Esperar a que la caja de texto aparezca (señal de que el chat cargó)
            # El selector '[contenteditable="true"]' es el más estable de WhatsApp Web
            wait = WebDriverWait(driver, 30)
            caja_texto = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[contenteditable="true"][data-tab="10"]')))

            # Verificación rápida: ¿Apareció el mensaje de "Número no válido"?
            time.sleep(2)
            error_popup = driver.find_elements(By.XPATH,
                                               '//div[contains(text(), "inválido") or contains(text(), "no existe")]')

            if error_popup:
                fallidos.append(f"{nombre} ({numero}) - No existe")
                continue

            # Enviar con ENTER directamente en la caja de texto
            time.sleep(1)
            caja_texto.send_keys(Keys.ENTER)
            enviados += 1
            print(f"✅ Enviado: {nombre}")

        except Exception:
            fallidos.append(f"{nombre} ({numero}) - No existe el número")
            print(f"❌ Falló: {nombre}")

        # Pausas humanas para evitar bloqueos
        time.sleep(random.randint(4, 7))

        # Pausa larga cada 15 mensajes para simular comportamiento humano
        if (index + 1) % 15 == 0:
            time.sleep(random.randint(40, 60))

    driver.quit()

    resumen = f"✅ Proceso finalizado\n\nEnviados: {enviados}"
    if fallidos:
        resumen += "\n\n❌ No enviados:\n" + "\n".join(fallidos)
    messagebox.showinfo("Resumen", resumen)


# ... (El resto de tu código de la Interfaz GUI se mantiene igual) ...
# =========================
# FILTRADO POR HORARIO
# =========================
def procesar_seleccion(opcion):
    """
    Filtra los datos del CSV según el bloque de horario seleccionado.
    """

    try:
        # Leer archivo CSV
        directorio_actual = os.path.dirname(os.path.abspath(__file__))
        ruta_csv = os.path.join(directorio_actual, 'datos - Numeros.csv')

        df = pd.read_csv(
            ruta_csv,
            sep=None,
            engine='python',
            dtype={"Carnet": str}
        )

        # Limpiar nombres de columnas
        df.columns = df.columns.str.strip()

        # Convertir columna de hora a formato datetime
        df['Hora_DT'] = pd.to_datetime(df['Hora'], errors='coerce').dt.time

        from datetime import time as dt_time

        # Filtrar por bloques de horario
        if opcion == 1:
            df_filtrado = df[(df['Hora_DT'] >= dt_time(7, 0)) & (df['Hora_DT'] <= dt_time(11, 0))]
        elif opcion == 2:
            df_filtrado = df[(df['Hora_DT'] >= dt_time(11, 1)) & (df['Hora_DT'] <= dt_time(14, 0))]
        elif opcion == 3:
            df_filtrado = df[(df['Hora_DT'] >= dt_time(14, 1)) & (df['Hora_DT'] <= dt_time(18, 0))]

        # Ocultar ventana mientras envía
        root.withdraw()

        iniciar_envio(df_filtrado)

        # Volver a mostrar interfaz
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

# Icono de la ventana
try:
    ruta_script = os.path.dirname(os.path.abspath(__file__))
    ruta_icono = os.path.join(ruta_script, "icono.ico")
    root.iconbitmap(ruta_icono)
except Exception as e:
    print(f"No se pudo cargar el icono: {e}")

# =========================
# LOGO
# =========================
try:
    img_path = os.path.join(ruta_script, "logo.png")
    img = Image.open(img_path)
    img = img.resize((200, 160), Image.LANCZOS)
    photo = ImageTk.PhotoImage(img)

    label_img = tk.Label(root, image=photo, bg=COLOR_PRIMARIO)
    label_img.pack(pady=20)

except Exception:
    # Si no hay imagen, muestra un emoji
    tk.Label(root, text="✨", font=("Arial", 30), bg=COLOR_PRIMARIO, fg=COLOR_ACENTO).pack(pady=20)

# Texto principal
lbl = tk.Label(
    root,
    text="¡Hola! Selecciona un bloque:",
    font=FUENTE_TIERNA,
    bg=COLOR_PRIMARIO,
    fg=COLOR_TEXTO,
    pady=10
)
lbl.pack()

# Estilo de botones
estilo_boton = {
    "font": FUENTE_TIERNA,
    "fg": COLOR_PRIMARIO,
    "bg": COLOR_ACENTO,
    "width": 25,
    "pady": 2,
    "relief": "flat",
    "cursor": "hand2",
    "activebackground": "#d9b504"
}

# Botones de bloques
tk.Button(root, text="Bloque 1 (07:00 - 11:00)", command=lambda: procesar_seleccion(1), **estilo_boton).pack(pady=10)
tk.Button(root, text="Bloque 2 (11:01 - 14:00)", command=lambda: procesar_seleccion(2), **estilo_boton).pack(pady=10)
tk.Button(root, text="Bloque 3 (14:01 - 18:00)", command=lambda: procesar_seleccion(3), **estilo_boton).pack(pady=10)

# Botón para cerrar
tk.Button(root, text="❌ SALIR", command=root.destroy, font=FUENTE_TIERNA, fg="white", bg="#B22222", relief="flat",
          width=25, pady=5).pack(pady=(30, 0))

# Ejecutar interfaz
root.mainloop()