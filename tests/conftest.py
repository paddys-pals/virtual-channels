import pytest

import eth_tester

from web3 import (
    Web3,
)
from web3.providers.eth_tester import (
    EthereumTesterProvider,
)

from .constants import (
    EMPTY_ADDRESS
)


from .configs import (
    TWO_PARTY_DIRECT_CHANNEL_PATH,
    MULTISPLITTER_CHANNEL_PATH,
    SPLITTER_CHANNEL_PATH,
)
from .utils import (
    compile_contract,
    deploy_contract,
)


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
def finalize_period():
    return 15


@pytest.fixture
def splitter_finalize_period():
    return 30


@pytest.fixture("session")
def direct_channel_contract_info():
    return compile_contract(TWO_PARTY_DIRECT_CHANNEL_PATH)


@pytest.fixture("session")
def splitter_contract_info():
    return compile_contract(SPLITTER_CHANNEL_PATH)


@pytest.fixture("session")
def multisplitter_contract_info():
    return compile_contract(MULTISPLITTER_CHANNEL_PATH)


@pytest.fixture
def channel_01(w3, direct_channel_contract_info, finalize_period):
    return deploy_contract(
        w3,
        *direct_channel_contract_info,
        [[w3.eth.accounts[0], w3.eth.accounts[1]], finalize_period],
    )


@pytest.fixture
def channel_12(w3, direct_channel_contract_info, finalize_period):
    return deploy_contract(
        w3,
        *direct_channel_contract_info,
        [[w3.eth.accounts[1], w3.eth.accounts[2]], finalize_period],
    )


@pytest.fixture
def channel_23(w3, direct_channel_contract_info, finalize_period):
    return deploy_contract(
        w3,
        *direct_channel_contract_info,
        [[w3.eth.accounts[2], w3.eth.accounts[3]], finalize_period],
    )


@pytest.fixture
def channel_02(w3, direct_channel_contract_info, finalize_period):
    return deploy_contract(
        w3,
        *direct_channel_contract_info,
        [[w3.eth.accounts[0], w3.eth.accounts[2]], finalize_period],
    )


@pytest.fixture
def channel_03(w3, direct_channel_contract_info, finalize_period):
    return deploy_contract(
        w3,
        *direct_channel_contract_info,
        [[w3.eth.accounts[0], w3.eth.accounts[3]], finalize_period],
    )


@pytest.fixture
def collateral():
    return 5


@pytest.fixture
def splitter_012(w3, splitter_contract_info, channel_02, collateral):
    return deploy_contract(
        w3,
        *splitter_contract_info,
        [
            [channel_02.address, w3.eth.accounts[1], EMPTY_ADDRESS, EMPTY_ADDRESS],
            collateral, finalize_period()
        ],
    )


@pytest.fixture
def multisplitter_0123(
        w3,
        direct_channel_contract_info,
        multisplitter_contract_info,
        channel_01,
        channel_12,
        channel_23,
        channel_03,
        collateral,
        splitter_finalize_period):
    intermediaries_contracts_addresses = [
        channel_01.address,
        channel_12.address,
        channel_23.address,
    ]
    intermediaries_addresses = [
        w3.eth.accounts[1],
        w3.eth.accounts[2],
    ]
    return deploy_contract(
        w3,
        *multisplitter_contract_info,
        [
            2,
            channel_03.address,
            collateral,
            splitter_finalize_period,
            intermediaries_contracts_addresses,
            intermediaries_addresses,
        ],
    )
