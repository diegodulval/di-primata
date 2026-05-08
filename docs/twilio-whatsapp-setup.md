# Twilio WhatsApp — Setup e Exposição para Testes

Guia para reconfigurar a integração do zero: recuperar credenciais, rodar o servidor local e expor o webhook publicamente para o sandbox Twilio.

---

## 1. Recuperar credenciais no Console Twilio

1. Acesse [console.twilio.com](https://console.twilio.com)
2. Na página inicial (Dashboard), copie:
   - **Account SID** — começa com `AC...`
   - **Auth Token** — clique no ícone de olho para revelar
3. O número WhatsApp do sandbox está em:
   **Messaging → Try it out → Send a WhatsApp message**
   - Número padrão do sandbox: `+14155238886`

---

## 2. Configurar o `.env`

Edite o arquivo `.env` na raiz do projeto:

```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_FROM=+14155238886
TWILIO_VALIDATE_SIGNATURE=False
```

> Em produção, use `TWILIO_VALIDATE_SIGNATURE=True` para validar a assinatura HMAC de cada requisição Twilio.

---

## 3. Instalar dependências e iniciar o servidor

```bash
make dev       # instala dependências (inclui twilio>=9.0.0)
make run       # inicia em http://localhost:8000
```

Verifique que está rodando:

```bash
curl http://localhost:8000/health
# {"status":"ok","version":"0.1.0"}
```

---

## 4. Expor o servidor publicamente

O Twilio precisa de uma URL HTTPS acessível pela internet para chamar o webhook.

### Opção A — cloudflared (sem cadastro, recomendado para testes rápidos)

```bash
# Baixar o binário (Linux x64)
curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
  -o /tmp/cloudflared && chmod +x /tmp/cloudflared

# Iniciar o tunnel apontando para o servidor local
/tmp/cloudflared tunnel --url http://localhost:8000 --no-autoupdate
```

A URL pública aparece nos logs:

```
INF | https://algum-nome-aleatorio.trycloudflare.com |
```

Confirme que está acessível:

```bash
curl https://algum-nome-aleatorio.trycloudflare.com/health
```

> URLs `trycloudflare.com` são temporárias e mudam a cada reinício. Para URL fixa veja a Opção B.

### Opção B — ngrok (URL fixa com conta gratuita)

```bash
# Instalar: https://ngrok.com/download
ngrok http 8000
```

Com conta gratuita é possível reservar um subdomínio fixo em **ngrok.com → Domains**.

### Opção C — localtunnel (via npm)

```bash
npx localtunnel --port 8000
```

---

## 5. Configurar o webhook no Sandbox Twilio

1. Acesse: **console.twilio.com → Messaging → Try it out → Send a WhatsApp message**
2. Clique na aba **Sandbox Settings**
3. No campo **"When a message comes in"**, cole:
   ```
   https://<sua-url-publica>/whatsapp/webhook
   ```
4. Método: **HTTP POST**
5. Clique **Save**

---

## 6. Conectar o celular ao sandbox

Na mesma tela **Sandbox Settings**, há uma instrução como:

> Envie `join <palavra-codigo>` para `+14155238886`

O número de destino deve enviar essa mensagem pelo WhatsApp antes de conseguir trocar mensagens com o sandbox.

---

## 7. Verificar o fluxo completo

### Envio manual via SDK (Python)

```python
from twilio.rest import Client

client = Client("ACxxxxxxxx", "xxxxxxxx")

msg = client.messages.create(
    from_="whatsapp:+14155238886",
    to="whatsapp:+55XXXXXXXXXXX",
    body="Olá pelo SDK Di Mata!",
)
print(msg.sid, msg.status)
```

### Envio de template (Content API)

```bash
curl 'https://api.twilio.com/2010-04-01/Accounts/<SID>/Messages.json' -X POST \
  --data-urlencode 'To=whatsapp:+55XXXXXXXXXXX' \
  --data-urlencode 'From=whatsapp:+14155238886' \
  --data-urlencode 'ContentSid=HXb5b62575e6e4ff6129ad7c8efe1f983e' \
  --data-urlencode 'ContentVariables={"1":"12/1","2":"3pm"}' \
  -u <SID>:<AUTH_TOKEN>
```

### Inbound — receber mensagem

Envie qualquer mensagem pelo WhatsApp para `+14155238886`. O servidor responde com o menu inicial:

```
Olá, <nome>! Sou o assistente Di Mata. 🌱

Como posso ajudar?
• 1 — Registrar atividade
• 2 — Consultar safra
• 3 — Falar com técnico
```

Monitore as sessões criadas:

```bash
curl http://localhost:8000/whatsapp/sessions
```

---

## 8. Referências

| Recurso | URL |
|---|---|
| Console Twilio | https://console.twilio.com |
| Sandbox WhatsApp | console.twilio.com → Messaging → Try it out |
| Twilio Python SDK | https://pypi.org/project/twilio |
| cloudflared releases | https://github.com/cloudflare/cloudflared/releases |
| ngrok | https://ngrok.com/download |
