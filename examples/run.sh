#!/bin/bash

if [ "$EUID" != "0" ]; then
    echo "Sorry dude! You must be root to run this script."
    exit 1
fi

SCRIPT_NAME='Umbra Examples Test: Scenarios + Orchestration'
COMMAND=$1

shift

echo_bold() {
    echo -e "\033[1m${1}\033[0m"
}

function printHelp() {
    echo_bold "Usage: "
    echo "run.sh <mode>  [ -c <config file path> ]"
    echo "    <mode> - one of 'start' or 'stop'"
    echo "      - 'start' - bring up the network specified in the <config file path>"
    echo "      - 'stop' - stop and clear the started setup"
    echo "    -c <config file path> - filepath of a config created using umbra-configs"
    echo "  run.sh -h (print this message)"

}

kill_process_tree() {
    top=$1
    pid=$2

    children=`ps -o pid --no-headers --ppid ${pid}`

    for child in $children
    do
        kill_process_tree 0 $child
    done

    if [ $top -eq 0 ]; then
        kill -9 $pid &> /dev/null
    fi
}

reset() {
    init=$1;
    if [ $init -eq 1 ]; then
        echo_bold "-> Resetting $SCRIPT_NAME";
    else
        echo_bold "-> Stopping child processes...";
        kill_process_tree 1 $$
    fi

    byobu kill-session -t "umbra"

}

function clearContainers() {
  CONTAINER_IDS=$(docker ps -a | awk '($2 ~ /dev-peer.*/) {print $1}')
  if [ -z "$CONTAINER_IDS" -o "$CONTAINER_IDS" == " " ]; then
    echo "---- No containers available for deletion ----"
  else
    docker rm -f $CONTAINER_IDS
  fi
}


while getopts ":h:c:" opt; do
  case "${opt}" in
    h | \?)
        printHelp
        exit 0
        ;;
    c)
        CONFIG_SOURCE=${OPTARG}
        ;;
  esac
done

case "$COMMAND" in
    start)
        if [ -z "${CONFIG_SOURCE}" ]; then
            echo_bold "Please, specify a config source path"
            exit 1
        fi

        echo_bold "-> Start"

        echo_bold "-> Creating docker network: umbra"
        docker network create umbra
        
        echo_bold "-> Starting umbra-scenarios"
        byobu new-session -d -s "umbra" "python2.7 -m umbra_scenarios --url http://172.17.0.1:8988  --debug"

        echo_bold "-> Starting umbra-orch"
        byobu new-window "python3 -m umbra_orch --host 172.17.0.1 --port 8989 --debug"

        sleep 5
        echo "########################################"
        echo "Running config ${CONFIG_SOURCE}"
        echo "########################################"

        ACK=$(curl -s -X POST --header "Content-Type: application/json" -d @"${CONFIG_SOURCE}" \
        http://172.17.0.1:8989/)

        echo_bold "Deployed config in umbra-orch: "${ACK}""       
        exit 0
        ;;

    stop)
        echo_bold "-> Stop"
        reset 1
        echo_bold "-> Cleaning mininet"
        mn -c

        echo_bold "-> Removing docker containers - (e.g., fabric chaincode)"
        clearContainers

        echo_bold "-> Prunning docker volumes"
        docker volume prune -f

        echo_bold "-> Removing docker network: umbra"
        docker network rm umbra
        
        exit 0
        ;;
    *)
        printHelp
        exit 1
esac
