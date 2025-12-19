up:
	docker-compose up -d

down:
	docker-compose down

producers:
	python -m src.ingestion.main

api:
	uvicorn src.api.main:app --reload --port 8080

dashboard:
	streamlit run dashboard/app.py

install:
	pip install -r requirements.txt
