#!/bin/bash

set -e

oc annotate inferenceservice/llama serving.kserve.io/stop=false --overwrite=true
oc annotate inferenceservice/gemma serving.kserve.io/stop=false --overwrite=true
oc scale sts/postgresql --replicas=1
oc scale deploy/backend --replicas=1
oc scale deploy/frontend --replicas=2
oc scale deploy/rag-server --replicas=1
