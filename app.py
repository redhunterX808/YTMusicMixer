import customtkinter as ctk
from tkinter import filedialog, messagebox, Canvas
import threading
import os
import time
import numpy as np
import cv2
import librosa
from moviepy.editor import *

# --- Configurações Globais ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# Cores em formato BGR (OpenCV Padrão)
CYBERPUNK_COLORS = {
    "Neon Magenta": ((255, 0, 255), (100, 0, 100)), 
    "Neon Cyan": ((255, 255, 0), (100, 100, 0)),
    "Synthwave Purple": ((255, 50, 150), (100, 20, 80)),
    "Matrix Green": ((0, 255, 0), (0, 100, 0)),
    "Electric Blue": ((255, 0, 0), (100, 0, 0)),
    "Golden Sun": ((0, 215, 255), (0, 100, 120))
}

# Mapeamento de Resoluções (Nome -> (Largura, Altura))
RESOLUTIONS = {
    "1080p (Full HD)": (1920, 1080),
    "720p (HD)": (1280, 720),
    "540p (Mobile/Test)": (960, 540)
}

class SpectrumApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Cyberpunk Waveform Automator v5")
        self.geometry("1100x850")
        self.minsize(1000, 800)

        # Variáveis
        self.audio_path = ctk.StringVar()
        self.image_path = ctk.StringVar()
        self.is_processing = False
        self.start_time = 0
        
        # Dados fictícios para preview
        self.dummy_data = self.generate_dummy_data()

        self.setup_ui()
        self.after(100, self.update_preview)

    def generate_dummy_data(self):
        x = np.linspace(0, np.pi, 128)
        data = np.sin(x) * 0.8 + np.random.rand(128) * 0.2
        return data

    def bgr_to_hex(self, bgr_tuple):
        b, g, r = bgr_tuple
        return f'#{r:02x}{g:02x}{b:02x}'

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # === Sidebar (Esquerda) ===
        self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=10)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(15, 5), pady=15)
        
        ctk.CTkLabel(self.sidebar, text="CONFIGURAÇÕES", font=("Orbitron", 16, "bold"), text_color="#00ffff").pack(pady=(20, 10))

        # Arquivos
        self.btn_audio = ctk.CTkButton(self.sidebar, text="📂 Pasta de Músicas", fg_color="#ff00ff", hover_color="#b300b3", command=self.select_audio_folder)
        self.btn_audio.pack(pady=10, padx=15, fill="x")
        self.lbl_audio = ctk.CTkLabel(self.sidebar, text="...", font=("Roboto", 11), wraplength=250, text_color="gray")
        self.lbl_audio.pack(pady=(0, 15))

        self.btn_image = ctk.CTkButton(self.sidebar, text="🖼️ Imagem de Fundo", fg_color="#00ffff", hover_color="#00b3b3", text_color="black", command=self.select_image)
        self.btn_image.pack(pady=10, padx=15, fill="x")
        self.lbl_image = ctk.CTkLabel(self.sidebar, text="...", font=("Roboto", 11), wraplength=250, text_color="gray")
        self.lbl_image.pack(pady=(0, 15))

        ctk.CTkLabel(self.sidebar, text="Exportação", font=("Orbitron", 14, "bold"), text_color="#ff00ff").pack(pady=(20, 5))

        # Resolução
        ctk.CTkLabel(self.sidebar, text="Resolução do Vídeo:").pack(anchor="w", padx=20)
        self.res_var = ctk.StringVar(value="1080p (Full HD)")
        self.res_menu = ctk.CTkOptionMenu(self.sidebar, variable=self.res_var, values=list(RESOLUTIONS.keys()), command=self.update_preview)
        self.res_menu.pack(fill="x", padx=15, pady=5)

        # Bitrate
        ctk.CTkLabel(self.sidebar, text="Qualidade de Áudio (Bitrate):").pack(anchor="w", padx=20)
        self.bitrate_var = ctk.StringVar(value="320k (Alta)")
        self.bitrate_menu = ctk.CTkOptionMenu(self.sidebar, variable=self.bitrate_var, values=["320k (Alta)", "192k (Padrão)", "128k (Baixa)"])
        self.bitrate_menu.pack(fill="x", padx=15, pady=5)


        # === Main Panel (Direita) ===
        self.main_panel = ctk.CTkFrame(self, corner_radius=10)
        self.main_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 15), pady=15)
        
        ctk.CTkLabel(self.main_panel, text="PREVIEW EM TEMPO REAL", font=("Orbitron", 14, "bold"), text_color="#ff00ff").pack(pady=(15, 5))

        # Canvas Preview
        self.preview_canvas = Canvas(self.main_panel, height=250, bg="#000000", highlightthickness=0)
        self.preview_canvas.pack(fill="x", padx=20, pady=10)

        # Controles Visuais
        ctk.CTkLabel(self.main_panel, text="Paleta de Cores:").pack(anchor="w", padx=25)
        self.color_var = ctk.StringVar(value="Neon Magenta")
        self.color_menu = ctk.CTkOptionMenu(self.main_panel, variable=self.color_var, values=list(CYBERPUNK_COLORS.keys()), command=self.update_preview)
        self.color_menu.pack(fill="x", padx=25, pady=(5, 10))

        ctk.CTkLabel(self.main_panel, text="Densidade (Bins):").pack(anchor="w", padx=25)
        self.sld_density = ctk.CTkSlider(self.main_panel, from_=32, to=256, number_of_steps=7, command=self.update_preview)
        self.sld_density.set(128)
        self.sld_density.pack(fill="x", padx=25, pady=(5, 10))

        ctk.CTkLabel(self.main_panel, text="Sensibilidade (Altura):").pack(anchor="w", padx=25)
        self.sld_sens = ctk.CTkSlider(self.main_panel, from_=0.5, to=3.0, number_of_steps=25, command=self.update_preview)
        self.sld_sens.set(1.5)
        self.sld_sens.pack(fill="x", padx=25, pady=(5, 10))
        
        ctk.CTkLabel(self.main_panel, text="Posição Vertical (Y) - % da Tela:").pack(anchor="w", padx=25)
        # Slider agora é porcentagem (0.1 a 0.9) para funcionar em qualquer resolução
        self.sld_pos_y = ctk.CTkSlider(self.main_panel, from_=0.1, to=0.9, number_of_steps=50, command=self.update_preview)
        self.sld_pos_y.set(0.6) # 60% da tela (aprox 600px em 1080p)
        self.sld_pos_y.pack(fill="x", padx=25, pady=(5, 10))

        self.check_pulse_var = ctk.BooleanVar(value=True)
        self.check_pulse = ctk.CTkCheckBox(self.main_panel, text="Ativar Pulso de Fundo", variable=self.check_pulse_var)
        self.check_pulse.pack(pady=5)

        # === Footer ===
        self.footer = ctk.CTkFrame(self, height=180, corner_radius=10, fg_color="#1a1a1a")
        self.footer.grid(row=1, column=0, columnspan=2, sticky="ew", padx=15, pady=(0, 15))

        # Container para Status e Timer
        self.status_frame = ctk.CTkFrame(self.footer, fg_color="transparent")
        self.status_frame.pack(fill="x", padx=25, pady=(10, 0))
        
        self.status_label = ctk.CTkLabel(self.status_frame, text="Pronto.", font=("Consolas", 11), text_color="gray", anchor="w")
        self.status_label.pack(side="left")

        # CRONÔMETRO
        self.lbl_timer = ctk.CTkLabel(self.status_frame, text="⏱ 00:00:00", font=("Consolas", 14, "bold"), text_color="#00ffff")
        self.lbl_timer.pack(side="right")

        self.progress_bar = ctk.CTkProgressBar(self.footer, height=15, mode="determinate", progress_color="#00ffff")
        self.progress_bar.pack(fill="x", padx=25, pady=(5, 10))
        self.progress_bar.set(0)

        self.btn_start = ctk.CTkButton(self.footer, text="INICIAR RENDERIZAÇÃO", font=("Orbitron", 14, "bold"), height=40, fg_color="green", hover_color="darkgreen", command=self.start_process)
        self.btn_start.pack(pady=(0, 15))

    # --- Lógica de Timer e Atualizações UI ---
    def update_timer_display(self):
        """Atualiza o cronômetro na interface"""
        if self.is_processing:
            elapsed = time.time() - self.start_time
            # Formata para HH:MM:SS
            m, s = divmod(int(elapsed), 60)
            h, m = divmod(m, 60)
            time_str = f"⏱ {h:02d}:{m:02d}:{s:02d}"
            self.lbl_timer.configure(text=time_str)
            self.after(1000, self.update_timer_display) # Chama novamente em 1 segundo

    def update_preview(self, _=None):
        self.preview_canvas.delete("all")
        
        w_canvas = self.preview_canvas.winfo_width()
        h_canvas = self.preview_canvas.winfo_height()
        if w_canvas < 10: w_canvas = 400 

        # Parâmetros
        n_bins = int(self.sld_density.get())
        sensitivity = self.sld_sens.get()
        pos_y_percent = self.sld_pos_y.get()
        
        # Converte Y percentual para pixels do canvas
        pos_y_canvas = pos_y_percent * h_canvas

        colors_bgr = CYBERPUNK_COLORS[self.color_var.get()]
        main_hex = self.bgr_to_hex(colors_bgr[0])
        glow_hex = self.bgr_to_hex(colors_bgr[1])

        indices = np.linspace(0, len(self.dummy_data)-1, n_bins).astype(int)
        current_data = self.dummy_data[indices] * sensitivity

        center_x = w_canvas / 2
        bar_width = (w_canvas / (n_bins * 2))
        max_bar_h = h_canvas / 3 

        for i in range(n_bins):
            bar_h = current_data[i] * max_bar_h
            x_offset = (i * bar_width) + (bar_width / 2)
            
            x_l = center_x - x_offset - (bar_width/2)
            x_r = center_x + x_offset - (bar_width/2)
            y_start = pos_y_canvas
            y_end = pos_y_canvas - bar_h

            self.preview_canvas.create_rectangle(x_l-1, y_start, x_l+bar_width, y_end, outline=glow_hex, fill=glow_hex)
            self.preview_canvas.create_rectangle(x_r-1, y_start, x_r+bar_width, y_end, outline=glow_hex, fill=glow_hex)
            self.preview_canvas.create_rectangle(x_l, y_start, x_l+bar_width-1, y_end, outline=main_hex, fill=main_hex)
            self.preview_canvas.create_rectangle(x_r, y_start, x_r+bar_width-1, y_end, outline=main_hex, fill=main_hex)

    def select_audio_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.audio_path.set(path)
            self.lbl_audio.configure(text=os.path.basename(path), text_color="white")

    def select_image(self):
        path = filedialog.askopenfilename(filetypes=[("Imagens", "*.jpg *.png *.jpeg")])
        if path:
            self.image_path.set(path)
            self.lbl_image.configure(text=os.path.basename(path), text_color="white")

    def set_loading(self, active=True):
        if active:
            self.progress_bar.configure(mode="indeterminate")
            self.progress_bar.start()
            self.btn_start.configure(state="disabled", text="PROCESSANDO...", fg_color="gray")
            # Inicia cronometro
            self.start_time = time.time()
            self.update_timer_display()
        else:
            self.progress_bar.stop()
            self.progress_bar.configure(mode="determinate")
            self.progress_bar.set(0)
            self.btn_start.configure(state="normal", text="INICIAR RENDERIZAÇÃO", fg_color="green")

    def log(self, text):
        self.status_label.configure(text=text)

    # --- LÓGICA PRINCIPAL ---
    def start_process(self):
        if self.is_processing: return
        if not self.audio_path.get() or not self.image_path.get():
            messagebox.showwarning("Aviso", "Selecione a pasta de áudio e a imagem!")
            return
        
        self.is_processing = True
        self.set_loading(True)
        threading.Thread(target=self.process_video_logic, daemon=True).start()

    def process_video_logic(self):
        try:
            # Obtém configurações da GUI
            res_name = self.res_var.get()
            target_w, target_h = RESOLUTIONS[res_name]
            
            bitrate_str = self.bitrate_var.get().split()[0] # Pega só "320k" do texto
            
            self.log(f"Config: {res_name} | Audio: {bitrate_str}")
            time.sleep(1)

            self.log("Lendo áudios...")
            audio_files = [f for f in os.listdir(self.audio_path.get()) if f.lower().endswith(('.mp3', '.wav'))]
            audio_files.sort()
            
            if not audio_files: raise Exception("Sem músicas na pasta.")

            full_audio_clips = []
            timestamps = []
            current_t = 0
            
            for f in audio_files:
                path = os.path.join(self.audio_path.get(), f)
                clip = AudioFileClip(path)
                full_audio_clips.append(clip)
                m, s = divmod(int(current_t), 60)
                timestamps.append(f"{m:02d}:{s:02d} - {os.path.splitext(f)[0]}")
                current_t += clip.duration
            
            with open(os.path.join(self.audio_path.get(), "tracklist.txt"), "w") as t:
                t.write("\n".join(timestamps))

            self.log("Unindo áudios...")
            final_audio = concatenate_audioclips(full_audio_clips)
            
            # Prepara Imagem na Resolução Escolhida
            self.log(f"Redimensionando imagem para {target_w}x{target_h}...")
            bg = cv2.imread(self.image_path.get())
            bg = cv2.resize(bg, (target_w, target_h))
            
            # Análise
            self.log("Analisando frequências (FFT)...")
            temp_wav = "temp_render_audio.wav"
            final_audio.write_audiofile(temp_wav, fps=22050, verbose=False, logger=None)
            y, sr = librosa.load(temp_wav, sr=22050)
            os.remove(temp_wav)
            
            D = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
            DB = librosa.amplitude_to_db(D, ref=np.max)
            
            # Parâmetros GUI
            n_bins = int(self.sld_density.get())
            sens = self.sld_sens.get()
            pos_y_percent = self.sld_pos_y.get()
            pos_y_pixel = int(pos_y_percent * target_h) # Converte % para pixel real
            
            colors = CYBERPUNK_COLORS[self.color_var.get()]
            pulse = self.check_pulse_var.get()
            main_color = colors[0]
            glow_color = colors[1]

            # Função de Frame Otimizada para Resolução Dinâmica
            def make_frame(t):
                idx = int(t * sr / 512)
                idx = min(idx, DB.shape[1] - 1)
                data = DB[:n_bins, idx]
                norm_data = (data + 80) / 80
                norm_data = np.clip(norm_data, 0, 1) * sens

                frame = bg.copy()
                h, w, _ = frame.shape
                
                if pulse:
                    bass = np.mean(norm_data[:5]) if len(norm_data) > 0 else 0
                    if bass > 0.6:
                        M = cv2.getRotationMatrix2D((w//2, h//2), 0, 1.0 + (bass * 0.02))
                        frame = cv2.warpAffine(frame, M, (w, h))

                c_x = w // 2
                b_w = int(w / (n_bins * 2))
                if b_w < 1: b_w = 1
                
                max_bar_h = h / 3
                
                for i in range(n_bins):
                    bh = int(norm_data[i] * norm_data[i] * max_bar_h)
                    x_l = c_x - (i * b_w) - b_w
                    x_r = c_x + (i * b_w)
                    y_e = pos_y_pixel - bh # Usa a posição calculada baseada na resolução
                    
                    # Espessura dinâmica baseada na resolução
                    glow_th = max(2, b_w + 4)
                    main_th = max(1, b_w - 2)

                    cv2.line(frame, (x_l+b_w//2, pos_y_pixel), (x_l+b_w//2, y_e), glow_color, glow_th)
                    cv2.line(frame, (x_r+b_w//2, pos_y_pixel), (x_r+b_w//2, y_e), glow_color, glow_th)
                    cv2.line(frame, (x_l+b_w//2, pos_y_pixel), (x_l+b_w//2, y_e), main_color, main_th)
                    cv2.line(frame, (x_r+b_w//2, pos_y_pixel), (x_r+b_w//2, y_e), main_color, main_th)

                return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            self.log(f"RENDERIZANDO ({target_w}x{target_h} @ {bitrate_str})...")
            video = VideoClip(make_frame, duration=final_audio.duration)
            video = video.set_audio(final_audio)
            
            out = os.path.join(self.audio_path.get(), f"Final_Mix_{res_name.split()[0]}_{int(time.time())}.mp4")
            
            # Exporta com os parâmetros escolhidos
            video.write_videofile(
                out, 
                fps=30, 
                codec="libx264", 
                audio_codec="aac", 
                audio_bitrate=bitrate_str, # Bitrate selecionado
                threads=4, 
                verbose=False, 
                logger=None
            )
            
            self.log("Concluído!")
            messagebox.showinfo("Sucesso", f"Vídeo salvo em:\n{out}")

        except Exception as e:
            messagebox.showerror("Erro", str(e))
            self.log("Erro no processo.")
        finally:
            self.is_processing = False
            self.set_loading(False)
            if 'full_audio_clips' in locals(): 
                for c in full_audio_clips: c.close()

if __name__ == "__main__":
    app = SpectrumApp()
    app.mainloop()
