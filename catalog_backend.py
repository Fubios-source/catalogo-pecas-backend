from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import httpx
import base64
import os
import json

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
                            "text": """Analise esta foto de uma peça automotiva. Retorne APENAS um JSON válido (sem markdown, sem explicação) com esta estrutura:
{
    "nome": "Nome da peça",
    "categoria": "elétrica/mecânica/hidráulica/etc",
    "codigos_oem_provaveis": ["código1", "código2"],
    "aplicacoes_provaveis": ["aplicação1", "aplicação2"],
    "confianca": "alta/média/baixa",
    "observacoes": "observações relevantes"
}"""
                        }
                    ],
                }
            ],
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(OPENROUTER_API_URL, json=payload, headers=headers)
            
        if response.status_code != 200:
            return {"success": False, "error": f"OpenRouter error: {response.text}"}
        
        result = response.json()
        text_content = result["content"][0]["text"]
        data = json.loads(text_content)
        
        return {
            "success": True,
            "data": {
                "nome": data.get("nome"),
                "categoria": data.get("categoria"),
                "codigos_oem_provaveis": data.get("codigos_oem_provaveis", []),
                "aplicacoes_provaveis": data.get("aplicacoes_provaveis", []),
                "confianca": data.get("confianca"),
                "observacoes": data.get("observacoes"),
            }
        }
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
        query = f"Buscar peça automotiva: {peca} para {montadora} {modelo}"
        if ano:
            query += f" ({ano})"
        if motor:
            query += f" motor {motor}"
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": "anthropic/claude-3.5-sonnet",
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user",
                    "content": f"""{query}

Retorne APENAS um JSON válido (sem markdown, sem explicação) com esta estrutura:
{{
    "nome": "Nome exato da peça",
    "categoria": "elétrica/mecânica/hidráulica/etc",
    "codigos_oem": ["código OEM verificado"],
    "codigos_fornecedores": ["Bosch XXX", "Denso YYY"],
    "aplicacoes_provaveis": ["aplicação 1", "aplicação 2"],
    "preco_referencia": "R$ XXX a R$ YYY",
    "confianca": "alta/média/baixa",
    "observacoes": "observações"
}}"""
                }
            ],
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(OPENROUTER_API_URL, json=payload, headers=headers)
        
        if response.status_code != 200:
            return {"success": False, "error": f"OpenRouter error: {response.text}"}
        
        result = response.json()
        text_content = result["content"][0]["text"]
        data = json.loads(text_content)
        
        return {
            "success": True,
            "data": {
                "nome": data.get("nome"),
                "categoria": data.get("categoria"),
                "codigos_oem": data.get("codigos_oem", []),
                "codigos_fornecedores": data.get("codigos_fornecedores", []),
                "aplicacoes_provaveis": data.get("aplicacoes_provaveis", []),
                "preco_referencia": data.get("preco_referencia"),
                "confianca": data.get("confianca"),
                "observacoes": data.get("observacoes"),
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)