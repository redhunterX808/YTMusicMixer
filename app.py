import customtkinter as ctk
from tkinter import filedialog, messagebox, Canvas
import threading
import os
import time
import json
import numpy as np
import cv2
import librosa
from moviepy.editor import *
import moviepy.audio.fx.all as afx
from PIL import Image

# --- Configurações Globais ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# Cores (BGR para OpenCV)
CYBERPUNK_COLORS = {
    "Neon Magenta": ((255, 0, 255), (100, 0, 100)), 
    "Neon Cyan": ((255, 255, 0), (100, 100, 0)),
    "Synthwave Purple": ((255, 50, 150), (100, 20, 80)),
    "Matrix Green": ((0, 255, 0), (0, 100, 0)),
    "Electric Blue": ((255, 0, 0), (100, 0, 0)),
    "Golden Sun": ((0, 215, 255), (0, 100, 120)),
    "Blood Red": ((0, 0, 255), (0, 0, 100))
}

RESOLUTIONS = {
    "1080p (Full HD)": (1920, 1080),
    "720p (HD)": (1280, 720),
    "540p (Mobile/Test)": (960, 540)
}

LOGO_POSITIONS = ["Centro", "Canto Sup. Esq.", "Canto Sup. Dir.", "Canto Inf. Esq.", "Canto Inf. Dir."]

class SpectrumApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Cyberpunk Waveform Automator v6 - Ultimate")
        self.geometry("1200x900")
        self.minsize(1000, 800)

        # Variáveis de Caminho
        self.audio_path = ctk.StringVar()
        self.image_path = ctk.StringVar()
        self.logo_path = ctk.StringVar()
        
        self.is_processing = False
        self.start_time = 0
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

        # === Sidebar (Esquerda - Arquivos e Presets) ===
        self.sidebar = ctk.CTkFrame(self, width=320, corner_radius=10)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(15, 5), pady=15)
        
        # Header Presets
        pres_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        pres_frame.pack(fill="x", pady=(15, 5))
        ctk.CTkButton(pres_frame, text="💾 Salvar Preset", width=120, fg_color="#444", command=self.save_preset).pack(side="left", padx=10)
        ctk.CTkButton(pres_frame, text="📂 Abrir Preset", width=120, fg_color="#444", command=self.load_preset).pack(side="right", padx=10)

        ctk.CTkLabel(self.sidebar, text="ARQUIVOS & MÍDIA", font=("Orbitron", 14, "bold"), text_color="#00ffff").pack(pady=(15, 5))

        # Inputs
        self.btn_audio = ctk.CTkButton(self.sidebar, text="📂 Pasta de Músicas", fg_color="#ff00ff", hover_color="#b300b3", command=self.select_audio_folder)
        self.btn_audio.pack(pady=5, padx=15, fill="x")
        self.lbl_audio = ctk.CTkLabel(self.sidebar, text="...", font=("Roboto", 10), text_color="gray")
        self.lbl_audio.pack(pady=(0, 10))

        self.btn_image = ctk.CTkButton(self.sidebar, text="🖼️ Imagem de Fundo", fg_color="#00ffff", hover_color="#00b3b3", text_color="black", command=self.select_image)
        self.btn_image.pack(pady=5, padx=15, fill="x")
        self.lbl_image = ctk.CTkLabel(self.sidebar, text="...", font=("Roboto", 10), text_color="gray")
        self.lbl_image.pack(pady=(0, 10))

        self.btn_logo = ctk.CTkButton(self.sidebar, text="💎 Logotipo (Opcional)", fg_color="#333", border_color="#00ffff", border_width=1, command=self.select_logo)
        self.btn_logo.pack(pady=5, padx=15, fill="x")
        self.lbl_logo = ctk.CTkLabel(self.sidebar, text="Nenhum logo", font=("Roboto", 10), text_color="gray")
        self.lbl_logo.pack(pady=(0, 10))

        # Config Exportação
        ctk.CTkLabel(self.sidebar, text="CONFIGURAÇÃO DE SAÍDA", font=("Orbitron", 14, "bold"), text_color="#00ffff").pack(pady=(15, 5))
        
        ctk.CTkLabel(self.sidebar, text="Resolução:").pack(anchor="w", padx=20)
        self.res_var = ctk.StringVar(value="1080p (Full HD)")
        self.res_menu = ctk.CTkOptionMenu(self.sidebar, variable=self.res_var, values=list(RESOLUTIONS.keys()), command=self.update_preview)
        self.res_menu.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(self.sidebar, text="Bitrate Áudio:").pack(anchor="w", padx=20)
        self.bitrate_var = ctk.StringVar(value="320k (Alta)")
        ctk.CTkOptionMenu(self.sidebar, variable=self.bitrate_var, values=["320k (Alta)", "192k (Padrão)", "128k (Baixa)"]).pack(fill="x", padx=15, pady=5)

        # Checkboxes de Audio
        self.check_norm = ctk.CTkCheckBox(self.sidebar, text="Normalizar Volume (0dB)", onvalue=True, offvalue=False)
        self.check_norm.select()
        self.check_norm.pack(pady=5, anchor="w", padx=20)
        
        self.check_fade = ctk.CTkCheckBox(self.sidebar, text="Crossfade Automático (4s)", onvalue=True, offvalue=False)
        self.check_fade.select()
        self.check_fade.pack(pady=5, anchor="w", padx=20)

        # === Main Panel (Direita - Visual) ===
        self.main_panel = ctk.CTkFrame(self, corner_radius=10)
        self.main_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 15), pady=15)
        
        ctk.CTkLabel(self.main_panel, text="VISUAL & PREVIEW", font=("Orbitron", 14, "bold"), text_color="#ff00ff").pack(pady=(10, 5))

        # Canvas
        self.preview_canvas = Canvas(self.main_panel, height=220, bg="#000000", highlightthickness=0)
        self.preview_canvas.pack(fill="x", padx=20, pady=10)

        # Controles Visuais
        ctk.CTkLabel(self.main_panel, text="Paleta de Cores:").pack(anchor="w", padx=25)
        self.color_var = ctk.StringVar(value="Neon Magenta")
        self.color_menu = ctk.CTkOptionMenu(self.main_panel, variable=self.color_var, values=list(CYBERPUNK_COLORS.keys()), command=self.update_preview)
        self.color_menu.pack(fill="x", padx=25, pady=(5, 10))

        # Sliders
        ctk.CTkLabel(self.main_panel, text="Densidade (Bins):").pack(anchor="w", padx=25)
        self.sld_density = ctk.CTkSlider(self.main_panel, from_=32, to=256, number_of_steps=7, command=self.update_preview)
        self.sld_density.set(128)
        self.sld_density.pack(fill="x", padx=25, pady=5)

        ctk.CTkLabel(self.main_panel, text="Sensibilidade (Altura):").pack(anchor="w", padx=25)
        self.sld_sens = ctk.CTkSlider(self.main_panel, from_=0.5, to=3.0, number_of_steps=25, command=self.update_preview)
        self.sld_sens.set(1.5)
        self.sld_sens.pack(fill="x", padx=25, pady=5)
        
        ctk.CTkLabel(self.main_panel, text="Posição Waveform (Y %):").pack(anchor="w", padx=25)
        self.sld_pos_y = ctk.CTkSlider(self.main_panel, from_=0.1, to=0.9, number_of_steps=50, command=self.update_preview)
        self.sld_pos_y.set(0.6)
        self.sld_pos_y.pack(fill="x", padx=25, pady=5)

        # Configurações do Logo
        ctk.CTkLabel(self.main_panel, text="Posição do Logotipo:").pack(anchor="w", padx=25)
        self.logo_pos_var = ctk.StringVar(value="Centro")
        ctk.CTkOptionMenu(self.main_panel, variable=self.logo_pos_var, values=LOGO_POSITIONS, command=self.update_preview).pack(fill="x", padx=25, pady=5)

        self.check_pulse_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self.main_panel, text="Reatividade: Fundo & Logo Pulsantes", variable=self.check_pulse_var).pack(pady=10)

        # === Footer ===
        self.footer = ctk.CTkFrame(self, height=180, corner_radius=10, fg_color="#1a1a1a")
        self.footer.grid(row=1, column=0, columnspan=2, sticky="ew", padx=15, pady=(0, 15))

        self.status_frame = ctk.CTkFrame(self.footer, fg_color="transparent")
        self.status_frame.pack(fill="x", padx=25, pady=(10, 0))
        
        self.status_label = ctk.CTkLabel(self.status_frame, text="Pronto.", font=("Consolas", 11), text_color="gray", anchor="w")
        self.status_label.pack(side="left")
        self.lbl_timer = ctk.CTkLabel(self.status_frame, text="⏱ 00:00:00", font=("Consolas", 14, "bold"), text_color="#00ffff")
        self.lbl_timer.pack(side="right")

        self.progress_bar = ctk.CTkProgressBar(self.footer, height=15, mode="determinate", progress_color="#00ffff")
        self.progress_bar.pack(fill="x", padx=25, pady=(5, 10))
        self.progress_bar.set(0)

        self.btn_start = ctk.CTkButton(self.footer, text="INICIAR RENDERIZAÇÃO", font=("Orbitron", 14, "bold"), height=40, fg_color="green", hover_color="darkgreen", command=self.start_process)
        self.btn_start.pack(pady=(0, 15))

    # --- Lógica de Presets ---
    def save_preset(self):
        preset = {
            "res": self.res_var.get(),
            "bitrate": self.bitrate_var.get(),
            "color": self.color_var.get(),
            "density": self.sld_density.get(),
            "sensitivity": self.sld_sens.get(),
            "pos_y": self.sld_pos_y.get(),
            "pulse": self.check_pulse_var.get(),
            "norm": self.check_norm.get(),
            "fade": self.check_fade.get(),
            "logo_pos": self.logo_pos_var.get()
        }
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Preset", "*.json")])
        if path:
            with open(path, "w") as f:
                json.dump(preset, f, indent=4)
            messagebox.showinfo("Salvo", "Preset salvo com sucesso!")

    def load_preset(self):
        path = filedialog.askopenfilename(filetypes=[("JSON Preset", "*.json")])
        if path:
            with open(path, "r") as f:
                data = json.load(f)
                self.res_var.set(data.get("res", "1080p (Full HD)"))
                self.bitrate_var.set(data.get("bitrate", "320k (Alta)"))
                self.color_var.set(data.get("color", "Neon Magenta"))
                self.sld_density.set(data.get("density", 128))
                self.sld_sens.set(data.get("sensitivity", 1.5))
                self.sld_pos_y.set(data.get("pos_y", 0.6))
                self.check_pulse_var.set(data.get("pulse", True))
                self.check_norm.select() if data.get("norm", True) else self.check_norm.deselect()
                self.check_fade.select() if data.get("fade", True) else self.check_fade.deselect()
                self.logo_pos_var.set(data.get("logo_pos", "Centro"))
                
                self.update_preview()
                messagebox.showinfo("Carregado", "Preset aplicado!")

    # --- UI Helpers ---
    def update_timer_display(self):
        if self.is_processing:
            elapsed = time.time() - self.start_time
            m, s = divmod(int(elapsed), 60)
            h, m = divmod(m, 60)
            self.lbl_timer.configure(text=f"⏱ {h:02d}:{m:02d}:{s:02d}")
            self.after(1000, self.update_timer_display)

    def select_audio_folder(self):
        path = filedialog.askdirectory()
        if path: self.audio_path.set(path); self.lbl_audio.configure(text=os.path.basename(path), text_color="white")

    def select_image(self):
        path = filedialog.askopenfilename(filetypes=[("Imagens", "*.jpg *.png *.jpeg")])
        if path: self.image_path.set(path); self.lbl_image.configure(text=os.path.basename(path), text_color="white")

    def select_logo(self):
        path = filedialog.askopenfilename(filetypes=[("Imagens PNG", "*.png")])
        if path: self.logo_path.set(path); self.lbl_logo.configure(text=os.path.basename(path), text_color="white")

    def update_preview(self, _=None):
        self.preview_canvas.delete("all")
        w, h = self.preview_canvas.winfo_width(), self.preview_canvas.winfo_height()
        if w < 10: w = 400
        
        # Desenha Waveform Simples
        n_bins = int(self.sld_density.get())
        sens = self.sld_sens.get()
        pos_y_canvas = self.sld_pos_y.get() * h
        colors = CYBERPUNK_COLORS[self.color_var.get()]
        
        indices = np.linspace(0, len(self.dummy_data)-1, n_bins).astype(int)
        data = self.dummy_data[indices] * sens
        
        cx, bar_w = w / 2, w / (n_bins * 2)
        
        for i in range(n_bins):
            bh = data[i] * (h/3)
            xl, xr = cx - (i * bar_w) - bar_w, cx + (i * bar_w)
            y_end = pos_y_canvas - bh
            
            c1, c2 = self.bgr_to_hex(colors[1]), self.bgr_to_hex(colors[0])
            self.preview_canvas.create_rectangle(xl, pos_y_canvas, xl+bar_w, y_end, fill=c2, outline=c1)
            self.preview_canvas.create_rectangle(xr, pos_y_canvas, xr+bar_w, y_end, fill=c2, outline=c1)

        # Desenha "Fantasma" do Logo
        if self.logo_path.get():
            pos = self.logo_pos_var.get()
            lx, ly = w/2, h/2 # Centro default
            margin = 20
            if "Sup. Esq" in pos: lx, ly = margin + 20, margin + 20
            elif "Sup. Dir" in pos: lx, ly = w - margin - 20, margin + 20
            elif "Inf. Esq" in pos: lx, ly = margin + 20, h - margin - 20
            elif "Inf. Dir" in pos: lx, ly = w - margin - 20, h - margin - 20
            
            self.preview_canvas.create_oval(lx-15, ly-15, lx+15, ly+15, outline="white", width=2, dash=(2,2))
            self.preview_canvas.create_text(lx, ly, text="LOGO", fill="white", font=("Arial", 8))

    def set_loading(self, active=True):
        if active:
            self.progress_bar.configure(mode="indeterminate")
            self.progress_bar.start()
            self.btn_start.configure(state="disabled", text="PROCESSANDO...", fg_color="gray")
            self.start_time = time.time()
            self.update_timer_display()
        else:
            self.progress_bar.stop()
            self.progress_bar.configure(mode="determinate")
            self.progress_bar.set(0)
            self.btn_start.configure(state="normal", text="INICIAR RENDERIZAÇÃO", fg_color="green")

    def log(self, text):
        self.status_label.configure(text=text)

    # --- Overlay Helper para Logo Transparente ---
    def overlay_image_alpha(self, img, img_overlay, x, y):
        """Sobrepõe img_overlay (com alpha) sobre img em (x,y)"""
        h, w = img.shape[:2]
        h_ov, w_ov = img_overlay.shape[:2]

        # Limites
        if y >= h or x >= w: return img
        if y + h_ov > h: h_ov = h - y
        if x + w_ov > w: w_ov = w - x
        if h_ov <= 0 or w_ov <= 0: return img

        overlay_crop = img_overlay[:h_ov, :w_ov]
        img_crop = img[y:y+h_ov, x:x+w_ov]

        # Separa canais
        alpha = overlay_crop[:, :, 3] / 255.0
        alpha_inv = 1.0 - alpha

        for c in range(3):
            img_crop[:, :, c] = (alpha * overlay_crop[:, :, c] + alpha_inv * img_crop[:, :, c])
        
        img[y:y+h_ov, x:x+w_ov] = img_crop
        return img

    # --- LÓGICA PRINCIPAL ---
    def start_process(self):
        if self.is_processing: return
        if not self.audio_path.get() or not self.image_path.get():
            messagebox.showwarning("Aviso", "Faltam arquivos obrigatórios (Áudio/Imagem)!")
            return
        
        self.is_processing = True
        self.set_loading(True)
        threading.Thread(target=self.process_video_logic, daemon=True).start()

    def process_video_logic(self):
        try:
            # 1. Configuração Inicial
            res_name = self.res_var.get()
            target_w, target_h = RESOLUTIONS[res_name]
            bitrate_str = self.bitrate_var.get().split()[0]
            
            self.log("Preparando arquivos de áudio...")
            audio_files = [os.path.join(self.audio_path.get(), f) for f in os.listdir(self.audio_path.get()) if f.lower().endswith(('.mp3', '.wav'))]
            audio_files.sort()
            
            if not audio_files: raise Exception("Pasta de áudio vazia.")

            # 2. Processamento Avançado de Áudio (Norm + Crossfade)
            processed_clips = []
            crossfade_duration = 4 if self.check_fade.get() else 0
            current_start = 0
            timestamps = []

            for i, path in enumerate(audio_files):
                clip = AudioFileClip(path)
                
                # Normalização (0dB)
                if self.check_norm.get():
                    clip = clip.fx(afx.audio_normalize)
                
                # Aplica Fade In/Out para suavizar
                if self.check_fade.get():
                    clip = clip.audio_fadein(2).audio_fadeout(2)
                
                # Define tempo de início (Overlap)
                start_t = max(0, current_start - crossfade_duration) if i > 0 else 0
                clip = clip.set_start(start_t)
                
                processed_clips.append(clip)
                
                # Timestamp Log
                real_start = start_t
                if i > 0 and self.check_fade.get(): real_start += 2 # Ajuste visual
                m, s = divmod(int(real_start), 60)
                timestamps.append(f"{m:02d}:{s:02d} - {os.path.splitext(os.path.basename(path))[0]}")
                
                current_start = start_t + clip.duration

            # Salva Tracklist
            with open(os.path.join(self.audio_path.get(), "tracklist.txt"), "w") as t:
                t.write("\n".join(timestamps))

            self.log("Renderizando Mixagem de Áudio (Composite)...")
            final_audio = CompositeAudioClip(processed_clips)
            
            # 3. Preparação Visual (Background + Logo)
            self.log("Processando Imagens...")
            bg = cv2.imread(self.image_path.get())
            bg = cv2.resize(bg, (target_w, target_h))
            
            logo_img = None
            if self.logo_path.get():
                # Carrega logo com Alpha (UNCHANGED)
                logo_img = cv2.imread(self.logo_path.get(), cv2.IMREAD_UNCHANGED)
                if logo_img is not None:
                    # Redimensiona logo para 15% da altura da tela
                    l_h = int(target_h * 0.15)
                    ratio = l_h / logo_img.shape[0]
                    l_w = int(logo_img.shape[1] * ratio)
                    logo_img = cv2.resize(logo_img, (l_w, l_h))
            
            # 4. Análise FFT
            self.log("Análise Espectral (Isso é rápido)...")
            temp_wav = "temp_mix.wav"
            final_audio.write_audiofile(temp_wav, fps=22050, verbose=False, logger=None)
            y, sr = librosa.load(temp_wav, sr=22050)
            os.remove(temp_wav)
            
            D = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
            DB = librosa.amplitude_to_db(D, ref=np.max)

            # 5. Parâmetros do Frame
            n_bins = int(self.sld_density.get())
            sens = self.sld_sens.get()
            pos_y_pixel = int(self.sld_pos_y.get() * target_h)
            colors = CYBERPUNK_COLORS[self.color_var.get()]
            pulse = self.check_pulse_var.get()
            logo_pos_setting = self.logo_pos_var.get()

            def make_frame(t):
                # Sincronia
                idx = int(t * sr / 512)
                idx = min(idx, DB.shape[1] - 1)
                data = DB[:n_bins, idx]
                norm_data = np.clip((data + 80) / 80, 0, 1) * sens
                
                # Bass Trigger (para pulso)
                bass = np.mean(norm_data[:5]) if len(norm_data) > 0 else 0
                
                # 1. Background Pulse
                frame = bg.copy()
                h, w, _ = frame.shape
                
                if pulse and bass > 0.6:
                    scale = 1.0 + (bass * 0.02)
                    M = cv2.getRotationMatrix2D((w//2, h//2), 0, scale)
                    frame = cv2.warpAffine(frame, M, (w, h))

                # 2. Desenha Waveform
                c_x, b_w = w // 2, int(w / (n_bins * 2))
                if b_w < 1: b_w = 1
                max_h = h / 3
                
                for i in range(n_bins):
                    bh = int(norm_data[i] ** 2 * max_h)
                    xl, xr = c_x - (i*b_w) - b_w, c_x + (i*b_w)
                    y_e = pos_y_pixel - bh
                    
                    cv2.line(frame, (xl+b_w//2, pos_y_pixel), (xl+b_w//2, y_e), colors[1], b_w+4) # Glow
                    cv2.line(frame, (xr+b_w//2, pos_y_pixel), (xr+b_w//2, y_e), colors[1], b_w+4)
                    cv2.line(frame, (xl+b_w//2, pos_y_pixel), (xl+b_w//2, y_e), colors[0], max(1, b_w-2)) # Main
                    cv2.line(frame, (xr+b_w//2, pos_y_pixel), (xr+b_w//2, y_e), colors[0], max(1, b_w-2))

                # 3. Desenha Logo Pulsante
                if logo_img is not None:
                    # Scale Logo
                    cur_logo = logo_img
                    if pulse:
                        l_scale = 1.0 + (bass * 0.1) # Logo pulsa mais forte
                        new_size = (int(logo_img.shape[1] * l_scale), int(logo_img.shape[0] * l_scale))
                        cur_logo = cv2.resize(logo_img, new_size)
                    
                    lh, lw = cur_logo.shape[:2]
                    margin = 40
                    
                    # Posicionamento
                    lx, ly = 0, 0
                    if logo_pos_setting == "Centro":
                        lx, ly = (w - lw)//2, (h - lh)//2
                    elif "Sup. Esq" in logo_pos_setting:
                        lx, ly = margin, margin
                    elif "Sup. Dir" in logo_pos_setting:
                        lx, ly = w - lw - margin, margin
                    elif "Inf. Esq" in logo_pos_setting:
                        lx, ly = margin, h - lh - margin
                    elif "Inf. Dir" in logo_pos_setting:
                        lx, ly = w - lw - margin, h - lh - margin
                    
                    frame = self.overlay_image_alpha(frame, cur_logo, lx, ly)

                return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            self.log(f"RENDERIZANDO ({target_w}x{target_h})...")
            video = VideoClip(make_frame, duration=final_audio.duration)
            video = video.set_audio(final_audio)
            
            out = os.path.join(self.audio_path.get(), f"Mix_v6_{int(time.time())}.mp4")
            
            video.write_videofile(out, fps=30, codec="libx264", audio_codec="aac", audio_bitrate=bitrate_str, threads=4, verbose=False, logger=None)
            
            self.log("Concluído!")
            messagebox.showinfo("Sucesso", f"Vídeo salvo em:\n{out}")

        except Exception as e:
            messagebox.showerror("Erro", str(e))
            self.log(f"Erro: {str(e)}")
        finally:
            self.is_processing = False
            self.set_loading(False)
            if 'processed_clips' in locals(): 
                for c in processed_clips: c.close()

if __name__ == "__main__":
    app = SpectrumApp()
    app.mainloop()
