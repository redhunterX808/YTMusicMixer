# 🎵 Cyberpunk Automator v9.0 (Visual Overlay Edition)

> Ferramenta profissional para criação de vídeos musicais (Music Mixes) com visualização de espectro reativa, aceleração por GPU e suporte a Chroma Key para animações de "Inscreva-se".

![Preview Interface](https://via.placeholder.com/800x450.png?text=Interface+v9.0+Cyberpunk+Preview)

## 🚀 O Que Há de Novo na v9.0?
* **🎬 Chroma Key & Overlays:** Importe vídeos com fundo verde (ex: animações de *Subscribe* ou *Like*). O script remove o fundo automaticamente e sobrepõe ao seu vídeo.
* **👁️ Preview Total:** Agora o Canvas mostra não apenas a onda sonora, mas também onde o **Logotipo** e a **Animação de Overlay** aparecerão, permitindo ajuste fino sem precisar renderizar.
* **🔄 Repetição Inteligente:** Defina intervalos (ex: a cada 5 minutos) para que a animação de *Subscribe* apareça automaticamente durante todo o mix.

## ✨ Funcionalidades Principais

### 🎚️ Áudio & Engenharia
* **Processamento em Lote:** Une pastas inteiras de músicas (MP3/WAV).
* **Crossfade Automático:** Transições suaves de 4 segundos entre faixas.
* **Normalização:** Nivela o volume de todas as músicas para 0dB.
* **Tracklist Automática:** Gera arquivo `.txt` com timestamps para o YouTube.

### 🎨 Visual & Estética
* **Waveform Reativa:** Espectro de áudio (FFT) com estilo Cyberpunk/Synthwave.
* **Reatividade:** O fundo e o logo "pulsam" (zoom in/out) nas batidas graves (Bass Kicks).
* **Identidade Visual:** Suporte para Logotipo (PNG) e Vídeos Overlay (MP4/MOV).
* **Presets:** Salve suas configurações favoritas (cores, posições, sensibilidade) em arquivos `.json`.

### ⚡ Performance
* **Aceleração GPU:** Detecta placas NVIDIA automaticamente para ativar o codec `NVENC` (até 5x mais rápido).
* **Fallback CPU:** Se não houver GPU, adapta-se automaticamente para renderização via software.

## 🛠️ Instalação

Pré-requisitos: [Python 3.10+](https://www.python.org/downloads/) e FFmpeg.

1.  Clone este repositório.
2.  Instale as dependências (Use um ambiente virtual):
    ```bash
    pip install -r requirements.txt
    ```
    *> **Nota:** É crucial instalar através deste arquivo para garantir a versão correta do MoviePy (1.0.3).*

## 🖥️ Como Usar

1.  Execute o script:
    ```bash
    python app.py
    ```
2.  **Configuração de Mídia:**
    * Selecione a **Pasta de Músicas** e a **Imagem de Fundo**.
    * (Opcional) Adicione seu **Logotipo**.
    * (Opcional) Em *Overlay / Chroma Key*, selecione seu vídeo de "Subscribe" com fundo verde.
3.  **Ajustes Visuais:**
    * Observe o quadro preto (Preview). Ele mostra a onda, o logo e uma imagem estática do seu overlay (sem o fundo verde) para você conferir a posição.
    * Ajuste a **Densidade** e **Cores** conforme seu gosto.
4.  **Renderização:**
    * Verifique o status da GPU na barra lateral (Verde = Rápido).
    * Clique em **INICIAR RENDERIZAÇÃO**.

## 📜 Changelog (Histórico)

### v9.0 - Visual Overlay Edition
* **Novo:** Pré-visualização do vídeo Chroma Key (sem fundo verde) diretamente no Canvas da GUI.
* **Melhoria:** Otimização do desenho de layers no preview.

### v8.0 - Chroma Key Support
* **Novo:** Suporte a vídeos com fundo verde (Green Screen).
* **Novo:** Lógica de repetição de overlay por intervalo de tempo.

### v7.0 - GPU Edition
* **Novo:** Detecção automática de aceleração de hardware (NVIDIA NVENC).
* **Novo:** Seletor dinâmico de codec (h264_nvenc vs libx264).

### v6.0 - Ultimate Audio
* **Novo:** Normalização de áudio e Crossfade.
* **Novo:** Sistema de Presets (.json).
* **Novo:** Logotipo com posicionamento customizável.

## ⚠️ Solução de Problemas

* **Erro "No module named moviepy.editor":**
    * Você provavelmente instalou a versão 2.0 do MoviePy. Corrija rodando:
    `pip install -r requirements.txt --force-reinstall`
* **Overlay não aparece no Preview:**
    * O script tenta capturar o quadro aos 2 segundos do vídeo. Se seu vídeo for muito curto ou começar preto, pode não aparecer no preview (mas aparecerá no vídeo final).

## 📝 Licença
Open Source.
