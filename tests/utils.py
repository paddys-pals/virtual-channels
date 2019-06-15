import copy
import json
import os.path
import subprocess
from typing import (
    List,
)


class ChannelState:
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

    def as_tuple(self):
        return (self.balances, self.balance_splitter, self.address_splitter, self.version)


def compile_contract(contract_path):
    out = subprocess.check_output([
        "solc",
        "--combined-json",
        "abi,bin",
        contract_path,
    ])
    contract_json = json.loads(out.strip())["contracts"]
    # XXX: assume we only have one contract in the file
    # assert len(contract_json) == 1
    contract_name = os.path.splitext(os.path.basename(str(contract_path)))[0]
    key = f"{str(contract_path)}:{contract_name}"
    contract = contract_json[key]
    return contract["abi"], contract["bin"]


def deploy_contract(w3, abi, bytecode, ctor_params):
    C = w3.eth.contract(
        abi=abi,
        bytecode=bytecode,
    )
    tx_hash = C.constructor(*ctor_params).transact({
        "from": w3.eth.accounts[-1]  # NOTE: paid by a non-relevant account
    })
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    return w3.eth.contract(
        address=tx_receipt.contractAddress,
        abi=abi,
    )


def int_to_big_endian(a):
    return a.to_bytes(32, 'big')


def sign_message_hash(w3, message_hash, privkey):
    signed_message = w3.eth.account.signHash(message_hash, privkey)
    assert message_hash == signed_message['messageHash']
    v, r, s = tuple(map(signed_message.get, ('v', 'r', 's')))
    return v, int_to_big_endian(r), int_to_big_endian(s)


def make_state_digest(w3, state: ChannelState):
    type_mapping = [
        ('uint256[2]', state.balances),
        ('uint256', state.balance_splitter),
        ('address', state.address_splitter),
        ('uint256', state.version),
    ]
    return w3.soliditySha3(
        [t[0] for t in type_mapping],
        [t[1] for t in type_mapping],
    )


def channel_setState(
        channel,
        state,
        sigs):
    return channel.functions.setState(
        state.as_tuple(),
        sigs
    )


def both_deposit_to_channel(w3, channel, dict_balances):
    assert len(dict_balances) == 2
    for index, value in dict_balances.items():
        channel.fallback().transact({
            'from': w3.eth.accounts[index],
            'value': value,
        })
        channel.fallback().transact({
            'from': w3.eth.accounts[index],
            'value': value,
        })


def set_state_funds_to_splitter(
        w3,
        channel,
        splitter,
        dict_balances,
        version,
        privkeys):
    assert len(dict_balances) == 2
    keys = tuple(dict_balances.keys())
    sum_balance = sum(dict_balances.values())
    state = ChannelState(
        balances=[0, 0],
        balance_splitter=sum_balance,
        address_splitter=splitter.address,
        version=version,
    )
    digest = make_state_digest(w3, state)
    sigs = [
        sign_message_hash(w3, digest, privkeys[keys[0]]),
        sign_message_hash(w3, digest, privkeys[keys[1]]),
    ]
    channel_setState(
        channel,
        state,
        sigs,
    ).transact({
        'from': w3.eth.accounts[-1]
    })
