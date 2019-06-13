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
def privkeys(tester):
    return tester.backend.account_keys


@pytest.fixture
def finalizePeriod():
    return 10


@pytest.fixture
def deployed_contract(contract_info, w3, finalizePeriod):
    abi, bytecode = contract_info
    C = w3.eth.contract(
        abi=abi,
        bytecode=bytecode,
    )
    tx_hash = C.constructor([w3.eth.accounts[0], w3.eth.accounts[1]], finalizePeriod).transact()
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


def test_startExitFromDeposit(w3, tester, deployed_contract, finalizePeriod):
    # Test: `startExitFromDeposit` should be called only both deposits are done.
    with pytest.raises(TransactionFailed):
        deployed_contract.functions.startExitFromDeposit().call({
            'from': w3.eth.accounts[0],
        })
    with pytest.raises(TransactionFailed):
        deployed_contract.functions.startExitFromDeposit().call({
            'from': w3.eth.accounts[1],
        })
    # Test: only participants can call this function.
    deployed_contract.fallback.transact({
        'from': w3.eth.accounts[0]
    })
    deployed_contract.fallback.transact({
        'from': w3.eth.accounts[1]
    })
    deployed_contract.functions.startExitFromDeposit().call({
        'from': w3.eth.accounts[0],
    })
    deployed_contract.functions.startExitFromDeposit().call({
        'from': w3.eth.accounts[1],
    })
    with pytest.raises(TransactionFailed):
        deployed_contract.functions.startExitFromDeposit().call({
            'from': w3.eth.accounts[2],
        })
    # Test: `finalizesAt` should be `0` before calling the function.
    assert 0 == deployed_contract.functions.finalizesAt().call()
    # Test: `finalizesAt` should be changed after calling the function.
    deployed_contract.functions.startExitFromDeposit().transact({
        'from': w3.eth.accounts[0],
    })
    assert deployed_contract.functions.finalizesAt().call() == w3.eth.blockNumber + finalizePeriod


def test_finalize(w3, tester, deployed_contract, finalizePeriod):
    # Test: if `finalizesAt` hasn't been set, the call should fail.
    with pytest.raises(TransactionFailed):
        deployed_contract.functions.finalize().call()
    # Test: after setting `finalizesAt` and `finalizesAt` blocks mined, the call should succeed.
    deployed_contract.fallback.transact({
        'from': w3.eth.accounts[0]
    })
    deployed_contract.fallback.transact({
        'from': w3.eth.accounts[1]
    })
    deployed_contract.functions.startExitFromDeposit().transact({
        'from': w3.eth.accounts[0],
    })
    tester.mine_blocks(finalizePeriod + 1)
    deployed_contract.functions.finalize().call()


def _int_to_big_endian(a):
    return a.to_bytes(32, 'big')


def _sign_message_hash(w3, message_hash, privkey):
    signed_message = w3.eth.account.signHash(message_hash, privkey)
    assert message_hash == signed_message['messageHash']
    v, r, s = tuple(map(signed_message.get, ('v', 'r', 's')))
    return v, _int_to_big_endian(r), _int_to_big_endian(s)


def _make_state_digest(w3, balances, version):
    return w3.soliditySha3(
        ['uint256[2]', 'uint256'],  # 'uint8', 'bytes32', 'bytes32'],
        [balances, version],  # 4, b"\x55" * 32, b"\x66" * 32],
    )


def _func_setStateWithoutStruct(w3, deployed_contract, balances, version, sigs):
    return deployed_contract.functions.setStateWithoutStruct(
        balances,
        version,
        sigs[0][0],
        sigs[0][1],
        sigs[0][2],
        sigs[1][0],
        sigs[1][1],
        sigs[1][2],
    )


def test_setStateWithoutStruct(w3, tester, deployed_contract, privkeys, finalizePeriod):
    orig_balances = [8, 7]
    balances = [10, 5]
    version = 1
    digest = _make_state_digest(w3, balances, version)
    sigs = [
        _sign_message_hash(w3, digest, privkeys[0]),
        _sign_message_hash(w3, digest, privkeys[1]),
    ]

    # Test: `setState` without full deposits from both side
    with pytest.raises(TransactionFailed):
        _func_setStateWithoutStruct(w3, deployed_contract, balances, version, sigs).call()
    # deposit 0
    deployed_contract.fallback.transact({
        'from': w3.eth.accounts[0],
        'value': orig_balances[0],
    })
    # the call fails
    with pytest.raises(TransactionFailed):
        _func_setStateWithoutStruct(w3, deployed_contract, balances, version, sigs).call()
    # deposit 1
    deployed_contract.fallback.transact({
        'from': w3.eth.accounts[1],
        'value': orig_balances[1],
    })
    # the call succeeds
    _func_setStateWithoutStruct(w3, deployed_contract, balances, version, sigs).call()

    # Test: `version` is not larger than the latest one, then fails.
    with pytest.raises(TransactionFailed):
        _func_setStateWithoutStruct(w3, deployed_contract, balances, 0, sigs).call()

    # Test: wrong signatures
    sigs_copied = sigs.copy()
    # `v` set to 5
    sigs_copied[0] = (5, sigs_copied[0][1], sigs_copied[0][2])
    with pytest.raises(TransactionFailed):
        _func_setStateWithoutStruct(w3, deployed_contract, balances, version, sigs_copied).call()

    # Test: change states
    _func_setStateWithoutStruct(w3, deployed_contract, balances, version, sigs).transact()
    balances_1 = [6, 9]
    version_1 = 2
    digest_1 = _make_state_digest(w3, balances_1, version_1)
    sigs_1 = [
        _sign_message_hash(w3, digest_1, privkeys[0]),
        _sign_message_hash(w3, digest_1, privkeys[1]),
    ]
    _func_setStateWithoutStruct(w3, deployed_contract, balances_1, version_1, sigs_1).call()

    # Test: fails to call it when the contract has finalized.
    assert 0 == deployed_contract.functions.finalizesAt().call()
    deployed_contract.functions.startExitFromDeposit().transact({
        "from": w3.eth.accounts[0],
    })
    assert 0 != deployed_contract.functions.finalizesAt().call()
    tester.mine_blocks(finalizePeriod + 10)
    orig_balance_1 = tester.get_balance(w3.eth.accounts[1])
    deployed_contract.functions.finalize().transact()
    with pytest.raises(TransactionFailed):
        _func_setStateWithoutStruct(w3, deployed_contract, balances_1, version_1, sigs_1).call()
    now_balance_1 = tester.get_balance(w3.eth.accounts[1])
    # Only check `balances[1]`, since `balances[0]` is changed after every transaction
    #   submitted by accounts[0].
    assert (now_balance_1 - orig_balance_1) == balances[1]


# def test_makeDigest(w3, deployed_contract):
#     balances = [1, 2]
#     version = 3
#     result_solidity = deployed_contract.functions.makeDigest(
#         balances, version
#     ).call()
#     result_w3 = _make_state_digest(w3, balances, version)
#     assert result_solidity == result_w3


# def test_recoverSignerWithoutStruct(w3, deployed_contract, privkeys, accounts):
#     digest = w3.soliditySha3(
#         ['bytes32', 'uint8', 'bytes32', 'bytes32'],
#         [b'\x11' * 32, 2, b'\x33' * 32, b'\x44' * 32],
#     )
#     v, r, s = _sign_message_hash(w3, digest, privkeys[0])
#     addr = deployed_contract.functions.recoverSignerWithoutStruct(
#         digest, v, r, s
#     ).call()
#     assert addr == accounts[0]
