import os
import time
import asyncio
import logging

from hfc.fabric import Client
from hfc.fabric_ca.caservice import CAClient, CAService


logger = logging.getLogger(__name__)


class FabricEvents:
    def __init__(self):
        self._async_loop = asyncio.get_event_loop()
        self._configtx_dir = None
        self._chaincode_dir = None
        self._config_sdk = None
        self._cli = None
        self._topo = None

    def config(self, topology, configsdk, chaincode, configtx):
        self._topo = topology
        self._configtx_dir = configtx
        self._chaincode_dir = chaincode
        self._config_sdk = configsdk
        if all([topology, configsdk, chaincode, configtx]):
            logger.info("FabricEvents configs OK")
            logger.info("configsdk %s, chaincode %s, configtx %s", configsdk, chaincode, configtx)
            
            self.config_gopath()
            self.build_cli()
            return True
        else:
            logger.info("FabricEvents configs FAILED")
            return False

    def config_gopath(self):
        gopath = os.path.normpath(os.path.join(
            self._chaincode_dir
        ))
        os.environ['GOPATH'] = os.path.abspath(gopath)

    def build_cli(self):
        pathlist = ["$HOME/hl/bin",] # TODO set dynamic config path for configtxgen bin
        os.environ["PATH"] += os.pathsep + os.pathsep.join(pathlist)

        self._cli = Client(net_profile=self._config_sdk)
        logger.debug("Fabric Orgs %s", self._cli.organizations)
        logger.debug("Fabric Peers %s", self._cli.peers)  
        logger.debug("Fabric Orderers %s", self._cli.orderers)  
        logger.debug("Fabric CAs %s", self._cli.CAs) 
        logger.info("Fabric Client SDK CLI Started") 

    def schedule(self, events):
        for _id,event in events.items():
            event_category = event.get("category")
            
            if event_category == "fabric":
                when = event.get("when")
                logger.info("Calling at %s event %s", when, event.get("params").get("action"))
                self.call_at(when, event.get("params"))
    
    def sched_time(self, when):
        if type(when) is float:
            if when >= time.time():
                rel_when = when - time.time()
            else:
                rel_when = 0
        elif type(when) is str:
            if when == "now":
                rel_when = 0
            else:
                rel_when = float(when)
        else:
            rel_when = 0
        return rel_when

    def call_at(self, when, event):
        rel_when = self.sched_time(when)
        self._async_loop.call_later(
            max(0, rel_when), self.call, event)

    def run_task(self, task):
        try:
            self._async_loop.create_task(task)
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.error("Exception in Fabric Event Task", exc_info=True)

    def call(self, event):
        task = None
        action = event.get("action")

        if action == "info_network":
            task = self.event_info_network(event)
        if action == "create_channel":
            task = self.event_create_channel(event)
        if action == "join_channel":
            task = self.event_join_channel(event)
        if action == "info_channels":
            task = self.event_info_channels(event)
        if action == "info_channel":
            task = self.event_info_channel(event)
        if action == "info_channel_config":
            task = self.event_info_channel_config(event)
        if action == "info_channel_chaincodes":
            task = self.event_info_channel_chaincodes(event)
        if action == "chaincode_install":
            task = self.event_chaincode_install(event)
        if action == "chaincode_instantiate":
            task = self.event_chaincode_instantiate(event)
        if action == "chaincode_invoke":
            task = self.event_chaincode_invoke(event)
        if action == "chaincode_query":
            task = self.event_chaincode_query(event)

        if task:
            self.run_task(task)
        else:
            logger.info("Unkown task for event %s", event)
    
    async def event_create_channel(self, ev):
        org_name = ev.get("org")
        user_name = ev.get("user")
        orderer_name = ev.get("orderer")
        channel = ev.get("channel")
        profile = ev.get("profile")

        orderer = self._topo.get("orderers").get(orderer_name)
        orderer_fqdn = orderer.get("orderer_fqdn")

        org = self._topo.get("orgs").get(org_name)
        org_fqdn = org.get("org_fqdn")
                
        if org_fqdn and orderer_fqdn:          
            org_user = self._cli.get_user(org_name=org_fqdn, name=user_name)
            
            response = await self._cli.channel_create(
                orderer=orderer_fqdn,
                channel_name=channel,
                requestor=org_user,
                config_yaml=self._configtx_dir,
                channel_profile=profile
            )
            logger.info("Create channel response %s", response)
            return response
        
        logger.info("unknown orderer %s and org %s", orderer_name, org_name)
        return None

    async def event_join_channel(self, ev):
        org_name = ev.get("org")
        user_name = ev.get("user")
        orderer_name = ev.get("orderer")
        channel = ev.get("channel")
        peers_names = ev.get("peers")

        orderer = self._topo.get("orderers").get(orderer_name)
        orderer_fqdn = orderer.get("orderer_fqdn")

        org = self._topo.get("orgs").get(org_name)
        org_fqdn = org.get("org_fqdn")
                
        if org_fqdn and orderer_fqdn:          
            org_user = self._cli.get_user(org_name=org_fqdn, name=user_name)

            peers = org.get("peers")
            peers_fqdn = [ peer.get("peer_fqdn") for peer in peers.values() if peer.get("name") in peers_names ]

            response = await self._cli.channel_join(
                requestor=org_user,
                channel_name=channel,
                peers=peers_fqdn,
                orderer=orderer_fqdn
            )
            logger.info("Join channel response %s", response)
            return response
        
        logger.info("unknown orderer %s and org %s", orderer_name, org_name)
        return None

    async def event_info_channel(self, ev):
        org_name = ev.get("org")
        user_name = ev.get("user")
        channel = ev.get("channel")
        peers_names = ev.get("peers")

        org = self._topo.get("orgs").get(org_name)
        org_fqdn = org.get("org_fqdn")

        peers = org.get("peers")
        peers_fqdn = [ peer.get("peer_fqdn") for peer in peers.values() if peer.get("name") in peers_names ]

        if org_fqdn and peers_fqdn:          
            org_user = self._cli.get_user(org_name=org_fqdn, name=user_name)

            response = await self._cli.query_info(
                requestor=org_user,
                channel_name=channel,
                peers=peers_fqdn,
                decode=True
            )
            logger.info("Info channel response %s", response)
            return response
        
        logger.info("unknown org %s and/org peers %s", org_name, peers_names)
        return None

    async def event_info_channels(self, ev):
        org_name = ev.get("org")
        user_name = ev.get("user")
        peers_names = ev.get("peers")

        org = self._topo.get("orgs").get(org_name)
        org_fqdn = org.get("org_fqdn")

        peers = org.get("peers")
        peers_fqdn = [ peer.get("peer_fqdn") for peer in peers.values() if peer.get("name") in peers_names ]

        if org_fqdn and peers_fqdn:          
            org_user = self._cli.get_user(org_name=org_fqdn, name=user_name)

            response = await self._cli.query_channels(
                requestor=org_user,
                peers=peers_fqdn,
                decode=True
            )
            logger.info("Info channels response %s", response)
            return response
        
        logger.info("unknown org %s and/org peers %s", org_name, peers_names)
        return None

    async def event_info_channel_config(self, ev):
        org_name = ev.get("org")
        user_name = ev.get("user")
        channel = ev.get("channel")
        peers_names = ev.get("peers")

        org = self._topo.get("orgs").get(org_name)
        org_fqdn = org.get("org_fqdn")

        peers = org.get("peers")
        peers_fqdn = [ peer.get("peer_fqdn") for peer in peers.values() if peer.get("name") in peers_names ]

        if org_fqdn and peers_fqdn:          
            org_user = self._cli.get_user(org_name=org_fqdn, name=user_name)

            response = await self._cli.get_channel_config(
                requestor=org_user,
                channel_name=channel,
                peers=peers_fqdn,
                decode=True
            )
            logger.info("Info channel config response %s", response)
            return response
        
        logger.info("unknown org %s and/org peers %s", org_name, peers_names)
        return None
        
    async def event_info_channel_chaincodes(self, ev):
        org_name = ev.get("org")
        user_name = ev.get("user")
        peers_names = ev.get("peers")

        org = self._topo.get("orgs").get(org_name)
        org_fqdn = org.get("org_fqdn")

        peers = org.get("peers")
        peers_fqdn = [ peer.get("peer_fqdn") for peer in peers.values() if peer.get("name") in peers_names ]

        if org_fqdn and peers_fqdn:          
            org_user = self._cli.get_user(org_name=org_fqdn, name=user_name)

            response = await self._cli.query_installed_chaincodes(
                requestor=org_user,
                peers=peers_fqdn,
                decode=True
            )
            logger.info("Info channel chaincodes response %s", response)
            return response
        
        logger.info("unknown org %s and/org peers %s", org_name, peers_names)
        return None

    async def event_info_network(self, ev):
        orderer_name = ev.get("orderer")
        orderer = self._topo.get("orderers").get(orderer_name)
        orderer_fqdn = orderer.get("orderer_fqdn")
        
        if orderer_fqdn:
            response = self._cli.get_net_info(
                'organizations',
                orderer_fqdn,
                'mspid'
            )
            logger.info("Info network response %s", response)
            return response
        
        logger.info("unknown orderer %s", orderer_name)
        return None

    async def event_chaincode_install(self, ev):
        org_name = ev.get("org")
        user_name = ev.get("user")
        peers_names = ev.get("peers")
        chaincode_name = ev.get("chaincode_name")
        chaincode_path = ev.get("chaincode_path")
        chaincode_version = ev.get("chaincode_version")
        
        org = self._topo.get("orgs").get(org_name)
        org_fqdn = org.get("org_fqdn")

        peers = org.get("peers")
        peers_fqdn = [ peer.get("peer_fqdn") for peer in peers.values() if peer.get("name") in peers_names ]
                
        if org_fqdn and peers_fqdn:          
            org_user = self._cli.get_user(org_name=org_fqdn, name=user_name)

            response = await self._cli.chaincode_install(
                requestor=org_user,
                peers=peers_fqdn,
                cc_path=chaincode_path,
                cc_name=chaincode_name,
                cc_version=chaincode_version
            )
            logger.info("Chaincode install response %s", response)
            return response
        
        logger.info("unknown org %s and/or peers %s", org_name, peers_names)
        return None

    async def event_chaincode_instantiate(self, ev):
        org_name = ev.get("org")
        user_name = ev.get("user")
        peers_names = ev.get("peers")
        channel = ev.get("channel")
        chaincode_args = ev.get("chaincode_args")
        chaincode_name = ev.get("chaincode_name")        
        chaincode_version = ev.get("chaincode_version")
        
        org = self._topo.get("orgs").get(org_name)
        org_fqdn = org.get("org_fqdn")

        peers = org.get("peers")
        peers_fqdn = [ peer.get("peer_fqdn") for peer in peers.values() if peer.get("name") in peers_names ]
                
        if org_fqdn and peers_fqdn:          
            org_user = self._cli.get_user(org_name=org_fqdn, name=user_name)

            response = await self._cli.chaincode_instantiate(
                requestor=org_user,
                channel_name=channel,
                peers=peers_fqdn,
                args=chaincode_args,
                cc_name=chaincode_name,
                cc_version=chaincode_version
            )
            logger.info("Chaincode instantiate response %s", response)
            return response
        
        logger.info("unknown org %s and/or peers %s", org_name, peers_names)
        return None

    async def event_chaincode_invoke(self, ev):
        org_name = ev.get("org")
        user_name = ev.get("user")
        peers_names = ev.get("peers")
        channel = ev.get("channel")
        chaincode_args = ev.get("chaincode_args")
        chaincode_name = ev.get("chaincode_name")        
        
        org = self._topo.get("orgs").get(org_name)
        org_fqdn = org.get("org_fqdn")

        peers = org.get("peers")
        peers_fqdn = [ peer.get("peer_fqdn") for peer in peers.values() if peer.get("name") in peers_names ]
                
        if org_fqdn and peers_fqdn:          
            org_user = self._cli.get_user(org_name=org_fqdn, name=user_name)

            response = await self._cli.chaincode_invoke(
                requestor=org_user,
                channel_name=channel,
                peers=peers_fqdn,
                args=chaincode_args,
                cc_name=chaincode_name
            )
            logger.info("Chaincode invoke response %s", response)
            return response
        
        logger.info("unknown org %s and/or peers %s", org_name, peers_names)
        return None

    async def event_chaincode_query(self, ev):
        org_name = ev.get("org")
        user_name = ev.get("user")
        peers_names = ev.get("peers")
        channel = ev.get("channel")
        chaincode_args = ev.get("chaincode_args")
        chaincode_name = ev.get("chaincode_name")        
        
        org = self._topo.get("orgs").get(org_name)
        org_fqdn = org.get("org_fqdn")

        peers = org.get("peers")
        peers_fqdn = [ peer.get("peer_fqdn") for peer in peers.values() if peer.get("name") in peers_names ]
                
        if org_fqdn and peers_fqdn:          
            org_user = self._cli.get_user(org_name=org_fqdn, name=user_name)

    
            response = await self._cli.chaincode_query(
                requestor=org_user,
                channel_name=channel,
                peers=peers_fqdn,
                args=chaincode_args,
                cc_name=chaincode_name
            )
            logger.info("Chaincode query response %s", response)
            return response
        
        logger.info("unknown org %s and/or peers %s", org_name, peers_names)
        return None