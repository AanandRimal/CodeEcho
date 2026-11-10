#!/usr/bin/env bash
# Mini demo (n=4 tasks x 2 conditions x 2 reps; NOT a statistically meaningful result, see D34).
# Usage: bash eval/mcp_demo/run.sh   -> results/mcp_demo/raw/*.json (agent transcripts) and runs.tsv
set -u
ROOT=$(cd "$(dirname "$0")/../.." && pwd); OUT=$ROOT/results/mcp_demo; mkdir -p "$OUT/raw" /tmp/claude-1000/mcpdemo
PY=$ROOT/.venv/bin/python
declare -A TASK
TASK[words]="Create devtrust/extra_words.py with a function words(name: str) -> list[str] that returns the lowercase words of an identifier, handling both snake_case and camelCase (e.g. 'parseHTTPResponse_v2' style names). Keep it short."
TASK[mean_ci]="Create devtrust/extra_stats.py with a function mean_ci(values: list[float]) -> tuple[float, float, float] returning the mean and a 95% bootstrap confidence interval (mean, low, high), deterministic with a seed. Keep it short."
TASK[is_test]="Create devtrust/extra_paths.py with a function looks_like_test_file(filename: str) -> bool that returns True when a Python file name looks like a test file. Keep it short."
TASK[rr]="Create devtrust/extra_rank.py with a function first_hit_score(ranked: list, relevant: set) -> float returning 1/rank of the first relevant item in the ranked list (0.0 if none). Keep it short."
declare -A HELPER=([words]="tokenize" [mean_ci]="bootstrap_ci" [is_test]="_is_test_file" [rr]="reciprocal_rank")
declare -A FILE=([words]="extra_words" [mean_ci]="extra_stats" [is_test]="extra_paths" [rr]="extra_rank")
: > "$OUT/runs.tsv"; echo -e "task\tcondition\trep\treused\tcalled_tool\tturns" >> "$OUT/runs.tsv"
for rep in 1 2; do for t in words mean_ci is_test rr; do for cond in without with; do
  D=/tmp/claude-1000/mcpdemo/$t-$cond-$rep; rm -rf "$D"; mkdir -p "$D"
  git -C "$ROOT" archive HEAD | tar -x -C "$D"; rm -f "$D/CLAUDE.md" "$D/devtrust/mcp_server.py"; cp "$ROOT/devtrust/mcp_server.py" "$D/devtrust/"
  ln -s "$ROOT/.cache" "$D/.cache"
  cat > "$D/mcp.json" <<J
{"mcpServers":{"devtrust":{"command":"bash","args":["-c","cd $D && exec $PY -m devtrust.mcp_server"]}}}
J
  if [ $cond = with ]; then EXTRA=(--mcp-config "$D/mcp.json" --strict-mcp-config --allowedTools "Read,Grep,Glob,Write,Edit,mcp__devtrust__search_existing_functions,mcp__devtrust__review_diff")
  else EXTRA=(--allowedTools "Read,Grep,Glob,Write,Edit"); fi
  (cd "$D" && timeout 900 claude -p "${TASK[$t]}" --output-format json --permission-mode acceptEdits --max-turns 25 "${EXTRA[@]}" > "$OUT/raw/$t-$cond-$rep.json" 2>"$OUT/raw/$t-$cond-$rep.err")
  F=$D/devtrust/${FILE[$t]}.py
  reused=no; [ -f "$F" ] && grep -q "${HELPER[$t]}" "$F" && reused=yes
  called=no; grep -q "search_existing_functions" "$OUT/raw/$t-$cond-$rep.json" && called=yes
  turns=$(grep -o '"num_turns":[0-9]*' "$OUT/raw/$t-$cond-$rep.json" | head -1 | cut -d: -f2)
  cp "$F" "$OUT/raw/$t-$cond-$rep.py" 2>/dev/null
  echo -e "$t\t$cond\t$rep\t$reused\t$called\t$turns" >> "$OUT/runs.tsv"
done; done; done
echo DONE >> "$OUT/runs.tsv"
