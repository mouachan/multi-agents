#!/bin/bash

set -e

oc annotate inferenceservice/llama serving.kserve.io/stop=true --overwrite=true
oc annotate inferenceservice/gemma serving.kserve.io/stop=true --overwrite=true
oc scale sts/postgresql --replicas=0
oc scale deploy/backend --replicas=0
oc scale deploy/frontend --replicas=0
oc scale deploy/rag-server --replicas=0
