# Mock Rust dependency for Counterparty Core
import logging
import time
import requests

logger = logging.getLogger(__name__)

VERSION = "11.0.4"


class Indexer:
    """Mock Indexer class that fetches blocks from Bitcoin RPC"""

    def __init__(self, config):
        self.config = config
        self.rpc_address = config.get("rpc_address", "http://bitcoind:18443")
        self.rpc_user = config.get("rpc_user", "dev")
        self.rpc_password = config.get("rpc_password", "devpass")
        self.current_height = config.get("start_height", 0)
        self.running = False
        logger.info(f"MockIndexer initialized with config: rpc_address={self.rpc_address}")

    def get_version(self):
        """Return the version string"""
        return VERSION

    def start(self):
        """Start the indexer"""
        self.running = True
        logger.info("MockIndexer started")

    def stop(self):
        """Stop the indexer"""
        self.running = False
        logger.info("MockIndexer stopped")

    def _rpc_call(self, method, params=None):
        """Make an RPC call to Bitcoin Core"""
        payload = {
            "jsonrpc": "2.0",
            "id": "mock",
            "method": method,
            "params": params or []
        }
        try:
            response = requests.post(
                self.rpc_address,
                json=payload,
                auth=(self.rpc_user, self.rpc_password),
                timeout=30
            )
            result = response.json()
            if "error" in result and result["error"]:
                logger.error(f"RPC error: {result['error']}")
                return None
            return result.get("result")
        except Exception as e:
            logger.error(f"RPC call failed: {e}")
            return None

    def get_block_non_blocking(self):
        """Get the next block non-blocking, returns None if not available"""
        if not self.running:
            return None

        # Get current blockchain height
        info = self._rpc_call("getblockchaininfo")
        if info is None:
            return None

        chain_height = info.get("blocks", 0)

        if self.current_height > chain_height:
            return None

        # Get block hash at current height
        block_hash = self._rpc_call("getblockhash", [self.current_height])
        if block_hash is None:
            return None

        # Get full block with transactions
        block = self._rpc_call("getblock", [block_hash, 2])  # verbosity 2 = full tx data
        if block is None:
            return None

        # Convert to expected format
        transactions = []
        for tx in block.get("tx", []):
            # Convert vin to expected format with hash and n
            vins = []
            for vin in tx.get("vin", []):
                vin_data = {
                    "hash": vin.get("txid", "0" * 64),  # Previous tx hash
                    "n": vin.get("vout", 0),  # Previous tx output index
                    "script_sig": vin.get("scriptSig", {}).get("hex", ""),
                    "sequence": vin.get("sequence", 0xffffffff),
                    "coinbase": vin.get("coinbase"),
                }
                # Add witness data if present
                if "txinwitness" in vin:
                    vin_data["witness"] = vin["txinwitness"]
                vins.append(vin_data)

            # Convert vout to expected format with script_pub_key
            vouts = []
            for vout in tx.get("vout", []):
                vout_data = {
                    "n": vout.get("n"),
                    "value": vout.get("value", 0),
                    "script_pub_key": vout.get("scriptPubKey", {}).get("hex", ""),
                }
                vouts.append(vout_data)

            # Check if this is a coinbase transaction
            is_coinbase = len(tx.get("vin", [])) > 0 and "coinbase" in tx.get("vin", [{}])[0]

            tx_data = {
                "tx_id": tx.get("txid"),
                "tx_hash": tx.get("hash", tx.get("txid")),
                "vin": vins,
                "vout": vouts,
                "segwit": tx.get("hash") != tx.get("txid"),
                "coinbase": is_coinbase,
            }
            transactions.append(tx_data)

        result = {
            "height": self.current_height,
            "block_index": self.current_height,
            "block_hash": block_hash,
            "block_time": block.get("time"),
            "hash_prev": block.get("previousblockhash", "0" * 64),
            "bits": block.get("bits", "0"),
            "transactions": transactions,
        }

        self.current_height += 1
        return result


class Deserializer:
    """Mock Deserializer class that uses Bitcoin RPC to decode transactions"""

    def __init__(self, config):
        self.config = config
        self.rpc_address = config.get("rpc_address", "http://bitcoind:18443")
        self.rpc_user = config.get("rpc_user", "dev")
        self.rpc_password = config.get("rpc_password", "devpass")
        logger.info(f"MockDeserializer initialized with rpc_address={self.rpc_address}")

    def _rpc_call(self, method, params=None):
        """Make an RPC call to Bitcoin Core"""
        payload = {
            "jsonrpc": "2.0",
            "id": "mock",
            "method": method,
            "params": params or []
        }
        try:
            response = requests.post(
                self.rpc_address,
                json=payload,
                auth=(self.rpc_user, self.rpc_password),
                timeout=30
            )
            result = response.json()
            if "error" in result and result["error"]:
                logger.error(f"RPC error: {result['error']}")
                return None
            return result.get("result")
        except Exception as e:
            logger.error(f"RPC call failed: {e}")
            return None

    def _convert_tx(self, tx, block_index, parse_vouts=False):
        """Convert Bitcoin Core tx format to Counterparty expected format"""
        vins = []
        for vin in tx.get("vin", []):
            vin_data = {
                "hash": vin.get("txid", "0" * 64),
                "n": vin.get("vout", 0),
                "script_sig": vin.get("scriptSig", {}).get("hex", ""),
                "sequence": vin.get("sequence", 0xffffffff),
            }
            if "coinbase" in vin:
                vin_data["coinbase"] = vin["coinbase"]
            if "txinwitness" in vin:
                vin_data["witness"] = vin["txinwitness"]
            vins.append(vin_data)

        vouts = []
        for vout in tx.get("vout", []):
            vout_data = {
                "n": vout.get("n"),
                "value": vout.get("value", 0),
                "script_pub_key": vout.get("scriptPubKey", {}).get("hex", ""),
            }
            vouts.append(vout_data)

        is_coinbase = len(tx.get("vin", [])) > 0 and "coinbase" in tx.get("vin", [{}])[0]

        return {
            "tx_id": tx.get("txid"),
            "tx_hash": tx.get("hash", tx.get("txid")),
            "vin": vins,
            "vout": vouts,
            "segwit": tx.get("hash") != tx.get("txid"),
            "coinbase": is_coinbase,
            "block_index": block_index,
        }

    def parse_transaction(self, tx_hex, block_index, parse_vouts=False):
        """Decode a raw transaction hex"""
        tx = self._rpc_call("decoderawtransaction", [tx_hex])
        if tx is None:
            return None
        return self._convert_tx(tx, block_index, parse_vouts)

    def parse_block(self, block_hex, block_index, parse_vouts=False):
        """Decode a raw block hex"""
        # This is rarely used - blocks are usually fetched via get_block_non_blocking
        block = self._rpc_call("decodeblock", [block_hex])
        if block is None:
            return None
        return block


class MockIndexerModule:
    """Module-level mock that exposes the Indexer and Deserializer classes"""
    Indexer = Indexer
    Deserializer = Deserializer

class MockUtils:
    """Mock utils class to replace counterparty_rs.utils"""
    
    def __init__(self):
        pass
    
    def decode_script(self, script):
        """Mock decode_script method"""
        logger.debug(f"MockUtils.decode_script called with: {script}")
        return {"type": "mock", "addresses": ["mock_address"]}
    
    def encode_script(self, script_data):
        """Mock encode_script method"""
        logger.debug(f"MockUtils.encode_script called with: {script_data}")
        return "mock_encoded_script"
    
    def __getattr__(self, name):
        """Return a mock method for any missing attributes"""
        def mock_method(*args, **kwargs):
            logger.debug(f"MockUtils.{name} called with args: {args}, kwargs: {kwargs}")
            return None
        return mock_method

class MockB58:
    """Mock b58 class to replace counterparty_rs.b58"""
    
    def __init__(self):
        pass
    
    def decode(self, data):
        """Mock decode method"""
        logger.debug(f"MockB58.decode called with: {data}")
        return b"mock_decoded"
    
    def encode(self, data):
        """Mock encode method"""
        logger.debug(f"MockB58.encode called with: {data}")
        return "mock_encoded"
    
    def __getattr__(self, name):
        """Return a mock method for any missing attributes"""
        def mock_method(*args, **kwargs):
            logger.debug(f"MockB58.{name} called with args: {args}, kwargs: {kwargs}")
            return None
        return mock_method

# Create module-level instances
indexer = MockIndexerModule()
utils = MockUtils()
b58 = MockB58()
