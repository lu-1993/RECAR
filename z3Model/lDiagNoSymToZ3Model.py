#!/usr/bin/python3
# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from z3 import *
from z3Model import Z3Model

# Here are some suppositions:
# The NOP operation is represented by the ID 0
# The faulty transition is labelled with 1
# A non observable transition is labelled with 2

class LDiagNoSymToZ3Model (Z3Model):
    # z3 variables.
    startLoop = Int("startLoop")
    endLoop = Int("endLoop")

    projStartStateNormal = Int("projStartStateNormal")
    projEndStateNormal = Int("projEndStateNormal")
    projStartStateFaulty = Int("projStartStateFaulty")
    projEndStateFaulty = Int("projEndStateFaulty")

    stateFaultyPath = [ Int("stateF_1") ]
    stateNormalPath = [ Int("stateN_1") ]

    # parameter
    BOUND = 0

    # 'constants'
    NOP = 0
    FAULT = 1
    NO_OBS = 2
    NOP_TRANSITION = 0

    def __init__(self, nameFile):
        """
        Constructor.

        :param nameFile: where is stored the automaton
        :type nameFile: str
        """
        self.symActicated = False
        super().__init__(nameFile, False)
        self.addConstraintOnIdTransition(0)

        self.s.add(self.startLoop < self.BOUND - 1)
        self.s.add(self.startLoop >= 0)

        self.s.add(self.endLoop <= self.startLoop)
        self.s.add(self.endLoop >= 0)
        self.s.add(self.projStartStateNormal == self.projEndStateNormal)
        self.s.add(self.projStartStateFaulty == self.projEndStateFaulty)

        self.s.add(self.projStartStateNormal != -1)
        self.s.add(self.projStartStateFaulty != -1)
        self.s.add(self.projEndStateNormal != -1)
        self.s.add(self.projEndStateFaulty != -1)

        self.addConstraintOnIdTransition(0)


    def addConstraintOnIdTransition(self, pos):
        """
        Add the constraint that fix the id of the transition pos in both
        idTransitionFaultyPath and idTransitionNormalPath.

        :param pos: the position of the operation we consider.
        :type pos: int
        """
        super().addConstraintOnIdTransition(pos)

        self.s.add(Implies(self.startLoop == pos, self.faultOccursByThePast[pos]))

        for j in range(len(self.transitionList)):
            self.s.add(Implies(self.faultyPath[pos - 1] == j, self.stateFaultyPath[pos] == self.transitionList[j][1]))
            self.s.add(Implies(self.normalPath[pos - 1] == j, self.stateNormalPath[pos] == self.transitionList[j][1]))

        if pos > 0:
            self.s.add(Implies(self.startLoop == pos - 1, self.projStartStateNormal == self.stateNormalPath[pos]))
            self.s.add(Implies(self.startLoop == pos - 1, self.projStartStateFaulty == self.stateFaultyPath[pos]))

        self.s.add(Implies(self.endLoop == pos, self.projEndStateNormal == self.stateNormalPath[pos]))
        self.s.add(Implies(self.endLoop == pos, self.projEndStateFaulty == self.stateFaultyPath[pos]))

        self.s.add(Or(self.startLoop < pos, Not(self.checkSynchro[pos]), self.idTransitionFaultyPath[pos] == self.idTransitionNormalPath[pos]))


    def incVariableList(self):
        """
        Increment all the list with one new z3 variable.
        """
        super().incVariableList()

        idx = len(self.faultyPath) + 1
        self.stateFaultyPath.append(Int("stateF_" + str(idx)))
        self.stateNormalPath.append(Int("stateN_" + str(idx)))


    def incBound(self):
        """
        Extend the bound allowing a new transition.
        """
        # increment the bound for the local variables.
        self.incVariableList()
        super().incBound()

        # get the last variable.
        idx = len(self.stateNormalPath) - 1
        assert(idx > 0)

        # we add the constraints that specify the id of the transition
        self.addConstraintOnIdTransition(idx)


    def displayInfo(self):
        self.printAutomatonInfo()
        print("[L DIAG] BOUND:", self.BOUND)
        print("[L DIAG] Symmetry activated:", self.symActicated)


    def checkModel(self, model):
        """
        [DEBUG FUNCTION]
        Check out if the given model satisfies basic property s.t. transitions
        follow a valid scheme, the id are correct, ...

        :param model: the model we want to check.
        :type model: a z3 model.
        """
        # TODO


    def printModel(self, model):
        """
        Print the model. That means information about the z3 variables and a output formal
        that can be considered for the checker.

        :param model: the model we want to check.
        :type model: a z3 model.
        """
        print("[L DIAG] startLoop =", model.evaluate(self.startLoop))
        print("[L DIAG] endLoop =", model.evaluate(self.endLoop))
        print("[L DIAG] projStartStateFaulty =", model.evaluate(self.projStartStateFaulty))
        print("[L DIAG] projEndStateFaulty =", model.evaluate(self.projEndStateFaulty))
        print("[L DIAG] projStartStateNormal =", model.evaluate(self.projStartStateNormal))
        print("[L DIAG] projEndStateNormal =", model.evaluate(self.projEndStateNormal))

        print("[L DIAG] stateFaultyPath: ")
        self.printOneIntArray(model, self.stateFaultyPath)
        print("[L DIAG] stateNormalPath: ")
        self.printOneIntArray(model, self.stateNormalPath)

        print()
        super().printModel(model)


    def run(self):
        """
        Run the main program.
        """
        cpt = 1
        while cpt < (self.BOUND):
            cpt += 1
            self.incBound()

        res = self.s.check()
        if res == sat:
            m = self.s.model()
            self.checkModel(m)
            self.printModel(m)
            return
        else:
            print("The problem is UNSAT")
