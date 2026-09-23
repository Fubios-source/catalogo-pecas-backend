"""
FastAPI Backend para Catálogo de Peças
- Proxy seguro pra API do Google Gemini (evita CORS)
- Identifica peça por foto ou busca por veículo
- Deploy: Render
"""

import os
import json
import base64
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import httpx
import uvicorn

app = FastAPI(title="Catálogo de Peças API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY não configurada. Define como variável de ambiente.")

MODEL = "gemini-2.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"


def encode_image_to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def normalizar_ano(ano_str: str) -> str:
    import re
    if not ano_str:
        return ano_str
    def repl(m):
        n = int(m.group(1))
        return f"20{m.group(1)}" if n <= 30 else f"19{m.group(1)}"
    return re.sub(r"\b(\d{2})\b", repl, ano_str)


def extract_text(result: dict) -> str:
    """Junta todos os pedaços de texto da resposta do Gemini."""
    try:
        parts = result["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts).strip()
    except (KeyError, IndexError):
        return ""


async def call_gemini(contents: list, tools: list = None, max_tokens: int = 2000) -> dict:
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": contents,
        "generationConfig": {"maxOutputTokens": max_tokens},
    }
    if tools:
        payload["tools"] = tools

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        return response.json()


@app.get("/health")
async def health():
    return {"status": "ok", "service": "Catálogo de Peças API"}


@app.post("/identify-part-by-photo")
async def identify_part_by_photo(file: UploadFile = File(...)):
    try:
        image_data = await file.read()
        b64_image = encode_image_to_base64(image_data)
        mime_type = file.content_type or "image/jpeg"

        prompt = """Você é um especialista em identificação de peças automotivas (motor, freio, suspensão, elétrica, etc). Olhe a foto e identifique a peça com o máximo de precisão possível.

Responda SOMENTE com um JSON válido, sem markdown, sem crases, exatamente neste formato:
{"nome":"nome comum da peça","categoria":"categoria geral (ex: motor, freio, suspensão, elétrica, arrefecimento, transmissão)","codigos_oem_provaveis":["código 1","código 2"],"aplicacoes_provaveis":["Marca Modelo Ano-Ano - observação"],"condicao_aparente":"nova, usada ou recondicionada","observacoes":"detalhes úteis, sinais de desgaste, cuidados","confianca":"alta, média ou baixa"}

Se não conseguir identificar com certeza, ainda assim dê o melhor palpite possível e marque confianca como baixa."""

        contents = [
            {
                "role": "user",
                "parts": [
                    {"inline_data": {"mime_type": mime_type, "data": b64_image}},
                    {"text": prompt},
                ],
            }
        ]

        result = await call_gemini(contents, max_tokens=1000)
        text_content = extract_text(result)

        if not text_content:
            raise ValueError("Nenhum texto retornado pela IA")

        clean_text = text_content.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)

        return {"success": True, "data": data}

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Resposta da IA não é JSON válido: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao identificar peça: {str(e)}")


@app.post("/search-part-by-vehicle")
async def search_part_by_vehicle(
    peca: str = Form(...),
    montadora: str = Form(...),
    modelo: str = Form(...),
    ano: str = Form(default=""),
    motor: str = Form(default=""),
):
    try:
        ano = normalizar_ano(ano.strip()) if ano else ano
        prompt = f"""Você é um especialista em peças automotivas e sabe pesquisar catálogos (OEM) e bases de dados de fornecedores na web para achar referências corretas.

Preciso de informações completas sobre esta peça, pesquise na web para confirmar:
- Peça: {peca}
- Montadora: {montadora}
- Modelo: {modelo}
- Ano/modelo: {ano or "não informado"}
- Motorização: {motor or "não informado"}

IMPORTANTE: Procura SOMENTE por informações verificáveis:
1. Códigos OEM da montadora (VW, Fiat, Ford, etc)
2. Números de referência reais de fornecedores (Bosch, Denso, Magneti Marelli, etc)
3. Preços de referência no mercado
4. Aplicações confirmadas em cada geração/motor

Responda por último SOMENTE com um JSON válido, sem markdown, sem crases, exatamente neste formato:
{{"nome":"nome comum da peça","categoria":"categoria geral (motor, freio, suspensão, elétrica, arrefecimento, transmissão)","codigos_oem":["código OEM 1","código OEM 2"],"codigos_fornecedores":["Bosch 123","Denso 456","Magneti Marelli 789"],"aplicacoes_provaveis":["Marca Modelo Ano-Ano Motor - observação"],"preco_referencia":"R$ 000,00 (opcional)","observacoes":"variações entre versões, compatibilidades, cuidados","confianca":"alta, média ou baixa"}}

Se não achar informação, ainda assim dê o melhor palpite e marque confianca como baixa. NUNCA invente um código apresentando como certeza alta se não confirmou na web."""

        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        tools = [{"google_search": {}}]

        result = await call_gemini(contents, tools=tools, max_tokens=2000)
        text_content = extract_text(result)

        if not text_content:
            raise ValueError("Nenhum texto retornado pela IA")

        clean_text = text_content.replace("```json", "").replace("```", "").strip()

        try:
            data = json.loads(clean_text)
        except json.JSONDecodeError:
            return {"success": False, "debug_raw_text": text_content}

        return {"success": True, "data": data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar peça: {str(e)}")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
