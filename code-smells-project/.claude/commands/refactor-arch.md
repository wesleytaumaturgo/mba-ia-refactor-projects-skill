---
description: Audita e refatora o projeto atual para MVC em 3 fases, com gate humano antes de qualquer escrita em código
---

Execute a skill **`refactor-arch`** sobre o diretório de trabalho atual.

Invoque-a agora com a ferramenta Skill (`skill: refactor-arch`), leia o `SKILL.md` por inteiro
e siga as três fases na ordem definida lá, sem improvisar etapas intermediárias.

Lembretes de execução, todos já normativos no `SKILL.md` — repetidos aqui porque são os pontos
em que a execução mais costuma desviar:

1. **Pré-condições primeiro.** Sem repositório VCS com working tree limpo, reporte e aborte.
   Registre o SHA do commit de baseline antes de qualquer coisa.
2. **Fases 1 e 2 são read-only.** A única escrita permitida antes do gate é o relatório em
   `reports/audit-<projeto>.md`.
3. **Pare no gate.** Ao fim da Fase 2, apresente findings, plano em 4 ondas, breaking changes e
   itens NEEDS-DECISION, pergunte `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`
   e **aguarde resposta explícita**. Silêncio não é aprovação; resposta parcial exige replanejar
   e reapresentar o gate.
4. **Fase 3 em ondas.** Boot após cada TR; smoke test completo contra o baseline ao fim de cada
   onda; commit apenas na onda verde, com a contagem de endpoints verificados na mensagem; onda
   vermelha → `git reset --hard` ao último commit verde e pare, reportando.

Se o usuário passou argumentos ao comando, trate-os como escopo adicional (por exemplo, um
subdiretório-alvo) e confirme o entendimento antes da Fase 1: $ARGUMENTS
