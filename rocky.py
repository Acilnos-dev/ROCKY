import customtkinter as ctk #type:ignore
import speech_recognition as sr #type:ignore
import ollama   #type:ignore
import pyttsx3 #type: ignore
import queue
import threading
import os
import datetime
import webbrowser
import psutil   #type:ignore
import pyautogui    #type:ignore
import pyperclip    #type:ignore
import time
import pywhatkit #type:ignore
from PIL import Image #type:ignore

try:
    import pytesseract #type:ignore
except ImportError:
    pytesseract = None

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class InterfazRocky(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ==========================================
        # 1. CONFIGURACIÓN DE LA VENTANA
        # ==========================================
        self.title("ROCKY - Terminal Central Optimizada")
        self.geometry("800x750")  # Ligeramente más alta para acomodar el núcleo
        self.attributes("-alpha", 0.94) 
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1) 
        
        self.historial_mensajes = []
        self.LIMITE_MEMORIA = 10 
        self.cerebro_lock = threading.Lock()
        self.micro_activado = True 
        
        self.alerta_ram_activada = False
        self.alerta_cpu_activada = False
        self.LIMITE_RAM_CRITICO = 95.0
        self.LIMITE_RAM_SEGURO = 80.0
        self.LIMITE_CPU_CRITICO = 90.0
        
        # ==========================================
        # 2. CAJA DE HERRAMIENTAS 
        # ==========================================
        self.mis_funciones = {
            'gestionar_programa': self.tool_gestionar_programa,
            'consultar_sistema': self.tool_consultar_sistema,
            'interactuar_web': self.tool_interactuar_web,
            'controlar_volumen': self.tool_controlar_volumen,
            'enviar_whatsapp': self.tool_enviar_whatsapp,
            'control_reproductor': self.tool_control_reproductor,
            'capturar_pantalla': self.tool_capturar_pantalla, 
            'leer_pantalla': self.tool_leer_pantalla        
        }

        self.herramientas_para_ia = [
            {
                "type": "function",
                "function": {
                    "name": "gestionar_programa",
                    "description": "Abre o cierra cualquier programa, aplicación o juego instalado en el ordenador.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "accion": {"type": "string", "enum": ["abrir", "cerrar"]},
                            "nombre_app": {"type": "string", "description": "Nombre exacto del programa (ej: discord, spotify, chrome)"}
                        },
                        "required": ["accion", "nombre_app"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "consultar_sistema",
                    "description": "Obtiene información del sistema: la hora actual, el estado de los componentes (CPU/RAM/Batería) o lee el portapapeles.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "tipo_info": {"type": "string", "enum": ["hora", "estado_pc", "portapapeles"]}
                        },
                        "required": ["tipo_info"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "interactuar_web",
                    "description": "Busca contenido en internet, ya sea vídeos en YouTube o información general en Google.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "plataforma": {"type": "string", "enum": ["youtube", "google"]},
                            "busqueda": {"type": "string", "description": "Lo que se quiere buscar. Usa 'inicio' para solo abrir la web principal sin buscar nada."}
                        },
                        "required": ["plataforma", "busqueda"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "controlar_volumen",
                    "description": "Sube, baja o silencia el volumen del ordenador.",
                    "parameters": {
                        "type": "object",
                        "properties": {"accion": {"type": "string", "enum": ["subir", "bajar", "mutear"]}},
                        "required": ["accion"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "enviar_whatsapp",
                    "description": "Envía un mensaje de texto a través de WhatsApp.",
                    "parameters": {
                        "type": "object",
                        "properties": {"mensaje": {"type": "string"}},
                        "required": ["mensaje"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "control_reproductor",
                    "description": "Pausa, reanuda o cambia la música/vídeos que estén sonando de fondo en programas como Spotify o VLC.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "accion": {"type": "string", "enum": ["playpause", "nexttrack", "prevtrack"]}
                        },
                        "required": ["accion"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "capturar_pantalla",
                    "description": "Toma una captura de la pantalla actual del usuario y la guarda.",
                    "parameters": {
                        "type": "object",
                        "properties": {"nombre_archivo": {"type": "string", "description": "Nombre opcional para el archivo"}},
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "leer_pantalla",
                    "description": "Usa escaneo óptico (OCR) para leer todo el texto que hay visible actualmente en la pantalla del usuario.",
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        ]

        # ==========================================
        # 3. INTERFAZ GRÁFICA MEJORADA CON J.A.R.V.I.S. CORE
        # ==========================================
        
        self.label_titulo = ctk.CTkLabel(self, text="[ SISTEMA DE MISIÓN ROCKY v3.2 ]", font=("Consolas", 22, "bold"), text_color="#00ffff")
        self.label_titulo.grid(row=0, column=0, pady=(15, 0))

        # --- INICIO EFECTO NÚCLEO J.A.R.V.I.S. ---
        self.frame_core = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_core.grid(row=1, column=0, pady=5)

        self.canvas_core = ctk.CTkCanvas(self.frame_core, width=120, height=120, bg="#242424", highlightthickness=0)
        self.canvas_core.pack()

        self.estado_pensando = False
        self.angulo_exterior = 0
        self.angulo_interior = 180

        self.anillo_exterior = self.canvas_core.create_arc(10, 10, 110, 110, start=self.angulo_exterior, extent=280, outline="#00d2ff", width=3, style="arc")
        self.anillo_interior = self.canvas_core.create_arc(25, 25, 95, 95, start=self.angulo_interior, extent=200, outline="#0088cc", width=5, style="arc")
        
        self.rotar_nucleo()
        # --- FIN EFECTO NÚCLEO J.A.R.V.I.S. ---

        # Panel de Telemetría Dual
        self.frame_telemetria = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_telemetria.grid(row=2, column=0, pady=(0, 10))
        
        self.label_cpu = ctk.CTkLabel(self.frame_telemetria, text="CPU:", font=("Consolas", 12), text_color="#808000")
        self.label_cpu.pack(side="left", padx=5)
        self.barra_cpu = ctk.CTkProgressBar(self.frame_telemetria, width=150, progress_color="#808000")
        self.barra_cpu.pack(side="left", padx=(0, 15))

        self.label_ram = ctk.CTkLabel(self.frame_telemetria, text="RAM:", font=("Consolas", 12), text_color="#008080")
        self.label_ram.pack(side="left", padx=5)
        self.barra_ram = ctk.CTkProgressBar(self.frame_telemetria, width=150, progress_color="#008080")
        self.barra_ram.pack(side="left")
        
        self.actualizar_telemetria() 

        # Caja de Chat
        self.caja_chat = ctk.CTkTextbox(self, font=("Consolas", 14), fg_color="#121212", text_color="#00d2ff", corner_radius=10)
        self.caja_chat.grid(row=3, column=0, padx=15, pady=(5, 10), sticky="nsew")

        mensaje_bienvenida = "========================================\n" \
                             " [ROCKY] Sistema Central Iniciado...\n" \
                             " Motor Neuronal: gemma4:e2b\n" \
                             " HUD Óptico J.A.R.V.I.S: En línea\n" \
                             " Arsenal: 8 Herramientas (Visión OCR)\n" \
                             "========================================\n\n"
        self.escribir_en_pantalla(mensaje_bienvenida, nueva_linea=False)

        # Marco Inferior
        self.frame_inferior = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_inferior.grid(row=4, column=0, padx=15, pady=(0, 15), sticky="ew")
        self.frame_inferior.grid_columnconfigure(0, weight=1)

        self.entrada_texto = ctk.CTkEntry(self.frame_inferior, placeholder_text="Escribe un comando táctico...", font=("Consolas", 14), height=45, corner_radius=8)
        self.entrada_texto.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.entrada_texto.bind("<Return>", lambda event: self.procesar_input()) 

        self.btn_mic = ctk.CTkButton(self.frame_inferior, text="🎙️ ON", width=80, height=45, font=ctk.CTkFont(weight="bold"), fg_color="#1f538d", hover_color="#14375e", corner_radius=8, command=self.alternar_micro)
        self.btn_mic.grid(row=0, column=1)

        # Hilos
        self.cola_audio = queue.Queue()
        threading.Thread(target=self.trabajador_audio, daemon=True).start()
        threading.Thread(target=self.bucle_voz, daemon=True).start()
        threading.Thread(target=self.precalentar_cerebro, daemon=True).start()

    # ==========================================
    # 4. FUNCIONES DE INTERFAZ, VOZ Y TELEMETRÍA
    # ==========================================
    
    # --- ANIMACIÓN DEL NÚCLEO ---
    def rotar_nucleo(self):
        if self.estado_pensando:
            velocidad_ext = 8
            velocidad_int = 12
            color_ext = "#ff8c00" # Naranja "Pensando"
            color_int = "#ff4500"
        else:
            velocidad_ext = 3
            velocidad_int = 5
            color_ext = "#00d2ff" # Azul "Calma"
            color_int = "#0088cc"

        self.angulo_exterior = (self.angulo_exterior - velocidad_ext) % 360 
        self.angulo_interior = (self.angulo_interior + velocidad_int) % 360 

        self.canvas_core.itemconfig(self.anillo_exterior, start=self.angulo_exterior, outline=color_ext)
        self.canvas_core.itemconfig(self.anillo_interior, start=self.angulo_interior, outline=color_int)

        self.after(40, self.rotar_nucleo)
    # ----------------------------

    def precalentar_cerebro(self):
        self.escribir_en_pantalla("[SISTEMA]: Inicializando enlaces sinápticos gemma4:e2b...")
        try:
            ollama.chat(
                model='gemma4:e2b',
                messages=[{'role': 'user', 'content': 'ping'}],
                keep_alive="1m", 
                options={"num_ctx": 2048}
            )
            self.escribir_en_pantalla("[SISTEMA]: Enlaces establecidos. Sensores online.")
        except Exception: pass

    def actualizar_telemetria(self):
        ram = psutil.virtual_memory().percent
        cpu = psutil.cpu_percent(interval=None)
        
        self.barra_ram.set(ram / 100.0)
        self.barra_cpu.set(cpu / 100.0)
        
        if ram >= self.LIMITE_RAM_CRITICO and not self.alerta_ram_activada:
            self.alerta_ram_activada = True
            self.barra_ram.configure(progress_color="#e74c3c")
            self.escribir_en_pantalla("\n[⚠️ ALERTA]: Uso de Memoria RAM CRÍTICO.")
            self.hablar("Advertencia. Memoria RAM saturada.")
        elif ram <= self.LIMITE_RAM_SEGURO and self.alerta_ram_activada:
            self.alerta_ram_activada = False
            self.barra_ram.configure(progress_color="#008080")
            self.escribir_en_pantalla("\n[SISTEMA]: RAM estabilizada.")

        if cpu >= self.LIMITE_CPU_CRITICO and not self.alerta_cpu_activada:
            self.alerta_cpu_activada = True
            self.barra_cpu.configure(progress_color="#e74c3c")
            self.escribir_en_pantalla("\n[⚠️ ALERTA]: Sobrecarga de CPU detectada.")
        elif cpu < self.LIMITE_CPU_CRITICO and self.alerta_cpu_activada:
            self.alerta_cpu_activada = False
            self.barra_cpu.configure(progress_color="#808000")

        self.after(2000, self.actualizar_telemetria)

    def alternar_micro(self):
        self.micro_activado = not self.micro_activado
        if self.micro_activado:
            self.btn_mic.configure(text="🎙️ ON", fg_color="#1f538d", hover_color="#14375e")
            self.escribir_en_pantalla("[SISTEMA]: Micrófono activado.")
        else:
            self.btn_mic.configure(text="🎙️ OFF", fg_color="#e74c3c", hover_color="#c0392b")
            self.escribir_en_pantalla("[SISTEMA]: Micrófono silenciado.")

    def escribir_en_pantalla(self, texto, nueva_linea=True):
        def actualizar_ui():
            self.caja_chat.configure(state="normal")
            self.caja_chat.insert("end", texto + ("\n" if nueva_linea else ""))
            self.caja_chat.see("end")
            self.caja_chat.configure(state="disabled")
        self.after(0, actualizar_ui) 

    def trabajador_audio(self):
        while True:
            texto = self.cola_audio.get() 
            if texto:
                motor = pyttsx3.init()
                motor.setProperty('rate', 160) 
                motor.say(texto)
                motor.runAndWait()
                del motor

    def hablar(self, texto):
        if texto.strip(): self.cola_audio.put(texto)

    def bucle_voz(self):
        recognizer = sr.Recognizer()
        while True:
            if not getattr(self, 'micro_activado', True):
                time.sleep(0.5); continue
                
            with sr.Microphone() as source:
                recognizer.pause_threshold = 0.5 
                recognizer.adjust_for_ambient_noise(source, duration=1)
                try:
                    audio = recognizer.listen(source, timeout=None, phrase_time_limit=5)
                    comando = recognizer.recognize_google(audio, language="es-ES").lower()
                    
                    if "rocky" in comando:
                        comandos_salir = ["apágate", "salir", "desconéctate", "adiós"]
                        if any(palabra in comando for palabra in comandos_salir):
                            with self.cerebro_lock:
                                self.escribir_en_pantalla("\nROCKY: Desconectando sistemas por voz...")
                                self.hablar("Desconectando sistemas. Hasta pronto.")
                                time.sleep(2); os._exit(0)
                        
                        with self.cerebro_lock: self.pensar_y_hablar(comando)
                except: pass 

    def procesar_input(self):
        texto = self.entrada_texto.get().lower().strip()
        if texto:
            self.entrada_texto.delete(0, "end")
            comandos_salir = ["salir", "apágate", "exit", "adiós"]
            if any(palabra in texto for palabra in comandos_salir):
                self.escribir_en_pantalla("\nROCKY: Cerrando interfaz...")
                self.hablar("Desconexión completa.")
                time.sleep(2); os._exit(0)
            
            threading.Thread(target=self.ejecutar_cerebro, args=(texto,), daemon=True).start()

    def ejecutar_cerebro(self, texto):
        with self.cerebro_lock: self.pensar_y_hablar(texto)

    # ==========================================
    # 5. SÚPER-HERRAMIENTAS Y MÓDULOS DE VISIÓN
    # ==========================================
    def tool_gestionar_programa(self, accion: str, nombre_app: str) -> str:
        if accion == "abrir":
            pyautogui.press("win"); time.sleep(0.5); pyautogui.write(nombre_app); time.sleep(1); pyautogui.press("enter")
            return f"He intentado abrir la aplicación '{nombre_app}'."
        elif accion == "cerrar":
            os.system(f"taskkill /f /im {nombre_app}.exe /t"); return f"Proceso '{nombre_app}' cerrado forzosamente."
        return "Acción no reconocida."

    def tool_consultar_sistema(self, tipo_info: str) -> str:
        if tipo_info == "hora": return datetime.datetime.now().strftime("La hora actual es %H:%M.")
        elif tipo_info == "estado_pc":
            cpu = psutil.cpu_percent(interval=0.5); ram = psutil.virtual_memory().percent
            bateria = psutil.sensors_battery()
            bat_txt = f"Batería al {bateria.percent}%" if bateria else "Conectado a la corriente"
            return f"Estado -> CPU: {cpu}%. RAM: {ram}%. Energía: {bat_txt}."
        elif tipo_info == "portapapeles":
            texto = pyperclip.paste(); return f"Portapapeles: '{texto}'" if texto.strip() else "El portapapeles está vacío."
        return "Tipo de información no válida."

    def tool_interactuar_web(self, plataforma: str, busqueda: str) -> str:
        if busqueda.lower() in ["inicio", "nada"]:
            url = "https://www.youtube.com" if plataforma == "youtube" else "https://www.google.com"
            webbrowser.open(url); return f"Página principal de {plataforma} abierta."
        else:
            url = f"https://www.youtube.com/results?search_query={busqueda.replace(' ', '+')}" if plataforma == "youtube" else f"https://www.google.com/search?q={busqueda.replace(' ', '+')}"
            webbrowser.open(url); return f"Búsqueda de '{busqueda}' realizada en {plataforma}."

    def tool_controlar_volumen(self, accion: str) -> str:
        if accion == "subir":
            for _ in range(5): pyautogui.press("volumeup")
            return "Volumen incrementado."
        elif accion == "bajar":
            for _ in range(5): pyautogui.press("volumedown")
            return "Volumen reducido."
        elif accion == "mutear": pyautogui.press("volumemute"); return "Volumen silenciado."
        return "Acción no reconocida."

    def tool_enviar_whatsapp(self, mensaje: str) -> str:
        numero_destino = "+34600000000" 
        try: pywhatkit.sendwhatmsg_instantly(numero_destino, mensaje, wait_time=15, tab_close=True, close_time=2); return "Mensaje enviado por WhatsApp correctamente."
        except Exception as e: return f"Error al enviar WhatsApp: {e}"

    def tool_control_reproductor(self, accion: str) -> str:
        if accion == "playpause": pyautogui.press("playpause"); return "He pausado o reanudado la reproducción."
        elif accion == "nexttrack": pyautogui.press("nexttrack"); return "He saltado a la siguiente pista."
        elif accion == "prevtrack": pyautogui.press("prevtrack"); return "He vuelto a la pista anterior."
        return "Acción multimedia no reconocida."

    def tool_capturar_pantalla(self, nombre_archivo="captura_rocky") -> str:
        try:
            if not os.path.exists("capturas_mision"): os.makedirs("capturas_mision")
            ruta = f"capturas_mision/{nombre_archivo}_{int(time.time())}.png"
            pyautogui.screenshot().save(ruta)
            os.startfile(ruta) 
            return f"Pantalla capturada y guardada exitosamente en: {ruta}"
        except Exception as e:
            return f"Error en los sensores ópticos al capturar: {e}"

    def tool_leer_pantalla(self) -> str:
        if not pytesseract:
            return "El escáner óptico (pytesseract) no está instalado en el sistema base."
        try:
            foto = pyautogui.screenshot()
            texto_extraido = pytesseract.image_to_string(foto, lang='spa') 
            if not texto_extraido.strip():
                return "Sensores activos, pero no detecto ningún texto legible en la pantalla actual."
            return f"He escaneado la pantalla. El texto detectado es:\n{texto_extraido[:800]}..." 
        except Exception as e:
            return f"Fallo en el módulo de lectura OCR: {e}"

    # ==========================================
    # 6. EL CEREBRO AUTÓNOMO
    # ==========================================
    def pensar_y_hablar(self, texto_usuario):
        pregunta_limpia = texto_usuario.replace("rocky", "").strip()
        if not pregunta_limpia: return

        self.escribir_en_pantalla(f"\nTú: {pregunta_limpia}")
        self.escribir_en_pantalla("   [ROCKY está procesando telemetría y opciones...]")
        
        # --- EL NÚCLEO PASA A ESTADO "PENSANDO" (Naranja) ---
        self.estado_pensando = True 
        
        self.historial_mensajes.append({'role': 'user', 'content': pregunta_limpia})
        
        sistema = {
            'role': 'system', 
            'content': 'Eres ROCKY, un ingeniero alienígena de Erid. Eres lógico y eficiente. '
                       'Tienes acceso a herramientas de sistema, control multimedia y visión OCR. '
                       'REGLA CRÍTICA: Si el usuario solo te saluda o charla casualmente, responde de forma natural y NO uses herramientas. '
                       'Usa las herramientas SOLO cuando se te pida una acción explícita (ej. "abre discord"). '
                       'Responde de forma breve, técnica y con el toque curioso de un eridiano.'
        }
        
        try:
            respuesta = ollama.chat(
                model='gemma4:e2b', 
                messages=[sistema] + self.historial_mensajes,
                tools=self.herramientas_para_ia, 
                stream=False,
                keep_alive=0,  
                options={
                    "num_ctx": 2048  
                }
            )
            
            mensaje_ia = respuesta['message']
            self.historial_mensajes.append(mensaje_ia)

            if mensaje_ia.get('tool_calls'):
                for tool in mensaje_ia['tool_calls']:
                    nombre_funcion = tool['function']['name']
                    argumentos = tool['function']['arguments']
                    
                    self.escribir_en_pantalla(f"   [SISTEMA]: Ejecutando rutina '{nombre_funcion}'...")
                    resultado_real = self.mis_funciones[nombre_funcion](**argumentos)
                    
                    self.escribir_en_pantalla(f"ROCKY: {resultado_real}")
                    self.hablar(resultado_real)
                    self.historial_mensajes.append({'role': 'assistant', 'content': resultado_real})
                
            else:
                texto_limpio = mensaje_ia['content'].replace("*", "").strip()
                
                # Escudo anti-código crudo
                if texto_limpio.startswith("{") and "}" in texto_limpio:
                    self.escribir_en_pantalla("   [SISTEMA]: Anomalía interceptada. Ocultando código crudo.")
                    texto_limpio = "Mis sensores de lenguaje tuvieron un pequeño salto. ¿Decías, Capitán?"
                    
                self.escribir_en_pantalla(f"ROCKY: {texto_limpio}")
                self.hablar(texto_limpio)
                
            if len(self.historial_mensajes) > self.LIMITE_MEMORIA:
                self.historial_mensajes = self.historial_mensajes[-self.LIMITE_MEMORIA:]
            
            # --- EL NÚCLEO VUELVE A LA CALMA (Azul) ---
            self.estado_pensando = False

        except Exception as e:
            self.escribir_en_pantalla(f"\n[Error del Sistema Neurológico: {e}]")
            self.hablar("He experimentado un fallo en mis conexiones lógicas principales.")
            
            # --- EL NÚCLEO VUELVE A LA CALMA TRAS ERROR ---
            self.estado_pensando = False

if __name__ == "__main__":
    app = InterfazRocky()
    app.mainloop()