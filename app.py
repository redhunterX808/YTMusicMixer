import customtkinter as ctk
from tkinter import filedialog, messagebox, Canvas
import threading
import os
import time
import json
import subprocess
import numpy as np
import cv2
import librosa
from moviepy.editor import *
import moviepy.audio.fx.all as afx
import moviepy.video.fx.all as vfx
from PIL import Image, ImageTk # Necessário para mostrar imagem no Canvas

# --- Configurações Globais ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

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

        self.title("Cyberpunk Automator v9 - Visual Overlay Edition")
        self.geometry("1250x950")
        self.minsize(1000, 850)

        # Variáveis
        self.audio_path = ctk.StringVar()
        self.image_path = ctk.StringVar()
        self.logo_path = ctk.StringVar()
        self.overlay_path = ctk.StringVar()
        
        self.is_processing = False
        self.start_time = 0
        self.dummy_data = self.generate_dummy_data()
        self.overlay_preview_img = None # Armazena a imagem processada do overlay
        
        self.gpu_available = self.check_nvenc_support()
        
        self.setup_ui()
        self.after(100, self.update_preview)

    def check_nvenc_support(self):
        try:
            result = subprocess.run(['ffmpeg', '-encoders'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return 'h264_nvenc' in result.stdout
        except: return False

    def generate_dummy_data(self):
        x = np.linspace(0, np.pi, 128)
        return np.sin(x) * 0.8 + np.random.rand(128) * 0.2

    def bgr_to_hex(self, bgr_tuple):
        b, g, r = bgr_tuple
        return f'#{r:02x}{g:02x}{b:02x}'

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # === Sidebar ===
        self.sidebar = ctk.CTkScrollableFrame(self, width=320, corner_radius=10)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(15, 5), pady=15)
        
        # Presets
        pres_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        pres_frame.pack(fill="x", pady=(10, 5))
        ctk.CTkButton(pres_frame, text="💾 Salvar", width=90, fg_color="#444", command=self.save_preset).pack(side="left", padx=5)
        ctk.CTkButton(pres_frame, text="📂 Abrir", width=90, fg_color="#444", command=self.load_preset).pack(side="right", padx=5)

        ctk.CTkLabel(self.sidebar, text="MÍDIA PRINCIPAL", font=("Orbitron", 14, "bold"), text_color="#00ffff").pack(pady=(15, 5))

        self.btn_audio = ctk.CTkButton(self.sidebar, text="📂 Pasta de Músicas", fg_color="#ff00ff", hover_color="#b300b3", command=self.select_audio_folder)
        self.btn_audio.pack(pady=5, padx=10, fill="x")
        self.lbl_audio = ctk.CTkLabel(self.sidebar, text="...", font=("Roboto", 10), text_color="gray")
        self.lbl_audio.pack(pady=(0, 10))

        self.btn_image = ctk.CTkButton(self.sidebar, text="🖼️ Imagem de Fundo", fg_color="#00ffff", hover_color="#00b3b3", text_color="black", command=self.select_image)
        self.btn_image.pack(pady=5, padx=10, fill="x")
        self.lbl_image = ctk.CTkLabel(self.sidebar, text="...", font=("Roboto", 10), text_color="gray")
        self.lbl_image.pack(pady=(0, 10))

        self.btn_logo = ctk.CTkButton(self.sidebar, text="💎 Logotipo (Opcional)", fg_color="#333", border_color="#00ffff", border_width=1, command=self.select_logo)
        self.btn_logo.pack(pady=5, padx=10, fill="x")
        self.lbl_logo = ctk.CTkLabel(self.sidebar, text="Nenhum logo", font=("Roboto", 10), text_color="gray")
        self.lbl_logo.pack(pady=(0, 10))

        # --- CHROMA KEY UI ---
        ctk.CTkLabel(self.sidebar, text="OVERLAY / CHROMA KEY", font=("Orbitron", 14, "bold"), text_color="#00ff00").pack(pady=(15, 5))
        
        self.btn_overlay = ctk.CTkButton(self.sidebar, text="🎬 Vídeo Subscribe (Verde)", fg_color="#00aa00", hover_color="#008800", command=self.select_overlay)
        self.btn_overlay.pack(pady=5, padx=10, fill="x")
        self.lbl_overlay = ctk.CTkLabel(self.sidebar, text="Nenhum vídeo", font=("Roboto", 10), text_color="gray")
        self.lbl_overlay.pack(pady=(0, 5))

        ctk.CTkLabel(self.sidebar, text="Repetir a cada (minutos):").pack(anchor="w", padx=20)
        self.sld_interval = ctk.CTkSlider(self.sidebar, from_=1, to=30, number_of_steps=29)
        self.sld_interval.set(5)
        self.sld_interval.pack(fill="x", padx=15, pady=5)
        
        # Config Exportação
        ctk.CTkLabel(self.sidebar, text="SAÍDA", font=("Orbitron", 14, "bold"), text_color="#00ffff").pack(pady=(15, 5))
        self.res_var = ctk.StringVar(value="1080p (Full HD)")
        self.res_menu = ctk.CTkOptionMenu(self.sidebar, variable=self.res_var, values=list(RESOLUTIONS.keys()), command=self.update_preview)
        self.res_menu.pack(fill="x", padx=15, pady=5)

        self.bitrate_var = ctk.StringVar(value="320k (Alta)")
        ctk.CTkOptionMenu(self.sidebar, variable=self.bitrate_var, values=["320k (Alta)", "192k (Padrão)", "128k (Baixa)"]).pack(fill="x", padx=15, pady=5)

        self.check_norm = ctk.CTkCheckBox(self.sidebar, text="Normalizar Volume", onvalue=True, offvalue=False); self.check_norm.select(); self.check_norm.pack(pady=5)
        self.check_fade = ctk.CTkCheckBox(self.sidebar, text="Crossfade (4s)", onvalue=True, offvalue=False); self.check_fade.select(); self.check_fade.pack(pady=5)

        # Status
        ctk.CTkLabel(self.sidebar, text="HARDWARE", font=("Orbitron", 12, "bold"), text_color="gray").pack(pady=(20, 5))
        lbl_hw = "⚡ NVENC ATIVO" if self.gpu_available else "⚠️ CPU MODE"
        color_hw = "#00ff00" if self.gpu_available else "#ff9900"
        ctk.CTkLabel(self.sidebar, text=lbl_hw, font=("Consolas", 12, "bold"), text_color=color_hw).pack()

        # === Main Panel ===
        self.main_panel = ctk.CTkFrame(self, corner_radius=10)
        self.main_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 15), pady=15)
        
        ctk.CTkLabel(self.main_panel, text="VISUAL & PREVIEW", font=("Orbitron", 14, "bold"), text_color="#ff00ff").pack(pady=(10, 5))

        self.preview_canvas = Canvas(self.main_panel, height=250, bg="#000000", highlightthickness=0)
        self.preview_canvas.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(self.main_panel, text="Paleta:").pack(anchor="w", padx=25)
        self.color_var = ctk.StringVar(value="Neon Magenta")
        ctk.CTkOptionMenu(self.main_panel, variable=self.color_var, values=list(CYBERPUNK_COLORS.keys()), command=self.update_preview).pack(fill="x", padx=25)

        ctk.CTkLabel(self.main_panel, text="Densidade:").pack(anchor="w", padx=25)
        self.sld_density = ctk.CTkSlider(self.main_panel, from_=32, to=256, number_of_steps=7, command=self.update_preview); self.sld_density.set(128); self.sld_density.pack(fill="x", padx=25)

        ctk.CTkLabel(self.main_panel, text="Altura:").pack(anchor="w", padx=25)
        self.sld_sens = ctk.CTkSlider(self.main_panel, from_=0.5, to=3.0, number_of_steps=25, command=self.update_preview); self.sld_sens.set(1.5); self.sld_sens.pack(fill="x", padx=25)
        
        ctk.CTkLabel(self.main_panel, text="Posição Y:").pack(anchor="w", padx=25)
        self.sld_pos_y = ctk.CTkSlider(self.main_panel, from_=0.1, to=0.9, number_of_steps=50, command=self.update_preview); self.sld_pos_y.set(0.6); self.sld_pos_y.pack(fill="x", padx=25)

        ctk.CTkLabel(self.main_panel, text="Logo Pos:").pack(anchor="w", padx=25)
        self.logo_pos_var = ctk.StringVar(value="Centro")
        ctk.CTkOptionMenu(self.main_panel, variable=self.logo_pos_var, values=LOGO_POSITIONS, command=self.update_preview).pack(fill="x", padx=25)

        self.check_pulse_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self.main_panel, text="Reatividade: Fundo & Logo Pulsantes", variable=self.check_pulse_var).pack(pady=10)

        # Footer
        self.footer = ctk.CTkFrame(self, height=180, corner_radius=10, fg_color="#1a1a1a")
        self.footer.grid(row=1, column=0, columnspan=2, sticky="ew", padx=15, pady=(0, 15))

        self.status_label = ctk.CTkLabel(self.footer, text="Pronto.", font=("Consolas", 11), text_color="gray"); self.status_label.pack(pady=5)
        self.progress_bar = ctk.CTkProgressBar(self.footer, height=15, mode="determinate", progress_color="#00ffff"); self.progress_bar.set(0); self.progress_bar.pack(fill="x", padx=25)
        self.btn_start = ctk.CTkButton(self.footer, text="INICIAR RENDERIZAÇÃO", font=("Orbitron", 14, "bold"), height=40, fg_color="green", hover_color="darkgreen", command=self.start_process); self.btn_start.pack(pady=15)

    # --- PROCESSAMENTO DE OVERLAY PARA PREVIEW ---
    def process_overlay_for_preview(self, path):
        """Extrai um frame, remove o verde e prepara para o Canvas"""
        try:
            # 1. Captura um frame usando OpenCV
            cap = cv2.VideoCapture(path)
            # Pula para o segundo 2 (ou meio do vídeo) para pegar a animação
            cap.set(cv2.CAP_PROP_POS_MSEC, 2000) 
            ret, frame = cap.read()
            cap.release()
            
            if not ret: return None

            # 2. Redimensiona para o Preview (Largura do Canvas approx 600px -> Overlay 30%)
            preview_w = 600
            scale_ratio = (preview_w * 0.3) / frame.shape[1]
            new_size = (int(frame.shape[1] * scale_ratio), int(frame.shape[0] * scale_ratio))
            frame = cv2.resize(frame, new_size)

            # 3. Chroma Key Manual (Simples com NumPy)
            # Converte BGR para RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Adiciona canal Alpha
            frame_rgba = np.dstack((frame_rgb, np.zeros((frame.shape[0], frame.shape[1]), dtype=np.uint8) + 255))

            # Detecta Verde (R<100, G>150, B<100) - Ajuste simples
            r, g, b = frame_rgb[:,:,0], frame_rgb[:,:,1], frame_rgb[:,:,2]
            mask = (g > 150) & (r < 150) & (b < 150)
            
            # Aplica transparência onde for verde
            frame_rgba[mask] = [0, 0, 0, 0]

            # 4. Converte para Image do PIL e depois ImageTk
            pil_img = Image.fromarray(frame_rgba)
            self.overlay_preview_img = ImageTk.PhotoImage(pil_img)
            return True

        except Exception as e:
            print(f"Erro preview overlay: {e}")
            return None

    # --- Funções UI ---
    def select_audio_folder(self):
        path = filedialog.askdirectory()
        if path: self.audio_path.set(path); self.lbl_audio.configure(text=os.path.basename(path), text_color="white")

    def select_image(self):
        path = filedialog.askopenfilename(filetypes=[("Imagens", "*.jpg *.png *.jpeg")])
        if path: self.image_path.set(path); self.lbl_image.configure(text=os.path.basename(path), text_color="white")

    def select_logo(self):
        path = filedialog.askopenfilename(filetypes=[("Imagens PNG", "*.png")])
        if path: self.logo_path.set(path); self.lbl_logo.configure(text=os.path.basename(path), text_color="white")

    def select_overlay(self):
        path = filedialog.askopenfilename(filetypes=[("Video Chroma", "*.mp4 *.mov *.avi")])
        if path: 
            self.overlay_path.set(path)
            self.lbl_overlay.configure(text=os.path.basename(path), text_color="#00ff00")
            # Gera o preview do overlay
            self.process_overlay_for_preview(path)
            self.update_preview()

    def update_preview(self, _=None):
        self.preview_canvas.delete("all")
        w, h = self.preview_canvas.winfo_width(), self.preview_canvas.winfo_height()
        if w < 10: w = 400
        
        # Desenha Waveform
        n_bins, sens = int(self.sld_density.get()), self.sld_sens.get()
        pos_y = self.sld_pos_y.get() * h
        colors = CYBERPUNK_COLORS[self.color_var.get()]
        
        indices = np.linspace(0, len(self.dummy_data)-1, n_bins).astype(int)
        data = self.dummy_data[indices] * sens
        cx, bar_w = w / 2, w / (n_bins * 2)
        
        for i in range(n_bins):
            bh = data[i] * (h/3)
            xl, xr = cx - (i * bar_w) - bar_w, cx + (i * bar_w)
            y_end = pos_y - bh
            c1, c2 = self.bgr_to_hex(colors[1]), self.bgr_to_hex(colors[0])
            self.preview_canvas.create_rectangle(xl, pos_y, xl+bar_w, y_end, fill=c2, outline=c1)
            self.preview_canvas.create_rectangle(xr, pos_y, xr+bar_w, y_end, fill=c2, outline=c1)

        # Desenha Logo
        if self.logo_path.get():
            self.preview_canvas.create_text(w/2, h/2, text="LOGO", fill="white", font=("Arial", 8, "bold"))

        # Desenha Overlay Preview (NOVO)
        if self.overlay_preview_img:
            # Posiciona no centro inferior (bottom center)
            # image_obj precisa ser mantido na memória (self.overlay_preview_img)
            self.preview_canvas.create_image(w/2, h - 20, image=self.overlay_preview_img, anchor="s")

    # --- Save/Load Presets & Loading Logic (Omissão para brevidade, igual v8) ---
    def save_preset(self):
        preset = {
            "res": self.res_var.get(), "bitrate": self.bitrate_var.get(), "color": self.color_var.get(),
            "density": self.sld_density.get(), "sensitivity": self.sld_sens.get(), "pos_y": self.sld_pos_y.get(),
            "pulse": self.check_pulse_var.get(), "logo_pos": self.logo_pos_var.get(), "interval": self.sld_interval.get()
        }
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Preset", "*.json")])
        if path:
            with open(path, "w") as f: json.dump(preset, f, indent=4)
            messagebox.showinfo("Salvo", "Preset salvo!")

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
                self.logo_pos_var.set(data.get("logo_pos", "Centro"))
                if "interval" in data: self.sld_interval.set(data["interval"])
                self.update_preview()
                messagebox.showinfo("Carregado", "Preset aplicado!")

    def set_loading(self, active=True):
        if active:
            self.progress_bar.configure(mode="indeterminate")
            self.progress_bar.start()
            self.btn_start.configure(state="disabled", text="PROCESSANDO...", fg_color="gray")
        else:
            self.progress_bar.stop()
            self.progress_bar.configure(mode="determinate")
            self.progress_bar.set(0)
            self.btn_start.configure(state="normal", text="INICIAR RENDERIZAÇÃO", fg_color="green")

    def overlay_image_alpha(self, img, img_overlay, x, y):
        h, w = img.shape[:2]
        h_ov, w_ov = img_overlay.shape[:2]
        if y >= h or x >= w: return img
        if y + h_ov > h: h_ov = h - y
        if x + w_ov > w: w_ov = w - x
        if h_ov <= 0 or w_ov <= 0: return img
        overlay_crop = img_overlay[:h_ov, :w_ov]
        img_crop = img[y:y+h_ov, x:x+w_ov]
        alpha = overlay_crop[:, :, 3] / 255.0
        alpha_inv = 1.0 - alpha
        for c in range(3):
            img_crop[:, :, c] = (alpha * overlay_crop[:, :, c] + alpha_inv * img_crop[:, :, c])
        img[y:y+h_ov, x:x+w_ov] = img_crop
        return img

    def start_process(self):
        if self.is_processing: return
        if not self.audio_path.get() or not self.image_path.get():
            messagebox.showwarning("Aviso", "Arquivos incompletos!"); return
        self.is_processing = True
        self.set_loading(True)
        threading.Thread(target=self.process_video_logic, daemon=True).start()

    def process_video_logic(self):
        try:
            res_name = self.res_var.get()
            target_w, target_h = RESOLUTIONS[res_name]
            bitrate_str = self.bitrate_var.get().split()[0]
            video_codec = "h264_nvenc" if self.gpu_available else "libx264"
            preset = "p4" if self.gpu_available else "ultrafast"

            self.status_label.configure(text="Lendo Áudios...")
            audio_files = [os.path.join(self.audio_path.get(), f) for f in os.listdir(self.audio_path.get()) if f.lower().endswith(('.mp3', '.wav'))]
            audio_files.sort()
            
            if not audio_files: raise Exception("Sem áudios.")

            processed_clips = []
            crossfade_duration = 4 if self.check_fade.get() else 0
            current_start = 0
            timestamps = []

            for i, path in enumerate(audio_files):
                clip = AudioFileClip(path)
                if self.check_norm.get(): clip = clip.fx(afx.audio_normalize)
                if self.check_fade.get(): clip = clip.audio_fadein(2).audio_fadeout(2)
                start_t = max(0, current_start - crossfade_duration) if i > 0 else 0
                clip = clip.set_start(start_t)
                processed_clips.append(clip)
                real_start = start_t + (2 if i > 0 and self.check_fade.get() else 0)
                m, s = divmod(int(real_start), 60)
                timestamps.append(f"{m:02d}:{s:02d} - {os.path.splitext(os.path.basename(path))[0]}")
                current_start = start_t + clip.duration

            with open(os.path.join(self.audio_path.get(), "tracklist.txt"), "w") as t: t.write("\n".join(timestamps))

            self.status_label.configure(text="Mixando...")
            final_audio = CompositeAudioClip(processed_clips)
            final_duration = final_audio.duration
            
            bg = cv2.imread(self.image_path.get())
            bg = cv2.resize(bg, (target_w, target_h))
            
            logo_img = None
            if self.logo_path.get():
                logo_img = cv2.imread(self.logo_path.get(), cv2.IMREAD_UNCHANGED)
                if logo_img is not None:
                    l_h = int(target_h * 0.15)
                    ratio = l_h / logo_img.shape[0]
                    l_w = int(logo_img.shape[1] * ratio)
                    logo_img = cv2.resize(logo_img, (l_w, l_h))
            
            self.status_label.configure(text="FFT Analysis...")
            temp_wav = "temp_mix.wav"
            final_audio.write_audiofile(temp_wav, fps=22050, verbose=False, logger=None)
            y, sr = librosa.load(temp_wav, sr=22050)
            os.remove(temp_wav)
            D = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
            DB = librosa.amplitude_to_db(D, ref=np.max)

            n_bins, sens = int(self.sld_density.get()), self.sld_sens.get()
            pos_y_pixel = int(self.sld_pos_y.get() * target_h)
            colors = CYBERPUNK_COLORS[self.color_var.get()]
            pulse, logo_pos_setting = self.check_pulse_var.get(), self.logo_pos_var.get()

            def make_frame(t):
                idx = int(t * sr / 512)
                idx = min(idx, DB.shape[1] - 1)
                data = DB[:n_bins, idx]
                norm_data = np.clip((data + 80) / 80, 0, 1) * sens
                bass = np.mean(norm_data[:5]) if len(norm_data) > 0 else 0
                
                frame = bg.copy()
                h, w, _ = frame.shape
                
                if pulse and bass > 0.6:
                    scale = 1.0 + (bass * 0.02)
                    M = cv2.getRotationMatrix2D((w//2, h//2), 0, scale)
                    frame = cv2.warpAffine(frame, M, (w, h))

                c_x, b_w = w // 2, int(w / (n_bins * 2))
                if b_w < 1: b_w = 1
                max_h = h / 3
                
                for i in range(n_bins):
                    bh = int(norm_data[i] ** 2 * max_h)
                    xl, xr = c_x - (i*b_w) - b_w, c_x + (i*b_w)
                    y_e = pos_y_pixel - bh
                    cv2.line(frame, (xl+b_w//2, pos_y_pixel), (xl+b_w//2, y_e), colors[1], b_w+4)
                    cv2.line(frame, (xr+b_w//2, pos_y_pixel), (xr+b_w//2, y_e), colors[1], b_w+4)
                    cv2.line(frame, (xl+b_w//2, pos_y_pixel), (xl+b_w//2, y_e), colors[0], max(1, b_w-2))
                    cv2.line(frame, (xr+b_w//2, pos_y_pixel), (xr+b_w//2, y_e), colors[0], max(1, b_w-2))

                if logo_img is not None:
                    cur_logo = logo_img
                    if pulse:
                        l_scale = 1.0 + (bass * 0.1)
                        new_size = (int(logo_img.shape[1] * l_scale), int(logo_img.shape[0] * l_scale))
                        cur_logo = cv2.resize(logo_img, new_size)
                    lh, lw = cur_logo.shape[:2]
                    margin = 40
                    lx, ly = 0, 0
                    if logo_pos_setting == "Centro": lx, ly = (w - lw)//2, (h - lh)//2
                    elif "Sup. Esq" in logo_pos_setting: lx, ly = margin, margin
                    elif "Sup. Dir" in logo_pos_setting: lx, ly = w - lw - margin, margin
                    elif "Inf. Esq" in logo_pos_setting: lx, ly = margin, h - lh - margin
                    elif "Inf. Dir" in logo_pos_setting: lx, ly = w - lw - margin, h - lh - margin
                    frame = self.overlay_image_alpha(frame, cur_logo, lx, ly)

                return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            spectrum_clip = VideoClip(make_frame, duration=final_duration)
            
            final_layers = [spectrum_clip]
            if self.overlay_path.get():
                self.status_label.configure(text="Aplicando Chroma Key...")
                ov_clip = VideoFileClip(self.overlay_path.get())
                ov_clip = ov_clip.fx(vfx.mask_color, color=[0, 255, 0], thr=100, s=5)
                ov_clip = ov_clip.resize(width=target_w * 0.3)
                ov_clip = ov_clip.set_position(("center", "bottom"))
                
                interval_sec = self.sld_interval.get() * 60
                current_ov_time = interval_sec
                while current_ov_time < final_duration - 10:
                    final_layers.append(ov_clip.set_start(current_ov_time))
                    current_ov_time += interval_sec
            
            self.status_label.configure(text=f"Renderizando ({len(final_layers)} layers)...")
            final_video = CompositeVideoClip(final_layers)
            final_video = final_video.set_audio(final_audio)
            
            out = os.path.join(self.audio_path.get(), f"Mix_v9_Overlay_{int(time.time())}.mp4")
            
            final_video.write_videofile(
                out, fps=30, codec=video_codec, preset=preset, 
                audio_codec="aac", audio_bitrate=bitrate_str, 
                threads=4, verbose=False, logger=None
            )
            
            messagebox.showinfo("Sucesso", f"Vídeo salvo:\n{out}")

        except Exception as e:
            messagebox.showerror("Erro", str(e))
        finally:
            self.is_processing = False
            self.set_loading(False)
            if 'processed_clips' in locals(): 
                for c in processed_clips: c.close()

if __name__ == "__main__":
    app = SpectrumApp()
    app.mainloop()
