genesis_base = {
    "block_v1": {
        "payload": {
            "height": "1",
            "prevBlockHash": "0000000000000000000000000000000000000000000000000000000000000000",
            "transactions": [
                {
                    "payload": {
                        "reducedPayload": {
                            "commands": [
                                {
                                    "createRole": {
                                        "permissions": [
                                            "can_add_peer",
                                            "can_add_signatory",
                                            "can_create_account",
                                            "can_create_domain",
                                            "can_get_all_acc_ast",
                                            "can_get_all_acc_ast_txs",
                                            "can_get_all_acc_detail",
                                            "can_get_all_acc_txs",
                                            "can_get_all_accounts",
                                            "can_get_all_signatories",
                                            "can_get_all_txs",
                                            "can_get_blocks",
                                            "can_get_roles",
                                            "can_read_assets",
                                            "can_remove_signatory",
                                            "can_set_quorum",
                                        ],
                                        "roleName": "admin",
                                    }
                                },
                                {
                                    "createRole": {
                                        "permissions": [
                                            "can_add_signatory",
                                            "can_get_my_acc_ast",
                                            "can_get_my_acc_ast_txs",
                                            "can_get_my_acc_detail",
                                            "can_get_my_acc_txs",
                                            "can_get_my_account",
                                            "can_get_my_signatories",
                                            "can_get_my_txs",
                                            "can_grant_can_add_my_signatory",
                                            "can_grant_can_remove_my_signatory",
                                            "can_grant_can_set_my_account_detail",
                                            "can_grant_can_set_my_quorum",
                                            "can_grant_can_transfer_my_assets",
                                            "can_receive",
                                            "can_remove_signatory",
                                            "can_set_quorum",
                                            "can_transfer",
                                        ],
                                        "roleName": "user",
                                    }
                                },
                                {
                                    "createRole": {
                                        "permissions": [
                                            "can_add_asset_qty",
                                            "can_create_asset",
                                            "can_receive",
                                            "can_transfer",
                                        ],
                                        "roleName": "creator",
                                    }
                                },
                            ],
                            "quorum": 1,
                        }
                    }
                }
            ],
            "txNumber": 1,
        }
    }
}
