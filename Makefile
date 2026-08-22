PYTHON ?= python3
.PHONY: fixture scrape serve test clean

fixture:
	$(PYTHON) -m brightdata.scrape --input brightdata/fixtures/brightdata-papers.json

scrape:
	@set -a; \
	if [ -f .env ]; then . ./.env; fi; \
	set +a; \
	cd src/backend && $(PYTHON) manage.py scrape_papers

serve: fixture
	$(PYTHON) -m http.server 8000

test:
	$(PYTHON) -m unittest discover -s brightdata/tests -v

clean:
	rm -f data/papers.db data/papers.json artifacts/brightdata-papers.json
