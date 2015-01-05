# import modules
import types;

# import custom modules
from . import state;

# Machine
# generic state machine class
class Machine :

    # _handleCall
    # helper function for calling an appropriate handler on the current state
    def _handleCall( self, func, params=() ) :
        # we're not currently running a state, so skip it
        if not self.state:
            raise StateMachineError( "attempted to call handler '{}' on an inactive state machine".format( func ) );
        
        # get the name of the handler on the state
        fname = "on_{}".format( func );
        
        if self.generic and not fname in state.REQUIRED_HANDLERS :
            raise AttributeError( "generic state machine cannot execute non-generic handler '{}'".format( fname ) );
    
        try :
            # get the handler itself if it exists
            state_func  = getattr( self.state, fname );
            return state_func( *params );
        except AttributeError :
            # the handler doesn't exist
            raise ValueError( "current state has no function attribute {}".format( fname ) );
          
    # _getHandlers
    # helper function for extracting a handler list from a given state
    def _getHandlers( self, state ) :
        self.handler_list = [];
        
        # get all attributes started with "on_" - those are our handlers
        for key in dir( state ) :
            if key.startswith( "on_" ) :
                self.handler_list.append( key[3:] );
        return self.handler_list;
        
    # _setPrevState
    # helper function for linking the previous state chain
    def _setPrevState( self, state ) :
        if state :
            state.prev_state    = self.prev_state;
        self.prev_state         = state;
        
    # backtrack
    # step back to the previous state
    def backtrack( self ) :
        if not self.state :
            raise StateMachineError( "attempted to backtrack in an inactive state machine" );
    
        if not self.prev_state :
            raise EndOfBacktrack( "backtrack limit reached" );
            
        self.changeState( self.prev_state, backtrack=True );
        self.prev_state = self.state._popPrevState();
        
    # changeState
    # changes to another state and calls all relevant handlers
    def changeState( self, new_state, backtrack=False, force=False ) :
        # if we're a strict machine, allow only properly typed states
        if not new_state :
            self.free();
            return;
        if not isinstance( new_state, self.state_type ) and not self.generic :
            raise TypeError( "changeState expects type {}, not {}".format( self.state_type, type( new_state ) ) );
            
        if not backtrack :
            self._setPrevState( self.state )
            
        # if the new state is already active, do nothing
        if not force and self.state and self.state == new_state :
            return;
            
        # call the on_exit handler and set up a new handler list if we're generic
        if self.state :
            self._handleCall( "exit" );
        if not self.handler_list :
            self._getHandlers( new_state );
        
        # set our relevant variables and call the on_enter handler
        self.state = new_state;
        self.state._config( self );
        self._handleCall( "enter" );

    # clearHistory
    # clears the previous state list
    def clearHistory( self ) :
        if self.prev_state :
            self.prev_state._clearHistory();
            self.prev_state = None;
            # this should self garbage collect
            
    def free( self ) :
        self.clearHistory();
        if self.state :
            self.state._free();
            self.state = None;
        self.handler_list = None;
        
    def __del__( self ) :
        self.free();
        
    # __init__
    def __init__( self, init_state=None, statetype=None, generic=False ) :
        if not isinstance( init_state, state.State ) :
            raise TypeError( "init_state expects type State or subclass, not {}".format( type( init_state ) ) );
        
        self.state      = None;
        self.generic    = generic;
        if generic and not statetype :
            self.state_type = state.State;
        elif statetype :
            self.state_type = statetype;
        elif init_state :
            self.state_type = type( init_state );
        else:
            self.state_type = state.State;
            
        self.changeState( init_state );

    # __getattr__
    # called when a given attribute is not found in the object's __dict__
    def __getattr__( self, name ) :
        if name == 'handler_list' :
            return None;

        if self.handler_list and name in self.handler_list :
            return lambda *params: self._handleCall( name, params );
        
        raise AttributeError( "'{}' object has no attribute '{}'".format( type( self ), name ) );
            
    # __setattr__
    # called when setting an attribute
    def __setattr__( self, name, value ) :
        if self.handler_list and name in self.handler_list :
            raise AttributeError( "cannot set attribute '{}' as it would overwrite a handler" );
            
        object.__setattr__( self, name, value );
        
    def __eq__( self, other ) :
        if isinstance( other, self.state_type ) :
            return self.state == other;
        else :
            return object.__eq__( self, other );
            
    def __ne__( self, other ) :
        if isinstance( other, self.state_type ) :
            return self.state != other;
        else :
            return object.__ne__( self, other );
        
class EndOfBacktrack( Exception ) :
    pass;

class StateMachineError( Exception ) :
    pass;