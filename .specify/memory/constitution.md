<!-- Sync Impact Report:
Version change: none → 1.0.0
List of modified principles: All new
Added sections: Core Principles, Requisitos Técnicos, Processo de Desenvolvimento, Governance
Removed sections: none
Templates requiring updates: plan-template.md (updated), spec-template.md (pending), tasks-template.md (pending)
Follow-up TODOs: none
-->
# BOT TELEGRAM PARA GESTÃO DE GRUPOS VIPS Constitution

## Core Principles

### Segurança de Pagamentos e Dados
Todos os pagamentos devem ser processados de forma segura utilizando a API do PIXGO com chaves protegidas. Dados sensíveis como API keys e endereços de carteira devem ser armazenados de forma criptografada e nunca expostos em logs ou código público.

### Controle de Acesso Estrito
Apenas administradores podem executar comandos administrativos no chat direto com o bot. Usuários comuns interagem apenas no grupo VIP, com acesso baseado em status de assinatura.

### Integração com APIs Externas
Utilizar a API do PIXGO para geração de pagamentos PIX e consulta de status. Suporte a endereço USDT Polygon fixo para pagamentos alternativos. Todas as integrações devem ser testadas e monitoradas.

### Comunicação e Logs
Manter logs detalhados de todas as ações do bot, incluindo entradas, banimentos e pagamentos. Comunicação com usuários deve ser clara e seguir regras definidas.

### Simplicidade e Escalabilidade
O código deve ser simples, seguindo princípios YAGNI. O sistema deve ser escalável para múltiplos grupos VIP, com renovação automática de assinaturas.

## Requisitos Técnicos

Utilizar Python ou Node.js para o bot Telegram. Integrar com Telegram Bot API usando token fornecido. Armazenar dados em banco de dados seguro (ex: PostgreSQL). Seguir boas práticas de segurança para APIs.

## Processo de Desenvolvimento

Desenvolver com testes automatizados. Revisão de código obrigatória. Deploy em produção após testes de integração.

## Governance

Constituição governa todas as práticas. Emendas requerem aprovação de administradores e documentação. Versão segue semver.

**Version**: 1.0.0 | **Ratified**: 2025-10-28 | **Last Amended**: 2025-10-28
