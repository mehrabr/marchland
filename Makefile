PYTHON ?= $(shell command -v python3 || echo python)

.PHONY: test battery receipts-check chronicle

test:
	$(PYTHON) -m pytest tests/ -v

battery:
	$(PYTHON) -m battery.ci

receipts-check:
	$(PYTHON) -m tools.receipts_grep

chronicle:
	$(PYTHON) -m clients.cli $(name) --seeds 12
