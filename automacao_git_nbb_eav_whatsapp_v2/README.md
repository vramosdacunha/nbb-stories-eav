# Automação Diária NBB Stories (EAV Produções) -> WhatsApp

Este repositório roda automaticamente no **GitHub Actions** todos os dias às **09:00 da manhã (horário de Brasília)**:
1. Consulta a tabela oficial da LNB (`lnb.com.br`).
2. Renderiza o vídeo vertical **MP4 (1080x1920, 30fps)** com as logos da **EAV Produções**, **NBB** e os **escudos oficiais dos clubes**.
3. Envia o arquivo `.mp4` direto para o seu WhatsApp (`+55 21 96744-7902`).

## Escudos Já Incluídos em `assets/teams/`
- Bauru Basket (`bauru.png`)
- Caixa Brasília (`brasilia.png`)
- Caxias do Sul (`caxias.png`)
- Corinthians (`corinthians.png`)
- Cruzeiro Basquete (`cruzeiro.png`)
- União Corinthians (`uniao_corinthians.png`)
- Flamengo (`flamengo.png`)
- Paulistano (`paulistano.png`)
- Basquete Cearense / Fortaleza (`cearense.png`)
- Botafogo (`botafogo.png`)

*(Para adicionar os outros clubes da temporada, basta jogar o PNG na pasta `assets/teams/` com o nome do time).*

## Como Ativar em 3 Passos no seu GitHub
1. Crie um repositório privado no seu GitHub e suba os arquivos deste ZIP.
2. Vá em **Settings > Secrets and variables > Actions** e adicione:
   - `WHATSAPP_API_URL`: URL da sua instância (Evolution API, Z-API ou Ultramsg).
   - `WHATSAPP_API_KEY`: Token/Chave da API.
3. Na aba **Actions**, clique em **Agenda Diaria NBB - EAV Prod** e aperte **Run workflow** para fazer o disparo de teste na hora!
