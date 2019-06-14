pragma solidity >=0.4.22 <0.6.0;

contract Splitter {

  address payable participants;
  address payable intermediary;
  uint256 collateral;
  uint256 received;

  constructor (
    address payable[2] memory addresses
  ) public {
    participants = addresses[0];
    intermediary = addresses[1];
  }

   function deposit () payable public {
    require(msg.value == collateral, "Received unexpected msg.value");
    if (received == 0) {
      received = msg.value;
      participants.transfer(collateral);
    } else {
      intermediary.transfer(collateral);
    }
  }

}
