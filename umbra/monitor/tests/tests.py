import requests
import json 

def send(url, data, **kwargs):
    headers = {'Content-Type': 'application/json'}
    json_data = json.dumps(data)
    try:
        response = requests.post(url, headers=headers, data=json_data, **kwargs)
    except requests.RequestException as exception:
        print('Requests fail - exception', exception)
        response = None
    else:
        try:
            response.raise_for_status()
        except Exception:
            response = None
    finally:
        return response



insts1 = {
    3: {
        "live": False,
        "url": "http://127.0.0.1:8989",
        "tool-name": "container",
        "parameters": {
            "target": "elastic",
            "duration": 3,
            "interval": 1,
        }
    },
}

insts2 = {
    5: {
        "live": False,
        "url": "http://127.0.0.1:8989",
        "tool-name": "tcpdump",
        "parameters": {
            "duration": "3",
            "interface": "s1-eth1",
            "pcap": "s1-eth1.pcap"
        }
    },
}

data = {
    "instructions": insts1,
    "callback": "",
}

ack = send("http://172.17.0.1:8990", data)
print(ack)

data = {
    "instructions": insts2,
    "callback": "",
}

ack = send("http://172.17.0.1:8990", data)
print(ack)