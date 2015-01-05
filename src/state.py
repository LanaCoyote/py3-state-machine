# import modules
import warnings;

# constants
#   these handlers are included by default in all states
REQUIRED_HANDLERS    = {'on_clear':(lambda machine: None),
                        'on_enter':None,
                        'on_exit':None,
                        'on_free':(lambda machine: None),
                        'on_init':(lambda machine: None),
                        'on_update':None};

# addGenericHandler
# adds a handler to the required handler list
# if fn is defined, it will be used as the default. Otherwise it will be None
def addGenericHandler( name, fn=None ) :
  REQUIRED_HANDLERS.setdefault( name, fn );
  
# bind
# binds a class to a state class
def bind( basestate, baseother=None ) :
  # single parameter mode binds with the base state class
  if not baseother :
    baseother = basestate;
    basestate = State;
    
  # create a dynamic class
  class bound_state (basestate, baseother) :
    def __init__( self, otherparams=(), stateparams=() ) :
      if not isinstance( otherparams, tuple ) or 
         not isinstance( stateparams, tuple ) :
        raise TypeError( "init parameters of bound states must be passed in tuple sequences." );
        
      basestate.__init__( self, *stateparams );
      baseother.__init__( self, *otherparams );
  return bound_state;
  
# State
# generic state class. Derive this to make your states
class State :
  # _clearHistory
  # clears the _prevlist recursively, ensuring everything is unconnected
  def _clearHistory( self ) :
    self._clearing = True;
    for state in self._prevlist :  
      if state and not state._clearing :
        state._clearHistory;
    self._prevlist.clear();
    self.on_clear( self.machine );
    self.machine = None;
    self._clearing = False;

  # _config
  # called when a state is loaded into a new machine for the first time
  def _config( self, machine ) :
    if self.machine and self.machine == machine :
      return;
    elif self.machine and self.machine != machine :
      warnings.warn( "detected the state {} is being used in two machines at once. This could corrupt the backtrack list.".format( self ),
        ResourceWarning,
        stacklevel=4 );
  
    self.machine = machine;
    self.on_init( machine );
    
  # _popPrevState
  # pops the last previous state off the _prevlist
  def _popPrevState( self ) :
    try:
      return self._prevlist.pop();
    except IndexError:
      return None;
    
  # _setPrevState
  # deals with adding another previous state
  def _setPrevState( self, state ) :
    self._prevlist.append( state );
    
  # _free
  # called when a machine is freed while this state is active
  def _free( self ) :
    self.on_exit();
    self.on_free( self.machine );
    self.machine = None;

  # __init__
  def __init__( self ) :
    self.machine  = None;
    self._prevlist  = [];
    for handler, deffn in REQUIRED_HANDLERS.items() : 
      if handler in dir( self ):
        continue;
        
      fn = lambda: None;
      if deffn:
        fn = deffn;
      setattr( self, handler, fn );
      
  # __getattr__
  # handle pulling states off the _prevlist as if they were exposed
  def __getattr__( self, name ) :
    if name == 'prev_state' :
      return self._prevlist[-1]
    elif name == '_clearing' :
      return False;
    
    raise AttributeError( "'{}' object has no attribute '{}'".format( 
      type( self ),
      name ) );
    
  # __setattr__
  # handle pushing states to the _prevlist
  def __setattr__( self, name, value ) :
    if name == 'prev_state' :
      self._setPrevState( value );
    else :
      object.__setattr__( self, name, value );