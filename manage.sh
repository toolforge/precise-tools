#!/usr/bin/env bash
# Management script for <del>stashbot</del> grid-deprecation kubernetes processes
# https://github.com/wikimedia/stashbot/blob/master/bin/stashbot.sh

set -e

DEPLOYMENT=grid-deprecation
POD_NAME=grid-deprecation

TOOL_DIR=/data/project/grid-deprecation/www/python/src

KUBECTL=/usr/bin/kubectl

_get_pod() {
    $KUBECTL get pods \
        --output=jsonpath={.items..metadata.name} \
        --selector=name=${POD_NAME}
}

case "$1" in
    start)
        echo "Starting grid-deprecation k8s deployment..."
        $KUBECTL create --validate=true -f ${TOOL_DIR}/k8s/
        ;;
    stop)
        echo "Starting grid-deprecation k8s deployment..."
        $KUBECTL delete -f ${TOOL_DIR}/k8s/
        # FIXME: wait for the pods to stop
        ;;
    restart)
        echo "Restarting grid-deprecation pod..."
        exec $KUBECTL delete pod $(_get_pod)
        ;;
    status)
        echo "Active pods:"
        exec $KUBECTL get pods -l name=${POD_NAME}
        ;;
    tail)
        exec $KUBECTL logs -f $(_get_pod)
        ;;
    attach)
        echo "Attaching to pod..."
        exec $KUBECTL exec -i -t $(_get_pod) -- /bin/bash
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|tail|attach}"
        exit 1
        ;;
esac

exit 0
# vim:ft=sh:sw=4:ts=4:sts=4:et:
