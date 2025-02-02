!!!note
    For clarity, the snippets of code presented here are a simplified version of the actual
    implementation. We refer the reader to the {{open_autonomy_api}} for the complete details.

The `AbciApp` abstract class provides the necessary interface for implementation of {{fsm_app}}s. Concrete implementations of the `AbciApp` class requires that the
developer implement the class attributes `initial_round_cls`,
`transition_function` and `final_states`. The internal
`_MetaRoundBehaviour` metaclass is used to enforce this during implementation by the developer.

An overview of the code looks as follows:

```python
# skills.abstract_round_behaviour.base.py

AppState = Type[AbstractRound]
AbciAppTransitionFunction = Dict[AppState, Dict[EventType, AppState]]
EventToTimeout = Dict[EventType, float]


class AbciApp(
    Generic[EventType], ABC, metaclass=_MetaAbciApp
):
    """
    Base class for ABCI apps.

    Concrete classes of this class implement the ABCI App.
    """

    initial_round_cls: AppState
    initial_states: Set[AppState] = set()
    transition_function: AbciAppTransitionFunction
    final_states: Set[AppState] = set()
    event_to_timeout: EventToTimeout = {}
    cross_period_persisted_keys: FrozenSet[str] = frozenset()

    def __init__(
        self,
        synchronized_data: BaseSynchronizedData,
        logger: logging.Logger,
    ):
        """Initialize the AbciApp."""

    def process_transaction(self, transaction: Transaction) -> None:
        """
        Process a transaction.

        The background round runs concurrently with other (normal) rounds.
        First we check if the transaction is meant for the background round,
        if not we forward to the current round object.

        :param transaction: the transaction.
        """

    def process_event(
        self, event: EventType, result: Optional[BaseSynchronizedData] = None
    ) -> None:
        """Process a round event."""

    def update_time(self, timestamp: datetime.datetime) -> None:
        """
        Observe timestamp from last block.

        :param timestamp: the latest block's timestamp.
        """
    # (...)
```

Some of its methods relate to concepts discussed in the [FSM section](./fsm.md):

- `process_transaction( )`: Processes the payload generated by the AEAs during a round.
- `process_event( )`: Allows for the execution of transitions to the next round based on the output of the current round.
- `update_time( )`: Allows for resetting of timeouts based on the timestamp from last
  block. This is the only form of time synchronization that exists in this
  system of asynchronously operating AEAs, an understanding of which is
  indispensable to a developer that needs to implement any sort of
  [time-based](https://open-aea.docs.autonolas.tech/agent-oriented-development/#time)
  logic as part of their agents' behaviour.


A concrete implementation of a subclass of `AbciApp` looks as follows:

```python
class MyAbciApp(AbciApp):
    """My ABCI-based Finite-State Machine Application execution behaviour"""

    initial_round_cls: AppState = RoundA
    initial_states: Set[AppState] = set()
    transition_function: AbciAppTransitionFunction = {
        RoundA: {
            Event.DONE: RoundB,
            Event.ROUND_TIMEOUT: RoundA,
            Event.NO_MAJORITY: RoundA,
        },
        RoundB: {
            Event.DONE: FinalRound,
            Event.ROUND_TIMEOUT: RoundA,
            Event.NO_MAJORITY: RoundA,
        },
        FinalRound: {},
    }
    final_states: Set[AppState] = {FinalRound}
    event_to_timeout: EventToTimeout = {
        Event.ROUND_TIMEOUT: 30.0,
    }
    db_pre_conditions: Dict[AppState, List[str]] = {
        RoundA: {
            get_name(BaseSynchronizedData.required_value),
        },
    }
    db_post_conditions: Dict[AppState, List[str]] = {
        FinalRound: {
            get_name(BaseSynchronizedData.generated_value),
        },
    }
    # (...)
```

<figure markdown>
<div class="mermaid">
stateDiagram-v2
direction LR
  [*] --> RoundA
  RoundA --> RoundB: DONE
  RoundA --> RoundA: <center>ROUND_TIMEOUT<br/>NO_MAJORITY</center>
  RoundB --> FinalRound: DONE
  RoundB --> RoundA: <center>ROUND_TIMEOUT<br/>NO_MAJORITY</center>
</div>
<figcaption>State diagram of the FSM implemented by MyAbciApp</figcaption>
</figure>

The mandatory field `initial_round_cls` indicates the round associated to the initial state of the FSM.
The set of `initial_states` is optionally provided by the developer. If none is provided,
provided a set containing the `initial_round_cls` is inferred automatically.
When the {{fsm_app}} processes an `Event` it schedules the round associated to the next state by looking at the corresponding transition from the `transition_function` and sets the associated timeouts, if
any.
The `db_pre_conditions` and `db_post_conditions` are conditions that need to be met when entering and when leaving 
the `AbciApp`. These are taken into consideration when chaining FSMs, in order to make sure that
the required data exist in the synchronized data. Therefore, an application can fail early, before running any rounds,
and inform the user about an incorrect chaining attempt. 
The pre- and post- conditions on the synchronized data need to be defined for each initial and final state 
in an `AbciApp`. If there are no conditions required for an app, they can be mapped to an empty list. 
Otherwise, the list should contain the names of all the required properties in the synchronized data.
The suggested way to do this is to use the `get_name` function, defined in the `abstract_round_abci`, 
so that strings are avoided as they can get out of sync.

In addition to the `AbciApp`class, the {{fsm_app}} also requires that the `AbstractRoundBehaviour` class be implemented in order to run the state transition logic contained in it.
