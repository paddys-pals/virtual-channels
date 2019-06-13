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
        if (msg.value < collateral) {
           require(false, "Insufficient collateral");
        } else if (msg.value > collateral) {
           require(false, "Too much collateral");
        }
        if (received == 0) {
            received = msg.value;
            participants.transfer(collateral);
        } else {
            intermediary.transfer(collateral);
        }
   }
   
}
