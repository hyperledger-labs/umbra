import os
import time
import asyncio
import logging
import binascii

from iroha.primitive_pb2 import can_set_my_account_detail
from iroha import Iroha, IrohaCrypto, IrohaGrpc


logger = logging.getLogger(__name__)


class IrohaEvents:
    PERMISSIONS = {
        "can_set_my_account_detail": can_set_my_account_detail,
    }

    def __init__(self):
        self._configs = None

    def config(self, configs):
        self._configs = configs

    def schedule(self, events):
        evs_sched = {}

        for event in events:
            ev_id = event.get("id")
            ev_data = event.get("event")
            action_call = self.create_call(ev_data)
            if action_call:
                evs_sched[ev_id] = (action_call, event.get("schedule"))
            else:
                logger.info(
                    f"Could not schedule fabric event task call for event {event}"
                )

        return evs_sched

    def create_call(self, event):
        task = None
        action = event.get("action")

        if action == "create_domain":
            task = self.create_domain(event)
        if action == "create_account":
            task = self.create_account(event)
        if action == "set_account_detail":
            task = self.set_account_detail(event)
        if action == "grant_permission":
            task = self.grant_permission(event)
        if action == "create_asset":
            task = self.create_asset(event)
        if action == "add_asset_quantity":
            task = self.add_asset_quantity(event)
        if action == "transfer_asset":
            task = self.transfer_asset(event)
        if action == "get_asset_info":
            task = self.get_asset_info(event)
        if action == "get_account_assets":
            task = self.get_account_assets(event)
        if action == "get_account_detail":
            task = self.get_account_detail(event)

        if task:
            return task
        else:
            logger.info("Unkown task for event %s", event)
            return None

    async def send_transaction(self, event_name, net, transaction):
        hex_hash = binascii.hexlify(IrohaCrypto.hash(transaction))
        logger.debug(
            "Event {} - Transaction hash = {}, creator = {}".format(
                event_name,
                hex_hash,
                transaction.payload.reduced_payload.creator_account_id,
            )
        )
        net.send_tx(transaction)
        for status in net.tx_status_stream(transaction):
            logger.debug(f"Event {event_name}: transaction status {status}")

    def get_node_settings(self, node_name):
        host, port = None, None

        nodes = self._configs.get("nodes", {})
        node = nodes.get(node_name, {})

        if node:
            port = node.get("port")
            host = node.get("environment-address")

        return host, port

    def get_user_settings(self, username):
        user_account, user_key_priv = None, None

        users = self._configs.get("users", {})
        user = users.get(username, {})

        if user:
            user_key_priv = user.get("keys").get("priv")
            user_account = user.get("account")

        logger.debug(
            f"User {username} settings: account {user_account} privkey {user_key_priv}"
        )
        return user_account, user_key_priv

    async def create_domain(self, event):
        event_node = event.get("node")
        event_user = event.get("user")

        event_host, event_port = self.get_node_settings(event_node)
        event_user_account, event_user_priv = self.get_user_settings(event_user)

        if event_host and event_port and event_user_account and event_user_priv:
            event_domain = event.get("domain")
            event_default_role = event.get("default_role")

            try:
                logger.debug(
                    f"Calling event {event.get('action')} - host:port {event_host}:{event_port}"
                )
                iroha = Iroha(event_user_account)
                net = IrohaGrpc("{}:{}".format(event_host, event_port))

                commands = [
                    iroha.command(
                        "CreateDomain",
                        domain_id=event_domain,
                        default_role=event_default_role,
                    ),
                ]
                tx = IrohaCrypto.sign_transaction(
                    iroha.transaction(commands), event_user_priv
                )
                coro_send_transaction = self.send_transaction(
                    event.get("action"), net, tx
                )
                asyncio.create_task(coro_send_transaction)
            except Exception as ex:
                logger.debug(
                    f"Could not make event transaction {event.get('action')} - exception {ex}"
                )
        else:
            logger.debug(
                f"Event {event.get('action')} error - missing fields event_host, event_port, event_user_account, event_user_priv"
            )
            logger.debug(
                f"Check if event {event.get('action')} contains correct node {event.get('node')} and user {event.get('user')}"
            )

    async def create_account(self, event):
        event_node = event.get("node")
        event_user = event.get("user")

        event_host, event_port = self.get_node_settings(event_node)
        event_user_account, event_user_priv = self.get_user_settings(event_user)

        if event_host and event_port and event_user_account and event_user_priv:
            event_domain = event.get("domain")
            event_account_name = event.get("account_name")
            event_account_public_key = event.get("account_pubkey")

            try:
                logger.debug(
                    f"Calling event {event.get('action')} - host:port {event_host}:{event_port}"
                )
                iroha = Iroha(event_user_account)
                net = IrohaGrpc("{}:{}".format(event_host, event_port))

                commands = [
                    iroha.command(
                        "CreateAccount",
                        account_name=event_account_name,
                        domain_id=event_domain,
                        public_key=event_account_public_key,
                    ),
                ]
                tx = IrohaCrypto.sign_transaction(
                    iroha.transaction(commands), event_user_priv
                )
                coro_send_transaction = self.send_transaction(
                    event.get("action"), net, tx
                )
                asyncio.create_task(coro_send_transaction)
            except Exception as ex:
                logger.debug(
                    f"Could not make event transaction {event.get('action')} - exception {ex}"
                )
        else:
            logger.debug(
                f"Event {event.get('action')} error - missing fields event_host, event_port, event_user_account, event_user_priv"
            )
            logger.debug(
                f"Check if event {event.get('action')} contains correct node {event.get('node')} and user {event.get('user')}"
            )

    async def set_account_detail(self, event):
        event_node = event.get("node")
        event_user = event.get("user")

        event_host, event_port = self.get_node_settings(event_node)
        event_user_account, event_user_priv = self.get_user_settings(event_user)

        if event_host and event_port and event_user_account and event_user_priv:
            event_account_id = event.get("account_id")
            event_account_detail_name = event.get("account_detail_name")
            event_account_detail_value = event.get("account_detail_value")

            try:
                logger.debug(
                    f"Calling event {event.get('action')} - host:port {event_host}:{event_port}"
                )
                iroha = Iroha(event_user_account)
                net = IrohaGrpc("{}:{}".format(event_host, event_port))

                commands = [
                    iroha.command(
                        "SetAccountDetail",
                        account_id=event_account_id,
                        key=event_account_detail_name,
                        value=event_account_detail_value,
                    ),
                ]
                tx = IrohaCrypto.sign_transaction(
                    iroha.transaction(commands), event_user_priv
                )
                coro_send_transaction = self.send_transaction(
                    event.get("action"), net, tx
                )
                asyncio.create_task(coro_send_transaction)
            except Exception as ex:
                logger.debug(
                    f"Could not make event transaction {event.get('action')} - exception {ex}"
                )
        else:
            logger.debug(
                f"Event {event.get('action')} error - missing fields event_host, event_port, event_user_account, event_user_priv"
            )
            logger.debug(
                f"Check if event {event.get('action')} contains correct node {event.get('node')} and user {event.get('user')}"
            )

    async def grant_permission(self, event):
        event_node = event.get("node")
        event_user = event.get("user")

        event_host, event_port = self.get_node_settings(event_node)
        event_user_account, event_user_priv = self.get_user_settings(event_user)

        if event_host and event_port and event_user_account and event_user_priv:
            event_account_id = event.get("account_id")
            event_permission = event.get("permission")
            event_account = event.get("account")

            try:
                logger.debug(
                    f"Calling event {event.get('action')} - host:port {event_host}:{event_port}"
                )
                iroha = Iroha(event_user_account)
                net = IrohaGrpc("{}:{}".format(event_host, event_port))

                commands = [
                    iroha.command(
                        "GrantPermission",
                        account_id=event_account_id,
                        permission=IrohaEvents.PERMISSIONS.get(event_permission, None),
                    ),
                ]
                tx = IrohaCrypto.sign_transaction(
                    iroha.transaction(commands, creator_account=event_account),
                    event_user_priv,
                )
                coro_send_transaction = self.send_transaction(
                    event.get("action"), net, tx
                )
                asyncio.create_task(coro_send_transaction)
            except Exception as ex:
                logger.debug(
                    f"Could not make event transaction {event.get('action')} - exception {ex}"
                )
        else:
            logger.debug(
                f"Event {event.get('action')} error - missing fields event_host, event_port, event_user_account, event_user_priv"
            )
            logger.debug(
                f"Check if event {event.get('action')} contains correct node {event.get('node')} and user {event.get('user')}"
            )

    async def create_asset(self, event):
        event_node = event.get("node")
        event_user = event.get("user")

        event_host, event_port = self.get_node_settings(event_node)
        event_user_account, event_user_priv = self.get_user_settings(event_user)

        if event_host and event_port and event_user_account and event_user_priv:
            event_asset_name = event.get("asset_name")
            event_domain = event.get("domain")
            event_asset_precision = event.get("asset_precision")

            try:
                logger.debug(
                    f"Calling event {event.get('action')} - host:port {event_host}:{event_port}"
                )
                iroha = Iroha(event_user_account)
                net = IrohaGrpc("{}:{}".format(event_host, event_port))

                commands = [
                    iroha.command(
                        "CreateAsset",
                        asset_name=event_asset_name,
                        domain_id=event_domain,
                        precision=event_asset_precision,
                    ),
                ]
                tx = IrohaCrypto.sign_transaction(
                    iroha.transaction(commands), event_user_priv
                )
                coro_send_transaction = self.send_transaction(
                    event.get("action"), net, tx
                )
                asyncio.create_task(coro_send_transaction)
            except Exception as ex:
                logger.debug(
                    f"Could not make event transaction {event.get('action')} - exception {ex}"
                )
        else:
            logger.debug(
                f"Event {event.get('action')} error - missing fields event_host, event_port, event_user_account, event_user_priv"
            )
            logger.debug(
                f"Check if event {event.get('action')} contains correct node {event.get('node')} and user {event.get('user')}"
            )

    async def add_asset_quantity(self, event):
        event_node = event.get("node")
        event_user = event.get("user")

        event_host, event_port = self.get_node_settings(event_node)
        event_user_account, event_user_priv = self.get_user_settings(event_user)

        if event_host and event_port and event_user_account and event_user_priv:
            event_asset_id = event.get("asset_id")
            event_asset_amount = event.get("asset_amount")

            try:
                logger.debug(
                    f"Calling event {event.get('action')} - host:port {event_host}:{event_port}"
                )
                iroha = Iroha(event_user_account)
                net = IrohaGrpc("{}:{}".format(event_host, event_port))

                commands = [
                    iroha.command(
                        "AddAssetQuantity",
                        asset_id=event_asset_id,
                        amount=event_asset_amount,
                    ),
                ]
                tx = IrohaCrypto.sign_transaction(
                    iroha.transaction(commands), event_user_priv
                )
                coro_send_transaction = self.send_transaction(
                    event.get("action"), net, tx
                )
                asyncio.create_task(coro_send_transaction)
            except Exception as ex:
                logger.debug(
                    f"Could not make event transaction {event.get('action')} - exception {ex}"
                )
        else:
            logger.debug(
                f"Event {event.get('action')} error - missing fields event_host, event_port, event_user_account, event_user_priv"
            )
            logger.debug(
                f"Check if event {event.get('action')} contains correct node {event.get('node')} and user {event.get('user')}"
            )

    async def transfer_asset(self, event):
        event_node = event.get("node")
        event_user = event.get("user")

        event_host, event_port = self.get_node_settings(event_node)
        event_user_account, event_user_priv = self.get_user_settings(event_user)

        if event_host and event_port and event_user_account and event_user_priv:
            event_asset_id = event.get("asset_id")
            event_asset_amount = event.get("asset_amount")
            event_src_account_id = event.get("src_account_id")
            event_dest_account_id = event.get("dest_account_id")
            event_description = event.get("description")

            try:
                logger.debug(
                    f"Calling event {event.get('action')} - host:port {event_host}:{event_port}"
                )
                iroha = Iroha(event_user_account)
                net = IrohaGrpc("{}:{}".format(event_host, event_port))

                commands = [
                    iroha.command(
                        "TransferAsset",
                        src_account_id=event_src_account_id,
                        dest_account_id=event_dest_account_id,
                        asset_id=event_asset_id,
                        description=event_description,
                        amount=event_asset_amount,
                    ),
                ]
                tx = IrohaCrypto.sign_transaction(
                    iroha.transaction(commands), event_user_priv
                )
                coro_send_transaction = self.send_transaction(
                    event.get("action"), net, tx
                )
                asyncio.create_task(coro_send_transaction)
            except Exception as ex:
                logger.debug(
                    f"Could not make event transaction {event.get('action')} - exception {ex}"
                )
        else:
            logger.debug(
                f"Event {event.get('action')} error - missing fields event_host, event_port, event_user_account, event_user_priv"
            )
            logger.debug(
                f"Check if event {event.get('action')} contains correct node {event.get('node')} and user {event.get('user')}"
            )

    async def get_asset_info(self, event):
        event_node = event.get("node")
        event_user = event.get("user")

        event_host, event_port = self.get_node_settings(event_node)
        event_user_account, event_user_priv = self.get_user_settings(event_user)

        if event_host and event_port and event_user_account and event_user_priv:
            event_asset_id = event.get("asset_id")

            try:
                logger.debug(
                    f"Calling event {event.get('action')} - host:port {event_host}:{event_port}"
                )
                iroha = Iroha(event_user_account)
                net = IrohaGrpc("{}:{}".format(event_host, event_port))

                query = iroha.query(
                    "GetAssetInfo",
                    asset_id=event_asset_id,
                )
                IrohaCrypto.sign_query(query, event_user_priv)

                response = net.send_query(query)
                data = response.asset_response.asset
                logger.debug(
                    "Event {}: asset id = {}, precision = {}".format(
                        event.get("action"), data.asset_id, data.precision
                    )
                )

            except Exception as ex:
                logger.debug(
                    f"Could not make event transaction {event.get('action')} - exception {ex}"
                )
        else:
            logger.debug(
                f"Event {event.get('action')} error - missing fields event_host, event_port, event_user_account, event_user_priv"
            )
            logger.debug(
                f"Check if event {event.get('action')} contains correct node {event.get('node')} and user {event.get('user')}"
            )

    async def get_account_assets(self, event):
        event_node = event.get("node")
        event_user = event.get("user")

        event_host, event_port = self.get_node_settings(event_node)
        event_user_account, event_user_priv = self.get_user_settings(event_user)

        if event_host and event_port and event_user_account and event_user_priv:
            event_account_id = event.get("account_id")

            try:
                logger.debug(
                    f"Calling event {event.get('action')} - host:port {event_host}:{event_port}"
                )
                iroha = Iroha(event_user_account)
                net = IrohaGrpc("{}:{}".format(event_host, event_port))

                query = iroha.query(
                    "GetAccountAssets",
                    account_id=event_account_id,
                )
                IrohaCrypto.sign_query(query, event_user_priv)

                response = net.send_query(query)
                data = response.account_assets_response.account_assets
                for asset in data:
                    logger.debug(
                        "Event {}: asset id = {}, balance = {}".format(
                            event.get("action"), asset.asset_id, asset.balance
                        )
                    )

            except Exception as ex:
                logger.debug(
                    f"Could not make event transaction {event.get('action')} - exception {ex}"
                )
        else:
            logger.debug(
                f"Event {event.get('action')} error - missing fields event_host, event_port, event_user_account, event_user_priv"
            )
            logger.debug(
                f"Check if event {event.get('action')} contains correct node {event.get('node')} and user {event.get('user')}"
            )

    async def get_account_detail(self, event):
        event_node = event.get("node")
        event_user = event.get("user")

        event_host, event_port = self.get_node_settings(event_node)
        event_user_account, event_user_priv = self.get_user_settings(event_user)

        if event_host and event_port and event_user_account and event_user_priv:
            event_account_id = event.get("account_id")

            try:
                logger.debug(
                    f"Calling event {event.get('action')} - host:port {event_host}:{event_port}"
                )
                iroha = Iroha(event_user_account)
                net = IrohaGrpc("{}:{}".format(event_host, event_port))

                query = iroha.query(
                    "GetAccountDetail",
                    account_id=event_account_id,
                )
                IrohaCrypto.sign_query(query, event_user_priv)

                response = net.send_query(query)
                data = response.account_detail_response
                logger.debug(
                    "Event {}: account id = {}, details = {}".format(
                        event.get("action"), event_account_id, data.detail
                    )
                )

            except Exception as ex:
                logger.debug(
                    f"Could not make event transaction {event.get('action')} - exception {ex}"
                )
        else:
            logger.debug(
                f"Event {event.get('action')} error - missing fields event_host, event_port, event_user_account, event_user_priv"
            )
            logger.debug(
                f"Check if event {event.get('action')} contains correct node {event.get('node')} and user {event.get('user')}"
            )
