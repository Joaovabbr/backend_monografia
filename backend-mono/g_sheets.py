# server/g_sheets.py
"""
g_sheets.py

Utilitário para gravar UMA LINHA por usuário no Google Sheets com a estrutura
exata requisitada:

Ordem das colunas:
1) idade
2) genero
3) etnia
4) escolaridade
5) estado
6..42) 37 colunas -> respostas QAP (q1..q37)
43) qap_sum
44..52) 9 colunas -> respostas Wiscosin (w1..w9)
53..76) 24 colunas -> 12 respostas imagens primeira tentativa (n1_1..n1_12) +
                      12 respostas imagens segunda tentativa (n2_1..n2_12)
77) game (string)
78) game_time_seconds (número)

Exemplo de payload esperado (chave -> tipo):
{
  "idade": 28,
  "genero": "feminino",
  "etnia": "parda",
  "escolaridade": "superior_completo",
  "estado": "São Paulo (SP)",
  "qap_responses": [3,5,2, ...] (len==37),
  "qap_sum": 120,  # opcional (se omitido, calculamos)
  "wiscosin": [1,3,2,...] (len==9),
  "news_first": [1,4,2,...] (len==12),
  "news_second": [2,3,1,...] (len==12),
  "game": "badnews",
  "game_time_seconds": 312  # inteiro ou float
}

Dependências: google-auth, google-api-python-client
"""

import os
import json
from typing import List, Sequence, Any, Optional, Dict
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")  # obrigatória
DEFAULT_TAB = os.getenv("SHEET_TAB", "Respostas")  # aba padrão se quiser configurar

def _get_service():
    sa_json = os.getenv("GOOGLE_SA_JSON")
    sa_path = os.getenv("GOOGLE_SA_JSON_PATH")  # se você subir arquivo e apontar o caminho
    creds_info = None

    if sa_path:
        if not os.path.exists(sa_path):
            raise RuntimeError(f"GOOGLE_SA_JSON_PATH apontado mas arquivo não existe: {sa_path}")
        with open(sa_path, "r", encoding="utf-8") as f:
            creds_info = json.load(f)
    elif sa_json:
        # aceita string JSON (possivelmente com quebras de linha)
        try:
            creds_info = json.loads(sa_json)
        except json.JSONDecodeError as e:
            raise RuntimeError("GOOGLE_SA_JSON não contém um JSON válido.") from e
    else:
        raise RuntimeError("GOOGLE_SA_JSON ou GOOGLE_SA_JSON_PATH não configurado.")

    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds, cache_discovery=False)
    return service

def _now_iso():
    return datetime.utcnow().isoformat() + "Z"

def _safe(v: Any):
    """Converte valor para string segura para planilha (vazio para None)."""
    if v is None:
        return ""
    # bool -> string
    if isinstance(v, bool):
        return "1" if v else "0"

def append_row(tab_name: str, values: Sequence[Any], value_input_option: str = "RAW") -> dict:
    """Append uma linha (values) ao tab_name e retorna a resposta da API."""
    if not SPREADSHEET_ID:
        raise RuntimeError("SPREADSHEET_ID não configurado.")
    service = _get_service()
    range_name = f"{tab_name}!A:Z"
    body = {"values": [list(values)]}
    try:
        result = service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
            valueInputOption=value_input_option,
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()
        return result
    except HttpError as e:
        # re-raise com mensagem legível
        raise RuntimeError(f"Google Sheets API error: {e}")

def append_full_response(payload: Dict[str, Any], tab_name: str = DEFAULT_TAB) -> dict:
    """
    Monta e envia UMA linha com a estrutura exata pedida.
    Lança ValueError em validações simples (comprimentos inválidos, etc).
    """
    # campos básicos
    idade = payload.get("idade", "")
    genero = payload.get("genero", "")
    etnia = payload.get("etnia", "")
    escolaridade = payload.get("escolaridade", "")
    estado = payload.get("estado", "")

    # QAP: 37 respostas
    qap = payload.get("qap_responses")
    if qap is None or not isinstance(qap, (list, tuple)) or len(qap) != 37:
        raise ValueError("Campo 'qap_responses' deve ser lista com 37 elementos.")
    # convert to ints (or empty)
    qap_vals = [int(x) if x is not None and x != "" else "" for x in qap]

    # qap_sum: opcional, se não informado calculamos somatória ignorando vazios
    qap_sum = payload.get("qap_sum")
    if qap_sum is None:
        # sum only numeric entries
        qap_sum = sum([int(x) for x in qap if isinstance(x, (int, float, str)) and str(x).strip() != ""])
    else:
        qap_sum = int(qap_sum)

    # Wiscosin: 9 respostas
    wisc = payload.get("wisconsin")
    if wisc is None or not isinstance(wisc, (list, tuple)) or len(wisc) != 5:
        raise ValueError("Campo 'wiscosin' deve ser lista com 5 elementos.")
    wisc_vals = [int(x) if x is not None and x != "" else "" for x in wisc]

    # Noticias: first and second (12 cada)
    news_first = payload.get("news_first")
    news_second = payload.get("news_second")
    if news_first is None or not isinstance(news_first, (list, tuple)) or len(news_first) != 12:
        raise ValueError("Campo 'news_first' deve ser lista com 12 elementos.")
    if news_second is None or not isinstance(news_second, (list, tuple)) or len(news_second) != 12:
        raise ValueError("Campo 'news_second' deve ser lista com 12 elementos.")
    news_first_vals = [int(x) if x is not None and x != "" else "" for x in news_first]
    news_second_vals = [int(x) if x is not None and x != "" else "" for x in news_second]

    # game and time
    game = payload.get("game", "")
    game_time = payload.get("game_time_seconds", "")

    # timestamp opcional
    timestamp = payload.get("timestamp", _now_iso())

    # montar a linha na ordem exata solicitada:
    # [idade, genero, etnia, escolaridade, estado,
    # q1..q37 (37 cols), qap_sum,
    # w1..w9 (9 cols),
    # n1_1..n1_12 (12 cols),
    # n2_1..n2_12 (12 cols),
    # game, game_time_seconds]
    row: List[Any] = []
    row.append(_safe(idade))
    row.append(_safe(genero))
    row.append(_safe(etnia))
    row.append(_safe(escolaridade))
    row.append(_safe(estado))

    # QAP 37
    row.extend([_safe(v) for v in qap_vals])  # 37 cols

    # QAP sum
    row.append(_safe(qap_sum))

    # Wiscosin 9
    row.extend([_safe(v) for v in wisc_vals])  # 9 cols

    # News first 12
    row.extend([_safe(v) for v in news_first_vals])  # 12 cols

    # News second 12
    row.extend([_safe(v) for v in news_second_vals])  # 12 cols

    # game
    row.append(_safe(game))

    # game time
    row.append(_safe(game_time))

    # final check: row length should be 5 + 37 +1 +9 +12 +12 +1 +1 = 78
    expected_len = 74
    if len(row) != expected_len:
        raise RuntimeError(f"Comprimento da linha inválido: {len(row)} (esperado {expected_len}). "
                           f"Verifique os campos do payload.")

    # prepend timestamp? se quiser, podemos gravar timestamp na primeira coluna.
    # se preferir timestamp como coluna adicional, ajuste aqui.
    # por enquanto, gravamos timestamp como primeira coluna (opcional).
    # Se NÃO quiser timestamp, comente a linha abaixo.
    row = [_safe(timestamp)] + row  # descomente se desejar timestamp como coluna A

    # enviar ao Google Sheets
    try:
        result = append_row(tab_name, row, value_input_option="RAW")
        return result
    except Exception as e:
        raise RuntimeError(f"Erro ao gravar linha no Google Sheets: {e}")
    
def count_rows(tab_name: str = "Respostas") -> int:
    """
    Retorna o número de linhas existentes em uma aba (tab_name).
    Usa a coluna A como referência (conta quantas células estão preenchidas).
    """
    if not SPREADSHEET_ID:
        raise RuntimeError("SPREADSHEET_ID não definido.")
    service = _get_service()
    range_name = f"{tab_name}!A:A"  # lê apenas a coluna A
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name
    ).execute()
    values = result.get("values", [])
    return len(values)


def get_cell_value(tab_name: str, cell: str = "A1") -> Optional[str]:
    """
    Lê e retorna o valor da célula especificada (ex: "A1") na aba tab_name.
    Retorna string vazia se estiver vazia.
    """
    if not SPREADSHEET_ID:
        raise RuntimeError("SPREADSHEET_ID não configurado.")
    service = _get_service()
    range_name = f"{tab_name}!{cell}"
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name
        ).execute()
        values = result.get("values", [])
        if not values or not values[0]:
            return ""
        return values[0][0]
    except HttpError as e:
        raise RuntimeError(f"Erro ao ler célula {cell} em {tab_name}: {e}")

def set_cell_value(tab_name: str, cell: str, value: Any) -> dict:
    """
    Escreve value na célula indicada (substitui o conteúdo).
    Retorna o resultado da API.
    """
    if not SPREADSHEET_ID:
        raise RuntimeError("SPREADSHEET_ID não configurado.")
    service = _get_service()
    range_name = f"{tab_name}!{cell}"
    body = {"values": [[_safe(value)]]}
    try:
        result = service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
            valueInputOption="RAW",
            body=body
        ).execute()
        return result
    except HttpError as e:
        raise RuntimeError(f"Erro ao escrever célula {cell} em {tab_name}: {e}")

def increment_counter(tab_name: str = "counter", cell: str = "A1") -> int:
    """
    Incrementa a célula (numérica) tab_name!cell em +1 atomically (na prática: read->+1->write).
    Retorna o novo valor (int).
    """
    # ler
    raw = get_cell_value(tab_name, cell)
    try:
        current = int(str(raw).strip()) if str(raw).strip() != "" else 0
    except ValueError:
        # se houver texto inválido, sobrescreve para 0 antes de incrementar
        current = 0

    new = current + 1
    # escrever novo valor
    set_cell_value(tab_name, cell, new)
    return new
