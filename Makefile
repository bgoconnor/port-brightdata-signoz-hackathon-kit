PYTHON ?= python3
COLLECTOR_ID ?=

.PHONY: fixture scrape serve test clean

fixture:
	$(PYTHON) scrape.py --input fixtures/brightdata-papers.json

scrape:
	@test -n "$(COLLECTOR_ID)" || (echo "Usage: make scrape COLLECTOR_ID=c_..." && exit 2)
	$(PYTHON) scrape.py --collector-id "$(COLLECTOR_ID)"

serve: fixture
	$(PYTHON) -m http.server 8000

test:
	$(PYTHON) -m unittest discover -s tests -v

clean:
	rm -f data/papers.db data/papers.json artifacts/brightdata-papers.json
