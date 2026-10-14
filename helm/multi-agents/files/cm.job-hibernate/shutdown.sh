#!/bin/bash
# Scale the Helm-managed workloads (backend, frontend, agents, PostgreSQL, MinIO) to
# zero and keep their replica counts in an annotation for wakeup.sh. Operator-managed
# workloads (OGX, MCP servers, NeMo, gateways) are left alone: their operators would
# scale them back.

set -e

for r in $(oc get deploy,sts -l app.kubernetes.io/managed-by=Helm -o name); do
  n=$(oc get "$r" -o jsonpath='{.spec.replicas}')
  [ "$n" = "0" ] && continue
  oc annotate "$r" hibernate.multi-agents/replicas="$n" --overwrite
  oc scale "$r" --replicas=0
done
