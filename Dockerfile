FROM quay.io/operator-framework/ansible-operator:latest

# Pin deprecated dependencies
COPY scripts/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy the operator itself
COPY roles/ /opt/ansible/roles
COPY watches.yaml /opt/ansible/watches.yaml
COPY deploy/crds/ /opt/ansible/deploy/crds/
COPY deploy/operator.yaml /opt/ansible/deploy/operator.yaml
COPY rbac/ /opt/ansible/rbac/

# send-events script
COPY scripts/ /opt/ansible/scripts/

# Install the community.kubernetes collection
RUN ansible-galaxy collection install community.kubernetes

# Ensure that the scripts directory is included in the PATH
ENV PATH="/opt/ansible/scripts:${PATH}"

WORKDIR /opt/ansible
