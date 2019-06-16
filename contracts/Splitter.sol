pragma solidity 0.5.0;
pragma experimental "ABIEncoderV2";

import "./Utils.sol";

contract Splitter {

  enum ContractState {
    UNKNOWN,
    SPLITTER,
    REFUNDER
  }

  /*
    A -- I -- B
  */

  /*
  These variables are set at contract deploy time and then never changed.
  */
  address payable abAddress;
  address payable intermediaryAddress;
  address payable aAddress;
  address payable bAddress;
  uint256 collateral;
  uint256 finalizePeriod;

  // These variables are set over the contract lifetime
  ContractState whoAmI;
  uint256 received;
  uint256 setsTypeAt;

  constructor (
    address payable[4] memory addresses,
    uint256 _collateral,
    uint256 _finalizePeriod
  ) public {
    abAddress = addresses[0];
    intermediaryAddress = addresses[1];
    aAddress = addresses[2];
    bAddress = addresses[3];
    collateral = _collateral;
    finalizePeriod = _finalizePeriod;
  }

  function deposit() public payable {
    require(msg.value == collateral, "Received unexpected msg.value");

    if (whoAmI == ContractState.SPLITTER) /* is splitter */ {
      if (received == 0) {
        received = msg.value;
        abAddress.transfer(collateral);
      } else {
        intermediaryAddress.transfer(collateral);
      }
    } else if (whoAmI == ContractState.REFUNDER) {
      aAddress.transfer(collateral / 2);
      bAddress.transfer(collateral / 2);
    } else {
      require(false);
    }

  }

  function startBecomeSomething() public {
    require(whoAmI == ContractState.UNKNOWN, "contract type already set");
    require(setsTypeAt == 0, "already in timeout period");
    setsTypeAt = block.number + finalizePeriod;
  }

  function becomeSplitter(
    Utils.Signature[3] memory sigs
  ) public {
    require(block.number < setsTypeAt, "wrong stage");
    bytes32 digest = keccak256(
      abi.encodePacked(
        aAddress,
        intermediaryAddress,
        bAddress
      )
    );
    whoAmI = ContractState.SPLITTER;
  }

  function becomeRefunder() public {
    require(block.number > setsTypeAt, "wrong stage");
    whoAmI = ContractState.REFUNDER;
  }

}
