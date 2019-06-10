pragma solidity 0.5.9;
pragma experimental "ABIEncoderV2";


contract TwoPartyDirectChannel {

  uint256 public aBal;
  uint256 public bBal;
  uint256 public aAddress;
  uint256 public bAddress;
  uint256 public finalizesAt;

  constructor (
    uint256 public aBal,
    uint256 public bBal,
    uint256 public aAddress,
    uint256 public bAddress,
  ) public {
    // TBD
  }

  // fallback function
  function () payable {
    // TBD
  }

  // add more functions as needed

}
