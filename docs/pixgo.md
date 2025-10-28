## PixGo API — Documentação resumida

Este documento organiza e apresenta de forma clara os principais pontos da API PixGo para integração de pagamentos via PIX.

## Sumário

- [Introdução](#introdução)
- [Base URL](#base-url)
- [Autenticação](#autenticação)
- [Endpoints principais](#endpoints-principais)
  - [Criar pagamento (POST /payment/create)](#criar-pagamento)
  - [Consultar status (GET /payment/{id}/status)](#consultar-status)
  - [Detalhes do pagamento (GET /payment/{id})](#detalhes-do-pagamento)
- [Regras de validação](#regras-de-validação)
- [Códigos de resposta & exemplos](#códigos-de-resposta--exemplos)
- [Status de pagamento](#status-de-pagamento)
- [Limites e Progressão de Níveis](#limites-e-progressão-de-níveis)
- [Exemplos de código](#exemplos-de-código)
- [Boas práticas e segurança](#boas-práticas-e-segurança)
- [Iniciando (Getting started)](#iniciando-getting-started)

---

## Introdução

PixGo oferece geração de cobranças PIX, acompanhamento em tempo real e notificações via webhooks. A comunicação é REST/JSON.

## Base URL

API base: https://pixgo.org/api/v1

## Autenticação

Todas as requisições devem incluir o cabeçalho `X-API-Key` com sua chave de API.

Exemplo de header:

```
X-API-Key: pk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

Mantenha a chave segura. Nunca publique em código cliente ou repositórios públicos.

## Endpoints principais

### Criar pagamento

- Método: POST
- Endpoint: `/api/v1/payment/create`
- Descrição: Cria uma nova cobrança PIX e retorna o payload do QR Code.

Parâmetros (JSON):

```json
{
  "amount": 25.50,
  "description": "Produto XYZ",
  "customer_name": "João Silva",
  "customer_cpf": "12345678901",
  "customer_email": "joao@exemplo.com",
  "customer_phone": "(11) 99999-9999",
  "customer_address": "Rua das Flores, 123, Centro, São Paulo, SP, 01234-567",
  "external_id": "pedido_123"
}
```

### Consultar status

- Método: GET
- Endpoint: `/api/v1/payment/{id}/status`
- Descrição: Retorna o status atual do pagamento.
- Observação: Rate limit — 1.000 requisições por 24h (contate o suporte para aumento).

### Detalhes do pagamento

- Método: GET
- Endpoint: `/api/v1/payment/{id}`
- Descrição: Retorna todos os dados do pagamento (inclui QR, endereço do cliente, timestamps, etc.).

## Regras de validação

- amount: obrigatório. Mínimo R$ 10,00. Máximo depende do seu nível de conta.
- customer_name: opcional, até 100 caracteres.
- customer_cpf: opcional — 11 dígitos (CPF) ou 14 dígitos (CNPJ).
- customer_email: opcional, formato válido, até 255 caracteres.
- customer_phone: opcional, até 20 caracteres (inclua DDD).
- customer_address: opcional, até 500 caracteres.
- external_id: opcional, até 50 caracteres.
- description: opcional, até 200 caracteres.

## Códigos de resposta & exemplos

Sucesso ao criar pagamento (HTTP 201):

```json
{
  "success": true,
  "data": {
    "payment_id": "dep_1234567890abcdef",
    "external_id": "pedido_123",
    "amount": 25.50,
    "status": "pending",
    "qr_code": "00020126580014BR.GOV.BCB.PIX...",
    "qr_image_url": "https://pixgo.org/qr/dep_1234567890abcdef.png",
    "expires_at": "2025-01-15T12:20:00",
    "created_at": "2025-01-15T12:00:00"
  }
}
```

Exemplo de erro por limite (HTTP 400):

```json
{
  "success": false,
  "error": "LIMIT_EXCEEDED",
  "message": "Valor excede seu limite atual de R$ 300,00",
  "current_limit": 300.00,
  "amount_requested": 500.00
}
```

Resposta de status (HTTP 200):

```json
{
  "success": true,
  "data": {
    "payment_id": "dep_1234567890abcdef",
    "external_id": "pedido_123",
    "amount": 25.50,
    "status": "completed",
    "customer_name": "João Silva",
    "customer_cpf": "12345678901",
    "customer_phone": "(11) 99999-9999",
    "created_at": "2025-01-15T12:00:00",
    "updated_at": "2025-01-15T12:15:30"
  }
}
```

## Status de pagamento

- pending — Aguardando pagamento
- completed — Pagamento confirmado
- expired — Expirado (padrão: 20 minutos)
- cancelled — Cancelado

## Limites e Progressão de Níveis

O sistema de limites é progressivo (7 níveis) baseado em histórico de pagamentos confirmados. Exemplo resumido:

- Nível 1 — Beginner: até R$ 299,99 confirmados — limite por QR: R$ 300,00
- Nível 2 — Bronze: R$ 300,00 a R$ 499,99 — limite por QR: R$ 500,00
- Nível 3 — Silver: R$ 500,00 a R$ 999,99 — limite por QR: R$ 1.000,00
- Nível 4 — Gold: R$ 1.000,00 a R$ 2.999,99 — limite por QR: R$ 1.500,00
- Nível 5 — Platinum: R$ 3.000,00 a R$ 4.999,99 — limite por QR: R$ 2.000,00
- Nível 6 — Diamond: R$ 5.000,00 a R$ 5.999,99 — limite por QR: R$ 2.500,00
- Nivel Máximo — Elite: R$ 6.000,00+ confirmados — limite por QR: R$ 3.000,00

Regras adicionais:

- Limite máximo por QR Code: R$ 3.000,00
- Limite diário por pagador (CPF/CNPJ): R$ 6.000,00
- Pagamentos confirmados (status "completed") contam para evolução de nível

## Exemplos de código

PHP (criar pagamento):

```php
$curl = curl_init();

curl_setopt_array($curl, [
    CURLOPT_URL => 'https://pixgo.org/api/v1/payment/create',
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST => true,
    CURLOPT_HTTPHEADER => [
        'Content-Type: application/json',
        'X-API-Key: pk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
    ],
    CURLOPT_POSTFIELDS => json_encode([
        'amount' => 25.50,
        'description' => 'Produto XYZ',
        'customer_name' => 'João Silva',
        'customer_cpf' => '12345678901',
        'customer_email' => 'joao@exemplo.com',
        'customer_phone' => '(11) 99999-9999',
        'customer_address' => 'Rua das Flores, 123, Centro, São Paulo, SP, 01234-567',
        'external_id' => 'pedido_123'
    ])
]);

$response = curl_exec($curl);
$httpCode = curl_getinfo($curl, CURLINFO_HTTP_CODE);
curl_close($curl);

if ($httpCode === 201) {
    $data = json_decode($response, true);
    echo "Pagamento criado: " . $data['data']['payment_id'] . "\n";
    echo "QR Code URL: " . $data['data']['qr_image_url'] . "\n";
} else {
    echo "Erro: " . $response . "\n";
}
```

JavaScript (Node.js + axios):

```js
const axios = require('axios');

async function createPayment() {
  try {
    const response = await axios.post('https://pixgo.org/api/v1/payment/create', {
      amount: 25.50,
      description: 'Produto XYZ',
      customer_name: 'João Silva',
      customer_cpf: '12345678901',
      customer_email: 'joao@exemplo.com',
      customer_phone: '(11) 99999-9999',
      customer_address: 'Rua das Flores, 123, Centro, São Paulo, SP, 01234-567',
      external_id: 'pedido_123'
    }, {
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': 'pk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
      }
    });

    console.log('Pagamento criado:', response.data.data.payment_id);
    console.log('QR Code URL:', response.data.data.qr_image_url);
  } catch (err) {
    console.error('Erro:', err.response?.data || err.message);
  }
}

createPayment();
```

## Boas práticas e segurança

- Nunca exponha a `X-API-Key` em código cliente ou públicos.
- Trate erros e códigos HTTP corretamente (400/401/403/500).
- Valide e sanitiza os campos enviados pelo cliente (CPF/CNPJ, e-mail, telefone).
- Considere armazenar `external_id` para mapear pagamentos com pedidos internos.

## Iniciando (Getting started)

1. Crie uma conta em pixgo.org
2. Valide sua carteira Liquid
3. Vá para a seção "Checkouts" e gere sua chave de API de produção
4. Integre o endpoint de criação de pagamento e salve `payment_id`

Importante: não existe ambiente de sandbox — todas as chaves são de produção. Use valores de teste com cuidado.

## Observações finais

- Recomenda-se consultar o status do pagamento periodicamente (ex.: a cada 30s) até `completed` ou `expired`.
- Pagamentos expiram em ~20 minutos por padrão.
- Para aumentos de limite ou suporte, contate a equipe via e-mail ou grupos indicados no dashboard.

---

Arquivo reorganizado: `doc/pixgo.md` — agora contém sumário, seções claras e exemplos formatados.
