# 🎵 Cyberpunk Automator v10.0 (Production Suite)

> A ferramenta definitiva para automação de canais de música. Crie mixes profissionais com estética Cyberpunk, efeitos retrô, thumbnails automáticas e faça upload direto para o YouTube sem sair do aplicativo.

![Interface Preview](https://via.placeholder.com/800x450.png?text=Cyberpunk+Automator+v10+Interface)

## 🚀 O Que Há de Novo na v10.0?

Esta versão transforma o script em uma **Suíte de Produção Completa**:

* **📺 Backgrounds de Vídeo (Loop):** Suporte nativo para vídeos (`.mp4`) ou GIFs em loop infinito como fundo, substituindo imagens estáticas.
* **📡 Upload Direto (YouTube API):** Envie o vídeo renderizado automaticamente para seu canal, incluindo Título, Descrição (com Tracklist), Tags e Thumbnail.
* **🖼️ Gerador de Thumbnails:** Cria automaticamente a capa do vídeo usando o fundo e o logo, com texto customizável (ex: "LO-FI MIX 2026").
* **📼 Efeitos de Pós-Processamento:** Adicione filtros retrô como **Scanlines** (TV de Tubo), **Ruído VHS** e **Glitch Cromático**.
* **🎵 Overlay "Tocando Agora":** Exibe o nome da música atual no canto da tela, sincronizado perfeitamente com a troca de faixas.

---

## ✨ Funcionalidades Principais

### 🎚️ Engenharia de Áudio
* **Mixagem Automática:** Une pastas inteiras de MP3/WAV.
* **Crossfade Inteligente:** Transições suaves de 4 segundos entre músicas.
* **Normalização (0dB):** Garante que todas as faixas tenham o mesmo volume.

### 🎨 Visual & Estética
* **Waveform Reativa:** Espectro de áudio (FFT) com cores Neon e Glow.
* **Reatividade Total:** Logo e Fundo "pulsam" nas batidas graves (Bass Kicks).
* **Chroma Key:** Suporte para animações de "Inscreva-se" (Fundo Verde) com repetição intervalada.
* **Live Preview:** Visualize efeitos, posições e cores em tempo real antes de renderizar.

### ⚡ Performance
* **Aceleração GPU:** Detecta e usa placas NVIDIA (NVENC) para renderização até 5x mais rápida.
* **Fallback CPU:** Funciona em qualquer computador via processamento de software.

---

## 🛠️ Instalação

### Pré-requisitos
* [Python 3.10+](https://www.python.org/downloads/)
* [FFmpeg](https://ffmpeg.org/) instalado e adicionado ao PATH do sistema.

### Passo a Passo
1.  Clone este repositório.
2.  Instale as dependências (incluindo as novas bibliotecas do Google):
    ```bash
    pip install -r requirements.txt
    ```

---

## 🔑 Configuração da API do YouTube (Para Upload Automático)

Para usar a função de Upload, você precisa de um arquivo `client_secret.json` do Google:

1.  Acesse o [Google Cloud Console](https://console.cloud.google.com/).
2.  Crie um novo Projeto.
3.  Vá em **APIs e Serviços > Biblioteca** e ative a **"YouTube Data API v3"**.
4.  Vá em **Tela de consentimento OAuth**, escolha "Externo" e preencha os dados básicos (email, nome). Adicione seu próprio email como "Usuário de Teste".
5.  Vá em **Credenciais > Criar Credenciais > ID do Cliente OAuth**.
    * Tipo de Aplicativo: **Desktop App**.
6.  Baixe o arquivo JSON gerado e renomeie para `client_secret.json`.
7.  No aplicativo, clique em **"Carregar Client Secret"** e selecione este arquivo.

> *Nota: O arquivo é criptografado localmente pelo script para segurança.*

---

## 🖥️ Guia de Uso

1.  **Mídia:**
    * Selecione a Pasta de Áudio.
    * Escolha o Fundo (Imagem `.jpg` ou Vídeo Loop `.mp4`).
    * (Opcional) Adicione Logo e Overlay de Chroma Key.
2.  **Visual:**
    * Ative **"Ativar Overlay de Faixa"** para mostrar os nomes das músicas.
    * Escolha um **Efeito de Pós-Processamento** (ex: Scanlines) para dar estilo.
3.  **YouTube & Saída:**
    * Marque **"Gerar Thumbnail"** e digite o texto da capa.
    * Preencha o Título, Tags e Descrição do vídeo.
    * Verifique se o status da API está verde ("Configuração Restaurada" ou "Arquivo Carregado").
4.  **Produção:**
    * Clique em **INICIAR PRODUÇÃO COMPLETA**.
    * O script fará: Renderização -> Geração de Thumb -> Upload Privado para o YouTube.

---

## 📜 Changelog (Histórico)

### v10.0 - Production Suite
* **Novo:** Suporte a Background de Vídeo (Loops).
* **Novo:** Integração com YouTube API v3 (Upload direto).
* **Novo:** Gerador de Thumbnails automático.
* **Novo:** Efeitos visuais (VHS, Glitch, Scanlines).
* **Novo:** Texto dinâmico "Tocando Agora".

### v9.0 - Visual Overlay
* **Novo:** Preview de Chroma Key no Canvas.
* **Melhoria:** Repetição inteligente de overlays.

### v8.0 - Chroma Key
* **Novo:** Remoção de fundo verde para vídeos de overlay.

### v7.0 - GPU Edition
* **Novo:** Detecção e uso de aceleração NVIDIA NVENC.

---

## ⚠️ Solução de Problemas Comuns

* **Erro de Autenticação (Google):**
    * Certifique-se de ter adicionado seu email como "Test User" no painel do Google Cloud, pois o app não foi verificado pela Google.
* **Vídeo de Fundo travando:**
    * Use vídeos curtos (10-30 segundos) que sejam leves. Vídeos 4K muito pesados podem consumir toda a RAM durante o loop.
* **Upload Falhou:**
    * Verifique sua conexão. O vídeo renderizado estará salvo na pasta de músicas, você pode fazer o upload manual se necessário.

## 📝 Licença
Open Source.
