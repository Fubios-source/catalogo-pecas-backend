from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import httpx
import base64
import os
import json
import re

app = FastAPI()

# CORS
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
    """Extrai JSON de uma string, removendo markdown se necessário"""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r'^```[a-zA-Z]*\n', '', text)
        text = re.sub(r'\n```$', '', text)
    return json.loads(text)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/identify-part-by-photo")
async def identify_part(file: UploadFile = File(...)):
    try:
        content = await file.read()
        base64_image = base64.b64encode(content).decode()
        media_type = file.content_type or "image/jpeg"
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://catalogo-pecas-backend.onrender.com",
        }
        
        payload = {
            "model": "anthropic/claude-3.5-sonnet",
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": base64_image,
                            },
                        },
                        {
                            "type": "text",
                            "text": """Analise esta foto de uma peça automotiva. Retorne APENAS JSON (sem markdown):
{
    "nome": "Nome da peça",
    "categoria": "elétrica",
    "codigos_oem_provaveis": ["código1"],
    "aplicacoes_provaveis": ["aplicação1"],
    "confianca": "alta",
    "observacoes": "observações"
}"""
                        }
                    ],
                }
            ],
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(OPENROUTER_API_URL, json=payload, headers=headers, timeout=60)
            
        if response.status_code != 200:
            return {"success": False, "error": f"Status {response.status_code}: {response.text}"}
        
        result = response.json()
        if not result.get("content"):
            return {"success": False, "error": "No content from API"}
        
        text_content = result["content"][0].get("text", "")
        data = extract_json(text_content)
        
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}

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
        
        payload = {
            "model": "anthropic/claude-3.5-sonnet",
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user",
                    "content": f"""{query}

Retorne APENAS JSON (sem markdown):
{{
    "nome": "Sensor de Oxigênio",
    "categoria": "elétrica",
    "codigos_oem": ["1H0906262"],
    "codigos_fornecedores": ["Bosch 0258006538"],
    "aplicacoes_provaveis": ["VW Gol 1.0"],
    "preco_referencia": "R$ 150-250",
    "confianca": "alta",
    "observacoes": "verificado"
}}"""
                }
            ],
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(OPENROUTER_API_URL, json=payload, headers=headers, timeout=60)
        
        if response.status_code != 200:
            return {"success": False, "error": f"Status {response.status_code}: {response.text}"}
        
        result = response.json()
        if not result.get("content"):
            return {"success": False, "error": "No content from API"}
        
        text_content = result["content"][0].get("text", "")
        data = extract_json(text_content)
        
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)