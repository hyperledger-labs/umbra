org1_policy = {
    "Readers": {
        "Type": "Signature",
        "Rule": "OR('org1MSP.admin', 'org1MSP.peer', 'org1MSP.client')",
    },
    "Writers": {"Type": "Signature", "Rule": "OR('org1MSP.admin', 'org1MSP.client')"},
    "Admins": {"Type": "Signature", "Rule": "OR('org1MSP.admin')"},
    "Endorsement": {
        "Type": "Signature",
        "Rule": "OR('org1MSP.peer')",
    },
}

org2_policy = {
    "Readers": {
        "Type": "Signature",
        "Rule": "OR('org2MSP.admin', 'org2MSP.peer', 'org2MSP.client')",
    },
    "Writers": {"Type": "Signature", "Rule": "OR('org2MSP.admin', 'org2MSP.client')"},
    "Admins": {"Type": "Signature", "Rule": "OR('org2MSP.admin')"},
    "Endorsement": {
        "Type": "Signature",
        "Rule": "OR('org1MSP.peer')",
    },
}


org3_policy = {
    "Readers": {
        "Type": "Signature",
        "Rule": "OR('org3MSP.admin', 'org3MSP.peer', 'org3MSP.client')",
    },
    "Writers": {"Type": "Signature", "Rule": "OR('org3MSP.admin', 'org3MSP.client')"},
    "Admins": {"Type": "Signature", "Rule": "OR('org3MSP.admin')"},
    "Endorsement": {
        "Type": "Signature",
        "Rule": "OR('org1MSP.peer')",
    },
}


org4_policy = {
    "Readers": {
        "Type": "Signature",
        "Rule": "OR('org4MSP.admin', 'org4MSP.peer', 'org4MSP.client')",
    },
    "Writers": {"Type": "Signature", "Rule": "OR('org4MSP.admin', 'org4MSP.client')"},
    "Admins": {"Type": "Signature", "Rule": "OR('org4MSP.admin')"},
    "Endorsement": {
        "Type": "Signature",
        "Rule": "OR('org1MSP.peer')",
    },
}


orderer_policy = {
    "Readers": {"Type": "Signature", "Rule": "OR('ordererMSP.member')"},
    "Writers": {"Type": "Signature", "Rule": "OR('ordererMSP.member')"},
    "Admins": {"Type": "Signature", "Rule": "OR('ordererMSP.admin')"},
}


ChannelCapabilities = {"V2_0": True}
OrdererCapabilities = {"V2_0": True}
ApplicationCapabilities = {"V2_0": True}

ApplicationDefaults = {
    "Organizations": None,
    "Policies": {
        "Readers": {"Type": "ImplicitMeta", "Rule": "ANY Readers"},
        "Writers": {"Type": "ImplicitMeta", "Rule": "ANY Writers"},
        "Admins": {"Type": "ImplicitMeta", "Rule": "MAJORITY Admins"},
        "LifecycleEndorsement": {
            "Type": "ImplicitMeta",
            "Rule": "MAJORITY Endorsement",
        },
        "Endorsement": {"Type": "ImplicitMeta", "Rule": "MAJORITY Endorsement"},
    },
    "Capabilities": ApplicationCapabilities,
}

OrdererDefaults = {
    "OrdererType": "etcdraft",
    "BatchTimeout": "2s",
    "BatchSize": {
        "MaxMessageCount": 10,
        "AbsoluteMaxBytes": "99 MB",
        "PreferredMaxBytes": "512 KB",
    },
    "Organizations": None,
    "Policies": {
        "Readers": {"Type": "ImplicitMeta", "Rule": "ANY Readers"},
        "Writers": {"Type": "ImplicitMeta", "Rule": "ANY Writers"},
        "Admins": {"Type": "ImplicitMeta", "Rule": "MAJORITY Admins"},
        "BlockValidation": {"Type": "ImplicitMeta", "Rule": "ANY Writers"},
    },
    "EtcdRaft": {
        "Consenters": [
            {
                "Host": "orderer.example.com",
                "Port": 7050,
                "ClientTLSCert": "./ordererOrganizations/example.com/orderers/orderer.example.com/tls/server.crt",
                "ServerTLSCert": "./ordererOrganizations/example.com/orderers/orderer.example.com/tls/server.crt",
            }
        ],
        # "Options": {
        #   "TickInterval": 50000,
        #   "ElectionTick": 1000,
        #   "HeartbeatTick": 1,
        #   # MaxInflightMsgs: 256
        #   # MaxSizePerMsg: 1048576
        # }
    },
}

ChannelDefaults = {
    "Policies": {
        "Readers": {"Type": "ImplicitMeta", "Rule": "ANY Readers"},
        "Writers": {"Type": "ImplicitMeta", "Rule": "ANY Writers"},
        "Admins": {"Type": "ImplicitMeta", "Rule": "MAJORITY Admins"},
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
                "SampleConsortium": {"Organizations": ["org1", "org2", "org3", "org4"]}
            },
        },
        "TwoOrgsChannel": {
            "Consortium": "SampleConsortium",
            "Application": {
                "Organizations": ["org1", "org2", "org3", "org4"],
                "Capabilities": ApplicationCapabilities,
            },
        },
    },
}


configtx["Profiles"]["TwoOrgsOrdererGenesis"].update(
    {k: v for k, v in ChannelDefaults.items() if v}
)
configtx["Profiles"]["TwoOrgsOrdererGenesis"]["Orderer"].update(
    {k: v for k, v in OrdererDefaults.items() if v}
)

configtx["Profiles"]["TwoOrgsChannel"].update(
    {k: v for k, v in ChannelDefaults.items() if v}
)
configtx["Profiles"]["TwoOrgsChannel"]["Application"].update(
    {k: v for k, v in ApplicationDefaults.items() if v}
)
