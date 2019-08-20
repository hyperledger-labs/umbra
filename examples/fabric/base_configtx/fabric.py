org1_policy = {
    "Readers": {
        "Type": "Signature",
        "Rule": "OR('org1MSP.admin', 'org1MSP.peer', 'org1MSP.client')"
    },                
    "Writers": {
        "Type": "Signature",
        "Rule": "OR('org1MSP.admin', 'org1MSP.client')"
    },
    "Admins": {
        "Type": "Signature",
        "Rule": "OR('org1MSP.admin')"
    },
}

org2_policy = {
    "Readers": {
        "Type": "Signature",
        "Rule": "OR('org2MSP.admin', 'org2MSP.peer', 'org2MSP.client')"
    },                
    "Writers": {
        "Type": "Signature",
        "Rule": "OR('org2MSP.admin', 'org2MSP.client')"
    },
    "Admins": {
        "Type": "Signature",
        "Rule": "OR('org2MSP.admin')"
    },
}

orderer_policy = {
    "Readers": {
        "Type": "Signature",
        "Rule": "OR('ordererMSP.member')"
    },                
    "Writers": {
        "Type": "Signature",
        "Rule": "OR('ordererMSP.member')"
    },
    "Admins": {
        "Type": "Signature",
        "Rule": "OR('ordererMSP.admin')"
    },
}


ChannelCapabilities = {"V1_3": True}
OrdererCapabilities = {"V1_1": True}
ApplicationCapabilities = {"V1_1": False, "V1_2": False, "V1_3": True}

ApplicationDefaults = {
    "Organizations": None,
    "Policies": {
        "Readers": {
            "Type": "ImplicitMeta",
            "Rule": "ANY Readers"
        },           
        "Writers": {
            "Type": "ImplicitMeta",
            "Rule": "ANY Writers"
        },
        "Admins": {
            "Type": "ImplicitMeta",
            "Rule": "MAJORITY Admins"
        }
    },
    "Capabilities": ApplicationCapabilities,
}

OrdererDefaults = {
    "OrdererType": "solo",
    "Addresses": [
        "orderer.example.com:7050",
    ],
    "BatchTimeout": "2s",
    "BatchSize": {
        "MaxMessageCount": 10,
        "AbsoluteMaxBytes": "99 MB",
        "PreferredMaxBytes": "512 KB",
    },
    "Kafka": {
        "Brokers": [ "127.0.0.1:9092" ],
    },  
    "Organizations": None,
    "Policies": {
        "Readers": {
            "Type": "ImplicitMeta",
            "Rule": "ANY Readers"
        },           
        "Writers": {
            "Type": "ImplicitMeta",
            "Rule": "ANY Writers"
        },
        "Admins": {
            "Type": "ImplicitMeta",
            "Rule": "MAJORITY Admins"
        },
        "BlockValidation": {
            "Type": "ImplicitMeta",
            "Rule": "ANY Writers"
        },
    }
}

ChannelDefaults = {
    "Policies": {
        "Readers": {
            "Type": "ImplicitMeta",
            "Rule": "ANY Readers"
        },           
        "Writers": {
            "Type": "ImplicitMeta",
            "Rule": "ANY Writers"
        },
        "Admins": {
            "Type": "ImplicitMeta",
            "Rule": "MAJORITY Admins"
        },
    },
    "Capabilities": ChannelCapabilities,
}



configtx = {
    "Organizations": [],
    "Capabilities": {
        "Channel": ChannelCapabilities,
        "Orderer": OrdererCapabilities,
        "Application": ApplicationCapabilities,
    },
    "Application": ApplicationDefaults,
    "Orderer": OrdererDefaults,
    "Channel": ChannelDefaults,
    "Profiles": {
        "TwoOrgsOrdererGenesis": {
            "Orderer": {
                "Organizations": ["orderer"],
                "Capabilities": OrdererCapabilities,
            },  
            "Consortiums": {
                "SampleConsortium": {
                    "Organizations": ["org1", "org2"]
                }
            }
        },            
        "TwoOrgsChannel": {
            "Consortium": "SampleConsortium",  
            "Application": {
                "Organizations": ["org1", "org2"],
                "Capabilities": ApplicationCapabilities,
            }
        }
    }
}


configtx["Profiles"]["TwoOrgsOrdererGenesis"].update({k:v for k,v in ChannelDefaults.items() if v})
configtx["Profiles"]["TwoOrgsOrdererGenesis"]["Orderer"].update({k:v for k,v in OrdererDefaults.items() if v})

configtx["Profiles"]["TwoOrgsChannel"].update({k:v for k,v in ChannelDefaults.items() if v})
configtx["Profiles"]["TwoOrgsChannel"]["Application"].update({k:v for k,v in ApplicationDefaults.items() if v})