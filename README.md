py3-state-machine
=================

Generic state machine written for Python 3

Created mostly as a test of github and to challenge myself. This state machine isn't meant to comply with any sort of standard, it's just built to manage and move between states and call handlers easily from the machine.

Currently the library supports:
 - Both strictly typed and generic state machines
 - Calls built in handlers on machine events (on_config, on_enter, on_exit, etc)
 - Call arbitrary handlers on the current state from the machine
 - Backtracking between states
 - Bind classes to states to quickly create new state classes

Basic example:

```python
from state_machine import *

# This is a state class
class SaySomethingState( State ) :
  def on_enter( self ) :    # Called whenever we enter a state machine
    print( "Entering new state..." )
  
  def on_exit( self ) :     # Called whenever we exit a state machine
    print( "Exiting state..." )
    
  def on_sayit( self ) :    # Called manually on the machine
    print( self.say_what )
  
  def __init__( self, saywhat ) :
    State.__init__( self )
    self.say_what = saywhat

# Set up some states
HelloState      = SaySomethingState( "Hello, world!" )
GoodbyeState    = SaySomethingState( "Goodbye, world!" )

# Create our machine and play around with it
MyMachine       = Machine( HelloState )
MyMachine.sayit()
MyMachine.changeState( GoodbyeState )
MyMachine.sayit()

#   Output:
# Entering new state...
# Hello, world!
# Exiting state...
# Entering new state...
# Goodbye, world!
# Exiting state...
```
