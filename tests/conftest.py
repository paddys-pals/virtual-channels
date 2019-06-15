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
    return 10


@pytest.fixture("session")
def channel_contract_info():
    return compile_contract(TWO_PARTY_DIRECT_CHANNEL_PATH)


@pytest.fixture
def deployed_channel(w3, channel_contract_info, finalize_period):
    abi, bytecode = channel_contract_info
    ctor_args = [[w3.eth.accounts[0], w3.eth.accounts[1]], finalize_period]
    return deploy_contract(w3, abi, bytecode, ctor_args)
