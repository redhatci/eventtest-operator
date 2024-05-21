# Design

At every reconciliation, the operator sends an event using the `EventsV1beta1Api` and re-triggers the reconciliation. 

The API `EventsV1beta1Api` is deprecated in OCP 4.12. In the eventest-operator, it's not used directly from the manifest but through the kubernetes Python package. We are going to simulate an upgrade from OCP 4.11 to OCP 4.13 and demostrated the problems with the application by running two demos:

- On OCP 4.13, showing how difficult it is to detect and debug the deprecated API inside the application since it will only manifest at runtime.
- On OCP 4.11, showcasing an Ansible role from the redhatci.ocp Ansible Galaxy collection, allowing us to detect possible problems in advance.

# Showcase the Deprecated API Detection Role on CRC

## Demo-1 on CRC 2.26.0-4.13.9

The goal is to demonstrate the issue occurring when the deprecated API manifests only at runtime after the OCP upgrade. This happens when the deprecated API is not in the manifest but within the software using a deprecated Kubernetes package (Golang, Python, etc.). In our case, it's a Python package `kubernetes==24.2.0` offering API `events.k8s.io/v1beta1`, which is removed in OCP 4.12 / K8s v1.25. The deprecation is showcased on [CRC 2.26.0-4.13.9](https://github.com/crc-org/crc/releases/tag/v2.26.0).

1. Install CRC 2.26.0-4.13.9 following the [official guide](https://crc.dev/crc/)

```
$ cd ~/Downloads
$ tar xvf crc-linux-amd64.tar.xz
$ mkdir -p ~/bin
$ cp ~/Downloads/crc-linux-*-amd64/crc ~/bin
$ export PATH=$PATH:$HOME/bin
$ echo 'export PATH=$PATH:$HOME/bin' >> ~/.bashrc

$ crc setup
```

2. Start CRC cluster and deploy the eventtest-operator on it

```
$ crc version
CRC version: 2.26.0+233df0
OpenShift version: 4.13.9
Podman version: 4.4.4

$ crc start  # to delete the cluster: crc delete

$ oc version
Client Version: 4.13.9
Kustomize Version: v4.5.7
Server Version: 4.13.9
Kubernetes Version: v1.26.6+6bf3f75

# login as kubeadmin
$ eval $(crc oc-env)
$ oc login -u kubeadmin https://api.crc.testing:6443

# deploy the operator
$ make deploy-all
-- snip --

# everything is deployed fine and the pod is running
$ make show
kubectl get crds | grep event
eventtests.eventtest.com                                          2024-05-17T16:33:21Z
kubectl get eventtests -n default
NAME           AGE
my-eventtest   5m2s
kubectl get pods
NAME                                 READY   STATUS    RESTARTS   AGE
eventtest-operator-87c7857b7-f87cb   1/1     Running   0          4m58s

# The problem is happening at runtime and it is difficult to debug
$ make logs
oc logs -l name=eventtest-operator --tail=100 -n default | grep 'Not Found' -B 2
TASK [eventtest : Trigger send_events.py] **************************************
task path: /opt/ansible/roles/eventtest/tasks/main.yml:2
-- snip --
\"status\":\"Failure\",\"message\":\"the server could not find the requested resource\",\"reason\":\"NotFound\",\"details\":{},\"code\":404}", "stdout_lines": ["Exception on creating event: (404)", "Reason: Not Found"
-- snip --
```

## Demo-2 on CRC 2.12.0-4.11.18

This demo shows how to ensure API validity before the OCP upgrade. We run the operator on [CRC 2.12.0-4.11.18](https://github.com/crc-org/crc/releases/tag/v2.12.0) where API `events.k8s.io/v1beta1` is not yet deprecated. We detect the soon-to-be deprecated situation using the [deprecated-api](https://github.com/redhatci/ansible-collection-redhatci-ocp/tree/main/roles/deprecated_api) role from redhat.ocp ansible-galaxy collection.

1. Start CRC cluster and deploy the eventtest-operator on it

```
$ crc-2.12 version
CRC version: 2.12.0+74565a6
OpenShift version: 4.11.18
Podman version: 4.2.0

$ crc-2.12 setup

$ crc-2.12 start

# login as kubeadmin
$ eval $(crc oc-env)
$ oc login -u kubeadmin https://api.crc.testing:6443

# deploy the operator
$ make deploy-all
-- snip --

$ make show
kubectl get crds | grep event
bmceventsubscriptions.metal3.io                                   2022-12-06T10:11:07Z
eventtests.eventtest.com                                          2024-05-17T22:32:06Z
kubectl get eventtests -n default
NAME           AGE
my-eventtest   30s
kubectl get pods
NAME                                 READY   STATUS    RESTARTS   AGE
eventtest-operator-978d77ddb-hh5cg   1/1     Running   0          28s

# eventtest-operator is running and sending events
$ oc get events | grep soon
21s         Normal    BreakingNews                                 eventtest/my-eventtest                    Rumors report messages sent to null. More updates expected soon. Stay tuned!
2s          Normal    BreakingNews                                 eventtest/my-eventtest                    Rumors report messages sent to null. More updates expected soon. Stay tuned!
12s         Normal    BreakingNews                                 eventtest/my-eventtest                    Rumors report messages sent to null. More updates expected soon. Stay tuned!
```

2. Detect soon-to-be-deprecated API using deprecated_api from ansible-galaxy redhatci.ocp collection 

```
$ ansible-galaxy collection install redhatci.ocp
$ cd deprecated_api
$ ansible-playbook -i inventory -v deprecated_api.yml
-- snip --
TASK [redhatci.ocp.deprecated_api : Compute OCP compatibility of the workload API for default] ******************************************************
ok: [127.0.0.1] => {"ansible_facts": {"ocp_compatibility": {"4.11": "compatible", "4.12": "events.v1beta1.events.k8s.io, podsecuritypolicies.v1beta1.policy", "4.13": "events.v1beta1.events.k8s.io, podsecuritypolicies.v1beta1.policy, prioritylevelconfigurations.v1beta1.flowcontrol.apiserver.k8s.io, flowschemas.v1beta1.flowcontrol.apiserver.k8s.io"}}, "changed": false}
-- snip --
```
