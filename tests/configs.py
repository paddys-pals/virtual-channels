import pathlib
import os.path

CONTRACT_PATH = pathlib.Path(f"{os.path.dirname(__file__)}/../virtual_channels/contracts")
TWO_PARTY_DIRECT_CHANNEL_PATH = CONTRACT_PATH / "TwoPartyDirectChannel.sol"
SPLITTER_CHANNEL_PATH = CONTRACT_PATH / "Splitter.sol"