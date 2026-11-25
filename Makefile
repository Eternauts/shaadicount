CLUSTER=festive-hacks
IMAGE=shaadicount:dev

run:
	uvicorn app.main:app --reload --port 8000

build:
	docker build -t $(IMAGE) .

load: build
	kind load docker-image $(IMAGE) --name $(CLUSTER)

secret:
	kubectl create secret generic shaadicount-env --from-env-file=.env --dry-run=client -o yaml | kubectl apply -f -

deploy: load secret
	kubectl apply -f k8s/
	kubectl rollout restart deployment/shaadicount
	kubectl rollout status deployment/shaadicount

forward:
	kubectl port-forward svc/shaadicount 8000:80
