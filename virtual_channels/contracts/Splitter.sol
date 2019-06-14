pragma solidity >=0.4.22 <0.6.0;

contract Splitter {

  /*
    A -- I -- B
  */

  /*
  These variables are set at contract deploy time and then never changed.
  */
  address payable abAddress;
  address payable intermediaryAddress;
  uint256 collateral;

  // This variable is set after the first thing is received
  uint256 received;

  constructor (
    address payable[2] memory addresses,
    uint256 _collateral
  ) public {
    abAddress = addresses[0];
    intermediaryAddress = addresses[1];
    collateral = _collateral;
  }

   function deposit () payable public {
    require(msg.value == collateral, "Received unexpected msg.value");
    if (received == 0) {
      received = msg.value;
      abAddress.transfer(collateral);
    } else {
      intermediaryAddress.transfer(collateral);
    }
  }

}
