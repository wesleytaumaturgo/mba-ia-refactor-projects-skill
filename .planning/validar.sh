#!/bin/bash
# Uso: ./.planning/validar.sh <projeto> [SEVERIDADE]
PROJ="$1"; FILTRO="${2:-}"
awk '
/^### \[/ { sev=$0; sub(/^### \[/,"",sev); sub(/\].*/,"",sev)
            id=$0;  sub(/^### \[[A-Z]+\] /,"",id); sub(/ —.*/,"",id) }
/^- \*\*Arquivo:\*\*/ { ref=$0; sub(/^[^`]*`/,"",ref); sub(/`.*/,"",ref)
            print sev"|"id"|"ref }
' ".planning/analise-manual/$PROJ.md" | while IFS='|' read -r sev id ref; do
  [ -n "$FILTRO" ] && [ "$sev" != "$FILTRO" ] && continue
  file="${ref%%:*}"; lines="${ref##*:}"
  start="${lines%%-*}"; end="${lines##*-}"
  echo "──────────────────────────────────────────────"
  echo "[$sev] $id  →  $PROJ/$file:$lines"
  if [ -f "$PROJ/$file" ]; then
    awk -v s="$start" -v e="$end" 'NR>=s && NR<=e {printf "  %5d | %s\n", NR, $0}' "$PROJ/$file"
  else
    echo "  ❌ ARQUIVO NÃO EXISTE"
  fi
done
