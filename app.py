import customtkinter as ctk
from tkinter import filedialog, messagebox, Canvas, colorchooser
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
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageFilter
from cryptography.fernet import Fernet
import pickle

# Google API
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

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
POST_PROCESS_EFFECTS = ["Nenhum", "Scanlines (TV Antiga)", "VHS Noise", "Glitch Cromático"]
TRACK_TEXT_POS = ["Inferior Esquerdo", "Inferior Direito", "Topo Central", "Rodapé Central"]

# Segurança para API Key
KEY_FILE = "secret.key"

class SpectrumApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Cyberpunk Automator v10 - Production Suite")
        self.geometry("1300x1000")
        self.minsize(1100, 900)

        # Variáveis
        self.audio_path = ctk.StringVar()
        self.bg_path = ctk.StringVar() # Agora aceita vídeo e imagem
        self.logo_path = ctk.StringVar()
        self.overlay_path = ctk.StringVar()
        self.client_secret_path = ctk.StringVar()
        
        self.is_processing = False
        self.start_time = 0
        self.dummy_data = self.generate_dummy_data()
        self.overlay_preview_img = None
        self.youtube_service = None
        
        self.gpu_available = self.check_nvenc_support()
        self.ensure_security_key()
        
        self.setup_ui()
        self.load_api_key_safe() # Tenta carregar API salva
        self.after(100, self.update_preview)

    def check_nvenc_support(self):
        try:
            result = subprocess.run(['ffmpeg', '-encoders'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return 'h264_nvenc' in result.stdout
        except: return False

    def ensure_security_key(self):
        if not os.path.exists(KEY_FILE):
            key = Fernet.generate_key()
            with open(KEY_FILE, "wb") as key_file:
                key_file.write(key)

    def get_cipher(self):
        with open(KEY_FILE, "rb") as key_file:
            key = key_file.read()
        return Fernet(key)

    def generate_dummy_data(self):
        x = np.linspace(0, np.pi, 128)
        return np.sin(x) * 0.8 + np.random.rand(128) * 0.2

    def bgr_to_hex(self, bgr_tuple):
        b, g, r = bgr_tuple
        return f'#{r:02x}{g:02x}{b:02x}'

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # === Sidebar (Scrollable) ===
        self.sidebar = ctk.CTkScrollableFrame(self, width=340, corner_radius=10)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(15, 5), pady=15)
        
        # Presets
        pres_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        pres_frame.pack(fill="x", pady=(10, 5))
        ctk.CTkButton(pres_frame, text="💾 Salvar", width=90, fg_color="#444", command=self.save_preset).pack(side="left", padx=5)
        ctk.CTkButton(pres_frame, text="📂 Abrir", width=90, fg_color="#444", command=self.load_preset).pack(side="right", padx=5)

        # Mídia Principal
        ctk.CTkLabel(self.sidebar, text="MÍDIA", font=("Orbitron", 14, "bold"), text_color="#00ffff").pack(pady=(15, 5))
        self.btn_audio = ctk.CTkButton(self.sidebar, text="📂 Pasta de Músicas", fg_color="#ff00ff", hover_color="#b300b3", command=self.select_audio_folder)
        self.btn_audio.pack(pady=5, padx=10, fill="x")
        self.lbl_audio = ctk.CTkLabel(self.sidebar, text="...", font=("Roboto", 10), text_color="gray"); self.lbl_audio.pack()

        # Botão unificado para Imagem ou Vídeo de fundo
        self.btn_bg = ctk.CTkButton(self.sidebar, text="🖼️/🎬 Fundo (Img/Vídeo)", fg_color="#00ffff", hover_color="#00b3b3", text_color="black", command=self.select_bg)
        self.btn_bg.pack(pady=5, padx=10, fill="x")
        self.lbl_bg = ctk.CTkLabel(self.sidebar, text="...", font=("Roboto", 10), text_color="gray"); self.lbl_bg.pack()

        self.btn_logo = ctk.CTkButton(self.sidebar, text="💎 Logotipo", fg_color="#333", border_color="#00ffff", border_width=1, command=self.select_logo)
        self.btn_logo.pack(pady=5, padx=10, fill="x")
        self.lbl_logo = ctk.CTkLabel(self.sidebar, text="Nenhum", font=("Roboto", 10), text_color="gray"); self.lbl_logo.pack()

        # Chroma Key
        ctk.CTkLabel(self.sidebar, text="OVERLAY", font=("Orbitron", 14, "bold"), text_color="#00ff00").pack(pady=(15, 5))
        self.btn_overlay = ctk.CTkButton(self.sidebar, text="🎬 Vídeo Subscribe (Verde)", fg_color="#00aa00", hover_color="#008800", command=self.select_overlay)
        self.btn_overlay.pack(pady=5, padx=10, fill="x")
        self.lbl_overlay = ctk.CTkLabel(self.sidebar, text="Nenhum", font=("Roboto", 10), text_color="gray"); self.lbl_overlay.pack()
        
        ctk.CTkLabel(self.sidebar, text="Repetir (min):").pack(anchor="w", padx=20)
        self.sld_interval = ctk.CTkSlider(self.sidebar, from_=1, to=30, number_of_steps=29); self.sld_interval.set(5); self.sld_interval.pack(fill="x", padx=15)

        # --- YOUTUBE UPLOAD (NOVO) ---
        ctk.CTkLabel(self.sidebar, text="YOUTUBE & THUMBNAIL", font=("Orbitron", 14, "bold"), text_color="#ff0000").pack(pady=(15, 5))
        
        # Thumbnail Gen
        self.check_thumb = ctk.CTkCheckBox(self.sidebar, text="Gerar Thumbnail Automática", onvalue=True, offvalue=False); self.check_thumb.select(); self.check_thumb.pack(pady=5, anchor="w", padx=10)
        self.entry_thumb_text = ctk.CTkEntry(self.sidebar, placeholder_text="Texto da Thumbnail (Ex: MIX 2026)"); self.entry_thumb_text.pack(fill="x", padx=10)
        
        # API Upload
        self.btn_api = ctk.CTkButton(self.sidebar, text="🔑 Carregar Client Secret (JSON)", fg_color="#cc0000", hover_color="#990000", command=self.load_client_secret)
        self.btn_api.pack(pady=10, padx=10, fill="x")
        self.lbl_api_status = ctk.CTkLabel(self.sidebar, text="Não Autenticado", text_color="gray", font=("Roboto", 10)); self.lbl_api_status.pack()

        self.entry_yt_title = ctk.CTkEntry(self.sidebar, placeholder_text="Título do Vídeo YouTube"); self.entry_yt_title.pack(fill="x", padx=10, pady=5)
        self.entry_yt_tags = ctk.CTkEntry(self.sidebar, placeholder_text="Tags (separadas por vírgula)"); self.entry_yt_tags.pack(fill="x", padx=10, pady=5)
        self.entry_yt_desc = ctk.CTkTextbox(self.sidebar, height=60); self.entry_yt_desc.insert("0.0", "Descrição (Tracklist será adicionada ao fim)"); self.entry_yt_desc.pack(fill="x", padx=10, pady=5)


        # Config Exportação
        ctk.CTkLabel(self.sidebar, text="RENDERIZAÇÃO", font=("Orbitron", 14, "bold"), text_color="#00ffff").pack(pady=(15, 5))
        self.res_var = ctk.StringVar(value="1080p (Full HD)")
        ctk.CTkOptionMenu(self.sidebar, variable=self.res_var, values=list(RESOLUTIONS.keys()), command=self.update_preview).pack(fill="x", padx=15, pady=5)

        self.bitrate_var = ctk.StringVar(value="320k (Alta)")
        ctk.CTkOptionMenu(self.sidebar, variable=self.bitrate_var, values=["320k (Alta)", "192k (Padrão)", "128k (Baixa)"]).pack(fill="x", padx=15, pady=5)

        self.check_norm = ctk.CTkCheckBox(self.sidebar, text="Normalizar Volume", onvalue=True, offvalue=False); self.check_norm.select(); self.check_norm.pack(pady=2, anchor="w", padx=20)
        self.check_fade = ctk.CTkCheckBox(self.sidebar, text="Crossfade (4s)", onvalue=True, offvalue=False); self.check_fade.select(); self.check_fade.pack(pady=2, anchor="w", padx=20)

        # Hardware Status
        ctk.CTkLabel(self.sidebar, text="HARDWARE", font=("Orbitron", 12, "bold"), text_color="gray").pack(pady=(20, 5))
        lbl_hw = "⚡ NVENC ATIVO" if self.gpu_available else "⚠️ CPU MODE"
        color_hw = "#00ff00" if self.gpu_available else "#ff9900"
        ctk.CTkLabel(self.sidebar, text=lbl_hw, font=("Consolas", 12, "bold"), text_color=color_hw).pack()

        # === Main Panel (Direita) ===
        self.main_panel = ctk.CTkFrame(self, corner_radius=10)
        self.main_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 15), pady=15)
        
        ctk.CTkLabel(self.main_panel, text="VISUAL & EFEITOS", font=("Orbitron", 14, "bold"), text_color="#ff00ff").pack(pady=(10, 5))

        self.preview_canvas = Canvas(self.main_panel, height=250, bg="#000000", highlightthickness=0)
        self.preview_canvas.pack(fill="x", padx=20, pady=10)

        # Controles
        ctk.CTkLabel(self.main_panel, text="Paleta:").pack(anchor="w", padx=25)
        self.color_var = ctk.StringVar(value="Neon Magenta")
        ctk.CTkOptionMenu(self.main_panel, variable=self.color_var, values=list(CYBERPUNK_COLORS.keys()), command=self.update_preview).pack(fill="x", padx=25)

        # Sliders Visualização
        frame_sliders = ctk.CTkFrame(self.main_panel, fg_color="transparent")
        frame_sliders.pack(fill="x", padx=20)
        
        ctk.CTkLabel(frame_sliders, text="Densidade:").grid(row=0, column=0, padx=5)
        self.sld_density = ctk.CTkSlider(frame_sliders, from_=32, to=256, number_of_steps=7, command=self.update_preview); self.sld_density.set(128); self.sld_density.grid(row=0, column=1, sticky="ew")
        
        ctk.CTkLabel(frame_sliders, text="Altura:").grid(row=1, column=0, padx=5)
        self.sld_sens = ctk.CTkSlider(frame_sliders, from_=0.5, to=3.0, number_of_steps=25, command=self.update_preview); self.sld_sens.set(1.5); self.sld_sens.grid(row=1, column=1, sticky="ew")

        ctk.CTkLabel(frame_sliders, text="Pos Y:").grid(row=2, column=0, padx=5)
        self.sld_pos_y = ctk.CTkSlider(frame_sliders, from_=0.1, to=0.9, number_of_steps=50, command=self.update_preview); self.sld_pos_y.set(0.6); self.sld_pos_y.grid(row=2, column=1, sticky="ew")

        # Configs Avançadas
        ctk.CTkLabel(self.main_panel, text="EFEITOS DE PÓS-PROCESSAMENTO").pack(pady=(15, 5))
        self.post_process_var = ctk.StringVar(value="Nenhum")
        ctk.CTkOptionMenu(self.main_panel, variable=self.post_process_var, values=POST_PROCESS_EFFECTS).pack(fill="x", padx=25)

        ctk.CTkLabel(self.main_panel, text="TEXTO 'TOCANDO AGORA'").pack(pady=(15, 5))
        self.check_now_playing = ctk.CTkCheckBox(self.main_panel, text="Ativar Overlay de Faixa", onvalue=True, offvalue=False, command=self.update_preview); self.check_now_playing.select(); self.check_now_playing.pack()
        self.now_playing_pos_var = ctk.StringVar(value="Inferior Esquerdo")
        ctk.CTkOptionMenu(self.main_panel, variable=self.now_playing_pos_var, values=TRACK_TEXT_POS, command=self.update_preview).pack(fill="x", padx=25, pady=5)

        self.check_pulse_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self.main_panel, text="Reatividade: Fundo & Logo Pulsantes", variable=self.check_pulse_var).pack(pady=10)

        # Footer
        self.footer = ctk.CTkFrame(self, height=180, corner_radius=10, fg_color="#1a1a1a")
        self.footer.grid(row=1, column=0, columnspan=2, sticky="ew", padx=15, pady=(0, 15))

        self.status_label = ctk.CTkLabel(self.footer, text="Pronto.", font=("Consolas", 11), text_color="gray"); self.status_label.pack(pady=5)
        self.progress_bar = ctk.CTkProgressBar(self.footer, height=15, mode="determinate", progress_color="#00ffff"); self.progress_bar.set(0); self.progress_bar.pack(fill="x", padx=25)
        self.btn_start = ctk.CTkButton(self.footer, text="INICIAR PRODUÇÃO COMPLETA", font=("Orbitron", 14, "bold"), height=40, fg_color="green", hover_color="darkgreen", command=self.start_process); self.btn_start.pack(pady=15)

    # --- LÓGICA DE PREVIEW ---
    def process_overlay_for_preview(self, path):
        try:
            cap = cv2.VideoCapture(path)
            cap.set(cv2.CAP_PROP_POS_MSEC, 2000) 
            ret, frame = cap.read()
            cap.release()
            if not ret: return None
            preview_w = 600
            scale_ratio = (preview_w * 0.3) / frame.shape[1]
            frame = cv2.resize(frame, (int(frame.shape[1] * scale_ratio), int(frame.shape[0] * scale_ratio)))
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_rgba = np.dstack((frame_rgb, np.zeros((frame.shape[0], frame.shape[1]), dtype=np.uint8) + 255))
            r, g, b = frame_rgb[:,:,0], frame_rgb[:,:,1], frame_rgb[:,:,2]
            mask = (g > 150) & (r < 150) & (b < 150)
            frame_rgba[mask] = [0, 0, 0, 0]
            pil_img = Image.fromarray(frame_rgba)
            self.overlay_preview_img = ImageTk.PhotoImage(pil_img)
        except: pass

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

        # "Tocando Agora" Preview
        if self.check_now_playing.get():
            pos = self.now_playing_pos_var.get()
            tx, ty = 20, h - 30
            anchor = "nw"
            if "Direito" in pos: tx, anchor = w - 120, "ne"
            elif "Topo" in pos: tx, ty, anchor = w/2, 20, "n"
            elif "Rodapé" in pos: tx, ty, anchor = w/2, h - 30, "s"
            
            self.preview_canvas.create_text(tx, ty, text="♫ Musica Exemplo - Artista", fill="white", font=("Arial", 10, "bold"), anchor=anchor)

        # Logo & Overlay
        if self.logo_path.get():
            self.preview_canvas.create_text(w/2, h/2, text="LOGO", fill="white", font=("Arial", 8, "bold"))
        if self.overlay_preview_img:
            self.preview_canvas.create_image(w/2, h - 20, image=self.overlay_preview_img, anchor="s")

    # --- SELEÇÃO DE ARQUIVOS ---
    def select_audio_folder(self):
        path = filedialog.askdirectory()
        if path: self.audio_path.set(path); self.lbl_audio.configure(text=os.path.basename(path), text_color="white")
    def select_bg(self):
        path = filedialog.askopenfilename(filetypes=[("Mídia", "*.jpg *.png *.mp4 *.gif")])
        if path: self.bg_path.set(path); self.lbl_bg.configure(text=os.path.basename(path), text_color="white")
    def select_logo(self):
        path = filedialog.askopenfilename(filetypes=[("PNG", "*.png")])
        if path: self.logo_path.set(path); self.lbl_logo.configure(text=os.path.basename(path), text_color="white")
    def select_overlay(self):
        path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.mov")])
        if path: 
            self.overlay_path.set(path); self.lbl_overlay.configure(text=os.path.basename(path), text_color="#00ff00")
            self.process_overlay_for_preview(path); self.update_preview()

    # --- API YOUTUBE (SEGURANÇA & AUTH) ---
    def load_client_secret(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")], title="Selecione client_secret.json do Google")
        if path:
            self.client_secret_path.set(path)
            # Criptografa e salva o caminho para uso futuro
            cipher = self.get_cipher()
            encrypted_path = cipher.encrypt(path.encode())
            with open("yt_config.dat", "wb") as f: f.write(encrypted_path)
            self.lbl_api_status.configure(text="Arquivo Carregado (Pronto para Autenticar)", text_color="#ffff00")

    def load_api_key_safe(self):
        if os.path.exists("yt_config.dat"):
            try:
                with open("yt_config.dat", "rb") as f: encrypted = f.read()
                path = self.get_cipher().decrypt(encrypted).decode()
                if os.path.exists(path):
                    self.client_secret_path.set(path)
                    self.lbl_api_status.configure(text="Configuração Restaurada", text_color="#00ff00")
            except: pass

    def authenticate_youtube(self):
        if not self.client_secret_path.get(): return None
        try:
            scopes = ["https://www.googleapis.com/auth/youtube.upload"]
            flow = InstalledAppFlow.from_client_secrets_file(self.client_secret_path.get(), scopes)
            creds = flow.run_local_server(port=0)
            return build("youtube", "v3", credentials=creds)
        except Exception as e:
            messagebox.showerror("Erro Auth", str(e)); return None

    # --- FUNÇÕES DE EFEITO (PÓS-PROCESSAMENTO) ---
    def apply_post_processing(self, frame, effect):
        if effect == "Scanlines (TV Antiga)":
            frame[::2, :] = (frame[::2, :] * 0.7).astype(np.uint8) # Escurece linhas alternadas
        elif effect == "VHS Noise":
            noise = np.random.normal(0, 15, frame.shape).astype(np.uint8)
            frame = cv2.add(frame, noise)
            # Desvio de cor simples (Simulação)
            b, g, r = cv2.split(frame)
            M = np.float32([[1, 0, 2], [0, 1, 0]]) # Shift Red
            r = cv2.warpAffine(r, M, (frame.shape[1], frame.shape[0]))
            frame = cv2.merge([b, g, r])
        elif effect == "Glitch Cromático":
            if np.random.rand() > 0.9: # Glitch aleatório
                slice_h = np.random.randint(10, 50)
                y = np.random.randint(0, frame.shape[0] - slice_h)
                frame[y:y+slice_h, :] = np.roll(frame[y:y+slice_h, :], np.random.randint(-20, 20), axis=1)
        return frame

    # --- GERADOR DE THUMBNAIL ---
    def generate_thumbnail(self, target_w, target_h, out_path):
        try:
            # 1. Base (Bg)
            if self.bg_path.get().endswith(('.mp4', '.gif')):
                cap = cv2.VideoCapture(self.bg_path.get())
                ret, frame = cap.read()
                cap.release()
                if ret: 
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    base = Image.fromarray(frame)
                else: base = Image.new("RGB", (target_w, target_h), "black")
            else:
                base = Image.open(self.image_path.get() if self.image_path.get() else self.bg_path.get())
            
            base = base.resize((target_w, target_h))
            draw = ImageDraw.Draw(base)
            
            # 2. Logo
            if self.logo_path.get():
                logo = Image.open(self.logo_path.get()).convert("RGBA")
                ratio = (target_h * 0.4) / logo.height
                logo = logo.resize((int(logo.width * ratio), int(logo.height * ratio)))
                base.paste(logo, (int(target_w/2 - logo.width/2), int(target_h/2 - logo.height/2)), logo)

            # 3. Texto
            text = self.entry_thumb_text.get()
            if text:
                try: font = ImageFont.truetype("arial.ttf", 100)
                except: font = ImageFont.load_default()
                
                # Borda do texto
                bbox = draw.textbbox((0,0), text, font=font)
                tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
                x, y = (target_w - tw)/2, target_h - th - 50
                
                # Glow effect manual (desenhar várias vezes deslocado)
                for off in range(-3, 4):
                    draw.text((x+off, y), text, font=font, fill="black")
                    draw.text((x, y+off), text, font=font, fill="black")
                draw.text((x, y), text, font=font, fill="#00ffff")

            base.save(out_path)
            return True
        except Exception as e:
            print(f"Erro Thumb: {e}")
            return False

    # --- PROCESSAMENTO PRINCIPAL ---
    def start_process(self):
        if self.is_processing: return
        if not self.audio_path.get() or not self.bg_path.get():
            messagebox.showwarning("Aviso", "Mídia incompleta!"); return
        
        self.is_processing = True
        
        # UI Loading
        self.progress_bar.configure(mode="indeterminate"); self.progress_bar.start()
        self.btn_start.configure(state="disabled", text="PRODUZINDO...", fg_color="gray")
        self.start_time = time.time()
        self.after(1000, self.update_timer)
        
        threading.Thread(target=self.run_production_pipeline, daemon=True).start()

    def update_timer(self):
        if self.is_processing:
            elapsed = time.time() - self.start_time
            m, s = divmod(int(elapsed), 60); h, m = divmod(m, 60)
            self.status_label.configure(text=f"Tempo: {h:02d}:{m:02d}:{s:02d}")
            self.after(1000, self.update_timer)

    def run_production_pipeline(self):
        try:
            # --- SETUP ---
            res_name = self.res_var.get()
            t_w, t_h = RESOLUTIONS[res_name]
            bitrate = self.bitrate_var.get().split()[0]
            gpu = self.gpu_available
            
            # --- 1. ÁUDIO ---
            self.status_label.configure(text="Processando Áudio...")
            audio_files = [os.path.join(self.audio_path.get(), f) for f in os.listdir(self.audio_path.get()) if f.lower().endswith(('mp3','wav'))]
            audio_files.sort()
            
            clips, timestamps, start_t = [], [], 0
            fade = 4 if self.check_fade.get() else 0
            
            for i, f in enumerate(audio_files):
                ac = AudioFileClip(f)
                if self.check_norm.get(): ac = ac.fx(afx.audio_normalize)
                if fade: ac = ac.audio_fadein(2).audio_fadeout(2)
                
                st = max(0, start_t - fade) if i > 0 else 0
                ac = ac.set_start(st)
                clips.append(ac)
                
                real_st = st + (2 if i>0 and fade else 0)
                m, s = divmod(int(real_st), 60)
                name = os.path.splitext(os.path.basename(f))[0]
                timestamps.append((real_st, name))
                start_t = st + ac.duration

            final_audio = CompositeAudioClip(clips)
            duration = final_audio.duration
            tracklist_str = "\n".join([f"{int(t[0]//60):02d}:{int(t[0]%60):02d} - {t[1]}" for t in timestamps])
            
            # --- 2. VÍDEO & FFT ---
            self.status_label.configure(text="Análise FFT & Mídia...")
            
            # Background (Loop de Vídeo ou Imagem)
            is_video_bg = self.bg_path.get().endswith(('.mp4', '.gif'))
            if is_video_bg:
                bg_clip = VideoFileClip(self.bg_path.get()).resize((t_w, t_h)).loop(duration=duration)
            else:
                bg_img = cv2.imread(self.bg_path.get())
                bg_img = cv2.resize(bg_img, (t_w, t_h))

            # Logo
            logo_img = None
            if self.logo_path.get():
                logo_img = cv2.imread(self.logo_path.get(), cv2.IMREAD_UNCHANGED)
                # Resize logic here (simplified)
                logo_img = cv2.resize(logo_img, (int(t_w*0.15), int(t_h*0.15)))

            # FFT Data
            temp_wav = "temp_anl.wav"
            final_audio.write_audiofile(temp_wav, fps=22050, verbose=False, logger=None)
            y, sr = librosa.load(temp_wav, sr=22050); os.remove(temp_wav)
            D = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
            DB = librosa.amplitude_to_db(D, ref=np.max)

            # Params
            n_bins, sens = int(self.sld_density.get()), self.sld_sens.get()
            pos_y_px = int(self.sld_pos_y.get() * t_h)
            colors = CYBERPUNK_COLORS[self.color_var.get()]
            pulse = self.check_pulse_var.get()
            effect_type = self.post_process_var.get()
            show_track = self.check_now_playing.get()
            track_pos = self.now_playing_pos_var.get()

            # --- FRAME GENERATOR ---
            def make_frame(t):
                # 1. Get Base Frame
                if is_video_bg:
                    frame = bg_clip.get_frame(t) # Returns RGB (MoviePy)
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR) # Convert to BGR for OpenCV drawing
                else:
                    frame = bg_img.copy()

                h, w, _ = frame.shape
                
                # 2. Audio Data
                idx = min(int(t * sr / 512), DB.shape[1] - 1)
                data = np.clip((DB[:n_bins, idx] + 80) / 80, 0, 1) * sens
                bass = np.mean(data[:5]) if len(data)>0 else 0
                
                # 3. Pulse Effect
                if pulse and bass > 0.6:
                    M = cv2.getRotationMatrix2D((w//2, h//2), 0, 1.0 + (bass * 0.02))
                    frame = cv2.warpAffine(frame, M, (w, h))

                # 4. Waveform Draw
                cx, bw = w // 2, max(1, int(w / (n_bins * 2)))
                max_h = h / 3
                c1, c2 = colors[1], colors[0] # Glow, Main
                
                for i in range(n_bins):
                    bh = int(data[i]**2 * max_h)
                    xl, xr = cx - (i*bw) - bw, cx + (i*bw)
                    y_end = pos_y_px - bh
                    cv2.line(frame, (xl+bw//2, pos_y_px), (xl+bw//2, y_end), c1, bw+4)
                    cv2.line(frame, (xr+bw//2, pos_y_px), (xr+bw//2, y_end), c1, bw+4)
                    cv2.line(frame, (xl+bw//2, pos_y_px), (xl+bw//2, y_end), c2, max(1, bw-2))
                    cv2.line(frame, (xr+bw//2, pos_y_px), (xr+bw//2, y_end), c2, max(1, bw-2))

                # 5. Logo Overlay (simplified alpha blend)
                if logo_img is not None:
                    # Centered logic (add positioning later if needed)
                    lx, ly = (w - logo_img.shape[1])//2, (h - logo_img.shape[0])//2
                    self.overlay_image_alpha(frame, logo_img, lx, ly)

                # 6. "Tocando Agora" Overlay
                if show_track:
                    # Find current song
                    cur_song = ""
                    for ts, name in timestamps:
                        if t >= ts: cur_song = name
                    
                    if cur_song:
                        # Convert to PIL for text
                        pil_f = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                        draw = ImageDraw.Draw(pil_f)
                        try: font = ImageFont.truetype("arial.ttf", 24)
                        except: font = ImageFont.load_default()
                        
                        text = f"♪ {cur_song}"
                        bbox = draw.textbbox((0,0), text, font=font)
                        tx, ty = 40, h - 60
                        if "Direito" in track_pos: tx = w - (bbox[2]-bbox[0]) - 40
                        elif "Topo" in track_pos: tx, ty = (w - (bbox[2]-bbox[0]))//2, 40
                        
                        # Shadow & Text
                        draw.text((tx+2, ty+2), text, font=font, fill="black")
                        draw.text((tx, ty), text, font=font, fill="white")
                        
                        frame = cv2.cvtColor(np.array(pil_f), cv2.COLOR_RGB2BGR)

                # 7. Post-Processing
                frame = self.apply_post_processing(frame, effect_type)
                
                return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # Return RGB for MoviePy

            base_clip = VideoClip(make_frame, duration=duration)
            
            # --- 3. OVERLAYS (CHROMA) ---
            layers = [base_clip]
            if self.overlay_path.get():
                ov = VideoFileClip(self.overlay_path.get()).fx(vfx.mask_color, color=[0,255,0], thr=100, s=5)
                ov = ov.resize(width=t_w*0.3).set_position(("center", "bottom"))
                
                interval = self.sld_interval.get() * 60
                curr = interval
                while curr < duration - 10:
                    layers.append(ov.set_start(curr))
                    curr += interval
            
            final_video = CompositeVideoClip(layers).set_audio(final_audio)
            
            # --- 4. RENDERIZAÇÃO ---
            out_file = f"Master_Mix_{int(time.time())}.mp4"
            self.status_label.configure(text="Renderizando (GPU)..." if gpu else "Renderizando (CPU)...")
            
            final_video.write_videofile(
                out_file, fps=30, 
                codec="h264_nvenc" if gpu else "libx264", 
                preset="p4" if gpu else "ultrafast",
                audio_codec="aac", audio_bitrate=bitrate,
                threads=4, verbose=False, logger=None
            )

            # --- 5. THUMBNAIL ---
            thumb_path = "thumbnail.jpg"
            if self.check_thumb.get():
                self.status_label.configure(text="Gerando Thumbnail...")
                self.generate_thumbnail(1280, 720, thumb_path)

            # --- 6. UPLOAD YOUTUBE ---
            if self.client_secret_path.get() and self.entry_yt_title.get():
                self.status_label.configure(text="Enviando para o YouTube...")
                
                # Auth
                youtube = self.authenticate_youtube()
                if youtube:
                    body = {
                        "snippet": {
                            "title": self.entry_yt_title.get(),
                            "description": self.entry_yt_desc.get("0.0", "end") + "\n\nTracklist:\n" + tracklist_str,
                            "tags": self.entry_yt_tags.get().split(","),
                            "categoryId": "10" # Music
                        },
                        "status": {"privacyStatus": "private"} # Upload como privado por segurança
                    }
                    
                    media = MediaFileUpload(out_file, chunksize=-1, resumable=True)
                    req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
                    resp = req.execute()
                    vid_id = resp.get("id")
                    
                    # Upload Thumbnail
                    if self.check_thumb.get() and os.path.exists(thumb_path):
                        youtube.thumbnails().set(videoId=vid_id, media_body=MediaFileUpload(thumb_path)).execute()
                    
                    messagebox.showinfo("Sucesso", f"Vídeo enviado!\nID: {vid_id}\nStatus: Privado")
                else:
                    messagebox.showwarning("Erro Upload", "Falha na autenticação.")
            else:
                messagebox.showinfo("Concluído", f"Vídeo salvo: {out_file}")

        except Exception as e:
            messagebox.showerror("Erro Fatal", str(e))
            print(e)
        finally:
            self.is_processing = False
            self.progress_bar.stop()
            self.btn_start.configure(state="normal", text="INICIAR PRODUÇÃO COMPLETA", fg_color="green")

    # Helper para overlay alpha
    def overlay_image_alpha(self, img, img_overlay, x, y):
        h, w = img.shape[:2]
        h_ov, w_ov = img_overlay.shape[:2]
        if y >= h or x >= w: return
        if y + h_ov > h: h_ov = h - y
        if x + w_ov > w: w_ov = w - x
        overlay_crop = img_overlay[:h_ov, :w_ov]
        img_crop = img[y:y+h_ov, x:x+w_ov]
        alpha = overlay_crop[:, :, 3] / 255.0
        alpha_inv = 1.0 - alpha
        for c in range(3):
            img_crop[:, :, c] = (alpha * overlay_crop[:, :, c] + alpha_inv * img_crop[:, :, c])
        img[y:y+h_ov, x:x+w_ov] = img_crop

    # Save/Load Presets omitidos para brevidade (mesma lógica anterior)
    def save_preset(self): pass 
    def load_preset(self): pass

if __name__ == "__main__":
    app = SpectrumApp()
    app.mainloop()
