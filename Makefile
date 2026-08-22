PYTHON ?= python3
COLLECTOR_ID ?=
ARXIV_ID ?=

.PHONY: fixture scrape enrich serve test clean

fixture:
	$(PYTHON) -m brightdata.scrape --input brightdata/fixtures/brightdata-papers.json

scrape:
	@test -n "$(COLLECTOR_ID)" || (echo "Usage: make scrape COLLECTOR_ID=c_..." && exit 2)
	@set -a; \
	if [ -f .env ]; then . ./.env; fi; \
	set +a; \
	$(PYTHON) -m brightdata.scrape --collector-id "$(COLLECTOR_ID)"

enrich:
	@test -n "$(ARXIV_ID)" || (echo "Usage: make enrich ARXIV_ID=2608.12345" && exit 2)
	@set -a; \
	if [ -f .env ]; then . ./.env; fi; \
	set +a; \
	cd src/backend && $(PYTHON) manage.py enrich_paper "$(ARXIV_ID)"

serve: fixture
	$(PYTHON) -m http.server 8000

test:
	$(PYTHON) -m unittest discover -s brightdata/tests -v

clean:
	rm -f data/papers.db data/papers.json artifacts/brightdata-papers.json
