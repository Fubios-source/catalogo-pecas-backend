from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HTML_CONTENT = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>BANCADA</title>
    <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <style>
        * { box-sizing: border-box; }
        body { margin: 0; font-family: Arial; background: #14161A; color: #fff; padding: 20px; }
        .container { max-width: 700px; margin: 0 auto; background: #1a1d23; padding: 30px; border-radius: 12px; }
        h1 { text-align: center; color: #FFB627; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; color: #FFB627; }
        input { width: 100%; padding: 10px; border: 2px solid #333; border-radius: 6px; background: #222; color: #fff; }
        button { width: 100%; padding: 12px; margin-top: 20px; background: #FFB627; color: #000; border: none; cursor: pointer; font-weight: bold; border-radius: 6px; }
        button:disabled { background: #666; }
        .result { border: 2px solid #FFB627; padding: 20px; margin-top: 30px; border-radius: 8px; background: #1f2229; }
        .error { color: #FF6B6B; background: #2a1a1a; padding: 15px; border-radius: 6px; margin-top: 20px; }
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
            const [error, setError] = React.useState("");

            const buscar = async () => {
                setLoading(true);
                setError("");
                setResult(null);

                try {
                    const formData = new FormData();
                    formData.append("peca", peca);
                    formData.append("montadora", montadora);
                    formData.append("modelo", modelo);
                    if (ano) formData.append("ano", ano);
                    if (motor) formData.append("motor", motor);

                    const response = await fetch("/search-part-by-vehicle", {
                        method: "POST",
                        body: formData,
                    });

                    const json = await response.json();
                    if (json.success && json.data) {
                        setResult(json.data);
                    } else {
                        setError("Erro na busca");
                    }
                } catch (err) {
                    setError("Erro: " + err.message);
                } finally {
                    setLoading(false);
                }
            };

            return (
                <div className="container">
                    <h1>🔧 BANCADA</h1>
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
                        <label>Peça:</label>
                        <input value={peca} onChange={e => setPeca(e.target.value)} />
                    </div>
                    {error && <div className="error">❌ {error}</div>}
                    <button onClick={buscar} disabled={loading}>
                        {loading ? "Buscando..." : "🔍 Buscar"}
                    </button>
                    {result && (
                        <div className="result">
                            <h2>✅ {result.nome}</h2>
                            <p><strong>Categoria:</strong> {result.categoria}</p>
                            <p><strong>Preço:</strong> {result.preco_referencia}</p>
                            <p><strong>Códigos OEM:</strong></p>
                            <ul>{result.codigos_oem.map((c, i) => <li key={i}>{c}</li>)}</ul>
                        </div>
                    )}
                </div>
            );
        }
        ReactDOM.render(<App />, document.getElementById("root"));
    </script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTML_CONTENT

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
    return {
        "success": True,
        "data": {
            "nome": f"Sensor O2 {montadora} {modelo}",
            "categoria": "Elétrica",
            "codigos_oem": ["1H0906262", "06A906262A"],
            "codigos_fornecedores": ["Bosch 0258006538"],
            "preco_referencia": "R$ 150-250",
            "confianca": "alta"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)