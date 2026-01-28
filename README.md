# 🎵 Cyberpunk Waveform Automator v7.0 (GPU Edition)

> Uma ferramenta desktop avançada para criação automática de vídeos musicais (Music Mixes) com visualização de espectro reativa, estética Synthwave, mixagem de áudio profissional e aceleração por hardware.

![Cyberpunk UI Screenshot](https://via.placeholder.com/800x450.png?text=Interface+Cyberpunk+v7.0)

## 🚀 Destaques da Versão 7.0
* **⚡ Aceleração por GPU (NVENC):** O script detecta automaticamente se você possui uma placa NVIDIA compatível e ativa a renderização via hardware, tornando o processo até **5x mais rápido**.
* **🎚️ Engenharia de Áudio:**
    * **Normalização Automática:** Nivela o volume de todas as faixas para 0dB.
    * **Crossfade (Transição):** Mistura o final de uma música com o início da próxima (4 segundos) para evitar cortes secos.
* **💎 Identidade Visual:** Suporte para **Logotipo** (PNG transparente) com posicionamento customizável e pulsação sincronizada com a batida.
* **💾 Presets:** Salve e carregue suas configurações favoritas (cores, sensibilidade, posições) instantaneamente.

## ✨ Funcionalidades Principais

* **Processamento em Lote:** Selecione uma pasta e o script une todas as músicas.
* **Visualizador FFT Reativo:** A onda responde às frequências reais (graves/médios/agudos) e não apenas ao volume.
* **Live Preview:** Visualize a estética da onda em tempo real antes de renderizar.
* **Exportação Flexível:**
    * **Resoluções:** 1080p, 720p, 540p.
    * **Áudio:** 320kbps, 192kbps, 128kbps.
* **Tracklist Automática:** Gera um `.txt` com os timestamps prontos para o YouTube.

## 🛠️ Instalação

Pré-requisitos: [Python 3.10+](https://www.python.org/downloads/) e [FFmpeg](https://ffmpeg.org/) instalado no sistema (O script tenta usar o binário interno, mas para GPU é recomendável ter drivers NVIDIA atualizados).

1.  Clone o repositório ou baixe os arquivos.
2.  Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```

## 🖥️ Como Usar

1.  Execute o script:
    ```bash
    python app.py
    ```
2.  **Verifique o Status da GPU:**
    * Olhe na barra lateral esquerda. Se estiver verde (**GPU DETECTADA**), a renderização será ultrarrápida. Se estiver laranja, será usada a CPU.
3.  **Configuração:**
    * Carregue a pasta de Músicas e a Imagem de Fundo.
    * (Opcional) Carregue seu Logotipo.
    * Marque **Normalizar Volume** e **Crossfade** para um resultado profissional.
4.  **Customização:**
    * Use os sliders para ajustar a densidade e altura da onda olhando o **Preview**.
5.  Clique em **INICIAR RENDERIZAÇÃO**.

## 📜 Changelog (Histórico de Mudanças)

### v7.0 - GPU Edition
* **Novo:** Detecção automática de GPU NVIDIA (NVENC).
* **Novo:** Fallback inteligente para CPU se não houver GPU.
* **Melhoria:** Otimização do loop de renderização de frames.

### v6.0 - Ultimate Audio & Branding
* **Novo:** Normalização de áudio (pydub/moviepy fx).
* **Novo:** Crossfade automático entre faixas.
* **Novo:** Suporte a Logotipo com transparência e posicionamento (Cantos/Centro).
* **Novo:** Sistema de Salvar/Carregar Presets (.json).

### v5.0 - Export Controls
* **Novo:** Seletor de Resolução (1080p/720p/540p).
* **Novo:** Seletor de Bitrate de Áudio.
* **Novo:** Cronômetro de renderização em tempo real.

### v4.0 - Visual Feedback
* **Novo:** Canvas de Preview em Tempo Real (simulação da onda).
* **Novo:** Conversão de cores BGR/HEX para interface.

## ⚠️ Solução de Problemas

* **Erro "No module named moviepy.editor":**
    * O script requer a versão `1.0.3`. Execute:
    `pip install -r requirements.txt --force-reinstall`
* **GPU não detectada:**
    * Certifique-se de ter drivers NVIDIA instalados.
    * Verifique se o comando `ffmpeg -encoders` no seu terminal lista `h264_nvenc`.

## 📝 Licença
Open Source. Sinta-se livre para modificar e usar em seus projetos.
