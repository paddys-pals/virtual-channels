pragma solidity 0.5.0;
pragma experimental "ABIEncoderV2";

contract MultiSplitter {
  /*
    A -- I1 -- ... -- In -- B
  */

  struct id {
    uint256 value;
    bool isValue;
  }

  uint256 n;  // Number of Intermediaries
  address payable abChannelAddress;  // the address of the AB channel
  uint256 collateral; // The symmetric collateral each participant locks in the virtual channel
  uint256 duration;  // How many blocks is the conditional timeout
  uint256 finalizesAt;  // The the block height at which the conditional timeout expires
  bool[] received;  // True if all collateral from this address are received
  mapping(address => id) intermediaryContractAddresses;  // Map every channel address to its index
  address payable[] intermediaries;

  constructor (
    uint256 _n,
    address payable _abChannelAddress,
    uint256 _collateral,
    uint256 _duration,
    address[] memory _intermediaryContractAddresses,
    address payable[] memory _intermediaries
  ) public {
    n = _n;
    duration = _duration;
    collateral = _collateral;
    abChannelAddress = _abChannelAddress;
    intermediaries = _intermediaries;
    received = new bool[](n + 1);
    for (uint i = 0; i < n + 1; i++) {
      intermediaryContractAddresses[_intermediaryContractAddresses[i]].value = i;
      intermediaryContractAddresses[_intermediaryContractAddresses[i]].isValue = true;
    }
  }

  function deposit() public payable {
    if (finalizesAt == 0) {
      finalizesAt = block.number + duration;
    }
    require(finalizesAt >= block.number, "Has finalized");
    require(msg.value == collateral, "Insufficient collateral");

    require(intermediaryContractAddresses[msg.sender].isValue, "Address does not exist");
    received[intermediaryContractAddresses[msg.sender].value] = true;
  }

  function finalize() public {
    require(finalizesAt < block.number, "Hasn't finalized");

    abChannelAddress.transfer(collateral);

    for (uint i = 0; i < n; i++) {
      if (received[i] && received[i + 1]) {
        intermediaries[i].transfer(collateral);
      }
    }
  }

}
