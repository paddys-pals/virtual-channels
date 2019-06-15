import json
import subprocess


def compile_contract(contract_path):
    out = subprocess.check_output([
        "solc",
        "--combined-json",
        "abi,bin",
        contract_path,
    ])
    contract_json = json.loads(out.strip())["contracts"]
    # XXX: assume we only have one contract in the file
    assert len(contract_json) == 1
    contract = tuple(contract_json.values())[0]
    return contract["abi"], contract["bin"]


def deploy_contract(w3, abi, bytecode, ctor_params):
    C = w3.eth.contract(
        abi=abi,
        bytecode=bytecode,
    )
    tx_hash = C.constructor(*ctor_params).transact()
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    return w3.eth.contract(
        address=tx_receipt.contractAddress,
        abi=abi,
    )
