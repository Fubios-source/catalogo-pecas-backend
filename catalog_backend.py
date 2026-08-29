"""
FastAPI Backend para Catálogo de Peças
- Proxy seguro pra API do Anthropic (evita CORS)
- Identifica peça por foto ou busca por veículo
- Deploy: Railway.app
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
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise RuntimeError("ANTHROPIC_API_KEY não configurada. Define como variável de ambiente.")

ANTHROPIC
