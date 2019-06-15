from .utils import (
    ChannelState,
    channel_setState,
    make_state_digest,
    sign_message_hash,
)


def test_compile(splitter_contract_info):
    pass


def test_deploy(splitter_012):
    pass


def test_splitter(
        w3,
        tester,
        channel_01,
        channel_12,
        channel_02,
        splitter_012,
        finalize_period,
        collateral,
        privkeys):

    # We get a chain of two `TwoPartyDirectChannel`s
    #
    # 0 ←────────────→ 1 ←──────────────→ 2
    #         ↑                 ↑
    #    channel_01         channel_12

    # First, we set up two channels respectively.

    # 0 and 1 deposits to `channel_01`

    balance_01 = [1, collateral - 1]
    channel_01.fallback().transact({
        'from': w3.eth.accounts[0],
        'value': balance_01[0],
    })
    channel_01.fallback().transact({
        'from': w3.eth.accounts[1],
        'value': balance_01[1],
    })
    # 1 and 2 deposits to channel_12
    balance_12 = [1, collateral - 1]
    channel_12.fallback().transact({
        'from': w3.eth.accounts[1],
        'value': balance_12[0],
    })
    channel_12.fallback().transact({
        'from': w3.eth.accounts[2],
        'value': balance_12[1],
    })

    # Now, 1 wants to leave. It must do the following steps:
    #   - First, 1 must set up a `channel_02`.
    #   - Second, 1 must deploy a `Splitter` contract.
    # It is already done now.
    # Then, it must set new states in both `channel_01` and
    #   `channel_12`, moving the both funds to the `Splitter` contract.
    state_01_0 = ChannelState(
        balances=[0, 0],
        balance_splitter=collateral,
        address_splitter=splitter_012.address,
        version=1,
    )
    digest_01 = make_state_digest(w3, state_01_0)
    sigs_01 = [
        sign_message_hash(w3, digest_01, privkeys[0]),
        sign_message_hash(w3, digest_01, privkeys[1]),
    ]
    channel_setState(
        channel_01,
        state_01_0,
        sigs_01,
    ).transact({
        'from': w3.eth.accounts[-1]
    })

    state_12_0 = ChannelState(
        balances=[0, 0],
        balance_splitter=collateral,
        address_splitter=splitter_012.address,
        version=1,
    )
    digest_12 = make_state_digest(w3, state_12_0)
    sigs_12 = [
        sign_message_hash(w3, digest_12, privkeys[1]),
        sign_message_hash(w3, digest_12, privkeys[2]),
    ]
    channel_setState(
        channel_12,
        state_12_0,
        sigs_12,
    ).transact({
        'from': w3.eth.accounts[-1]
    })

    # Finally, finalize both `channel_01` and `channel_12`.
    orig_balance_1 = tester.get_balance(w3.eth.accounts[1])
    tester.mine_blocks(finalize_period + 5)
    channel_01.functions.finalize().transact({
        'from': w3.eth.accounts[-1]
    })
    channel_12.functions.finalize().transact({
        'from': w3.eth.accounts[-1]
    })

    # Now, both 1 and `channel_02` should get back funds `collateral`.
    assert tester.get_balance(channel_02.address) == collateral
    assert tester.get_balance(w3.eth.accounts[1]) - orig_balance_1 == collateral
