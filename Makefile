MACHINE=$(shell uname -m)
IMAGE=pi-k8s-fitches-chore-event-daemon
VERSION=0.5
TAG="$(VERSION)-$(MACHINE)"
ACCOUNT=gaf3
NAMESPACE=fitches
VARIABLES=-e REDIS_HOST='host.docker.internal' -e REDIS_PORT='6379' -e REDIS_SPEECH_CHANNEL='speech' -e REDIS_EVENT_CHANNEL='event' -e SLEEP='1'
VOLUMES=-v ${PWD}/lib/:/opt/pi-k8s/lib/ -v ${PWD}/test/:/opt/pi-k8s/test/ -v ${PWD}/bin/:/opt/pi-k8s/bin/

ifeq ($(MACHINE),armv7l)
BASE=resin/raspberry-pi-alpine-python:3.6.1
else
BASE=python:3.6-alpine3.8
endif

.PHONY: build shell test run push create update delete create-dev update-dev delete-dev

build:
	docker build . --build-arg BASE=$(BASE) -t $(ACCOUNT)/$(IMAGE):$(TAG)

shell:
	docker run -it $(VARIABLES) $(VOLUMES) $(ACCOUNT)/$(IMAGE):$(TAG) sh

test:
	docker run -it $(VARIABLES) $(VOLUMES) $(ACCOUNT)/$(IMAGE):$(TAG) sh -c "coverage run -m unittest discover -v test && coverage report -m --include lib/*.py"

run:
	docker run -it $(VARIABLES) $(VOLUMES) --rm -h $(IMAGE) $(ACCOUNT)/$(IMAGE):$(TAG)

push: build
	docker push $(ACCOUNT)/$(IMAGE):$(TAG)

create:
	kubectl --context=pi-k8s create -f k8s/pi-k8s.yaml

update:
	kubectl --context=pi-k8s replace -f k8s/pi-k8s.yaml

delete:
	kubectl --context=pi-k8s delete -f k8s/pi-k8s.yaml

create-dev:
	kubectl --context=minikube create -f k8s/minikube.yaml

update-dev:
	kubectl --context=minikube replace -f k8s/minikube.yaml

delete-dev:
	kubectl --context=minikube delete -f k8s/minikube.yaml
