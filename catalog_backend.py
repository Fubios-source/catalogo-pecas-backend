from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    """Retorna dados MOCK para testar"""
    try:
        # Dados de teste
        return {
            "success": True,
            "data": {
                "nome": f"Sensor O2 para {montadora} {modelo}",
                "categoria": "elétrica",
                "codigos_oem": ["1H0906262", "06A906262A"],
                "codigos_fornecedores": ["Bosch 0258006538", "Denso 234-4028"],
                "aplicacoes_provaveis": [f"{montadora} {modelo} {ano}"],
                "preco_referencia": "R$ 150-250",
                "confianca": "alta",
                "observacoes": "Sensor de oxigênio pré-catalisador. Compatível com motores 1.0-1.6L"
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)