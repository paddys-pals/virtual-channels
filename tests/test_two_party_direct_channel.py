import json

import os.path

import subprocess

from eth_account.messages import (
    defunct_hash_message,
)

import eth_tester
from eth_tester.exceptions import (
    TransactionFailed,
)

from web3 import (
    Web3,
)
from web3.providers.eth_tester import (
    EthereumTesterProvider,
)

import pytest


CONTRACT_PATH = f"{os.path.dirname(__file__)}/../virtual_channels/contracts/TwoPartyDirectChannel.sol"  # noqa: E501


@pytest.fixture("module")
def contract_info():
    out = subprocess.check_output([
        "solc",
        "--combined-json",
        "abi,bin",
        CONTRACT_PATH,
    ])
    contract_json = json.loads(out.strip())["contracts"]
    # XXX: assume we only have one contract in the file
    assert len(contract_json) == 1
    contract = tuple(contract_json.values())[0]
    return contract["abi"], contract["bin"]


@pytest.fixture
def tester():
    return eth_tester.EthereumTester(eth_tester.PyEVMBackend())


@pytest.fixture
def w3(tester):
    return Web3(EthereumTesterProvider(tester))


@pytest.fixture
def accounts(tester):
    return tester.get_accounts()


@pytest.fixture
def privkeys(tester):
    return tester.backend.account_keys



@pytest.fixture
def deployed_contract(contract_info, w3, accounts):
    abi, bytecode = contract_info
    C = w3.eth.contract(
        abi=abi,
        bytecode=bytecode,
    )
    tx_hash = C.constructor([accounts[0], accounts[1]], 80640).transact()
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    return w3.eth.contract(
        address=tx_receipt.contractAddress,
        abi=abi,
    )


def test_compile(contract_info):
    pass


def test_deploy_contract(deployed_contract):
    pass


def test_fallback(w3, deployed_contract):
    # Test: try to send from the other accounts
    with pytest.raises(TransactionFailed):
        deployed_contract.fallback.call({
            'from': w3.eth.accounts[2]
        })
    # Test: send from accounts passed to the constructor
    deployed_contract.fallback.call({
        'from': w3.eth.accounts[0]
    })
    deployed_contract.fallback.call({
        'from': w3.eth.accounts[1]
    })

    # Test: send twice from the accounts passed to the constructor
    deployed_contract.fallback.transact({
        'from': w3.eth.accounts[1]
    })
    with pytest.raises(TransactionFailed):
        deployed_contract.fallback.call({
            'from': w3.eth.accounts[1]
        })


def test_signing(w3, deployed_contract, privkeys, accounts):
    message_hash = b'\x12' * 32
    signed_message = w3.eth.account.signHash(message_hash, privkeys[0])
    assert message_hash == signed_message['messageHash']
    v, r, s = tuple(map(signed_message.get, ('v', 'r', 's')))
    account = w3.eth.account.recoverHash(message_hash, vrs=(v, r, s))
    assert account == accounts[0]
