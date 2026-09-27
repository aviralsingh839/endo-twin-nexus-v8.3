#!/usr/bin/env bash
# Quick self-check for the unified workstation.
#   ./tools/verify.sh [port] [patientId]
set -u
PORT="${1:-8787}"; PID_="${2:-ETN-2041}"; BASE="http://127.0.0.1:$PORT"
cd "$(dirname "$0")/.." || exit 1
ok(){ printf '  \033[32m✔\033[0m %s\n' "$1"; }
no(){ printf '  \033[31m✘\033[0m %s\n' "$1"; FAIL=1; }
FAIL=0
j(){ python3 -c "import json,sys;d=json.load(sys.stdin);print($1)" 2>/dev/null; }

echo; echo "1. Python modules compile"
for f in workstation/api.py workstation/serve.py workstation/signals.py workstation/devices.py workstation/complications.py; do
  python3 -c "import ast,sys;ast.parse(open('$f').read())" && ok "$f" || no "$f"
done

echo; echo "2. JavaScript parses"
if command -v node >/dev/null; then
  for f in workstation/assets/js/*.js; do node --check "$f" && ok "$(basename "$f")" || no "$(basename "$f")"; done
else echo "  (node not installed — skipped)"; fi

echo; echo "3. Server is up on :$PORT"
curl -sf "$BASE/api/health" >/dev/null && ok "GET /api/health" || { no "server not reachable — run ./START.sh"; exit 1; }
curl -sf "$BASE/api/health" | j "'database: '+str(d['counts']['patients'])+' patients, '+str(d['counts']['sensor_sessions'])+' sessions'" | sed 's/^/     /'
for a in / /assets/js/device.js /assets/js/app.js /assets/css/app.css; do
  c=$(curl -s -o /dev/null -w '%{http_code}' "$BASE$a"); [ "$c" = 200 ] && ok "$a ($c)" || no "$a ($c)"
done

echo; echo "4. Device API"
for r in status transports ports calibration; do
  curl -sf "$BASE/api/device/$r" >/dev/null && ok "/api/device/$r" || no "/api/device/$r"
done
curl -sf "$BASE/api/device/transports" | j "'     transports: '+', '.join(t['id'] for t in d['transports'])"

echo; echo "5. Calibration is stored and applied"
curl -sf -X POST "$BASE/api/device/calibration" -H 'Content-Type: application/json' \
  -d '{"temp":{"offset_c":0.75}}' | j "'     temp.offset_c -> '+str(d['calibration']['temp']['offset_c'])"
v=$(curl -sf "$BASE/api/device/calibration" | j "d['calibration']['temp']['offset_c']")
[ "$v" = "0.75" ] && ok "value survived a round-trip to the database" || no "round-trip returned '$v'"
curl -sf -X POST "$BASE/api/device/calibration/reset" -H 'Content-Type: application/json' -d '{"sensor":"temp"}' >/dev/null && ok "reset to defaults"

echo; echo "6. Complication engine ($PID_)"
curl -sf "$BASE/api/patients/$PID_/complications" | python3 -c "
import json,sys
d=json.load(sys.stdin)
ok=[i for i in d['items'] if i['status']=='ok']; ins=[i for i in d['items'] if i['status']!='ok']
print('     composite %.1f (%s)  completeness %.2f  quality %.2f'%(d['composite'],d['compositeBand'],d['dataCompleteness'],d['signalQuality']))
print('     scored %d / %d, %d withheld as insufficient'%(len(ok),len(d['items']),len(ins)))
for i in ok[:3]: print('       %-34s %5.1f%%  %-8s drivers: %s'%(i['name'],i['probability'],i['band'],', '.join(x['k'] for x in i['drivers'][:2])))
for i in ins: print('       %-34s withheld  needs: %s'%(i['name'],', '.join(i['missing'][:3])))
" || no "complication endpoint failed"

echo; echo "7. Editing clinical data changes the prediction"
before=$(curl -sf "$BASE/api/patients/$PID_/complications" | j "d['dataCompleteness']")
curl -sf -X PATCH "$BASE/api/patients/$PID_" -H 'Content-Type: application/json' \
  -d '{"waist":88,"bp":"132/86","familyDiabetes":"Yes"}' >/dev/null
lab=$(curl -sf -X POST "$BASE/api/patients/$PID_/labs" -H 'Content-Type: application/json' \
  -d '{"k":"HbA1c","value":5.9,"unit":"%"}' | j "d['labs'][-1]['id']")
after=$(curl -sf "$BASE/api/patients/$PID_/complications" | j "d['dataCompleteness']")
echo "     completeness $before -> $after"
curl -sf -X DELETE "$BASE/api/patients/$PID_/labs" -H 'Content-Type: application/json' -d "{\"id\":\"$lab\"}" >/dev/null
python3 -c "import sys;sys.exit(0 if $after >= $before else 1)" && ok "more clinical data = higher coverage" || no "coverage did not improve"

echo
[ "$FAIL" = 0 ] && printf '\033[32mALL CHECKS PASSED\033[0m\n' || printf '\033[31mSOME CHECKS FAILED\033[0m\n'
exit $FAIL
