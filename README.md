# Virtual-channels

Consider the following scenario. Alice and Charlie enter into a contract with a single intermediary Bob. Alice locks up amount **a<sub>0</sub>**, similarily, Charlie locks up collateral **c<sub>0</sub>**. The total channel   with a total collateral then, **k = a<sub>0</sub> + c<sub>0</sub>**. Bob, the intermediary, offers to lock up funds equal to (**b<sub>0</sub> = k**) in exchange for some specified reteurn **r**. This results in a single direction payment chanel between Alice and Charlie with intermediary Bob.

<center>
<img src="docs/images/overview.png">
</center>
<br></br>

We define the following four protocols:

1. Virtual channel establishment
2. Offchain transactions
3. Ejections/Evictions
4. (Un)Cooperative channel closure

### Virtual channel establishment
Establishing a virtual chain has the following sub components.
  1. Channel A,I<sub>B</sub>
  2. Channel I<sub>B</sub>,C  

  <center>
  <img src="docs/images/vchain_proc.png">
  </center>
  <br></br>

Alice has the following proceedure :
  1. Alice contract Audit
  2. Transfer ether to contract.  
     - This contract is not yet submitted to on chain
  3. State submission to contract

Similarily, the proceedure Bob follows:
  1. Bob contract Audit
  2. Transfer ether to contract.  
    - This contract is not yet submitted to on chain
  3. State submission to contract


### Offchain transactions

### Ejections/Evictions



### (Un)cooperative channel closure
