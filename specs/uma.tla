----------------------------- MODULE uma -----------------------------
EXTENDS Naturals

CONSTANT
indexApprovedSet, \* approved indices
timestampSet,     \* timestamps
ancillaryDataSet, \* miscillaneous data
currencySet,      \* currencies for rewards
rewardSet,        \* possible rewards
proposerBond,     \* proposer bond as a function of index
disputerBond,     \* disputer bond as a function of index
livenessPeriod,   \* window for disputes after proposal
accounts,         \* Ethereum accounts
answerSet,        \* possible answers to all requests 
storeContractID,  \* UMA's Address
escrowAddress     \* dummy address for conservation of money

ASSUME escrowAddress \in accounts
ASSUME storeContractID \in accounts
ASSUME proposerBond \in [indexApprovedSet -> Nat] 
ASSUME disputerBond \in [indexApprovedSet -> Nat] 
ASSUME livenessPeriod \in  Nat
ASSUME rewardSet \subseteq Nat

VARIABLE
requestSet, \* outstanding requests
proposeSet, \* outstanding proposals
disputeSet, \* outstanding disputes
acceptSet,  \* expired proposals and resolved disputes
balanceOf,  \* ETH balance as a function of address
time        \* time ticks

requests == 
    [identifier: indexApprovedSet, 
     timestamp: timestampSet, 
     ancillaryData: ancillaryDataSet, 
     currency: currencySet, 
     reward: rewardSet, 
     requestAddress: accounts]

proposals == 
    [requestItem: requests, 
     timestamp: timestampSet,
     answer: answerSet,
     proposeAddress: accounts]


disputes ==
    [proposeItem: proposals,
     timestamp: timestampSet,
     disputeAddress: accounts]

accepts ==
    [proposeOrDisputeItem: proposals \union disputes,
     answer : answerSet,
     indentifier : indexApprovedSet, 
     timestamp : timestampSet]

requestAction(requestItem, currentTime) == 
    /\ requestItem.timestamp = currentTime
    /\ balanceOf[requestItem.requestAddress] \geq requestItem.reward 
    /\ requestSet' = requestSet \union {requestItem}
    /\ balanceOf' = [balanceOf EXCEPT !.requestItem.requestAddress = @ - requestItem.reward,
                                      !.escrowAddress = @ + requestItem.reward]
    /\ time' = time + 1
    /\ UNCHANGED <<disputeSet, acceptSet, proposeSet>>

requestActionExists ==   
    \E requestItem \in requests : requestAction(requestItem, time)

proposeAction(proposeItem, currentTime) == 
    LET index == proposeItem.requestItem.identifier 
        proposerAddress == proposeItem.proposeAddress IN 
        /\ proposeItem.requestItem \in requestSet
        /\ proposeItem.timestamp = currentTime
        /\ balanceOf[proposeItem.proposeAddress] \geq proposerBond[index] 
        /\ proposeSet' = proposeSet \union {proposeItem}
        /\ requestSet' = requestSet \ {proposeItem.requestItem}  
        /\ balanceOf' = [balanceOf EXCEPT !.proposerAddress = @ - 
                                                              proposerBond[index] + 
                                                              proposeItem.requestItem.reward, 
                                          !.escrowAddress = @ + 
                                                            proposerBond[index] - 
                                                            proposeItem.requestItem.reward] 
        /\ time' = time + 1
        /\ UNCHANGED <<acceptSet, disputeSet>>

proposeActionExists ==
     \E proposeItem \in proposals: proposeAction(proposeItem, time)






disputeAction(disputeItem, currentTime) == 
    LET index == disputeItem.proposeItem.requestItem.identifier IN 
        /\ disputeItem.proposeItem \in proposeSet
        /\ currentTime \leq disputeItem.proposeItem.timeStamp + livenessPeriod
        /\ disputeItem.timestamp = currentTime
        /\ balanceOf[disputeItem.disputeAddress] \geq disputerBond[index] 
        /\ disputerBond \equiv proposerBond[index]
        /\ disputeSet' = disputeSet \union {disputeItem}
        /\ proposeSet' = proposeSet \ {disputeItem.proposeItem}
        /\ balanceOf' = [balanceOf EXCEPT !.disputeItem.disputeAddress = @ - disputerBond[index], 
                                          !.escrowAddress = @ + disputerBond[index]] 
        /\ time' = time + 1
        /\ UNCHANGED <<acceptSet, requestSet>>

disputeActionExists ==
    \E disputeItem \in disputes: disputeAction(disputeItem, time)

dvmAction(acceptItem, dvmResult, dvmAnswer, currentTime) == 
    /\ acceptItem.proposeOrdisputeItem \in disputeSet
    /\ acceptItem.timestamp = currentTime
    /\ LET index == acceptItem.proposeOrdisputeItem.proposeItem.requestItem.identifier 
           proposerAddress == acceptItem.proposeOrDisputeItem.proposeItem.proposeAddress 
           disputerAddress == acceptItem.proposeOrDisputeItem.disputeAddress IN 
            /\ acceptItem.identifier = index
            /\ IF dvmResult THEN
                /\ acceptItem.answer = acceptItem.disputeOrProposeItem.proposeItem.answer
                /\ balanceOf' = [balanceOf EXCEPT !.proposerAddress = @ + 
                                                                      proposerBond[index] + 
                                                                      (disputerBond[index] \div 2),
                                                  !.storeContractID = @ + 
                                                                      (disputerBond[index] \div 2),
                                                  !.escrowAddress = @ - 
                                                                    disputerBond[index] - 
                                                                    proposerBond[index]] 
                ELSE 
                    /\ acceptItem.answer = dvmAnswer
                    /\ balanceOf' = [balanceOf EXCEPT !.disputerAddress = @ + 
                                                                          disputerBond[index] + 
                                                                          (proposerBond[index] \div 2),
                                                      !.storeContractID = @ + 
                                                                          (proposerBond[index] \div 2),
                                                      !.escrowAddress = @ - 
                                                                        disputerBond[index] - 
                                                                        proposerBond[index]] 
    /\ disputeSet' = disputeSet \ {acceptItem.proposeOrdisputeItem}
    /\ acceptSet' = acceptSet \union {acceptItem}
    /\ time' = time + 1     
    /\ UNCHANGED <<requestSet, proposeSet>>

dvmActionExists == 
    \E acceptItem \in accepts,  
       dvmResult \in BOOLEAN,
       dvmAnswer \in answerSet  : dvmAction(acceptItem, dvmResult, dvmAnswer, time)

proposeExpire(acceptItem, currentTime) == 
        /\ acceptItem.proposeOrDisputeItem \in proposeSet
        /\ acceptItem.identifier = acceptItem.proposeOrDisputeItem.requestItem.identifier
        /\ acceptItem.answer = acceptItem.proposeOrDisputeItem.answer
        /\ acceptItem.timestamp = currentTime
        /\ currentTime \geq acceptItem.proposeOrDisputeItem.proposeTimeStamp + livenessPeriod
        /\ proposeSet' = proposeSet \ {acceptItem.proposeOrDisputeItem}
        /\ acceptSet' = acceptSet \union {acceptItem}
        /\ time' = time + 1
        /\ UNCHANGED <<requestSet, disputeSet, balanceOf>>

proposeExpireExists ==
    \E acceptItem \in accepts: proposeExpire(acceptItem, time) 

timeAdvance == 
    /\ time' = time + 1
    /\ UNCHANGED <<acceptSet, requestSet, proposeSet, disputeSet, balanceOf>>

Init == 
    /\ acceptSet = {}
    /\ requestSet = {}
    /\ proposeSet = {}
    /\ disputeSet = {}
    /\ balanceOf \in [accounts -> Nat]
    /\ time = 0

Next == 
    \/ requestActionExists
    \/ proposeActionExists
    \/ disputeActionExists 
    \/ dvmActionExists
    \/ proposeExpireExists
    \/ timeAdvance

vars == <<acceptSet, requestSet, proposeSet, disputeSet, balanceOf, time>>
Spec == Init /\ [][Next]_vars
======================================================================


