from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


CONTRACT_ABI = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "incidentId", "type": "bytes32"},
            {"internalType": "bytes32", "name": "logHash", "type": "bytes32"},
            {"internalType": "bytes32", "name": "cameraId", "type": "bytes32"},
            {"internalType": "bytes32", "name": "robotId", "type": "bytes32"},
            {"internalType": "bytes32", "name": "subjectId", "type": "bytes32"},
            {"internalType": "uint8", "name": "severity", "type": "uint8"},
            {"internalType": "uint8", "name": "action", "type": "uint8"},
        ],
        "name": "recordIncident",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "robotId", "type": "bytes32"},
            {"internalType": "bytes32", "name": "incidentId", "type": "bytes32"},
        ],
        "name": "recordEmergencyStop",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]


@dataclass
class BlockchainRecorder:
    web3: Any
    account: str
    private_key: str
    contract: Any

    @classmethod
    def from_environment(cls) -> "BlockchainRecorder | None":
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except ImportError:
            pass

        rpc_url = os.getenv("HRC_RPC_URL")
        private_key = os.getenv("HRC_GATEWAY_PRIVATE_KEY")
        contract_address = os.getenv("HRC_CONTRACT_ADDRESS")
        if not rpc_url or not private_key or not contract_address:
            return None

        try:
            from web3 import Web3
        except ImportError as exc:
            raise RuntimeError(
                "Blockchain is configured but web3 is not installed. "
                "Run: pip install web3"
            ) from exc

        web3 = Web3(Web3.HTTPProvider(rpc_url))
        if not web3.is_connected():
            raise RuntimeError(f"Cannot connect to Blockchain RPC: {rpc_url}")

        account = web3.eth.account.from_key(private_key).address
        contract = web3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=CONTRACT_ABI,
        )
        return cls(web3, account, private_key, contract)

    def record(self, event: dict[str, Any]) -> tuple[str, str]:
        Web3 = self.web3
        incident_id = Web3.keccak(text=event["incident_id"])
        log_hash = bytes.fromhex(event["log_sha256"])
        camera_id = Web3.keccak(text=event["camera_id"])
        robot_id = Web3.keccak(text=event["robot_id"])
        subject_id = Web3.keccak(text=event.get("track_id") or "UNKNOWN")

        transaction = self.contract.functions.recordIncident(
            incident_id,
            log_hash,
            camera_id,
            robot_id,
            subject_id,
            1,
            2,
        ).build_transaction(
            {
                "from": self.account,
                "nonce": self.web3.eth.get_transaction_count(self.account),
                "chainId": self.web3.eth.chain_id,
                "gas": 500_000,
                "gasPrice": self.web3.eth.gas_price,
            }
        )
        signed = self.web3.eth.account.sign_transaction(transaction, self.private_key)
        incident_tx = self.web3.eth.send_raw_transaction(signed.raw_transaction)
        self.web3.eth.wait_for_transaction_receipt(incident_tx)

        stop_transaction = self.contract.functions.recordEmergencyStop(
            robot_id,
            incident_id,
        ).build_transaction(
            {
                "from": self.account,
                "nonce": self.web3.eth.get_transaction_count(self.account),
                "chainId": self.web3.eth.chain_id,
                "gas": 200_000,
                "gasPrice": self.web3.eth.gas_price,
            }
        )
        signed_stop = self.web3.eth.account.sign_transaction(
            stop_transaction,
            self.private_key,
        )
        stop_tx = self.web3.eth.send_raw_transaction(signed_stop.raw_transaction)
        return incident_tx.hex(), stop_tx.hex()
