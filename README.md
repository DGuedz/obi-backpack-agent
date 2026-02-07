# OBIWORK | Institutional Trading Engineering

OBIWORK é a interface do OBI Agent focada em prova de volume, métricas reais de liquidez e transparência operacional para o hackathon. O produto apresenta dados, reputação e mecanismos de validação do agente em ambiente de produção.

## Produção

https://obi-backpack-agent.vercel.app/

## Foco no Hackathon

- Prova de volume e reputação do agente com métricas visíveis no front
- Demonstração de desempenho operacional com latência e uptime
- Pipeline de relatórios e evidências com endpoints dedicados
- Narrativa técnica alinhada à execução e transparência do OBI

## Rotas principais

- /
- /dashboard
- /marketplace
- /manifesto
- /apply
- /clones
- /access

## APIs

- /api/backpack/stats
- /api/reports/latest
- /api/chat
- /api/mentorship/events
- /api/payments/cielo

## Rodar localmente

```bash
npm install
npm run dev
```

Abra http://localhost:3000 no navegador.

## Deploy

Deploy recomendado via Vercel com Node 20.x.
