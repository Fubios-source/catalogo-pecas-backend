"""
FastAPI Backend para Catálogo de Peças
- Proxy seguro pra API do OpenRouter (evita CORS)
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

# Permite requisições do seu app (ajusta o origin se necessário)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, restringe a teus domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lê a chave API das variáveis de ambiente
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY não configurada. Define como variável de ambiente.")

OPENROUTER_URL = "https://openrouter.ai/api/v1/messages"
MODEL = "anthropic/claude-sonnet-4.6"


def encode_image_to_base64(image_bytes: bytes) -> str:
    """Converte bytes da imagem pra base64."""
    return base64.b64encode(image_bytes).decode("utf-8")


def normalizar_ano(ano_str: str) -> str:
    """Converte ano de 2 digitos isolado pra 4 digitos (ex: 95 -> 1995, 00 -> 2000).
    Nao mexe em numeros de 4 digitos ja completos (ex: 2010, 2010-2015)."""
    import re
    if not ano_str:
        return ano_str
    def repl(m):
        n = int(m.group(1))
        return f"20{m.group(1)}" if n <= 30 else f"19{m.group(1)}"
    return re.sub(r"\b(\d{2})\b", repl, ano_str)


async def call_anthropic(messages: list, tools: list = None, max_tokens: int = 1000) -> dict:
    """
    Chama o Claude via OpenRouter, usando o endpoint compatível com o formato
    da Anthropic Messages API (backend-to-backend, evita CORS no navegador).
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://catalogo-pecas-backend.onrender.com",
        "X-Title": "BANCADA",
    }

    payload = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "messages": messages,
    }

    if tools:
        payload["tools"] = tools

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(OPENROUTER_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok", "service": "Catálogo de Peças API"}


@app.post("/identify-part-by-photo")
async def identify_part_by_photo(file: UploadFile = File(...)):
    """
    Identifica uma peça a partir de uma foto.
    
    - Upload a foto (jpeg, png)
    - Retorna: nome, categoria, códigos OEM, aplicações, observações, confiança
    """
    try:
        # Lê a imagem
        image_data = await file.read()
        b64_image = encode_image_to_base64(image_data)

        # Determina o MIME type
        mime_map = {
            "image/jpeg": "image/jpeg",
            "image/png": "image/png",
            "image/webp": "image/webp",
            "image/gif": "image/gif",
        }
        mime_type = mime_map.get(file.content_type, "image/jpeg")

        # Prompt pra identificação
        prompt = """Você é um especialista em identificação de peças automotivas (motor, freio, suspensão, elétrica, etc). Olhe a foto e identifique a peça com o máximo de precisão possível.

Responda SOMENTE com um JSON válido, sem markdown, sem crases, exatamente neste formato:
{"nome":"nome comum da peça","categoria":"categoria geral (ex: motor, freio, suspensão, elétrica, arrefecimento, transmissão)","codigos_oem_provaveis":["código 1","código 2"],"aplicacoes_provaveis":["Marca Modelo Ano-Ano - observação"],"condicao_aparente":"nova, usada ou recondicionada","observacoes":"detalhes úteis, sinais de desgaste, cuidados","confianca":"alta, média ou baixa"}

Se não conseguir identificar com certeza, ainda assim dê o melhor palpite possível e marque confianca como baixa."""

        # Chama Claude com visão
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": mime_type, "data": b64_image}},
                    {"type": "text", "text": prompt},
                ],
            }
        ]

        result = await call_anthropic(messages, max_tokens=1000)

        # Extrai o texto da resposta
        text_content = next(
            (block["text"] for block in result.get("content", []) if block.get("type") == "text"),
            None,
        )

        if not text_content:
            raise ValueError("Nenhum texto retornado pela IA")

        # Limpa markdown e parseia JSON
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
    """
    Busca uma peça pelo veículo (montadora, modelo, ano, motor).
    Pesquisa na web pra confirmar códigos e aplicações reais.
    
    Parâmetros (form data):
    - peca: nome da peça (ex: "válvula solenoide")
    - montadora: marca (ex: "Volkswagen")
    - modelo: modelo (ex: "Gol")
    - ano: período (ex: "2010-2015") [opcional]
    - motor: motorização (ex: "1.0", "1.6") [opcional]
    """
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

        messages = [{"role": "user", "content": prompt}]

        # Usa web search tool pra pesquisar (formato OpenRouter)
        tools = [{"type": "openrouter:web_search"}]

        result = await call_anthropic(messages, tools=tools, max_tokens=2000)

        # Extrai o último bloco de texto (após web search)
        text_blocks = [block["text"] for block in result.get("content", []) if block.get("type") == "text"]

        if not text_blocks:
            raise ValueError("Nenhum texto retornado pela IA")

        last_text = text_blocks[-1]

        # Limpa markdown e parseia JSON
        clean_text = last_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)

        return {"success": True, "data": data}

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Resposta da IA não é JSON válido: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar peça: {str(e)}")


@app.post("/process-request")
async def process_request(prompt: str = Form(...)):
    """
    Endpoint genérico pra processar qualquer requisição Claude.
    Retorna: conteúdo da resposta (lista de blocos com type e conteúdo)
    """
    try:
        messages = [{"role": "user", "content": prompt}]
        result = await call_anthropic(messages, max_tokens=2000)
        return {"success": True, "data": result.get("content", [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar: {str(e)}")


if __name__ == "__main__":
    # Pra rodar local: python catalog_backend.py
    # Depois acessa em http://localhost:8000
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
