# Regenerates every number in the README from scratch. Slow: hours on CPU (see README, "How to reproduce").
# Needs: .venv (uv venv --python 3.12; uv pip install -r requirements.txt), GITHUB_TOKEN in .env,
# node/npm for jscpd (npm install --prefix .cache/tools jscpd@5.4.3; .cache/tools/node_modules/.bin/jscpd --semantic-download).
PY = .venv/bin/python

.PHONY: test reproduce tables
test:
	$(PY) -m pytest -q

tables:
	$(PY) -m eval.report

reproduce: test
	$(PY) -m eval.retrieval_eval
	$(PY) -m eval.duplication_eval --jscpd --final
	$(PY) -m eval.agent_data
	$(PY) -m eval.agent_eval run
	$(PY) -m eval.agent_eval analyze
	$(PY) -m eval.report
