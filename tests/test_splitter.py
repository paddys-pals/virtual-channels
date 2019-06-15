from .utils import (
    ChannelState,
    both_deposit_to_channel,
    channel_setState,
    make_state_digest,
    set_state_funds_to_splitter,
    make_splitter_digest,
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
    balances_01 = {0: 1, 1: collateral - 1}
    both_deposit_to_channel(w3, channel_01, balances_01)
    # 1 and 2 deposits to channel_12
    balances_12 = {1: 1, 2: collateral - 1}
    both_deposit_to_channel(w3, channel_12, balances_12)

    # Now, 1 wants to leave. It must do the following steps:
    #   - First, 1 must set up a `channel_02`.
    #   - Second, 1 must deploy a `Splitter` contract, and make it a splitter
    # It is already done now.
    # Then, it must set new states in both `channel_01` and
    #   `channel_12`, moving the both funds to the `Splitter` contract.
    set_state_funds_to_splitter(
        w3,
        channel_01,
        splitter_012,
        balances_01,
        1,
        privkeys,
    )
    set_state_funds_to_splitter(
        w3,
        channel_12,
        splitter_012,
        balances_12,
        1,
        privkeys,
    )

    digest_splitter = make_splitter_digest(w3, [
        w3.eth.accounts[0],
        w3.eth.accounts[1],
        w3.eth.accounts[2],
    ])
    sigs_splitter = [
        sign_message_hash(w3, digest_splitter, privkeys[0]),
        sign_message_hash(w3, digest_splitter, privkeys[1]),
        sign_message_hash(w3, digest_splitter, privkeys[2])
    ]

    splitter_012.functions.startBecomeSomething().transact({
        'from': w3.eth.accounts[-1]
    })
    splitter_012.functions.becomeSplitter(
        sigs_splitter
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
