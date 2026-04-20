import customtkinter as ctk

# Configuración básica del estilo
ctk.set_appearance_mode("dark")  # Modo oscuro
ctk.set_default_color_theme("blue")  # Color de los acentos

class InterfazRocky(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuración de la ventana
        self.title("ROCKY - Asistente de IA")
        self.geometry("600x500")

        # 1. Caja de texto para el chat (Ocupa casi toda la pantalla)
        self.caja_chat = ctk.CTkTextbox(self, width=560, height=400, font=("Consolas", 14))
        self.caja_chat.grid(row=0, column=0, columnspan=2, padx=20, pady=20)
        self.caja_chat.insert("0.0", "--- SISTEMA ROCKY INICIADO ---\nEsperando comandos...\n\n")
        self.caja_chat.configure(state="disabled") # Para que el usuario no pueda borrar el historial

        # 2. Barra para escribir
        self.entrada_texto = ctk.CTkEntry(self, width=440, placeholder_text="Escribe tu mensaje aquí...", font=("Consolas", 14))
        self.entrada_texto.grid(row=1, column=0, padx=(20, 10), pady=10)

        # 3. Botón de enviar
        self.boton_enviar = ctk.CTkButton(self, text="Enviar", width=100, command=self.enviar_mensaje)
        self.boton_enviar.grid(row=1, column=1, padx=(10, 20), pady=10)

    def enviar_mensaje(self):
        # Esta función recogerá el texto y lo pondrá en pantalla
        texto = self.entrada_texto.get()
        if texto:
            self.caja_chat.configure(state="normal")
            self.caja_chat.insert("end", f"\nTú: {texto}\n")
            self.caja_chat.configure(state="disabled")
            self.entrada_texto.delete(0, "end")
            self.caja_chat.see("end") # Hace scroll hacia abajo

if __name__ == "__main__":
    app = InterfazRocky()
    app.mainloop()