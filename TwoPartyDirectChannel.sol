pragma solidity 0.5.9;
pragma experimental "ABIEncoderV2";

contract TwoPartyDirectChannel {

  struct State {
    uint256[2] balances;
    uint256 version;
  }

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

  address payable[2] participants;
  uint256 finalizesAt;
  State latestState;

  constructor (
    address payable[2] memory _participants
  ) public {
    participants = _participants;
  }

  function setState (
    State memory newState, Signature[2] memory signatures
  ) public {
    /*
    1. check that newState is more recent than latestState
    2. check that newState is properly signed
    3. check that channel has not finalized yet
    4. if this function has never been called before, set finalizesAt
    5. set latestState to newState
    */
  }

  function finalize() public {
    /*
    1. check that channel is finalized
    2. transfer mony based on latestState
    */
  }

}
