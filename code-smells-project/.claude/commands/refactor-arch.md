---
description: Audita e refatora o projeto atual para MVC em 3 fases, com gate humano antes de qualquer escrita em código
---

Execute a skill **`refactor-arch`** sobre o diretório de trabalho atual.

Invoque-a agora com a ferramenta Skill (`skill: refactor-arch`), leia o `SKILL.md` por inteiro
e siga as três fases na ordem definida lá, sem improvisar etapas intermediárias.

Lembretes de execução, todos já normativos no `SKILL.md` — repetidos aqui porque são os pontos
em que a execução mais costuma desviar:

1. **Pré-condições primeiro.** Sem repositório VCS com working tree limpo, reporte e aborte.
   Registre o SHA do commit de baseline no registro de ondas, e resolva `REPORT_PATH` e
   `BASELINE_PATH` **ancorados na raiz do repositório** (`git rev-parse --show-toplevel`), não
   no diretório de trabalho. Imprima os dois caminhos absolutos antes de gravar.
2. **Fases 1 e 2 não tocam código.** As únicas escritas permitidas antes do gate são o baseline
   (`BASELINE_PATH`, fim da Fase 1) e o relatório (`REPORT_PATH`, Fase 2) — ambos artefato
   aditivo, ambos sob a raiz do repositório.
3. **Pare no gate.** Ao fim da Fase 2, apresente findings, plano por onda — onda sem TR atribuído
   é declarada vazia ali mesmo, e é o plano que a define —, breaking changes e
   itens NEEDS-DECISION, pergunte `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`
   e **aguarde resposta explícita**. Silêncio não é aprovação; resposta parcial exige replanejar
   e reapresentar o gate.
4. **Fase 3 em ondas.** Boot após cada TR — dois consertos sem sucesso tornam a onda vermelha
   com o TR já isolado. Smoke test completo ao fim de cada onda; verde é `M/M`, fração parcial
   não é verde. Commit só na onda verde, com a contagem na mensagem, e anote o SHA devolvido no
   registro de ondas. Onda vermelha → `git reset --hard` na **última linha verde do registro**
   (o baseline só é esse alvo quando é a Onda 1 que falha), e pare, reportando.

5. **Argumentos.** Se o usuário passou algo ao comando, interprete assim e confirme o
   entendimento antes da Fase 1:
   - **caminho terminado em `.md`** → é o `REPORT_PATH` do relatório da Fase 2, e vence o default
     das pré-condições. Caminho relativo é resolvido contra a raiz do repositório.
   - **qualquer outra coisa** → escopo adicional (por exemplo, um subdiretório-alvo).

   $ARGUMENTS
