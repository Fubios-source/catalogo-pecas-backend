# 🧪 Teste do Catálogo de Peças com SKUs AutoZone

Antes de replicar pra verdade, vamos fazer um teste rápido local. Siga passo a passo.

---

## Passo 1: Instalar dependências do backend

```bash
pip install fastapi uvicorn httpx python-multipart --break-system-packages
```

---

## Passo 2: Configurar a chave API

```bash
# No terminal, exporta a variável
export ANTHROPIC_API_KEY="sk-ant-..."
```

Substitui `sk-ant-...` pela sua chave real do Anthropic.

---

## Passo 3: Rodar o backend

```bash
python catalog_backend.py
```

Se tudo funcionar, você vai ver algo como:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Deixa esse terminal aberto** enquanto faz o teste.

---

## Passo 4: Testar o backend (terminal novo)

Em outro terminal, testa se o backend tá respondendo:

```bash
curl http://localhost:8000/health
```

Deve retornar:
```json
{"status":"ok","service":"Catálogo de Peças API"}
```

---

## Passo 5: Teste prático com busca por veículo

Agora vamos fazer um teste de verdade. Abra o artifact React `catalogo-pecas.jsx` no navegador.

### Teste 1: Buscar sensor O2 pra um Gol 1.0

Na aba **"Por veículo"**, preenche assim:

```
Montadora: Volkswagen
Modelo: Gol
Motor: 1.0
Ano: 2010-2015
Peça: sensor O2
```

Clica em "Buscar peça".

**O que esperar:**
- A IA vai pesquisar na web
- Vai retornar:
  - ✅ Nome correto: "Sensor de Oxigênio" ou "Sensor Lambda"
  - ✅ Categoria: "elétrica"
  - ✅ Códigos OEM: tipo "1H0906262" (VW)
  - ✅ Códigos de Fornecedores: tipo "Bosch 0 258 006 538", "Denso 234-4020"
  - ✅ Aplicações: "VW Gol 2010-2015 1.0 - sensor pré-catalisador"
  - ✅ Nível de confiança: "alta" ou "média"

Se tudo aparecer com códigos VERIFICADOS, o teste passou! ✅

---

### Teste 2: Buscar válvula solenoide pra Fiat Uno 1.0

Na aba **"Por veículo"**, preenche assim:

```
Montadora: Fiat
Modelo: Uno
Motor: 1.0
Ano: 2012-2020
Peça: válvula solenoide turbo
```

**O que esperar:**
- Códigos OEM (se tiver turbo)
- SKUs AutoZone específicos
- Confirmação se é N75 ou N108

---

### Teste 3: Identificar pela foto

Se quiser testar também a identificação por foto:

1. Va pra aba **"Foto"**
2. Tira/escolhe uma foto de uma peça
3. Clica "Tirar/escolher foto"

A IA vai identificar. Mas nesse teste, não vai trazer SKU AutoZone (foto não tem dados suficientes).

---

## Passo 6: Adicionar ao catálogo

Depois que a busca retornar os dados:

1. Coloca um preço (opcional): "R$ 250,00"
2. Clica "Adicionar ao catálogo"

Se der "Salvo com sucesso" (ou similar), tudo funcionou! ✅

---

## Passo 7: Verificar no catálogo

Vai pra aba **"Catálogo"** e procura a peça que acabou de adicionar.

Deve aparecer um card mostrando:
- Foto (se adicionou via foto)
- Nome da peça
- **OEM: 1H0906262** (código OEM em amarelo)
- **AZ: 121234567** (SKU AutoZone em vermelho) ← NOVO
- Preço
- Botão WhatsApp pra chamar

---

## Se der erro

### Erro: "Method Not Allowed"
→ Backend não tá rodando. Volta pra Passo 3 e certifica que rodou:
```bash
python catalog_backend.py
```

### Erro: "invalid_request_error" / "invalid API key"
→ A chave ANTHROPIC_API_KEY não tá configurada corretamente:
```bash
echo $ANTHROPIC_API_KEY
# Deve exibir algo que começa com "sk-ant-"
```

### Erro: "Resposta da IA não é JSON válido"
→ A IA retornou um texto que não é JSON. Tenta novamente — às vezes a web search demora mais.

### Erro: "CORS" no navegador
→ Certifica que o backend tá rodando localmente. Tenta recarregar a página.

---

## Pronto! ✅

Se chegou aqui sem erros, seu app tá funcionando com:
- ✅ Identificação por foto
- ✅ Busca por veículo com web search
- ✅ SKUs AutoZone
- ✅ Catálogo compartilhado
- ✅ WhatsApp integrado

---

## Próximo passo: Deploy no Railway

Quando tiver pronto:
1. Copia os arquivos pra um repo GitHub
2. Conecta ao Railway
3. Configura variável ANTHROPIC_API_KEY
4. Faz deploy

Segue as instruções em `DEPLOY_INSTRUCTIONS.md`.

---

## Dúvidas ou problemas?

Se der ruim, manda:
1. A mensagem de erro exata
2. Qual passo tá falhando
3. Uma screenshot se possível

Vai ficar certo! 🚀
