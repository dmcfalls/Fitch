import fitch
import util
import time

def main():

    # Shorthand for passing a problem to the solver and printing the time it took to execute
    def prove(premises, goal):
        start_time = time.time()
        fitch.solveFitchProof(premises, goal)
        runtime = time.time() - start_time
        print "Time to execute: %s seconds" % runtime
        print ""

    ###########################################################################################
    # The following section includes exercises from an introductory course that Stanford      #
    # offers on logic and automated reasoning. My solver can finish most of them efficiently, #
    # but a few required proofs either too long or complicated for the system I have in place #
    # so far. Those exercises commented out fall into this category.                          #
    ###########################################################################################

    # 4.1
    prove("* p * q * p AND q => r", "r")
    # 4.2
    prove("* p AND q", "q OR r")
    # 4.3
    prove("* p => q * q <=> r", "p => r")

    # 4.4 (prelude 1)
    prove("* p => r * q => r * p OR q", "r")
    # 4.4 (prelude 2)
    prove("* p => q * m => p OR q * q => q", "m => q")
    # 4.4 (prelude 3)
    prove("* p => q * m => p OR q", "q => q")
    
    # 4.4 (this one takes a little under a minute, so don't be surprised if it hangs here for a while)
    prove("* p => q * m => p OR q", "m => q")
    # 4.5
    prove("* p => q => r", "( p => q ) => p => r")
    # 4.6
    prove(None, "p => q => p")

    # 4.7 (this one takes a while: around 1735-2000 seconds. it's commented out here to allow the other tests to run)
    # prove(None, "( p => q => r ) => ( p => q ) => p => r")

    # 4.8
    prove(None, "( ~p => q ) => ( ~p => ~q ) => p")
    # 4.9
    prove("* p", "NOT NOT p")
    # 4.10
    prove("* p => q", "NOT q => NOT p")

    # The following tests fall into the category of "too tough" for my baby logician, due to either complexity or difficulty.
    # 4.11, 4.13, and 4.14 require assuming the negation of the goal, which is left for future work.
    # 4.12 requires too long a proof, so the search space gets too big for it to terminate in reasonable time.

    # 4.11
    # prove("* p => q", "NOT p OR q")
    # 4.12
    # prove(None, "((p => q) => p) => q")
    # 4.13
    # prove("* NOT ( p OR q )", "NOT p AND NOT q")
    # 4.14
    # prove(None, "p OR NOT p")

    ##########################################################################
    # The following are some example premises/goal pairs that I came up with #
    # to test the solver.                                                    #
    ##########################################################################

    # Simple proof using only Reiteration
    print "Given 'p', prove 'p':\n"
    prove("* p", "p")

    # Implication Elimination
    print "Given 'p -> q' and 'p', prove 'q':\n"
    prove("* p => q * p", "q")

    # Uses Assumption and Implication Introduction
    print "Given 'p' and 'q', prove 'p -> q':\n"
    prove("* p * q", "p => q")

    # Uses And Introduction and Implication Elimination
    print "Prove 'r' from the premises 'p', 'p -> q', and '(p && q) -> r':\n"
    prove("* p * p => q * ( p AND q ) => r", "r")

    # Uses And Introduction and Elimination
    print "Prove 'p && q' from the premises 'p' and 'p -> q':\n"
    prove("* p * p => q", "p AND q")

    # Even more complicated Implication Introduction
    print "From the empty set of premises, prove 'p -> q -> p -> p':\n"
    prove(None, "p => q => p => p")

    # Basic test of Negation Introduction
    print "Given 'p => q' and 'p => ~q', prove '~p':\n"
    prove("* p => q * p => ~q", "~p")

    # More complicated Negation Introduction
    print "Prove '~p' from the premises 'q' and '~q':\n"
    prove("* q * NOT q", "NOT p")

    # Implication Introduction, Negation Introduction, and Negation Elimination
    print "Prove 'p' from the premises 'q' and '~q':\n"
    prove("* q * NOT q", "p")
    
    #######################################################################
    # The following is an example of something the solver can't prove yet #
    #######################################################################

    # Proof of tautology "p || ~p" from empty set of premises
    # print "Prove 'p || ~p' from empty set of premises:\n"
    # prove(None, "p OR NOT p")

if __name__ == "__main__":
    main()
