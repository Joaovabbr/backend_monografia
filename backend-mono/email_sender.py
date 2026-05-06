import os
import requests
import json
import base64
from dotenv import load_dotenv
load_dotenv()


BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"

def envia_email_simples(destinatario: str) -> bool:
    """
    Envia o TCLE via Brevo (ex-Sendinblue) API.
    Isto funciona em plataformas como o Render que bloqueiam portas SMTP.

    Requer as variáveis de ambiente:
    - EMAIL_FROM: (o seu email@gmail.com, que deve ser verificado no Brevo)
    - BREVO_API_KEY: (a sua chave de API v3 do Brevo)
    
    Retorna True se enviado com sucesso, False caso contrário.
    """
    
    
    api_key = os.getenv("BREVO_API_KEY")
    from_email = os.getenv("EMAIL_FROM")

    if not api_key:
        print("Erro: Variável de ambiente BREVO_API_KEY não configurada.")
        return False
    if not from_email:
        print("Erro: Variável de ambiente EMAIL_FROM não configurada.")
        return False
    
    caminho_tcle = "./data/pdf/TCLE_assinado.pdf"
    try:
        with open(caminho_tcle, "rb") as f:
            conteudo_binario = f.read()
            # O Brevo espera uma string base64
            tcle_base64 = base64.b64encode(conteudo_binario).decode("utf-8")
    except FileNotFoundError:
        print(f"Erro: Arquivo {caminho_tcle} não encontrado para anexo.")
        return False

    
    assunto = ("Termo de Consentimento Livre e Esclarecido (TCLE) - "
               "Pesquisa: Do jogo à realidade: a relação da metacognição no reconhecimento de fake news")
    termo_consentimento = (

        """Olá! Você aceitou participar da pesquisa “Do jogo à realidade: a relação da metacognição no reconhecimento de fake news com uso da gamificação”

        Em anexo segue sua via do TCLE com todos os detalhes da pesquisa. Em caso de dúvidas ou desistência em participar da pesquisa basta entrar em contato com a pesquisadora pelos meios abaixo."""
    )

    
    payload = {
        "sender": {"email": from_email},
        "to": [{"email": destinatario}],
        "subject": assunto,
        "textContent": termo_consentimento, 
        "htmlContent": termo_consentimento.replace("\n", "<br/>"), 
        "attachment": [
            {
                "content": tcle_base64,
                "name": "TCLE Pesquisa.pdf" 
            }
        ]
    }

    
    headers = {
        "api-key": api_key, 
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    print(f"Tentando enviar e-mail para {destinatario} via Brevo API...")

    try:
        resp = requests.post(BREVO_API_URL, headers=headers, data=json.dumps(payload), timeout=15)
        
        # O Brevo retorna 201 (Created) em caso de sucesso no envio da API
        if resp.status_code == 201:
            print(f"Email enviado com sucesso para {destinatario} (status {resp.status_code})")
            return True
        else:
            # Log útil para depuração
            body_text = resp.text
            print(f"Falha ao enviar email para {destinatario}: status {resp.status_code} - {body_text}")
            return False
            
    except requests.RequestException as e:
        print(f"Erro de rede ao tentar enviar email para {destinatario}: {e}")
        return False
    except Exception as e:
        print(f"Erro inesperado ao enviar email para {destinatario}: {e}")
        return False