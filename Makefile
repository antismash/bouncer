unit:
	pytest -v

coverage:
	pytest --cov=antismash_bouncer --cov-report=html --cov-report=term-missing
