#!/usr/bin/env python3

# Docs on events.k8s.io API: 
# current: https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/EventsV1Api.md
# deprecated: https://github.com/kubernetes-client/python/blob/release-24.0/kubernetes/docs/EventsV1beta1Api.md
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from kubernetes.config.config_exception import ConfigException
from datetime import datetime
import random, string, os

def send_event():
    try:
        config.load_kube_config()
    except ConfigException as e:
        print("Exception on loading config: %s\n" % e)
        return

    custom_api = client.CustomObjectsApi()
    try:
        cr = custom_api.get_namespaced_custom_object("eventtest.com", "v1", "default", "eventtests", "my-eventtest")
    except ApiException as e:
        print("Exception when calling CustomObjectsApi->get_namespaced_custom_object: %s\n" % e)
        return

    send_customized_event(cr = cr,
               event_type = "Normal",
               reason = "BreakingNews",
               message = "Rumors report messages sent to null. More updates expected soon. Stay tuned!")


def send_customized_event(cr, event_type, reason, message):
    api_instance = client.EventsV1beta1Api()

    now = datetime.now()
    date_time = now.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    event = {
        # Removed in OCP 4.12 / K8s v1.25
        'apiVersion': 'events.k8s.io/v1beta1', 
        'kind': 'Event', 
        'metadata': {
            # randomize the event name to allow for sending the subsequent events
            'name': cr['metadata']['name'] + '-' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=6)),
            'namespace': cr['metadata']['namespace'],
            'ownerReferences': [{
                'apiVersion': cr['apiVersion'],
                'kind': cr['kind'],
                'name': cr['metadata']['name'],
                'uid': cr['metadata']['uid'],
                'controller': True
                }]
            },
            'type': event_type,
            'eventTime': date_time,
            'series': {
                'lastObservedTime': date_time, 
                'count': 2
                }, 
            'reason': reason, 
            'action': reason, 
            'note': message, 
            'regarding': {
                'namespace': cr['metadata']['namespace'], 
                'kind': cr['kind'], 
                'name': cr['metadata']['name'], 
                'uid': cr['metadata']['uid']
                }, 
                'reportingController': 'pod/' + os.environ['HOSTNAME'], 
                'reportingInstance': cr['metadata']['name']
                }

    try:
        namespace = cr['metadata']['namespace']
        api_instance.create_namespaced_event(namespace, event)
    except ApiException as e:
        print("Exception on creating event: %s\n" % e)

if __name__ == "__main__":
    send_event()
