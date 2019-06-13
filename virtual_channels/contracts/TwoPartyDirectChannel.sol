pragma solidity ^0.5.0;
pragma experimental "ABIEncoderV2";

contract TwoPartyDirectChannel {

  struct State {
    uint256[2] balances;
    uint256 version;
  }

  struct Signature {
    uint8 v;
    bytes32 r;
    bytes32 s;
  }

  address payable[2] participants;
  uint256 public finalizesAt;
  State latestState;

  bool[2] hasDeposited;
  uint256 finalizePeriod;

  constructor (
    address payable[2] memory _participants, uint256 _finalizePeriod
  ) public {
    participants = _participants;
    finalizePeriod = _finalizePeriod;
  }

  // FIXME: should use `Struct` whenever possible
  function setStateWithoutStruct (
    uint256[2] memory balances,
    uint256 version,
    uint8 v0,
    bytes32 r0,
    bytes32 s0,
    uint8 v1,
    bytes32 r1,
    bytes32 s1
  ) public {
    /*
    1. check that newState is more recent than latestState
    2. check that newState is properly signed
    3. check that channel has not finalized yet
    4. if this function has never been called before, set finalizesAt
    5. set latestState to newState
    */
    State memory newState = State(balances, version);
    require(
      hasDeposited[0] && hasDeposited[1],
      "`latestState` can be changed only after both sides have deposited"
    );

    require(
      newState.version > latestState.version,
      "`newState.version` should be larger than `latestState.version`"
    );

    bytes32 digest = makeDigest(newState);
    address address0 = recoverSignerWithoutStruct(digest, v0, r0, s0);
    address address1 = recoverSignerWithoutStruct(digest, v1, r1, s1);
    require(address0 == participants[0], "`signatures[0]` does not match `accounts[0]`");
    require(address1 == participants[1], "`signatures[1]` does not match `accounts[1]`");

    if (finalizesAt != 0) {
      require(finalizesAt > block.number, "Has finalized");
    }
    latestState = newState;
  }

  function makeDigest(
    State memory state
  ) public pure returns (bytes32) {
    return keccak256(
      abi.encode(state.balances[0], state.balances[1], state.version)
    );
  }

  function finalize() public {
    /*
    1. check that channel is finalized
    2. transfer money based on latestState
    */
    require(finalizesAt != 0, "`finalizesAt` hasn't been set");
    require(finalizesAt <= block.number, "Hasn't finalized");
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
    require(
      hasDeposited[0] && hasDeposited[1],
      "`startExitFromDeposit` should only be called after both deposits are done"
    );
    require(
      msg.sender == participants[0] || msg.sender == participants[1],
      "Non-participants are banned from calling this `startExitFromDeposit`"
    );
    if (finalizesAt == 0) {
      finalizesAt = block.number + finalizePeriod;
    }
  }

  // FIXME: should use `Struct` whenever possible
  function recoverSignerWithoutStruct(
    bytes32 digest,
    uint8 v,
    bytes32 r,
    bytes32 s
  ) internal pure returns (address) {
    return ecrecover(digest, v, r, s);
  }

}
