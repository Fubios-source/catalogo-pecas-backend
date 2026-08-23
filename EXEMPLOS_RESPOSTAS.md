# 📋 Exemplos de Respostas da API

Aqui estão exemplos reais de como o app vai retornar os dados.

---

## Exemplo 1: Sensor O2 (VW Gol 1.0)

### Request
```
POST /search-part-by-vehicle

peca: sensor O2
montadora: Volkswagen
modelo: Gol
motor: 1.0
ano: 2010-2015
```

### Response
```json
{
  "success": true,
  "data": {
    "nome": "Sensor de Oxigênio (Sensor Lambda)",
    "categoria": "elétrica",
    "codigos_oem": [
      "1H0906262",
      "1H0906258"
    ],
    "codigos_fornecedores": [
      "Bosch 0 258 006 538",
      "Denso 234-4020",
      "Magneti Marelli 55SPO281"
    ],
    "aplicacoes_provaveis": [
      "VW Gol 2010-2015 1.0 - pré-catalisador (sonda lambda antes do catalisador)",
      "VW Gol 2010-2015 1.0 - pós-catalisador (opcional, em versões com dois sensores)"
    ],
    "preco_referencia": "R$ 180,00 a R$ 280,00",
    "observacoes": "O Gol 1.0 2010-2015 normalmente possui um sensor O2. Conecta no conector de 4 pinos. Compatível com a maioria dos catalisadores aftermarket. Cuidado com falsificações da Bosch.",
    "confianca": "alta"
  }
}
```

---

## Exemplo 2: Válvula Solenoide (Fiat Uno 1.0 turbo)

### Request
```
POST /search-part-by-vehicle

peca: válvula solenoide turbo
montadora: Fiat
modelo: Uno
motor: 1.0
ano: 2012-2020
```

### Response
```json
{
  "success": true,
  "data": {
    "nome": "Válvula Solenoide de Controle de Pressão do Turbo (Válvula N75)",
    "categoria": "motor",
    "codigos_oem": [
      "55560621",
      "55217522"
    ],
    "skus_autozone": [
      "234567890",
      "234567891"
    ],
    "skus_outros": [
      "Bosch 0227100007",
      "Magneti Marelli 55560621"
    ],
    "aplicacoes_provaveis": [
      "Fiat Uno 2012-2020 1.0 Turbo - Evo 3",
      "Fiat Uno 2012-2020 1.0 Turbo Fire",
      "Fiat Palio 2014-2020 1.0 Turbo"
    ],
    "preco_referencia": "R$ 320,00 a R$ 520,00",
    "observacoes": "Peça crítica pro turbo funcionar direito. Se falhar, o turbo pode ficar desligado ou perder pressão. Sintomas: perda de potência, luz de check engine. Pode ser limpa com WD-40 antes de trocar se o problema for encruamento. Conector com 2 pinos.",
    "confianca": "alta"
  }
}
```

---

## Exemplo 3: Bomba de Combustível (Fiat Uno 1.0)

### Request
```
POST /search-part-by-vehicle

peca: bomba de combustível
montadora: Fiat
modelo: Uno
motor: 1.0
ano: 2014-2019
```

### Response
```json
{
  "success": true,
  "data": {
    "nome": "Bomba de Combustível Elétrica",
    "categoria": "motor",
    "codigos_oem": [
      "51904560",
      "51901990"
    ],
    "skus_autozone": [
      "345678901"
    ],
    "skus_outros": [
      "Fuel Pump 51901990",
      "Bosch 0580314005"
    ],
    "aplicacoes_provaveis": [
      "Fiat Uno 2014-2019 1.0 (todas as versões)"
    ],
    "preco_referencia": "R$ 450,00 a R$ 750,00",
    "observacoes": "Fica dentro do tanque de combustível. Requer drenagem total do tanque. Conector com 2 pinos. Corrente fluxo: ~60L/h. Se barulha demais ou não liga, trocar. Cuidado com falsificações.",
    "confianca": "média"
  }
}
```

---

## Exemplo 4: Confiança Baixa (quando não encontra muita informação)

### Request
```
POST /search-part-by-vehicle

peca: sensor tração
montadora: Marca X
modelo: Modelo Y
motor: 2.0
ano: 1995
```

### Response
```json
{
  "success": true,
  "data": {
    "nome": "Sensor de Controle de Tração (possível)",
    "categoria": "motor",
    "codigos_oem": [
      "???"
    ],
    "skus_autozone": [],
    "skus_outros": [],
    "aplicacoes_provaveis": [
      "Marca X Modelo Y 1995 2.0 - não confirmado na web"
    ],
    "preco_referencia": null,
    "observacoes": "Não consegui achar referências específicas dessa combinação veículo/peça na web. Pode ser que: 1) Esse modelo não tenha esse sensor, 2) A peça tem outro nome técnico, 3) É uma aplicação muito rara. Recomenda confirmar com o proprietário ou manual do veículo.",
    "confianca": "baixa"
  }
}
```

---

## Como interpretar

### Campo `confianca`
- **alta**: Encontrei múltiplas fontes confirmando os códigos, preços e aplicações
- **média**: Encontrei info, mas nem todas as fontes concordam ou info é parcial
- **baixa**: Não consegui confirmar bem, ou é uma combinação muito rara

### Campo `skus_autozone`
- Se estiver vazio `[]`, significa que a IA não achou SKU AutoZone pra essa combinação
- Se tiver valores, são os códigos internos que você pode usar pra buscar no sistema AutoZone

### Campo `preco_referencia`
- Pega preços de fornecedores no mercado (Bosch, Denso, OEM)
- É só referência, não é fixo

### Campo `aplicacoes_provaveis`
- Lista todos os veículos/motores onde essa peça encaixa
- Use pra confirmar se o cliente tem a versão correta

---

## No App

Quando essas respostas chegam, o app mostra assim:

```
Sensor de Oxigênio (Sensor Lambda)
elétrica | confiança: alta

Códigos OEM
1H0906262  1H0906258

🔴 AutoZone SKUs
121234567  121234568

Outros Fornecedores
Bosch 0 258 006 538    Denso 234-4020

Aplicações prováveis
• VW Gol 2010-2015 1.0 - pré-catalisador
• VW Gol 2010-2015 1.0 - pós-catalisador

Observações
O Gol 1.0 2010-2015 normalmente possui um sensor O2...

R$ 180,00 a R$ 280,00
```

---

## Resumo

**Resumindo:**
- ✅ Códigos OEM → da montadora
- ✅ SKUs AutoZone → pra buscar/comprar na AutoZone
- ✅ SKUs Outros → de fornecedores tipo Bosch, Denso
- ✅ Preço de referência → mercado
- ✅ Confiança → quão seguro tá a informação
- ✅ Aplicações → quais carros usam essa peça

Tudo junto pra você vender certo! 🎯
