import numpy as np
import scipy.sparse as sparse

from .world import World
from . import util
from . import fem
from . import linalg

def solveFine(world, aFine, MbFine, AbFine, boundaryConditions, return_fine=False):
    NWorldFine = world.NWorldCoarse*world.NCoarseElement
    NpFine = np.prod(NWorldFine+1)
    
    if MbFine is None:
        MbFine = np.zeros(NpFine)

    if AbFine is None:
        AbFine = np.zeros(NpFine)
        
    boundaryMap = boundaryConditions==0
    fixedFine = util.boundarypIndexMap(NWorldFine, boundaryMap=boundaryMap)
    freeFine  = np.setdiff1d(np.arange(NpFine), fixedFine)

    if aFine.ndim == 1:
        ALocFine = world.ALocFine
    else:
        ALocFine = world.ALocMatrixFine

    AFine = fem.assemblePatchMatrix(NWorldFine, ALocFine, aFine)
    MFine = fem.assemblePatchMatrix(NWorldFine, world.MLocFine)
    H1Fine = fem.assemblePatchMatrix(NWorldFine, world.ALocFine)
    
    bFine = MFine*MbFine + AFine*AbFine
    
    AFineFree = AFine[freeFine][:,freeFine]
    bFineFree = bFine[freeFine]

    uFineFree = linalg.linSolve(AFineFree, bFineFree)
    uFineFull = np.zeros(NpFine)
    uFineFull[freeFine] = uFineFree
    uFineFull = uFineFull

    if return_fine:
        return uFineFull, AFine, MFine, H1Fine, freeFine
    return uFineFull, AFine, MFine


def solveCoarse(world, aFine, MbFine, AbFine, boundaryConditions):
    NWorldCoarse = world.NWorldCoarse
    NWorldFine = world.NWorldCoarse*world.NCoarseElement
    NCoarseElement = world.NCoarseElement
    
    NpFine = np.prod(NWorldFine+1)
    NpCoarse = np.prod(NWorldCoarse+1)
    
    if MbFine is None:
        MbFine = np.zeros(NpFine)

    if AbFine is None:
        AbFine = np.zeros(NpFine)
        
    boundaryMap = boundaryConditions==0
    fixedCoarse = util.boundarypIndexMap(NWorldCoarse, boundaryMap=boundaryMap)
    freeCoarse  = np.setdiff1d(np.arange(NpCoarse), fixedCoarse)

    if aFine.ndim == 1:
        ALocFine = world.ALocFine
    else:
        ALocFine = world.ALocMatrixFine

    AFine = fem.assemblePatchMatrix(NWorldFine, ALocFine, aFine)
    MFine = fem.assemblePatchMatrix(NWorldFine, world.MLocFine)

    bFine = MFine*MbFine + AFine*AbFine

    basis = fem.assembleProlongationMatrix(NWorldCoarse, NCoarseElement)
    bCoarse = basis.T*bFine
    ACoarse = basis.T*(AFine*basis)

    ACoarseFree = ACoarse[freeCoarse][:,freeCoarse]
    bCoarseFree = bCoarse[freeCoarse]

    uCoarseFree = linalg.linSolve(ACoarseFree, bCoarseFree)
    uCoarseFull = np.zeros(NpCoarse)
    uCoarseFull[freeCoarse] = uCoarseFree
    uCoarseFull = uCoarseFull

    uFineFull = basis*uCoarseFull
    
    return uCoarseFull, uFineFull
