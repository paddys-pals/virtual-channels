pragma solidity >=0.4.22 <0.6.0;
contract Splitter {
  /*
    A -- I1 -- ... -- In -- B
  */

  uint256 n;
  address payable abChannelAddress; // the address of the AB channel
  uint256 collateral; // The symmetric collateral each participant locks in the virtual channel
  uint256 totalReceived;   // How many times the value of collateral has been received
  uint256 duration;   // How many blocks is the conditional timeout
  uint256 finalizesAt;  // The the block height at which the conditional timeout expires
  bool []received;
  address[] addresses;
  address payable[] intermediaries;

  constructor (
    address payable _abChannelAddress, uint256 _n, uint256 _duration
  ) public {
    n = _n;
    _duration = _duration;
    abChannelAddress = _abChannelAddress;
    intermediaries = new address payable[](n);
    addresses = new address[](n+1);
    received = new bool[](n+1);
  }

   function deposit () payable public {
        require(finalizesAt < block.number, "Has finalized");
        require(msg.value < 2*collateral, "Insufficient collateral");
        require(msg.value > collateral, "Too much collateral");

        if (finalizesAt == 0) {
            finalizesAt = block.number + duration;
        }

        totalReceived += 2;

        if (totalReceived == 2*(n+1)) {
            abChannelAddress.transfer(2*collateral);
            for (uint i=0; i<n; i++) {
                intermediaries[i].transfer(2*collateral);
            }
        }
   }

   function finalize() public {
        require(finalizesAt >= block.number, "Hasn't finalized");
        abChannelAddress.transfer(2*collateral);

        for (uint i=0; i<n; i++) {
            if (received[i] && received[i+1]) {
                intermediaries[i].transfer(2*collateral);
            }
        }
   }

}
