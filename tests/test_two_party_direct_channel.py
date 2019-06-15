from eth_tester.exceptions import (
    TransactionFailed,
)

import pytest

from .utils import (
    ChannelState,
    channel_setState,
    make_state_digest,
    sign_message_hash,
)

from .constants import (
    EMPTY_ADDRESS
)


def test_compile(direct_channel_contract_info):
    pass


def test_deploy_contract(channel_01):
    pass


def test_finalize(w3, tester, channel_01, finalize_period):
    # Test: if `finalizesAt` hasn't been set, the call should fail.
    with pytest.raises(TransactionFailed):
        channel_01.functions.finalize().call()
    # Test: after setting `finalizesAt` and `finalizesAt` blocks mined, the call should succeed.
    channel_01.fallback.transact({
        'from': w3.eth.accounts[0]
    })
    channel_01.fallback.transact({
        'from': w3.eth.accounts[1]
    })
    tester.mine_blocks(finalize_period + 1)
    # channel_01.functions.finalize().call()


def test_setStateWithoutStruct(
        w3,
        tester,
        channel_01,
        splitter_contract_info,
        privkeys,
        finalize_period):
    state = ChannelState(
        balances=[10, 5],
        balance_splitter=0,
        address_splitter=w3.eth.accounts[3],
        version=1,
    )
    digest = make_state_digest(w3, state)
    sigs = [
        sign_message_hash(w3, digest, privkeys[0]),
        sign_message_hash(w3, digest, privkeys[1]),
    ]
    # deposit
    channel_01.fallback().transact({
        'from': w3.eth.accounts[0],
        'value': state.balances[0],
    })
    channel_01.fallback().transact({
        'from': w3.eth.accounts[1],
        'value': state.balances[1],
    })
    # Test: succeeds
    channel_setState(w3, channel_01, state, sigs).call()

    # Test: `version` is not larger than the latest one, then fails.
    state_older_version = state.copy(version=0)
    with pytest.raises(TransactionFailed):
        channel_setState(w3, channel_01, state_older_version, sigs).call()

    # Test: wrong signatures
    sigs_copied = sigs.copy()
    # `v` set to 5
    sigs_copied[0] = (5, sigs_copied[0][1], sigs_copied[0][2])
    with pytest.raises(TransactionFailed):
        channel_setState(w3, channel_01, state, sigs_copied).call()

    # Test: change states
    channel_setState(w3, channel_01, state, sigs).transact()
    state_1 = ChannelState(
        balances=[6, 9],
        balance_splitter=0,
        address_splitter=w3.eth.accounts[3],
        version=2,
    )
    digest_1 = make_state_digest(w3, state_1)
    sigs_1 = [
        sign_message_hash(w3, digest_1, privkeys[0]),
        sign_message_hash(w3, digest_1, privkeys[1]),
    ]
    channel_setState(w3, channel_01, state_1, sigs_1).call()

    # Test: fails to call it when the contract has finalized.
    assert 0 != channel_01.functions.finalizesAt().call()
    tester.mine_blocks(finalize_period + 10)
    orig_balance_1 = tester.get_balance(w3.eth.accounts[1])
    channel_01.functions.finalize().transact()
    with pytest.raises(TransactionFailed):
        channel_setState(w3, channel_01, state_1, sigs_1).call()
    now_balance_1 = tester.get_balance(w3.eth.accounts[1])
    # Only check `balances[1]`, since `balances[0]` is changed after every transaction
    #   submitted by accounts[0].
    assert (now_balance_1 - orig_balance_1) == state.balances[1]

def test_makeDigest(w3, channel_01):
    state = ChannelState(
        balances=[1, 2],
        balance_splitter=0,
        address_splitter=EMPTY_ADDRESS,
        version=3,
    )
    result_solidity = channel_01.functions.makeDigest(
        state.as_tuple()
    ).call()
    result_w3 = make_state_digest(w3, state)
    assert result_solidity == result_w3


def test_recoverSigner(w3, channel_01, privkeys):
    digest = w3.soliditySha3(
        ['bytes32', 'uint8', 'bytes32', 'bytes32'],
        [b'\x11' * 32, 2, b'\x33' * 32, b'\x44' * 32],
    )
    v, r, s = sign_message_hash(w3, digest, privkeys[0])
    addr = channel_01.functions.recoverSigner(
        digest, (v, r, s)
    ).call()
    assert addr == w3.eth.accounts[0]
