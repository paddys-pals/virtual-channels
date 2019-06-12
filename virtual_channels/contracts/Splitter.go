pragma solidity >=0.4.22 <0.6.0;

contract Splitter {

  struct Signature {
    bytes32 r;
    uint8 v;
    bytes32 s;
  }
  
  function recoverSigner(
    bytes32 digest, Signature memory sig
  ) internal pure returns (address) {
    return ecrecover(digest, sig.v, sig.r, sig.s);
  }

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
  
   function deposit () payable {
        if msg.value != collateral {
           // error
        }
        if deposit == 0 {
            deposit = msg.value
            participants.transfer(collateral);
        } else {
            intermediary.transfer(collateral)
        }
   }
   
}
