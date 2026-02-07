#  Guia de Integração: OBIWORK x Google Calendar

Atualmente, o sistema está rodando em **Modo Simulação (Mock)**. Para que o **Mentorship Hub** gerencie sua agenda real e crie links do Google Meet, precisamos conectar um "Robô" (Service Account) à sua conta.

Não é necessário fazer login com senha (OAuth). O método profissional é usar uma **Service Account**.

##  Passo a Passo (5 Minutos)

### 1. Criar o Robô (Google Cloud Console)
1. Acesse o [Google Cloud Console](https://console.cloud.google.com/).
2. Crie um **Novo Projeto** (ex: `obiwork-production`).
3. No menu lateral, vá em **APIs e Serviços > Biblioteca**.
4. Pesquise e **Ative** estas duas APIs:
   - `Google Calendar API`
   - `Google Drive API`

### 2. Gerar as Credenciais
1. Vá em **APIs e Serviços > Credenciais**.
2. Clique em **Criar Credenciais > Conta de Serviço (Service Account)**.
   - Nome: `obiwork-bot`
   - Clique em "Concluir".
3. Na lista de Contas de Serviço, clique no email criado (ex: `obiwork-bot@obiwork-production.iam.gserviceaccount.com`).
4. Vá na aba **Chaves** > **Adicionar Chave** > **Criar nova chave** > **JSON**.
5. Um arquivo `.json` será baixado. **Guarde-o, essa é a chave mestra.**

### 3. Conectar ao seu Calendário (O Pulo do Gato )
O Robô existe, mas não tem permissão para ver sua agenda pessoal.
1. Abra seu [Google Calendar](https://calendar.google.com/).
2. No menu esquerdo, passe o mouse no seu calendário principal, clique nos três pontos `⋮` e em **Configurações e compartilha**.
3. Em "Compartilhar com pessoas específicas", clique em **Adicionar pessoas**.
4. Cole o **email da Service Account** (aquele `...iam.gserviceaccount.com`).
5. **Permissão:** Selecione **"Fazer alterações nos eventos"**.
6. Clique em Enviar.

### 4. Configurar o Projeto (ObiWork)
Abra o arquivo `.json` baixado no passo 2 com um editor de texto. Copie os valores para o seu arquivo `.env`:

```bash
# .env (na raiz do projeto ou em obiwork_web)

# O email do robô (client_email no json)
GOOGLE_CLIENT_EMAIL="obiwork-bot@obiwork-production.iam.gserviceaccount.com"

# A chave privada completa (private_key no json)
# IMPORTANTE: Copie tudo, incluindo -----BEGIN PRIVATE KEY... e as quebras de linha (\n)
GOOGLE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggS7AgEAAoIBAQC..."

# (Opcional) ID do calendário. Se usou o principal, deixe 'primary'
GOOGLE_CALENDAR_ID="primary"
```

---

###  Teste Final
Após salvar o `.env`, reinicie o servidor (`npm run dev`).
O indicador no Dashboard mudará de **Amarelo** para **Azul (Google Calendar Synced)** e seus eventos reais aparecerão na lista.
