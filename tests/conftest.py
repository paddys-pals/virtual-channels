import pytest

import eth_tester

from web3 import (
    Web3,
)
from web3.providers.eth_tester import (
    EthereumTesterProvider,
)


from .configs import (
    TWO_PARTY_DIRECT_CHANNEL_PATH,
    SPLITTER_CHANNEL_PATH,
)
from .utils import (
    compile_contract,
    deploy_direct_channel,
    deploy_splitter,
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
    return 10


@pytest.fixture("session")
def direct_channel_contract_info():
    return compile_contract(TWO_PARTY_DIRECT_CHANNEL_PATH)


@pytest.fixture("session")
def splitter_contract_info():
    return compile_contract(SPLITTER_CHANNEL_PATH)


@pytest.fixture
def channel_01(w3, direct_channel_contract_info, finalize_period):
    return deploy_direct_channel(
        w3,
        direct_channel_contract_info,
        w3.eth.accounts[0],
        w3.eth.accounts[1],
        finalize_period,
    )


@pytest.fixture
def channel_12(w3, direct_channel_contract_info, finalize_period):
    return deploy_direct_channel(
        w3,
        direct_channel_contract_info,
        w3.eth.accounts[1],
        w3.eth.accounts[2],
        finalize_period,
    )


@pytest.fixture
def channel_02(w3, direct_channel_contract_info, finalize_period):
    return deploy_direct_channel(
        w3,
        direct_channel_contract_info,
        w3.eth.accounts[0],
        w3.eth.accounts[2],
        finalize_period,
    )


@pytest.fixture
def collateral():
    return 5


@pytest.fixture
def splitter_012(w3, splitter_contract_info, channel_02, collateral):
    return deploy_splitter(
        w3,
        splitter_contract_info,
        channel_02.address,
        w3.eth.accounts[1],
        collateral,
    )
