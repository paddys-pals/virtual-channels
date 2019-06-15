import copy

from typing import (
    List,
)

from eth_tester.exceptions import (
    TransactionFailed,
)

import pytest


class State:
    balances: List[int]  # uint256
    balance_splitter: int  # uint256
    address_splitter: bytes  # bytes32
    version: int  # uint256

    def __init__(self, balances, balance_splitter, address_splitter, version):
        self.balances = balances
        self.balance_splitter = balance_splitter
        self.address_splitter = address_splitter
        self.version = version

    def copy(self, **kwargs):
        new_state = copy.deepcopy(self)
        for key, value in kwargs.items():
            if key in self.__dict__:
                setattr(new_state, key, value)
        return new_state


def test_compile(channel_contract_info):
    pass


def test_deploy_contract(deployed_channel):
    pass


def test_finalize(w3, tester, deployed_channel, finalize_period):
    # Test: if `finalizesAt` hasn't been set, the call should fail.
    with pytest.raises(TransactionFailed):
        deployed_channel.functions.finalize().call()
    # Test: after setting `finalizesAt` and `finalizesAt` blocks mined, the call should succeed.
    deployed_channel.fallback.transact({
        'from': w3.eth.accounts[0]
    })
    deployed_channel.fallback.transact({
        'from': w3.eth.accounts[1]
    })
    tester.mine_blocks(finalize_period + 1)
    # deployed_channel.functions.finalize().call()


def _int_to_big_endian(a):
    return a.to_bytes(32, 'big')


def _sign_message_hash(w3, message_hash, privkey):
    signed_message = w3.eth.account.signHash(message_hash, privkey)
    assert message_hash == signed_message['messageHash']
    v, r, s = tuple(map(signed_message.get, ('v', 'r', 's')))
    return v, _int_to_big_endian(r), _int_to_big_endian(s)


def _make_state_digest(w3, state: State):
    type_mapping = [
        ('uint256[2]', state.balances),
        ('uint256', state.balance_splitter),
        ('address', state.address_splitter),
        ('uint256', state.version),
    ]
    return w3.soliditySha3(
        [t[0] for t in type_mapping],
        [t[1] for t in type_mapping]
    )


def _func_setStateWithoutStruct(
        w3,
        deployed_channel,
        state,
        sigs,
):
    return deployed_channel.functions.setStateWithoutStruct(
        state.balances,
        state.balance_splitter,
        state.address_splitter,
        state.version,
        sigs[0][0],
        sigs[0][1],
        sigs[0][2],
        sigs[1][0],
        sigs[1][1],
        sigs[1][2],
    )


def test_setStateWithoutStruct(w3, tester, deployed_channel, privkeys, finalize_period):
    state = State(
        balances=[10, 5],
        balance_splitter=0,
        address_splitter=w3.eth.accounts[3],
        version=1,
    )
    digest = _make_state_digest(w3, state)
    sigs = [
        _sign_message_hash(w3, digest, privkeys[0]),
        _sign_message_hash(w3, digest, privkeys[1]),
    ]
    # deposit
    deployed_channel.fallback().transact({
        'from': w3.eth.accounts[0],
        'value': state.balances[0],
    })
    deployed_channel.fallback().transact({
        'from': w3.eth.accounts[1],
        'value': state.balances[1],
    })
    # Test: succeeds
    _func_setStateWithoutStruct(w3, deployed_channel, state, sigs).call()

    # Test: `version` is not larger than the latest one, then fails.
    state_older_version = state.copy(version=0)
    with pytest.raises(TransactionFailed):
        _func_setStateWithoutStruct(w3, deployed_channel, state_older_version, sigs).call()

    # Test: wrong signatures
    sigs_copied = sigs.copy()
    # `v` set to 5
    sigs_copied[0] = (5, sigs_copied[0][1], sigs_copied[0][2])
    with pytest.raises(TransactionFailed):
        _func_setStateWithoutStruct(w3, deployed_channel, state, sigs_copied).call()

    # Test: change states
    _func_setStateWithoutStruct(w3, deployed_channel, state, sigs).transact()
    state_1 = State(
        balances=[6, 9],
        balance_splitter=0,
        address_splitter=w3.eth.accounts[3],
        version=2,
    )
    digest_1 = _make_state_digest(w3, state_1)
    sigs_1 = [
        _sign_message_hash(w3, digest_1, privkeys[0]),
        _sign_message_hash(w3, digest_1, privkeys[1]),
    ]
    _func_setStateWithoutStruct(w3, deployed_channel, state_1, sigs_1).call()

    # Test: fails to call it when the contract has finalized.
    assert 0 != deployed_channel.functions.finalizesAt().call()
    tester.mine_blocks(finalize_period + 10)
    orig_balance_1 = tester.get_balance(w3.eth.accounts[1])
    deployed_channel.functions.finalize().transact()
    with pytest.raises(TransactionFailed):
        _func_setStateWithoutStruct(w3, deployed_channel, state_1, sigs_1).call()
    now_balance_1 = tester.get_balance(w3.eth.accounts[1])
    # Only check `balances[1]`, since `balances[0]` is changed after every transaction
    #   submitted by accounts[0].
    assert (now_balance_1 - orig_balance_1) == state.balances[1]

# FIXME(mhchia): Clean up these debugging tests.
# def test_makeDigest(w3, deployed_channel):
#     state = State(
#         balances=[1, 2],
#         balance_splitter=0,
#         address_splitter=EMPTY_ADDRESS,
#         version=3,
#     )
#     result_solidity = deployed_channel.functions.makeDigestWithoutStruct(
#         state.balances, state.balance_splitter, state.address_splitter, state.version,
#     ).call()
#     result_w3 = _make_state_digest(w3, state)
#     assert result_solidity == result_w3


# def test_recoverSignerWithoutStruct(w3, deployed_channel, privkeys):
#     digest = w3.soliditySha3(
#         ['bytes32', 'uint8', 'bytes32', 'bytes32'],
#         [b'\x11' * 32, 2, b'\x33' * 32, b'\x44' * 32],
#     )
#     v, r, s = _sign_message_hash(w3, digest, privkeys[0])
#     addr = deployed_channel.functions.recoverSignerWithoutStruct(
#         digest, v, r, s
#     ).call()
#     assert addr == w3.eth.accounts[0]
