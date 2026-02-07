import os
import time
import requests
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from datetime import datetime
import hashlib

# Arquivo para salvar o último anúncio visto e evitar spam
STATE_FILE = "tools/last_announcement_state.json"

def get_announcement():
    load_dotenv()
    api_key = os.getenv("COLOSSEUM_API_KEY")
    if not api_key:
        return None, "API Key missing"

    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        res = requests.get("https://agents.colosseum.com/api/agents/status", headers=headers)
        if res.status_code == 200:
            data = res.json()
            return data.get('announcement'), None
        return None, f"HTTP {res.status_code}"
    except Exception as e:
        return None, str(e)

def send_macos_notification(title, message):
    """Envia notificação nativa do macOS"""
    safe_title = title.replace('"', '\\"')
    safe_message = message.replace('"', '\\"')
    os.system(f"""osascript -e 'display notification "{safe_message}" with title "{safe_title}" sound name "Glass"'""")

def send_email_notification(announcement):
    """Envia email se configurado no .env"""
    sender = os.getenv("EMAIL_SENDER") # Ex: seu_email@gmail.com
    password = os.getenv("EMAIL_PASSWORD") # Ex: senha_de_app
    recipient = os.getenv("EMAIL_RECIPIENT") # Ex: seu_email@gmail.com (ou outro)
    
    if not (sender and password and recipient):
        print("️  Email não configurado no .env (EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENT). Pulando envio.")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = recipient
        msg['Subject'] = f" OBI ALERT: Novo Anúncio Colosseum - {announcement.get('title', 'Update')}"

        body = f"""
        Mestre,

        A organização do Colosseum Hackathon acabou de publicar um novo anúncio:

        TÍTULO: {announcement.get('title')}
        
        MENSAGEM:
        {announcement.get('message')}

        --------------------------------------------------
        OBI Sentinel Agent
        """
        msg.attach(MIMEText(body, 'plain'))

        # Conexão SMTP (Exemplo Gmail)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, password)
        text = msg.as_string()
        server.sendmail(sender, recipient, text)
        server.quit()
        print(" Email de alerta enviado com sucesso!")
        return True
    except Exception as e:
        print(f" Falha ao enviar email: {e}")
        return False

def main_loop():
    print(" OBI SENTINEL: Monitor de Anúncios Ativado")
    print("   (Verificando a cada 5 minutos...)")
    
    while True:
        announcement, error = get_announcement()
        
        if error:
            print(f"️ Erro ao checar status: {error}")
        
        elif announcement:
            # Gerar Hash do anúncio para comparar com o último visto
            content_str = json.dumps(announcement, sort_keys=True)
            current_hash = hashlib.sha256(content_str.encode()).hexdigest()
            
            # Carregar estado anterior
            last_hash = ""
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, 'r') as f:
                    try:
                        state = json.load(f)
                        last_hash = state.get('hash', "")
                    except:
                        pass
            
            # Se for novo anúncio
            if current_hash != last_hash:
                print(f"\n NOVO ANÚNCIO DETECTADO! [{datetime.now().strftime('%H:%M')}]")
                print(f"   Título: {announcement.get('title')}")
                
                # 1. Notificação Visual (Mac)
                send_macos_notification("Colosseum Hackathon", f"Novo Anúncio: {announcement.get('title')}")
                
                # 2. Notificação por Email (Se configurado)
                send_email_notification(announcement)
                
                # Salvar novo estado
                with open(STATE_FILE, 'w') as f:
                    json.dump({'hash': current_hash, 'timestamp': time.time()}, f)
            else:
                # Nada novo
                pass
                # print(".", end="", flush=True) # Heartbeat visual
        
        time.sleep(300) # 5 minutos

if __name__ == "__main__":
    main_loop()
