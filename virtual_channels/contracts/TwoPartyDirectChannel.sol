pragma solidity 0.5.0;
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

  /*
  These variables are set at contract deploy time and then never changed.
  */
  address payable[2] participants;
  uint256 finalizePeriod;

  /*
  These variables are changed during the dispute period
  */
  uint256 public finalizesAt;
  State latestState;

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
    } else {
      finalizesAt = block.number + finalizePeriod;
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
