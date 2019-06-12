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

  address payable[2] participants;
  uint256 finalizesAt;
  State latestState;

  bool[2] hasDeposited;
  uint256 finalizePeriod;

  uint256 b;

  constructor (
    address payable[2] memory _participants, uint256 _finalizePeriod
  ) public {
    participants = _participants;
    finalizePeriod = _finalizePeriod;
    b = 1;
  }

  // function testState(uint256 a) public {
  //   b = a;
  // }

  function getB() public view returns (uint256) {
    return b;
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
    require(
      hasDeposited[0] && hasDeposited[1],
      "`latestState` can be changed only after both sides have deposited"
    );

    require(
      newState.version > latestState.version,
      "`newState.version` should be larger than `latestState.version`"
    );

    bytes32 digest = keccak256(abi.encode(newState));
    address address0 = recoverSigner(digest, signatures[0]);
    address address1 = recoverSigner(digest, signatures[1]);
    require(address0 == participants[0], "`signatures[0]` does not match `accounts[0]`");
    require(address1 == participants[1], "`signatures[1]` does not match `accounts[1]`");

    if (finalizesAt != 0) {
      require(finalizesAt <= block.number, "Has finalized");
    }
    latestState = newState;
  }

  function finalize() public {
    /*
    1. check that channel is finalized
    2. transfer money based on latestState
    */
    require(finalizesAt > block.number, "Hasn't finalized");
    participants[0].transfer(latestState.balances[0]);
    participants[1].transfer(latestState.balances[1]);
  }

  // fallback function
  function () external payable {
    uint index;
    if (msg.sender == participants[0]) {
      index = 0;
    } else if (msg.sender == participants[1]) {
      index = 1;
    } else {
      require(false, "Deposit from non-participants");
    }
    if (hasDeposited[index]) {
      require(false, "The participant has deposited before");
    }
    latestState.balances[index] = msg.value;
    hasDeposited[index] = true;
  }

  function startExitFromDeposit() public {
    if (finalizesAt == 0) {
      finalizesAt = block.number + finalizePeriod;
    }
  }

  function recoverSigner(
    bytes32 digest, Signature memory sig
  ) internal pure returns (address) {
    return ecrecover(digest, sig.v, sig.r, sig.s);
  }

}
