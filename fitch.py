######################################################
# File: fitch.py                                     #
# Author: Dan McFalls (dmcfalls@stanford.edu)        #
# Project: Fitch Proof Automation with State-Search  #
# Final Project for CS221: Artificial Intelligence   #
######################################################

import util
import random

########################
#   Helper Functions   #
########################

# Returns a copy of the sentence with extra outer parentheses removed if they exist.
# The general structure of this algorithm is from Gareth Rees on stackoverflow.com:
# http://stackoverflow.com/questions/4284991/parsing-nested-parentheses-in-python-grab-content-by-level
def stripOuterParens(sentence):
    if sentence == "": return sentence
    start = 0
    end = len(sentence)
    stack = []
    pairs = {}
    for i, char in enumerate(sentence):
        if char == '(':
            stack.append(i)
        elif char == ')' and stack:
            pairs[stack.pop()] = i
    for i in range(0, end):
        if i not in pairs.keys() or pairs[i] != (end - 1):
            return sentence[start : end]
        start = i + 1
        end = pairs[i]
    raise Exception("Execution should never reach here.")

# Returns True if the parentheses in the string are balanced and False otherwise.
def parensBalanced(string):
    stack = []
    for i, char in enumerate(string):
        if char == '(':
            stack.append(i)
        elif char == ')':
            if not stack: return False
            stack.pop()
    if stack: return False
    return True

# Returns (isImplication, antecedent, consequent) where:
#   * isImplication is a boolean specifying whether statement has an outermost implication
#   * antecedent is the antecedent of such an implication if it exists
#   * consequent is the consequent of such an implication if it exists
def processImplication(sentence):
    imp_index = sentence.find(" -> ")
    # Scans the string, looking for "phi -> psi" were phi and psi are properly formatted.
    # Takes the first example found since implications generally bind to the left.
    while imp_index > 0:
        antecedent = sentence[:(imp_index)]
        consequent = sentence[(imp_index + 4):]
        if '(' in antecedent or ')' in antecedent:
            if not parensBalanced(antecedent):
                imp_index += 4 + sentence[(imp_index + 4):].find(" -> ")
                continue
            antecedent = stripOuterParens(antecedent.strip())
        if '(' in consequent or ')' in consequent:
            if not parensBalanced(consequent):
                imp_index += 4 + sentence[(imp_index + 4):].find(" -> ")
                continue
            consequent = stripOuterParens(consequent.strip())
        return (True, antecedent, consequent)
    return (False, None, None)

################################################
#   Fitch Proof Search Problem Formalization   #
################################################

# Defines finding a proof in the Fitch system as a search problem
# SearchProblem class from CS221: Artificial Intelligence assignment 3: Text Reconstruction
class FitchProblem(util.SearchProblem):
    # @param premises = list [] of statements using the supplied symbolic conventions
    # @param goal = a statement to be proved, written using the supplied symbolic convenctions
    def __init__(self, premises, goal, symbolSet, statementSet, connectiveSet):
        self.premises = premises
        self.goal = goal
        self.symbols = symbolSet
        self.statementSet = statementSet
        self.connectiveSet = connectiveSet

    # Defines the start state of the search graph given the premises, goal, and symbols
    # The start state is a proof consisting only of premises at assumption level 0.
    def startState(self):
        # A state is defined by a list of tuples, each tuple containing a true statement, its justification, and its proof depth
        statements = []
        for premise in self.premises:
            statements.append((premise, "Premise", 0))
        # The full form of a state is tuple([list of statement, justification, depth tuples], sub-proof level).
        # Subproof level is initially 0.
        return (tuple(statements), 0)

    # Defines the end state of the search graph
    # The end state is defined to be any proof which contains the goal as a non-premise at sub-proof level 0
    def isEnd(self, state):
        statements = list(state[0])
        if len(statements) == 0: return False
        lastStatement = statements[len(statements) - 1]
        # For a state to be the end state, must contain the goal and be at base level (not in a subproof)
        if lastStatement[0] == self.goal and lastStatement[1] != "Premise" and lastStatement[2] == 0:
            return True
        return False

    # Defines the successor state and costs of the given state, represnting a partial proof
    # Successor states are a proof with an added set of lines generated by using one of the Fitch
    # rules of inference.
    # The proof generator only considers proof steps on symbols contained in the symbol set.
    # For the prototype, all paths will have the same cost.
    #
    # @return a list of possible (action, newState, cost) tuples representing successor states.
    #   The return type is:    list of (string, [(sentence, justification, depth), (sentence, justification, depth), etc.], int) tuples
    def succAndCost(self, state):
        
        # Occassionally prints the current state being searched (for testing)
        '''
        if random.random() > 0.9995:
            print state
        '''

        results = []
        allStatements = list(state[0])      # (sentence, justification, depth) tuples
        proofDepth = state[1]               # the subproof depth of the last statement in the proof
        whitespace = ""
        for _ in range(proofDepth):
            whitespace += "  "

        # Extract the statements that matter from the list of all statements made in the proof so far
        # This includes all statements at level 0 and anything in the scope of the current subproof
        # Also makes a list of the sentences alone to help check whether we're being redundent
        statements = []
        sentences = []
        maxDepthAllowed = proofDepth
        for i, statement in reversed(list(enumerate(allStatements))):
            depth = statement[2]
            if depth < maxDepthAllowed:
                maxDepthAllowed -= 1
            elif depth > maxDepthAllowed:
                continue
            statements.append(statement)
            sentences.append(statement[0])
        # Puts all the statements back into the correct ordering
        statements.reverse()

        # An edge case of sorts: if we already have the answer but as a premise, just reiterate it and move on.
        if self.goal in sentences:
            succStatements = list(state[0])
            succStatements.append((self.goal, "R", state[1]))
            succState = (tuple(succStatements), state[1])
            results.append((whitespace + "Reiteration: " + self.goal, succState, 1))
            return results

        # Assumptions
        def Acost(depth):
            if depth <= 2: return max(1, depth)
            return 2**(depth)
        # Bias argument allows adjustment of cost if, say, we know the assumption is probably a good idea.
        def addAssumption(symbol, bias = 1):
            cost = Acost(state[1] + 1) * bias
            succStatements = list(state[0])
            succStatements.append((symbol, "A", state[1] + 1))
            succState = (tuple(succStatements), state[1] + 1)
            A_whitespace = "  " + whitespace
            results.append((A_whitespace + "Assumption: " + symbol, succState, cost))

        # Tries to assume the opposite (of a non-implication) or the antecedent (of an implication)
        isImplication = False
        assumedSomething = False
        for sentence in self.statementSet:
            if len(allStatements) <= len(self.statementSet) and sentence != self.goal:
                if "->" in sentence:
                    isImplication, antecedent, consequent = processImplication(sentence)
                    if isImplication:
                        if sentence not in sentences:
                            addAssumption(sentence, 0.25)
                            assumedSomething = True
                        if antecedent not in sentences:
                            addAssumption(antecedent, 0.25)
                            assumedSomething = True

                # The following ended up being too specific a strategy for the general problem, so I've omitted it.
                '''
                if not isImplication:
                    if ("&&" in sentence or "||" in sentence or "->" in sentence):
                        addAssumption("~(" + sentence + ")", 0.75)
                        assumedSomething = True
                    else:
                        addAssumption("~" + sentence, 0.75)
                        assumedSomething = True
                '''

        # Assumptions of single propositional constants and their negations
        for symbol in self.symbols:
            cost = 3 if assumedSomething else 1
            addAssumption(symbol, cost)
            addAssumption("~" + symbol, cost)

        # Used for And Introduction and And Elimination
        if "&&" in self.connectiveSet:
            atoms = set()
            conjuncts = set()

        # Used for Or Elimination
        if "||" in self.connectiveSet:
            disjuncts = set()

        # Gathers implications -- Used for Negation Introduction (and Or Elimination, if applicable)
        phi_to_psi = {}                 # Dict from string to list(string) representing phi to all psi
        phi_to_not_psi = {}             # Dict from string to list(string) representing phi to all not psi

        # Most of the rules of inference are covered or prepped for within this for loop.
        for statement in statements:

            if "&&" in self.connectiveSet:
                # And Introduction
                sentence = statement[0]
                atoms.add(sentence)

                # And Elimination
                sentenceCopy = statement[0]
                and_index = sentenceCopy.find(" && ")
                while and_index != -1:
                    conjunct = sentenceCopy[:(and_index)]
                    # If the parentheses are balanced in the string it is assumed to be a proper conjunct
                    if parensBalanced(conjunct):
                        conjuncts.add(conjunct)
                    sentenceCopy = sentenceCopy[(and_index + 4):]
                    and_index = sentenceCopy.find(" && ")
                # Loop and a half
                conjunct = sentenceCopy
                if conjunct != "":
                    if parensBalanced(conjunct):
                        conjuncts.add(conjunct)

            if "||" in self.connectiveSet:
                # Or Introduction
                sentence = statement[0]
                def addDisjunction(disjunction):
                    # The cost below determines the efficiency of the algorithm to a large degree
                    cost = 1 if (disjunction == self.goal) else len(disjunction)
                    succStatements = list(state[0])
                    succStatements.append((disjunction, "OI", state[1]))
                    succState = (tuple(succStatements), state[1])
                    results.append((whitespace + "Or Introduction: " + disjunction, succState, cost))
                # We deliberately hamper this rule because it is not very interesting.
                if len(sentence) == 1:
                    for symbol in self.symbols:
                        disjunction = sentence + " || " + symbol
                        if disjunction not in sentences:
                            addDisjunction(disjunction)
                        not_disjunction = sentence + " || ~" + symbol
                        if not_disjunction not in sentences:
                            addDisjunction(not_disjunction)

                # Or Elimination
                sentenceCopy = statement[0]
                disjunct = []   # List of statements connected by "||"
                or_index = sentenceCopy.find(" || ")
                if or_index > -1:
                    while or_index > -1:
                        atom = sentenceCopy[:(or_index)]
                        # If the parentheses are balanced for the atom, we take it to properly be part of a disjunction
                        if parensBalanced(atom):
                            disjunct.append(atom)
                        sentenceCopy = sentenceCopy[(or_index + 4):]
                        or_index = sentenceCopy.find(" || ")
                    # Loop and a half
                    disjunct.append(sentenceCopy)
                    disjuncts.add(tuple(disjunct))

            # Negation Introduction
            sentence = statement[0]
            isImplication, antecedent, consequent = processImplication(sentence)
            if isImplication:
                if consequent[0] == "~":
                    if antecedent not in phi_to_not_psi.keys():
                        phi_to_not_psi[antecedent] = list()
                    phi_to_not_psi[antecedent].append(consequent[1:])
                else:
                    if antecedent not in phi_to_psi.keys():
                        phi_to_psi[antecedent] = list()
                    phi_to_psi[antecedent].append(consequent)

            # Negation Elimination
            if sentence[:2] == "~~":
                newSentence = stripOuterParens(sentence[2:])
                if newSentence not in sentences:
                    succStatements = list(state[0])
                    succStatements.append((newSentence, "NE", state[1]))
                    succState = (tuple(succStatements), state[1])
                    results.append((whitespace + "Negation Elimination: " + newSentence, succState, 1))

            # Implication Elimination
            # Reuses the implication processing from the NI step.
            if isImplication:
                # Loops through all statements and sees if antecedent appears enabling us to derive consequent
                for statement2 in statements:
                    if statement2 == statement:
                        continue
                    sentence2 = statement2[0]
                    if sentence2 == antecedent and consequent not in sentences:
                        succStatements = list(state[0])
                        succStatements.append((consequent, "IE", state[1]))
                        succState = (tuple(succStatements), state[1])
                        results.append((whitespace + "Implication Elimination: " + consequent, succState, 1))

            # Biconditional Elimination
            def addBicondElimStatement(lhs, rhs, statements):
                newImplication = lhs + " -> " + rhs
                if newImplication not in sentences:
                    succStatements = list(state[0])
                    succStatements.append((newImplication, "BE", state[1]))
                    succState = (tuple(succStatements), state[1])
                    results.append((whitespace + "Biconditional Elimination: " + newImplication, succState, 1))

            if "<->" in self.connectiveSet:
                sentence = statement[0]
                bicond_index = sentence.find(" <-> ")
                while bicond_index > 0:
                    first = sentence[:(bicond_index)]
                    second = sentence[(bicond_index + 5):]
                    addBicondElimStatement(first, second, statements)
                    addBicondElimStatement(second, first, statements)
                    bicond_index = sentence[(bicond_index + 5):].find(" <-> ")

        if "&&" in self.connectiveSet:
            # Finishes adding all possible statements from And Introduction
            for atom1 in atoms:
                for atom2 in atoms:
                    conjunction = atom1.strip() + " && " + atom2.strip()
                    if conjunction not in sentences:
                        # We punish this rule of inference as well for being, quite frankly, not very interesting
                        cost = 10 if atom1 == atom2 else 3
                        succStatements = list(state[0])
                        succStatements.append((conjunction, "AI", state[1]))
                        succState = (tuple(succStatements), state[1])
                        results.append((whitespace + "And Introduction: " + conjunction, succState, cost))

            # Finishes adding all possible statements from And Elimination
            for conjunct in conjuncts:
                if conjunct not in sentences:
                    succStatements = list(state[0])
                    succStatements.append((conjunct, "AE", state[1]))
                    succState = (tuple(succStatements), state[1])
                    results.append((whitespace + "And Elimination: " + conjunct, succState, 1))   

        if "||" in self.connectiveSet:
            # Finishes adding all possible statement from Or Elimination
            def addOrElimStatement(psi):
                succStatements = list(state[0])
                succStatements.append((psi, "OE", state[1]))
                succState = (tuple(succStatements), state[1])
                results.append((whitespace + "Or Elimination: " + psi, succState, 1))
            
            # Iterates through atoms in each disjunct and derives all things implied by every disjuncted unit
            for disjunction in list(disjuncts):    # List of disjuncted atoms
                isEntailed = True
                # Populate a list with all examples of psi for some implication statement (phi -> psi)
                psi_list = []
                for psi_l in phi_to_psi.values():
                    for psi in psi_l:
                        psi_list.append(psi)
                for not_psi_l in phi_to_not_psi.values():
                    for not_psi in not_psi_l:
                        psi_list.append("~" + not_psi)
                # Iterate through every psi and, if (phi -> psi) exists for every phi in the disjunction,
                # then we can add an or elimination statement containing psi
                for psi in psi_list:
                    if psi[:1] == "~":
                        for phi in disjunction:
                           if phi not in phi_to_not_psi.keys() or psi.strip("~") not in phi_to_not_psi[phi]:
                                isEntailed = False
                    else:
                        for phi in disjunction:
                            if phi not in phi_to_psi.keys() or psi not in phi_to_psi[phi]:
                                isEntailed = False
                    if isEntailed and psi not in sentences:
                        addOrElimStatement(psi)

        # Processes the dicts built during the above for loop to cover Negation Introduction cases
        for phi in phi_to_psi.keys():
            for psi in phi_to_psi[phi]:
                if phi in phi_to_not_psi.keys() and psi in phi_to_not_psi[phi]:
                    negation = "~" + phi
                    if negation not in sentences:
                        succStatements = list(state[0])
                        succStatements.append((negation, "NI", state[1]))
                        succState = (tuple(succStatements), state[1])
                        results.append((whitespace + "Negation Introduction: " + negation, succState, 1))

        # Implication Introduction and Reiteration
        if proofDepth > 0:
            subproof = []
            # Gets a list of all statements in the most recent subproof
            for i in range(len(statements)):
                if statements[i][2] < proofDepth:
                    subproof = []
                    continue
                elif statements[i][2] > proofDepth:
                    continue
                subproof.append(statements[i])

            # Allows Implication Introduction from the assumption to any reached conclusion
            assumption = subproof[0]
            assert assumption[1] == "A"
            for statement in subproof[1:]:
                # If the antecedent contains an implication or biconditional, we need parens around it
                if "->" in assumption[0]:
                    antecedent = "(" + assumption[0] + ")"
                else:
                    antecedent = assumption[0]
                newImplication = antecedent + " -> " + statement[0]
                if newImplication not in sentences:
                    succStatements = list(state[0])
                    succStatements.append((newImplication, "II", state[1] - 1))
                    succState = (tuple(succStatements), state[1] - 1)
                    II_whitespace = whitespace[2:]
                    results.append((II_whitespace + "Implication Introduction: " + newImplication, succState, 1))

            # Reiteration of statements allowed if we're inside a subproof
            for sentence in sentences:
                if sentence not in subproof or self.goal == sentence:
                    succStatements = list(state[0])
                    succStatements.append((sentence, "R", state[1]))
                    succState = (tuple(succStatements), state[1])
                    results.append((whitespace + "Reiteration: " + sentence, succState, 1))


        # Biconditional Introduction
        # If 'phi -> psi' and 'psi -> phi' for any phi and psi, can derive 'phi <-> psi'
        if "<->" in self.connectiveSet:
            phi_to_psi.update(phi_to_not_psi)   # Merges the 2 implication dicts
            for phi in phi_to_psi.keys():
                psi = phi_to_psi[phi]
                if psi in phi_to_psi.keys() and phi in phi_to_psi[psi]:
                    newBicond = phi + " <-> " + psi
                    if newBicond not in sentences:
                        succStatements = list(state[0])
                        succStatements.append((newBicond, "BI", state[1]))
                        succState = (tuple(succStatements), state[1])
                        results.append((whitespace + "Biconditional Introduction: " + newBicond, succState, 1))
        
        return results

# Uses a search problem and UCS to find a proof of a goal given premises
def solveFitchProof(premises, goal):
    # The first section formats the input into a usable format and extracts symbols
    symbolSet = set()
    # The statement set is used to keep track of full, parenthesized statements
    statementSet = set()
    connectiveSet = set()

    formattedPremises = []
    if premises != None:
        premiseSymbols = premises.split()
    else:
        premiseSymbols = []
    goalSymbols = goal.split()

    currPremise = 0     # The number of premises added to the list so far
    currUnit = ""       # The formatted premise so far

    inParens = False    # Keeps track of whether inside parentheses
    parensDepth = 0     # Depth of parentheses
    currParenUnit = ""  # The parenthesized unit made so far

    for symbol in premiseSymbols:
        if symbol == "*":
            if currPremise == 0:
                currPremise += 1
                continue
            formattedPremises.append(currUnit)
            currPremise += 1
            currUnit = ""

        elif symbol == "(":
            parensDepth += 1
            inParens = True
            currUnit += "("
        elif symbol == ")":
            parensDepth -= 1
            if parensDepth == 0: inParens = False
            currUnit += ")"
            currParenUnit = ""

        elif symbol == "AND" or symbol == "and" or symbol == "&&" or symbol == "&":
            currUnit += " && "
            connectiveSet.add("&&")
            if inParens: currParenUnit += " && "
        elif symbol == "OR" or symbol == "or" or symbol == "||" or symbol == "|":
            currUnit += " || "
            connectiveSet.add("||")
            if inParens: currParenUnit += " || "
        elif symbol == "NOT" or symbol == "not" or symbol == "~":
            currUnit += "~"
            if inParens: currParenUnit += "~"
        elif symbol == "=>" or symbol == "->":
            currUnit += " -> "
            if inParens: currParenUnit += " -> "
        elif symbol == "<=>" or symbol == "<->":
            currUnit += " <-> "
            connectiveSet.add("<->")
            if inParens: currParenUnit += " <-> "

        else:
            currUnit += symbol
            if inParens: currParenUnit += symbol
            symbolSet.add(symbol)

    # One and a half loops (less than a half, actually)
    if premises != None:
        formattedPremises.append(currUnit)

    currUnit = ""
    for symbol in goalSymbols:
        if symbol == "(":
            parensDepth += 1
            inParens = True
            currUnit += "("
        elif symbol == ")":
            parensDepth -= 1
            if parensDepth == 0: inParens = False
            currUnit += ")"
            currParenUnit = ""

        elif symbol == "AND" or symbol == "and" or symbol == "&&" or symbol == "&":
            currUnit += " && "
            connectiveSet.add("&&")
            if inParens: currParenUnit += " && "
        elif symbol == "OR" or symbol == "or" or symbol == "||" or symbol == "|":
            currUnit += " || "
            connectiveSet.add("||")
            if inParens: currParenUnit += " || "
        elif symbol == "NOT" or symbol == "not" or symbol == "~":
            currUnit += "~"
            if inParens: currParenUnit += "~"
        elif symbol == "=>" or symbol == "->":
            currUnit += " -> "
            if inParens: currParenUnit += " -> "
        elif symbol == "<=>" or symbol == "<->":
            currUnit += " <-> "
            connectiveSet.add("<->")
            if inParens: currParenUnit += " <-> "

        else:
            currUnit += symbol
            if inParens: currParenUnit += symbol
            symbolSet.add(symbol)

    formattedGoal = currUnit
    
    # Adds the goal to the statement set, since we might want to assume its negation.
    statementSet.add(formattedGoal)

    # Breaks the formatted goal into its parenthesized units and adds each of them to statementSet.
    def genParenUnits(formattedGoal):
        units = []
        stack = []
        for i, c in enumerate(formattedGoal):
            if c == "(":
                stack.append(i)
            elif c == ")" and stack:
                start = stack.pop()
                units.append(formattedGoal[start + 1 : i])
        return units

    units = genParenUnits(formattedGoal)
    for unit in units:
        if unit == "": continue
        statementSet.add(unit)

    # Prints the set of "meaningful statements" from the goal (for testing)
    # print statementSet

    # Prints the processed versions of the premises and goal (for testing)
    '''
    for premise in formattedPremises:
        print "Premise: ", premise
    print "Goal: ", formattedGoal
    '''

    # Solve the search problem with UCS
    ucs = util.UniformCostSearch(verbose = 0)
    ucs.solve(FitchProblem(formattedPremises, formattedGoal, symbolSet, statementSet, connectiveSet))
    proof = ucs.actions

    # Prints the premises, which do not appear in the solved proof's actions.
    for premise in formattedPremises:
        print "Premise: ", premise

    # Prints the proof, step by step.
    for step in proof:
        print step
    
    return proof
