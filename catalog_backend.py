from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import httpx
import base64
import os
import json
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/messages"

def extract_json(text):
    """Extrai JSON de uma string"""
    text = text.strip()
    # Remove markdown
    if "```" in text:
        text = re.sub(r'^```json\n', '', text)
        text = re.sub(r'\n```$', '', text)
        text = re.sub(r'^```\n', '', text)
        text = re.sub(r'\n```$', '', text)
    return json.loads(text)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/search-part-by-vehicle")
async def search_part_by_vehicle(
    peca: str = Form(...),
    montadora: str = Form(...),
    modelo: str = Form(...),
    ano: str = Form(None),
    motor: str = Form(None),
):
    try:
        query = f"Buscar: {peca} para {montadora} {modelo}"
        if ano:
            query += f" ({ano})"
        if motor:
            query += f" motor {motor}"
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://catalogo-pecas-backend.onrender.com",
        }
        
        # Prompt mais detalhado
        prompt = f"""Você é um especialista em peças automotivas. 
        
Pesquise informações sobre: {peca}
Para veículo: {montadora} {modelo} {ano or 'qualquer ano'} {motor or 'qualquer motor'}

Retorne APENAS um JSON válido (sem markdown, sem explicação):
{{
    "nome": "Nome da peça",
    "categoria": "elétrica/mecânica/hidráulica/fluidos",
    "codigos_oem": ["código1", "código2"],
    "codigos_fornecedores": ["Bosch XXX", "Denso YYY"],
    "aplicacoes_provaveis": ["aplicação1"],
    "preco_referencia": "R$ XXX-YYY",
    "confianca": "alta",
    "observacoes": "observações relevantes"
}}

IMPORTANTE: Retorne SOMENTE JSON, nada mais."""
        
        payload = {
            "model": "anthropic/claude-3.5-sonnet",
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
        }
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(OPENROUTER_API_URL, json=payload, headers=headers)
        
        if response.status_code != 200:
            return {
                "success": False, 
                "error": f"Status {response.status_code}",
                "details": response.text
            }
        
        result = response.json()
        if not result.get("content"):
            return {"success": False, "error": "No content from API"}
        
        text_content = result["content"][0].get("text", "")
        
        # Tenta extrair JSON
        try:
            data = extract_json(text_content)
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": "JSON parse error",
                "raw_response": text_content[:500]
            }
        
        return {"success": True, "data": data}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)