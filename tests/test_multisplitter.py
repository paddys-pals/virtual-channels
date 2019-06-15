
from .utils import (
    both_deposit_to_channel,
    set_state_funds_to_splitter,
)


def test_multisplitter(
        w3,
        tester,
        channel_01,
        channel_12,
        channel_23,
        channel_03,
        multisplitter_0123,
        finalize_period,
        splitter_finalize_period,
        collateral,
        privkeys):
    balances_01 = {0: 1, 1: collateral - 1}
    balances_12 = {1: 1, 2: collateral - 1}
    balances_23 = {2: 1, 3: collateral - 1}
    both_deposit_to_channel(w3, channel_01, balances_01)
    set_state_funds_to_splitter(
        w3,
        channel_01,
        multisplitter_0123,
        balances_01,
        1,
        privkeys,
    )
    both_deposit_to_channel(w3, channel_12, balances_12)
    set_state_funds_to_splitter(
        w3,
        channel_12,
        multisplitter_0123,
        balances_12,
        1,
        privkeys,
    )
    both_deposit_to_channel(w3, channel_23, balances_23)
    set_state_funds_to_splitter(
        w3,
        channel_23,
        multisplitter_0123,
        balances_23,
        1,
        privkeys,
    )

    tester.mine_blocks(finalize_period)
    channel_01.functions.finalize().transact({
        'from': w3.eth.accounts[-1]
    })
    channel_12.functions.finalize().transact({
        'from': w3.eth.accounts[-1]
    })
    channel_23.functions.finalize().transact({
        'from': w3.eth.accounts[-1]
    })
    orig_balance_1 = tester.get_balance(w3.eth.accounts[1])
    orig_balance_2 = tester.get_balance(w3.eth.accounts[2])
    tester.mine_blocks(splitter_finalize_period)
    multisplitter_0123.functions.finalize().transact({
        'from': w3.eth.accounts[-1]
    })

    assert tester.get_balance(channel_03.address) == collateral
    assert tester.get_balance(w3.eth.accounts[1]) - orig_balance_1 == collateral
    assert tester.get_balance(w3.eth.accounts[2]) - orig_balance_2 == collateral
