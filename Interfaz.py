# =========================
# IMPORTACIÓN DE LIBRERÍAS
# =========================
import pandas as pd  # Para manejo de datos (CSV)
from selenium import webdriver  # Para automatizar el navegador
from selenium.webdriver.edge.options import Options  # Opciones de Edge
from selenium.webdriver.common.keys import Keys  # Para enviar teclas (ENTER)
import urllib.parse  # Para codificar mensajes en URL
import time  # Para pausas
import os  # Manejo de rutas
import random  # Para tiempos aleatorios (evitar bloqueo)
import tkinter as tk  # Interfaz gráfica
from tkinter import messagebox  # Ventanas emergentes
from PIL import Image, ImageTk  # Manejo de imágenes
import ctypes  # Ajustes de resolución (DPI)

# =========================
# CONFIGURACIÓN DE PANTALLA (DPI)
# =========================
# Esto ayuda a que la interfaz no se vea borrosa en Windows
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# =========================
# COLORES Y ESTILO
# =========================
COLOR_PRIMARIO = "#681A73"  # Morado
COLOR_ACENTO = "#F2CB05"    # Amarillo
COLOR_TEXTO = "#FFFFFF"     # Blanco
FUENTE_TIERNA = ("Comic Sans MS", 11, "bold")  # Fuente amigable

# =========================
# FUNCIÓN PRINCIPAL DE ENVÍO
# =========================
def iniciar_envio(df_filtrado):
    """
    Recibe un DataFrame con los contactos filtrados
    y envía mensajes por WhatsApp Web automáticamente.
    """

    # Validación: si no hay datos
    if df_filtrado.empty:
        messagebox.showwarning("Sin datos", "No hay registros en el bloque seleccionado.")
        return

    # Configuración del navegador Edge
    edge_options = Options()

    # Ruta donde se guardará la sesión (evita escanear QR cada vez)
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_sesion = os.path.join(directorio_actual, "sesion_whatsapp")

    edge_options.add_argument(f"user-data-dir={ruta_sesion}")

    # Configuración para evitar detección como bot
    edge_options.add_argument("--disable-blink-features=AutomationControlled")
    edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    edge_options.add_experimental_option("useAutomationExtension", False)

    # Intentar abrir navegador
    try:
        driver = webdriver.Edge(options=edge_options)
    except Exception:
        messagebox.showerror("Error de Sesión",
                             "No se pudo abrir el navegador.\n\nCierra WhatsApp Web antes de iniciar.")
        return

    # Abrir WhatsApp Web
    driver.get("https://web.whatsapp.com")

    # Esperar a que el usuario inicie sesión
    messagebox.showinfo("WhatsApp Web", "Espera a que carguen tus chats y presiona Aceptar.")

    # =========================
    # ENVÍO DE MENSAJES
    # =========================
    for index, (idx_original, fila) in enumerate(df_filtrado.iterrows()):

        # Obtener datos del CSV
        nombre = str(fila['Nombre']).strip()
        carnet = str(fila['Carnet']).strip()
        numero_crudo = str(fila['Numero']).replace(".0", "").strip()
        # Si el número NO empieza con 52, se lo agregamos
        if not numero_crudo.startswith("52"):
            numero = "52" + numero_crudo
        else:
            numero = numero_crudo
        hora_cita = str(fila['Hora']).strip()
        fecha_cita = str(fila['Fecha de cita']).strip()
        hora_cita = str(fila['Hora']).strip()
        fecha_cita = str(fila['Fecha de cita']).strip()

        # Construir mensaje personalizado
        mensaje_completo = (
            f"Buen día {nombre}, le recordamos la cita del paciente con carnet {carnet} programada para el día {fecha_cita} a las {hora_cita} en CRIT Tijuana. "
            f"Le pedimos confirmar de recibido respondiendo con la palabra 'Recibido'. ¡Gracias!"

        )

        # Convertir mensaje a formato URL
        mensaje_url = urllib.parse.quote(mensaje_completo)

        # Crear enlace de WhatsApp
        url = f"https://web.whatsapp.com/send?phone={numero}&text={mensaje_url}"

        # Abrir chat del contacto
        driver.get(url)

        # Espera para que cargue el chat
        time.sleep(random.randint(15, 20))

        try:
            # Enviar mensaje presionando ENTER
            acciones = webdriver.ActionChains(driver)
            acciones.send_keys(Keys.ENTER)
            acciones.perform()
        except Exception as e:
            print(f"Error con {nombre}: {e}")

        # Espera entre mensajes (simula comportamiento humano)
        time.sleep(random.randint(5, 8))

        # Pausa larga cada 15 mensajes (evitar bloqueo)
        if (index + 1) % 15 == 0 and (index + 1) < len(df_filtrado):
            time.sleep(random.randint(60, 90))

    # Mensaje final
    messagebox.showinfo("Finalizado", "Proceso completado.")

    # Cerrar navegador
    driver.quit()

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
btn_cerrar = tk.Button(
    root,
    text="❌ CERRAR PROGRAMA",
    command=root.destroy,
    font=FUENTE_TIERNA,
    fg=COLOR_PRIMARIO,
    bg=COLOR_ACENTO,
    relief="flat",
    width=25,
    pady=8,
    cursor="hand2",
    activebackground="#d9b504"
)
btn_cerrar.pack(pady=(20, 20))

# Ejecutar interfaz
root.mainloop()