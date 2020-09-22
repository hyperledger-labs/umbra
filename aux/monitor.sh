#!/bin/bash 

COMMAND=$1

INFLUX_DIR=$PWD/influxdb
GRAPHANA_DIR=$PWD/graphana

INFLUXDB=umbra
INFLUXDB_USERNAME=umbra-influxdb
INFLUXDB_PASSWORD=umbra-influxdb

GRAFANA_USERNAME=umbra-graphana
GRAFANA_PASSWORD=umbra-graphana


#TODO: if needed, add volumes to influxdb and graphana

function start() {
    # mkdir -p $INFLUX_DIR
    # mkdir -p $GRAPHANA_DIR
 
    # -v $INFLUX_DIR:/var/lib/influxdb \
    docker run -d --name umbra-influxdb \
        -p 8086:8086 \
        -e INFLUXDB_DB=${INFLUXDB} \
        -e INFLUXDB_ADMIN_USER=${INFLUXDB_USERNAME} \
        -e INFLUXDB_ADMIN_PASSWORD=${INFLUXDB_PASSWORD} \
        influxdb:latest

    # -v $GRAPHANA_DIR:/var/lib/grafana \
    docker run -d --name umbra-graphana \
        -p 3000:3000 \
        -e GF_SECURITY_ADMIN_USER=${GRAFANA_USERNAME} \
        -e GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD} \
        grafana/grafana:latest
}


function stop() {
    docker stop -t0 umbra-influxdb
    docker rm umbra-influxdb

    docker stop -t0 umbra-graphana
    docker rm umbra-graphana

    # rm -fR $INFLUX_DIR
    # rm -fR $GRAPHANA_DIR
}


function printHelp() {
    echo_bold "Usage: "
    echo "monitor.sh <mode> "
    echo "    <mode> - one of 'start' or 'stop'"
    echo "      - 'start' - starts influxdb and graphana containers."
    echo "      - 'stop' - stop influxdb and graphana containers."
    echo "  monitor.sh -h (print this message)"

}


case "$COMMAND" in
    start)
        start
        exit 0
        ;;  

    stop)
        stop
        exit 0
        ;;
    *)
        printHelp
        exit 1
esac
