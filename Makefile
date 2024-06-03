IMAGE_NAME := quay.io/tkrishtop/eventtest-operator:latest
NAMESPACE := default

all:
	podman build -t $(IMAGE_NAME) .
	podman push $(IMAGE_NAME)
	kubectl apply -f deploy/crds/eventtest_v1_eventtest_crd.yaml
	kubectl apply -f deploy/crds/eventtest_v1_eventtest_cr.yaml
	kubectl apply -f rbac/eventtest_operator_service_account.yaml
	kubectl apply -f deploy/operator.yaml

deploy-all:
	kubectl apply -f deploy/crds/eventtest_v1_eventtest_crd.yaml
	kubectl apply -f deploy/crds/eventtest_v1_eventtest_cr.yaml
	kubectl apply -f rbac/eventtest_operator_service_account.yaml
	kubectl apply -f deploy/operator.yaml

show:
	- kubectl get crds | grep eventtest
	- kubectl get eventtests -n $(NAMESPACE)
	- kubectl get pods

logs:
	kubectl logs -l name=eventtest-operator --tail=100 -n $(NAMESPACE) | grep 'Not Found' -B 2

remove-all: 
	- kubectl delete -f deploy/operator.yaml
	- kubectl delete -f rbac/eventtest_operator_service_account.yaml
	- kubectl delete -f deploy/crds/eventtest_v1_eventtest_cr.yaml
	- kubectl delete -f deploy/crds/eventtest_v1_eventtest_crd.yaml

.PHONY: all deploy-all remove-all show logs
