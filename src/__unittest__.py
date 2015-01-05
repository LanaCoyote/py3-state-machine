import machine
import state
import random
import unittest

# Classes and functions used in testing
def val_triple_plus_one( val ) :
    return val * 3 + 1;
    
def val_half( val ) :
    return val // 2;

class CollatzState(state.State) :
    def on_update( self, val ) :
        if val % 2 :
            self.machine.changeState( OddState );
        else :
            self.machine.changeState( EvenState );
        return self.machine.operate( val );
        
    def __init__( self, opfn=(lambda: None) ) :
        state.State.__init__( self );
        
        self.on_operate = opfn
        
class BindMe :
    def on_function( self ) :
        self.value += 1;
        return self.value;
        
    def on_getvalue( self ) :
        return self.value;
        
    def __init__( self, value=0 ) :
        self.value = value;
        
OddState    = CollatzState( opfn=val_triple_plus_one );
EvenState   = CollatzState( opfn=val_half );

# Test cases
# StateMachineTest
# Generic state machine operation tests
class StateMachineTest( unittest.TestCase ) :
    
    # Build some simple states and a machine to use for testing
    def setUp( self ) :
        self.value          = None;
        self.exit_value     = None;
        
        class SetValueState(state.State) :
            def on_enter( telf ) :
                self.value = telf.val;
                
            def on_exit( telf ) :
                self.exit_value = telf.val;
        
            def __init__( telf, val ) :
                state.State.__init__( telf );
                telf.val        = val;
                telf.on_dothis  = lambda: None;
        
        self.HelloState     = SetValueState( "Hello!" );
        self.GoodbyeState   = SetValueState( "Goodbye!" );
        self.RegState       = state.State();
        
        self.Machine        = machine.Machine( self.HelloState );
        self.GenMachine     = machine.Machine( self.HelloState, generic=True );
    
    # Make sure we can change states and their callbacks fire correctly
    def test_change_state( self ) :
        self.Machine.changeState( self.HelloState );
        self.Machine.changeState( self.GoodbyeState );
        self.assertEqual( self.value, "Goodbye!" );
        self.assertEqual( self.exit_value, "Hello!" );
        
    # Test the strictly typed functionality of our state machine
    def test_strict_typing( self ) :
        self.assertRaises( TypeError, self.Machine.changeState, self.RegState );
        
    # Test the generic typed functionality of our state machine
    def test_generic_typing( self ) :
        self.GenMachine.changeState( self.RegState );
        self.assertEqual( self.GenMachine.state, self.RegState );
        
    # Test that strictly typed machines can execute handlers
    def test_strict_handlers( self ) :
        self.Machine.changeState( self.HelloState );
        self.Machine.enter();
        self.Machine.update();
        self.Machine.dothis();
        
    # Test that generic typed state machines can execute generic handlers
    def test_generic_handers( self ) :
        self.GenMachine.enter();
        self.GenMachine.update();
        self.assertRaises( AttributeError, self.GenMachine.dothis );
        
    # Tests that comparison between a machine and a state works
    def test_state_comparison( self ) :
        self.Machine.changeState( self.HelloState );
        self.assertEqual( self.Machine, self.HelloState );
        self.assertTrue( self.Machine != self.GoodbyeState );
        
    # Test that machines can clear history successfully
    def test_clear( self ) :
        self.Machine.changeState( self.HelloState );
        self.Machine.changeState( self.GoodbyeState );
        self.Machine.changeState( self.GoodbyeState );
        self.Machine.changeState( self.HelloState );
        self.Machine.changeState( self.GoodbyeState );
        self.Machine.changeState( self.GoodbyeState );
        prevlen = self.Machine.state._prevlist;
        self.assertTrue( len( prevlen ) > 0 );
        self.Machine.clearHistory();
        self.assertEqual( len( prevlen ), 0 );
        self.assertEqual( self.Machine.prev_state, None );
        
    # Test that machines can shut down successfully
    def test_free( self ) :
        self.Machine.changeState( self.HelloState );
        self.Machine.changeState( self.GoodbyeState );
        self.Machine.changeState( self.GoodbyeState );
        self.Machine.changeState( self.HelloState );
        self.Machine.changeState( self.GoodbyeState );
        self.Machine.changeState( self.GoodbyeState );
        prevlen = self.Machine.state._prevlist;
        self.assertTrue( len( prevlen ) > 0 );
        self.Machine.free();
        self.assertEqual( len( prevlen ), 0 );
        self.assertEqual( self.Machine.state, None );
        self.assertRaises( machine.StateMachineError, self.Machine.backtrack );
        
    # Make sure we can backtrack at least once
    def test_back_state( self ) :
        self.Machine.changeState( self.HelloState );
        self.Machine.clearHistory();
        self.Machine.changeState( self.GoodbyeState );
        self.assertEqual( self.value, "Goodbye!" );
        self.Machine.backtrack();
        self.assertEqual( self.value, "Hello!" );
        
    # Make sure we can backtrack multiple times
    def test_back_state_multiple( self ) :
        self.Machine.changeState( self.HelloState );
        self.Machine.clearHistory();
        self.Machine.changeState( self.GoodbyeState );
        self.Machine.changeState( self.HelloState );
        self.Machine.changeState( self.GoodbyeState );
        self.assertEqual( self.value, "Goodbye!" );
        self.Machine.backtrack();
        self.assertEqual( self.value, "Hello!" );
        self.Machine.backtrack();
        self.assertEqual( self.value, "Goodbye!" );
        self.Machine.backtrack();
        self.assertEqual( self.value, "Hello!" );
        
    # Make sure we can backtrack over the same states through a long chain
    def test_back_state_far( self ) :
        steps   = 10;
        self.Machine.changeState( self.HelloState );
        self.Machine.clearHistory();
        for i in range( steps ) :
            self.Machine.changeState( self.GoodbyeState );
        for i in range( steps ) :
            self.Machine.backtrack();
        self.assertEqual( self.value, "Hello!" );
            
    # Stress test how far we can backtrack
    def test_back_state_very_far( self ) :
        steps   = 1000;
        self.Machine.changeState( self.HelloState );
        self.Machine.clearHistory();
        for i in range( steps ) :
            self.Machine.changeState( self.GoodbyeState );
        for i in range( steps ) :
            self.Machine.backtrack();
        self.assertEqual( self.value, "Hello!" );
            
    # Make sure that we can't backtrack too far
    def test_back_state_error( self ) :
        self.Machine.changeState( self.HelloState );
        self.Machine.clearHistory();
        self.assertRaises( machine.EndOfBacktrack, self.Machine.backtrack );

# BindingTest
# Tests the ability to bind states with other classes
class _BindingTest( unittest.TestCase ) :
    
    def test_bind( self ) :
        bindclass   = state.bind( BindMe );
        mystate     = bindclass();
        self.assertTrue( isinstance( mystate, BindMe ) );
        self.assertTrue( isinstance( mystate, state.State ) );
        mymachine   = machine.Machine( mystate );
        self.assertEqual( mymachine.function(), 1 );
        self.assertEqual( mymachine.function(), 2 );
        self.assertEqual( mymachine.function(), 3 );
        
    def test_base_bind( self ) :
        bindclass   = state.bind( state.State, BindMe );
        mystate     = bindclass();
        self.assertTrue( isinstance( mystate, BindMe ) );
        self.assertTrue( isinstance( mystate, state.State ) );
        mymachine   = machine.Machine( mystate );
        self.assertEqual( mymachine.function(), 1 );
        self.assertEqual( mymachine.function(), 2 );
        self.assertEqual( mymachine.function(), 3 );
        
    def test_multi_bind( self ) :
        bindclass   = state.bind( CollatzState, BindMe );
        mystate     = bindclass();
        self.assertTrue( isinstance( mystate, BindMe ) );
        self.assertTrue( isinstance( mystate, CollatzState ) );
        mymachine   = machine.Machine( mystate );
        self.assertEqual( mymachine.function(), 1 );
        self.assertEqual( mymachine.function(), 2 );
        self.assertEqual( mymachine.function(), 3 );
        
    def test_bind_init( self ) :
        bindclass   = state.bind( BindMe );
        mystate     = bindclass( ( 5, ) );
        self.assertEqual( mystate.value, 5 );
        self.assertRaises( TypeError, bindclass, 5 );
        
    def test_multiple_bound_states( self ) :
        bindclass   = state.bind( BindMe );
        state1      = bindclass();
        state2      = bindclass();
        state3      = bindclass( ( 2, ) );
        mymachine   = machine.Machine( state1 );
        self.assertEqual( mymachine.function(), 1 );
        self.assertEqual( mymachine.function(), 2 );
        mymachine.changeState( state2 );
        self.assertEqual( mymachine.function(), 1 );
        mymachine.changeState( state3 );
        self.assertEqual( mymachine.function(), 3 );
        mymachine.backtrack();
        self.assertEqual( mymachine.function(), 2 );
        self.assertEqual( mymachine.function(), 3 );
        mymachine.changeState( state1 );
        self.assertEqual( mymachine.function(), 3 );
        
# CollatzTest
# Tests the real world applications of the state machine by using it to build collatz sequences
class _CollatzTest( unittest.TestCase ) :
    
    def setUp( self ) :
        self.Machine    = machine.Machine( OddState );
        
    def collatz( self, min, max=0 ) :
        if max > min:
            self.value = random.randint(min,max);
        else:
            self.value = min;
            
        self.Machine.changeState( OddState );
        
        while self.value > 1 :
            self.value = self.Machine.update( self.value );
        self.Machine.free();
    
    def test_collatz( self ) :
        self.collatz( 78 );
        self.assertEqual( self.value, 1 );
    
    def test_rand_collatz( self ) :
        self.collatz( 1, 100 );
        self.assertEqual( self.value, 1 );
        
    def test_long_collatz( self ) :
        self.collatz( 1000000 );
        self.assertEqual( self.value, 1 );
        
if __name__ == "__main__" :
    unittest.main();
