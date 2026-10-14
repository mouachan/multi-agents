#!/bin/bash
# Restore the replica counts saved by shutdown.sh.

set -e

for r in $(oc get deploy,sts -l app.kubernetes.io/managed-by=Helm -o name); do
  n=$(oc get "$r" -o jsonpath='{.metadata.annotations.hibernate\.multi-agents/replicas}')
  [ -n "$n" ] && oc scale "$r" --replicas="$n"
done
