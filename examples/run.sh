#!/bin/bash

# if [ "$EUID" != "0" ]; then
#     echo "Sorry dude! You must be root to run this script."
#     exit 1
# fi

SCRIPT_NAME='Umbra Examples'
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
    echo "    -d enable debug mode to print more logs"
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

    echo_bold "Cleaning logs"
    files=(./logs/*)
    if [ ${#files[@]} -gt 0 ]; then
        rm ./logs/*
    fi 

    scenarioPID=`ps -o pid --no-headers -C umbra-scenario`
    brokerPID=`ps -o pid --no-headers -C umbra-broker`
    examplesPID=`ps -o pid --no-headers -C examples.py`
    
    if [ -n "$brokerPID" ]
    then
        echo_bold "Stopping umbra-broker ${brokerPID}"
        kill -9 $brokerPID &> /dev/null
    fi
    
    if [ -n "$scenarioPID" ]
    then
        echo_bold "Stopping umbra-scenario ${scenarioPID}"
        sudo kill -9 $scenarioPID &> /dev/null
    fi

    if [ -n "$examplesPID" ]
    then
        echo_bold "Stopping examples script ${examplesPID}"
        kill -9 $examplesPID &> /dev/null
    fi
}

function clearContainers() {
  CONTAINER_IDS=$(docker ps -a | awk '($2 ~ /dev-peer.*/) {print $1}')
  if [ -z "$CONTAINER_IDS" -o "$CONTAINER_IDS" == " " ]; then
    echo "---- No containers available for deletion ----"
  else
    docker rm -f $CONTAINER_IDS
  fi
}


while getopts ":h:c:d" opt; do
  case "${opt}" in
    h | \?)
        printHelp
        exit 0
        ;;
    c)
        CONFIG_SOURCE=${OPTARG}
        ;;
    d)
        DEBUG='--debug'
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
        mkdir -p logs

        echo_bold "-> Creating docker network: umbra"
        docker network create umbra

        scenario="sudo umbra-scenario --uuid scenario --address 172.17.0.1:8988 ${DEBUG}"
        echo_bold "-> Starting umbra-scenarios"
        echo_bold "\$ ${scenario}"
        nohup ${scenario} > logs/scenario.log 2>&1 &
        scenariosPID=$!
        echo_bold "Scenario PID ${scenariosPID}"

        broker="umbra-broker --uuid broker --address 172.17.0.1:8989 ${DEBUG}"
        echo_bold "-> Starting umbra-broker"
        echo_bold "\$ ${broker}"
        nohup ${broker} > logs/broker.log 2>&1 &
        brokerPID=$!
        echo_bold "Broker PID ${brokerPID}"
        
        echo "########################################"
        echo "Running config ${CONFIG_SOURCE}"
        echo "########################################"
       
        sleep 6
        examples="/usr/bin/python3.7 ./examples.py --config ${CONFIG_SOURCE}"
        nohup ${examples} > logs/examples.log 2>&1 &
        examplesPID=$!
        echo_bold "Examples PID ${examplesPID}"
        
        exit 0
        ;;

    stop)
        echo_bold "-> Stop"
        reset 1
        
        echo_bold "-> Cleaning mininet"
        sudo mn -c

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
