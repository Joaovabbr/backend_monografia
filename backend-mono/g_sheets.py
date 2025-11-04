# server/g_sheets.py
"""
g_sheets.py (com logs)
Utilitário para gravar UMA LINHA por usuário no Google Sheets.
"""

import os
import json
import logging
from typing import List, Sequence, Any, Optional, Dict
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime

# --- logging setup (controlável por env LOG_LEVEL) ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("g_sheets")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")  # obrigatória
DEFAULT_TAB = os.getenv("SHEET_TAB", "Respostas")  # aba padrão se quiser configurar

def _get_service():
    logger.debug("Entrando em _get_service()")
    sa_json = os.getenv("GOOGLE_SA_JSON")
    sa_path = os.getenv("GOOGLE_SA_JSON_PATH")  # se você subir arquivo e apontar o caminho
    creds_info = None

    try:
        if sa_path:
            logger.debug("Usando GOOGLE_SA_JSON_PATH=%s", sa_path)
            if not os.path.exists(sa_path):
                raise RuntimeError(f"GOOGLE_SA_JSON_PATH apontado mas arquivo não existe: {sa_path}")
            with open(sa_path, "r", encoding="utf-8") as f:
                creds_info = json.load(f)
        elif sa_json:
            logger.debug("Usando GOOGLE_SA_JSON (string JSON)")
            try:
                creds_info = json.loads(sa_json)
            except json.JSONDecodeError as e:
                logger.error("Falha ao decodificar GOOGLE_SA_JSON: %s", e)
                raise RuntimeError("GOOGLE_SA_JSON não contém um JSON válido.") from e
        else:
            raise RuntimeError("GOOGLE_SA_JSON ou GOOGLE_SA_JSON_PATH não configurado.")
    except Exception:
        logger.exception("Erro ao carregar credenciais do service account.")
        raise

    try:
        creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        service = build("sheets", "v4", credentials=creds, cache_discovery=False)
        logger.debug("Serviço Google Sheets inicializado com sucesso.")
        return service
    except Exception:
        logger.exception("Erro ao criar cliente Google Sheets (Credentials/build).")
        raise

def _now_iso():
    return datetime.utcnow().isoformat() + "Z"

def _safe(v: Any) -> str:
    """Converte valor para string segura para planilha (vazio para None)."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, (int, float)):
        return str(v)
    # para strings: strip e retornar
    s = str(v).strip()
    return s

def append_row(tab_name: str, values: Sequence[Any], value_input_option: str = "RAW") -> dict:
    """Append uma linha (values) ao tab_name e retorna a resposta da API."""
    logger.info("append_row: tab=%s len_values=%d", tab_name, len(values) if values is not None else 0)
    if not SPREADSHEET_ID:
        logger.error("SPREADSHEET_ID não configurado.")
        raise RuntimeError("SPREADSHEET_ID não configurado.")
    try:
        service = _get_service()
    except Exception as e:
        logger.exception("append_row: falha ao obter serviço.")
        raise

    range_name = f"{tab_name}!A:Z"
    body = {"values": [list(values)]}
    logger.debug("append_row: range=%s body_preview=%s", range_name, json.dumps(body["values"][0][:10], ensure_ascii=False))
    try:
        result = service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
            valueInputOption=value_input_option,
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()
        logger.info("append_row: sucesso, updates=%s", result.get("updates"))
        return result
    except HttpError as e:
        # log detalhado do HttpError
        logger.exception("Google Sheets API error durante append_row: %s", e)
        raise RuntimeError(f"Google Sheets API error: {e}") from e
    except Exception:
        logger.exception("Erro inesperado em append_row")
        raise

def append_full_response(payload: Dict[str, Any], tab_name: str = DEFAULT_TAB) -> dict:
    logger.info("append_full_response: iniciando. tab=%s", tab_name)
    # Log parcial do payload (não logar tudo em produção)
    try:
        logger.debug("payload keys: %s", list(payload.keys()))
    except Exception:
        logger.debug("append_full_response: não foi possível logar payload keys")

    # campos básicos
    idade = payload.get("idade", "")
    genero = payload.get("genero", "")
    etnia = payload.get("etnia", "")
    escolaridade = payload.get("escolaridade", "")
    estado = payload.get("estado", "")

    # QAP: 37 respostas
    qap = payload.get("qap_responses")
    if qap is None or not isinstance(qap, (list, tuple)) or len(qap) != 37:
        logger.error("Validação QAP falhou: tipo=%s len=%s", type(qap), len(qap) if qap is not None else None)
        raise ValueError("Campo 'qap_responses' deve ser lista com 37 elementos.")
    qap_vals = [int(x) if x is not None and x != "" else "" for x in qap]

    # qap_sum: opcional
    qap_sum = payload.get("qap_sum")
    if qap_sum is None:
        try:
            qap_sum = sum([int(x) for x in qap if isinstance(x, (int, float, str)) and str(x).strip() != ""])
        except Exception:
            logger.exception("Erro ao calcular qap_sum dinamicamente.")
            raise
    else:
        qap_sum = int(qap_sum)

    # Wiscosin: 5 respostas (corrigido para 5)
    wisc = payload.get("wisconsin")
    if wisc is None or not isinstance(wisc, (list, tuple)) or len(wisc) != 5:
        logger.error("Validação Wiscosin falhou: tipo=%s len=%s", type(wisc), len(wisc) if wisc is not None else None)
        raise ValueError("Campo 'wisconsin' deve ser lista com 9 elementos.")
    wisc_vals = [int(x) if x is not None and x != "" else "" for x in wisc]

    # Noticias: first and second (12 cada)
    news_first = payload.get("news_first")
    news_second = payload.get("news_second")
    if news_first is None or not isinstance(news_first, (list, tuple)) or len(news_first) != 12:
        logger.error("Validação news_first falhou: tipo=%s len=%s", type(news_first), len(news_first) if news_first is not None else None)
        raise ValueError("Campo 'news_first' deve ser lista com 12 elementos.")
    if news_second is None or not isinstance(news_second, (list, tuple)) or len(news_second) != 12:
        logger.error("Validação news_second falhou: tipo=%s len=%s", type(news_second), len(news_second) if news_second is not None else None)
        raise ValueError("Campo 'news_second' deve ser lista com 12 elementos.")
    news_first_vals = [int(x) if x is not None and x != "" else "" for x in news_first]
    news_second_vals = [int(x) if x is not None and x != "" else "" for x in news_second]

    # game and time
    game = payload.get("game", "")
    game_time = payload.get("game_time_seconds", "")

    # timestamp opcional
    timestamp = payload.get("timestamp", _now_iso())

    # montar a linha na ordem exata pedida
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

    # expected length: 5 + 37 + 1 + 9 + 12 + 12 + 1 + 1 = 78
    expected_len = 78
    logger.debug("Linha montada length=%d expected=%d", len(row), expected_len)
    if len(row) != expected_len:
        logger.error("Comprimento da linha inválido: %d (esperado %d). Payload keys: %s", len(row), expected_len, list(payload.keys()))
        raise RuntimeError(f"Comprimento da linha inválido: {len(row)} (esperado {expected_len}). Verifique os campos do payload.")

    # opcional: prepend timestamp como coluna A
    row = [_safe(timestamp)] + row

    # enviar ao Google Sheets
    try:
        logger.info("Enviando linha para planilha tab=%s SPREADSHEET_ID=%s", tab_name, "set" if SPREADSHEET_ID else "unset")
        result = append_row(tab_name, row, value_input_option="RAW")
        logger.info("append_full_response: OK, result=%s", result.get("updates") if isinstance(result, dict) else str(result))
        return result
    except Exception as e:
        logger.exception("Erro ao gravar linha no Google Sheets: %s", e)
        raise RuntimeError(f"Erro ao gravar linha no Google Sheets: {e}") from e

def count_rows(tab_name: str = "Respostas") -> int:
    logger.debug("count_rows: tab=%s", tab_name)
    if not SPREADSHEET_ID:
        logger.error("count_rows: SPREADSHEET_ID não definido.")
        raise RuntimeError("SPREADSHEET_ID não definido.")
    try:
        service = _get_service()
        range_name = f"{tab_name}!A:A"
        result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
        values = result.get("values", [])
        logger.debug("count_rows: encontrado %d linhas", len(values))
        return len(values)
    except HttpError as e:
        logger.exception("count_rows: HttpError")
        raise RuntimeError(f"Erro ao contar linhas em {tab_name}: {e}") from e
    except Exception:
        logger.exception("count_rows: erro inesperado")
        raise

def get_cell_value(tab_name: str, cell: str = "A1") -> Optional[str]:
    logger.debug("get_cell_value: tab=%s cell=%s", tab_name, cell)
    if not SPREADSHEET_ID:
        logger.error("get_cell_value: SPREADSHEET_ID não configurado.")
        raise RuntimeError("SPREADSHEET_ID não configurado.")
    service = _get_service()
    range_name = f"{tab_name}!{cell}"
    try:
        result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
        values = result.get("values", [])
        if not values or not values[0]:
            logger.debug("get_cell_value: célula vazia")
            return ""
        logger.debug("get_cell_value: valor='%s'", values[0][0])
        return values[0][0]
    except HttpError as e:
        logger.exception("Erro ao ler célula %s em %s: %s", cell, tab_name, e)
        raise RuntimeError(f"Erro ao ler célula {cell} em {tab_name}: {e}") from e

def set_cell_value(tab_name: str, cell: str, value: Any) -> dict:
    logger.info("set_cell_value: tab=%s cell=%s value_preview=%s", tab_name, cell, str(value)[:100])
    if not SPREADSHEET_ID:
        logger.error("set_cell_value: SPREADSHEET_ID não configurado.")
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
        logger.debug("set_cell_value: resultado=%s", result)
        return result
    except HttpError as e:
        logger.exception("set_cell_value: HttpError ao escrever célula")
        raise RuntimeError(f"Erro ao escrever célula {cell} em {tab_name}: {e}") from e

def increment_counter(tab_name: str = "counter", cell: str = "A1") -> int:
    logger.info("increment_counter: tab=%s cell=%s", tab_name, cell)
    # ler
    raw = get_cell_value(tab_name, cell)
    logger.debug("increment_counter: raw='%s'", raw)
    try:
        current = int(str(raw).strip()) if str(raw).strip() != "" else 0
    except ValueError:
        logger.warning("increment_counter: valor atual invalido -> sobrescrevendo para 0")
        current = 0

    new = current + 1
    try:
        set_cell_value(tab_name, cell, new)
        logger.info("increment_counter: novo valor=%d", new)
        return new
    except Exception:
        logger.exception("increment_counter: falha ao escrever novo valor")
        raise
