from g_sheets import  append_full_response, increment_counter
from fastapi import Request, FastAPI, HTTPException
import os
from email_sender import envia_email_simples
from dotenv import load_dotenv
from pydantic import BaseModel


load_dotenv()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Ajuste as origens conforme necessário
origins = [
    "http://localhost:5173",      # dev Vite
    "http://localhost:8000",      
    "https://monografia-frontend.onrender.com",  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

INVERT_QAP_ITEMS_1BASED = {1,2,5,7,8,12,13,15,16,19,22,23,25,26,29,33,35}

# === 1️⃣ Endpoint: recebe email e devolve grupo ===
@app.get("/api/get-group")
async def register_email(request: Request):
    """
    Recebe { "email": "..." } e devolve { group: "par"|"impar" }.
    O grupo é definido pelo valor do contador na planilha:
    - A cada requisição, incrementa a célula A1 da aba configurada (default 'contador').
    - Se o contador for par → grupo 'par'
    - Se o contador for ímpar → grupo 'impar'
    """

    # Nome da aba de contador (pode configurar no .env)
    contador_tab = os.getenv("SHEET_contador_TAB", "contador")

    try:
        # incrementa o contador e obtém o novo valor
        new_count = increment_counter(tab_name=contador_tab, cell="A1")

        # define grupo a partir do contador
        group = "par" if (new_count - 1) % 2 == 0 else "impar"

        # aqui futuramente você pode chamar envia_email_simples(email, group)
        print(f"contador={new_count - 1} | grupo={group}")

        return {"ok": True, "group": group, "contador": new_count}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar registro: {e}")


@app.post("/api/finaliza-pesquisa")
async def finaliza_pesquisa(request: Request):
    """
    Recebe dados completos, calcula qap_sum com inversões nos itens especificados
    e grava UMA linha usando append_full_response.
    """
    try:
        data = await request.json()
    except Exception:
        detail = "JSON inválido."
        print(detail)
        raise HTTPException(status_code=400, detail= detail)
        

    # Validações básicas sobre qap_responses
    qap = data.get("qap_responses")
    if not isinstance(qap, (list, tuple)) or len(qap) != 37:
        detail = "Campo 'qap_responses' deve ser lista com 37 elementos."
        print(detail)
        raise HTTPException(status_code=400, detail= detail)

    # converte e valida cada resposta (garante número inteiro entre 1 e 5)
    qap_ints = []
    try:
        for i, val in enumerate(qap, start=0):
            if val is None or str(val).strip() == "":
                raise ValueError(f"Item QAP {i} está vazio.")
            v = int(val)
            if v < 1 or v > 5:
                raise ValueError(f"Item QAP {i} com valor inválido: {v}. Deve ser 1..5.")
            qap_ints.append(v)
    except ValueError as ve:
        print(str(ve))
        raise HTTPException(status_code=400, detail=str(ve))

    # calcula a soma com inversões nos índices listados
    processed_vals_for_sum = []
    for idx1, v in enumerate(qap_ints, start=0):
        if idx1 in INVERT_QAP_ITEMS_1BASED:
            inverted = 6 - v   # 1->5, 2->4, 3->3, 4->2, 5->1
            processed_vals_for_sum.append(inverted)
        else:
            processed_vals_for_sum.append(v)

    qap_sum_computed = sum(processed_vals_for_sum)

    # define no payload (sobrescreve/insere) para gravar a soma correta
    data["qap_sum"] = int(qap_sum_computed)

    # opcional: você pode também gravar a versão "processada" em outra chave para auditoria:
    # data["qap_processed_for_sum"] = processed_vals_for_sum

    # garantir timestamp se necessário
    if not data.get("timestamp"):
        from datetime import datetime
        data["timestamp"] = datetime.utcnow().isoformat() + "Z"

    # grava usando append_full_response (essa função validará formatos e tamanhos novamente)
    try:
        append_full_response(data, tab_name=os.getenv("SHEET_TAB", "responses"))
        return {
            "ok": True,
            "message": "Pesquisa finalizada e gravada com sucesso.",
        }
    except ValueError as ve:
        detail = f"Erro de validação: {ve}"
        print(detail)
        raise HTTPException(status_code=400, detail=detail)
    except Exception as e:
        detail = f"Erro ao gravar no Google Sheets: {e}"
        print(detail)
        raise HTTPException(status_code=500, detail= detail)


class EmailRequest(BaseModel):
    destinatario: str

@app.post("/api/tcle")
async def envia_email(request: EmailRequest):
    """
    Endpoint que envia o Termo de Consentimento para o email informado.
    Exemplo de chamada:
        POST /api/tcle
        {
            "destinatario": "usuario@exemplo.com"
        }
    """
    destinatario = request.destinatario.strip()
    if not destinatario:
        raise HTTPException(status_code=400, detail="Campo 'destinatario' é obrigatório.")

    ok = envia_email_simples(destinatario)
    if not ok:
        raise HTTPException(status_code=500, detail="Falha ao enviar o email.")

    return {"ok": True, "message": f"Termo de consentimento enviado para {destinatario}."}


@app.get("/health")
def health():
    return {"ok": True}
