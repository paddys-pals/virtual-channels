pragma solidity 0.5.0;
pragma experimental "ABIEncoderV2";

import "./Utils.sol";
import "./Splitter.sol";

contract TwoPartyDirectChannel {

  struct State {
    uint256[2] balances;
    uint256 balanceSplitter;
    address payable splitter;
    uint256 version;
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

  constructor (
    address payable[2] memory _participants, uint256 _finalizePeriod
  ) public {
    participants = _participants;
    finalizePeriod = _finalizePeriod;
  }

  function setState (
    State memory newState,
    Utils.Signature[2] memory sigs
  ) public {
    /*
    1. check that newState is more recent than latestState
    2. check that newState is properly signed
    3. check that channel has not finalized yet
    4. if this function has never been called before, set finalizesAt
    5. set latestState to newState
    */
    require(
      newState.version > latestState.version,
      "`newState.version` should be larger than `latestState.version`"
    );

    bytes32 digest = makeDigest(newState);
    address address0 = recoverSigner(digest, sigs[0]);
    address address1 = recoverSigner(digest, sigs[1]);
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
      abi.encodePacked(
        state.balances,
        state.balanceSplitter,
        state.splitter,
        state.version
      )
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
    // Only transfer if `splitter` is set.
    if (latestState.balanceSplitter != 0) {
      Splitter splitter = Splitter(latestState.splitter);
      splitter.deposit.value(latestState.balanceSplitter)();
    }
  }

  // fallback function
  function () external payable {
  }

  function recoverSigner(
    bytes32 digest,
    Utils.Signature memory signature
  ) public pure returns (address) {
    return ecrecover(digest, signature.v, signature.r, signature.s);
  }

}
