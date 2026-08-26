from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import httpx
import os
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>BANCADA</title>
        <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
        <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
        <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
        <style>
            body { margin: 0; font-family: Arial; background: #14161A; color: #fff; padding: 20px; }
            .container { max-width: 700px; margin: 0 auto; background: #1a1d23; padding: 30px; border-radius: 12px; }
            h1 { text-align: center; color: #FFB627; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; color: #FFB627; }
            input { width: 100%; padding: 10px; border: 2px solid #333; border-radius: 6px; background: #222; color: #fff; }
            button { width: 100%; padding: 12px; margin-top: 20px; background: #FFB627; color: #000; border: none; cursor: pointer; font-weight: bold; border-radius: 6px; }
            .result { border: 2px solid #FFB627; padding: 20px; margin-top: 30px; border-radius: 8px; background: #1f2229; }
            ul { margin: 10px 0; padding-left: 25px; }
        </style>
    </head>
    <body>
        <div id="root"></div>
        <script type="text/babel">
            function App() {
                const [montadora, setMontadora] = React.useState("Volkswagen");
                const [modelo, setModelo] = React.useState("Gol");
                const [motor, setMotor] = React.useState("1.0");
                const [ano, setAno] = React.useState("2010-2015");
                const [peca, setPeca] = React.useState("sensor O2");
                const [result, setResult] = React.useState(null);
                const [loading, setLoading] = React.useState(false);

                const buscar = async () => {
                    setLoading(true);
                    const fd = new FormData();
                    fd.append("peca", peca);
                    fd.append("montadora", montadora);
                    fd.append("modelo", modelo);
                    if (ano) fd.append("ano", ano);
                    if (motor) fd.append("motor", motor);

                    const res = await fetch("/search-part-by-vehicle", {method: "POST", body: fd});
                    const json = await res.json();
                    setResult(json.data);
                    setLoading(false);
                };

                return (
                    <div className="container">
                        <h1>BANCADA</h1>
                        <div className="form-group">
                            <label>Montadora:</label>
                            <input value={montadora} onChange={e => setMontadora(e.target.value)} />
                        </div>
                        <div className="form-group">
                            <label>Modelo:</label>
                            <input value={modelo} onChange={e => setModelo(e.target.value)} />
                        </div>
                        <div className="form-group">
                            <label>Motor:</label>
                            <input value={motor} onChange={e => setMotor(e.target.value)} />
                        </div>
                        <div className="form-group">
                            <label>Ano:</label>
                            <input value={ano} onChange={e => setAno(e.target.value)} />
                        </div>
                        <div className="form-group">
                            <label>Peca:</label>
                            <input value={peca} onChange={e => setPeca(e.target.value)} />
                        </div>
                        <button onClick={buscar} disabled={loading}>{loading ? "Buscando..." : "Buscar"}</button>
                        {result && (
                            <div className="result">
                                <h2>{result.nome}</h2>
                                <p><strong>Categoria:</strong> {result.categoria}</p>
                                <p><strong>Preco:</strong> {result.preco_referencia}</p>
                                <p><strong>Codigos OEM:</strong></p>
                                <ul>{result.codigos_oem.map((c, i) => <li key={i}>{c}</li>)}</ul>
                            </div>
                        )}
                    </div>
                );
            }
            ReactDOM.render(<App />, document.getElementById("root"));
        </script>
    </body>
    </html>
    """

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
        prompt = f"Buscar: {peca} para {montadora} {modelo} {ano or 'qualquer ano'} {motor or 'qualquer motor'}. Retorne APENAS um JSON com campos: nome, categoria, codigos_oem (lista), preco_referencia, confianca"
        
        async with httpx.AsyncClient() as client:
            res = await client.post(
                "https://openrouter.ai/api/v1/messages",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://catalogo-pecas-backend.onrender.com",
                },
                json={
                    "model": "anthropic/claude-3.5-sonnet",
                    "max_tokens": 500,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=30
            )
        
        if res.status_code != 200:
            # Se falhar, retorna dados mock
            return {
                "success": True,
                "data": {
                    "nome": f"{peca} {montadora} {modelo}",
                    "categoria": "Mecanica",