# myTeam.py
# ---------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


from captureAgents import CaptureAgent
import random, time, util
from game import Directions
import game
from util import *
from operator import itemgetter
import capture
import random

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'DynamicAgent', second = 'DefenseAgent'):
  """
  This function should return a list of two agents that will form the
  team, initialized using firstIndex and secondIndex as their agent
  index numbers.  isRed is True if the red team is being created, and
  will be False if the blue team is being created.

  As a potentially helpful development aid, this function can take
  additional string-valued keyword arguments ("first" and "second" are
  such arguments in the case of this function), which will come from
  the --redOpts and --blueOpts command-line arguments to capture.py.
  For the nightly contest, however, your team will be created without
  any extra arguments, so you should make sure that the default
  behavior is what you want for the nightly contest.
  """

  # The following line is an example only; feel free to change it.
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########

class DynamicAgent(CaptureAgent):
  """
  A Dummy agent to serve as an example of the necessary agent structure.
  You should look at baselineTeam.py for more details about how to
  create an agent as this is the bare minimum.
  """

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.data = set()
    self.dictionary = {}
    self.holdingFood = 0
    
    # MODIFIED class constructor to hold data variables

  def registerInitialState(self, gameState):
    """
    This method handles the initial setup of the
    agent to populate useful fields (such as what team
    we're on).

    A distanceCalculator instance caches the maze distances
    between each pair of positions, so your agents can use:
    self.distancer.getDistance(p1, p2)

    IMPORTANT: This method may run for at most 15 seconds.
    """

    '''
    Make sure you do not delete the following line. If you would like to
    use Manhattan distances instead of maze distances in order to save
    on initialization time, please take a look at
    CaptureAgent.registerInitialState in captureAgents.py.
    '''
    CaptureAgent.registerInitialState(self, gameState)

    '''
    Your initialization code goes here, if you need any.
    '''
    self.start = gameState.getAgentPosition(self.index)


  # you can check if the opponent's agent is a pacman even when it is not close to our agents (but we don't know the exact position of their agents)
  def closestOppPacman(self, gameState):
    oppPacman = []

    for oppIndex in self.getOpponents(gameState):
      oppPosition = gameState.getAgentState(oppIndex).getPosition()
      if gameState.getAgentState(oppIndex).isPacman and oppPosition != None:
        oppPacman.append([oppIndex, oppPosition])

    return oppPacman

  def opponents(self, gameState):
    oppPacman = []

    for oppIndex in self.getOpponents(gameState):
      oppPosition = gameState.getAgentState(oppIndex).getPosition()
      if  oppPosition != None:
        oppPacman.append((oppIndex, oppPosition))

    return oppPacman


  def getClosestFoodDistance(self, gameState):
    # cannot declare a global food variable since the food position can be changed
    food = self.getFood(gameState).asList()
    minFoodDistance = float('inf')
    for foodPos in food:
      foodDistance = self.getMazeDistance(gameState.getAgentState(self.index).getPosition(), foodPos)
      minFoodDistance = min(minFoodDistance, foodDistance)
    return minFoodDistance
  
  def closestSafeSpace(self, gameState, position):
    walls = gameState.getWalls()
    gridList = walls.asList(key=False)
    # print(gameState.data)
    safeSpaces = halfList(l=gridList, grid=walls, red=self.red)
    # print(safeSpaces)
    closest_safe_space=None
    for safe_square in safeSpaces:
      if closest_safe_space==None or self.distancer.getDistance(position, safe_square) < closest_safe_space[0]:
        closest_safe_space = (self.distancer.getDistance(position, safe_square), safe_square)
  
    return closest_safe_space

  def chooseAction(self, gameState):
    """
    Picks among actions randomly.
    """
    actions = gameState.getLegalActions(self.index)

    '''
    Find nearest food distance (called foodDistance)
    Check if the opponent's agent is a pacman and we can get its position
      -> Yes, calculate chaseDistance using mazeDistance
        -> If chaseDistance * 2 < foodDistance -> iterate through actions to get the suitable one (??? how to check)
      -> Else, go to the nearest food
    ''' 
    closestFoodDistance = self.getClosestFoodDistance(gameState)
    opps = self.opponents(self.getCurrentObservation())

    midpoint = gameState.getWalls().width//2

    if(self.red):
      oppPacmans = [opp for opp in opps if opp[1][0]<midpoint]
      oppTheirSide = [opp for opp in opps if opp[1][0]>=midpoint]
    else:
      oppPacmans = [opp for opp in opps if opp[1][0]>=midpoint]
      oppTheirSide = [opp for opp in opps if opp[1][0]<midpoint]

    # if(opps):
    #   print("ourSide:", oppOurSide)
    #   print("theirSide:", oppTheirSide)

    

    if len(oppPacmans) > 0:
      minChaseDistance = float('inf')
      for [oppIndex, oppPosition] in oppPacmans:
        chaseDistance = self.getMazeDistance(gameState.getAgentState(self.index).getPosition(), oppPosition)
        minChaseDistance = min(minChaseDistance, chaseDistance)

      
      # chase the opponent
      if minChaseDistance * 2 < closestFoodDistance:
        for action in actions:
          successor = self.getSuccessor(gameState, action)
          if self.getMazeDistance(successor.getAgentState(self.index).getPosition(), oppPosition) < chaseDistance:
            return action

    # TODO Uncomment code above, it wasn't working for me so I commented it out.
          
    
    # Code to get nearest food and return home. After returning home it goes back for another food. The number of food to be collected before returning home can be changed by changing holdingFood < x.

    # NOTE: This does not check if there are ghosts nearby, it is a pretty naive implementation.

    actions = gameState.getLegalActions(self.index)

    currentFood = self.getFood(gameState).asList()

    agentPos = gameState.getAgentState(self.index).getPosition()

    enemyPresence = False
    goHome = False

    # successor = [(action, self.getSuccessor(gameState, action).getAgentPosition(self.index)) for action in actions]

    if(self.holdingFood < 2):
      minFoodPos = None
      minFoodDist = None
      for foodPos in currentFood:
        foodDist = self.distancer.getDistance(agentPos, foodPos)            

        if not minFoodPos or foodDist < minFoodDist:
          minFoodDist = self.distancer.getDistance(agentPos, foodPos)
          minFoodPos = foodPos

      

      # print(actions)
      distFromFoodToHome = self.closestSafeSpace(gameState, minFoodPos)[0]
      for opp in oppTheirSide:
          if self.distancer.getDistance(agentPos, opp[1]) < ((minFoodDist+distFromFoodToHome)*1.5):
            goHome = True

      if not goHome:
        distances = []
        for action in actions:
          successor = self.getSuccessor(gameState, action)
          successorPos = successor.getAgentPosition(self.index)
          distances.append((action, self.distancer.getDistance(successorPos, minFoodPos)))

        distances = sorted(distances, key=itemgetter(1))

        if(distances[0][1]==0):
          self.holdingFood+=1
        
        # print("chasing Food")
        return distances[0][0]
    
    if(goHome or self.holdingFood):

      if not oppTheirSide:
        closest_safe = self.closestSafeSpace(gameState, agentPos)
        distances = []
        for action in actions:
          successor = self.getSuccessor(gameState, action)
          successorPos = successor.getAgentPosition(self.index)
          nextDist = self.distancer.getDistance(successorPos, closest_safe[1])
          if nextDist < closest_safe[0]:
            if nextDist == 0:
              self.holdingFood=0
            # print("going home, no threat")
            return action

        # distances = sorted(distances, key=itemgetter(1))

        # if(distances[0][1]==0):
        #   self.holdingFood=0

        # print("going home, no threat")
        # return distances[0][0]

      else:
        walls = gameState.getWalls()
        gridList = walls.asList(key=False)
        # print(gameState.data)
        safeSpaces = halfList(l=gridList, grid=walls, red=self.red)
        # print(safeSpaces)
        best_score=None
        for safe_square in safeSpaces:
          for opp in oppTheirSide:
            for action in actions:
              successor = self.getSuccessor(gameState, action)
              successorPos = successor.getAgentPosition(self.index)

              distToSafe = self.distancer.getDistance(successorPos, safe_square)
              distFromOpp = self.distancer.getDistance(successorPos, opp[1])
              score = distToSafe - distFromOpp

              if not best_score or score < best_score[0]:
                best_score = (score, action, distToSafe)
              elif score == best_score[0] and distToSafe < self.getMazeDistance(agentPos, safe_square):
                 best_score = (score, action, distToSafe)
        
        if best_score[2]==0:
          self.holdingFood=0
          
        # print("going home, avoiding enemy")
        return best_score[1]
              

          

      # print(closest_safe_space)
      
          

    # go to the nearest food 
    # INSERT YOUR GETTING FOOD FUNCTION HERE

    print("random choice dynamic")
    return random.choice(actions)
  
  def getSuccessor(self, gameState, action):
    """
    Finds the next successor which is a grid position (location tuple).
    """
    successor = gameState.generateSuccessor(self.index, action)
    pos = successor.getAgentState(self.index).getPosition()
    if pos != nearestPoint(pos):
      # Only half a grid position was covered
      return successor.generateSuccessor(self.index, action)
    else:
      return successor

class DefenseAgent(CaptureAgent):
  """
  A Dummy agent to serve as an example of the necessary agent structure.
  You should look at baselineTeam.py for more details about how to
  create an agent as this is the bare minimum.
  """

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.randomDefPos = None
    self.decay = 0
    
    # MODIFIED class constructor to hold data variables

  def registerInitialState(self, gameState):
    """
    This method handles the initial setup of the
    agent to populate useful fields (such as what team
    we're on).

    A distanceCalculator instance caches the maze distances
    between each pair of positions, so your agents can use:
    self.distancer.getDistance(p1, p2)

    IMPORTANT: This method may run for at most 15 seconds.
    """

    '''
    Make sure you do not delete the following line. If you would like to
    use Manhattan distances instead of maze distances in order to save
    on initialization time, please take a look at
    CaptureAgent.registerInitialState in captureAgents.py.
    '''
    CaptureAgent.registerInitialState(self, gameState)

    '''
    Your initialization code goes here, if you need any.
    '''
    self.start = gameState.getAgentPosition(self.index)


  # you can check if the opponent's agent is a pacman even when it is not close to our agents (but we don't know the exact position of their agents)
  def closestOppPacman(self, gameState):
    oppPacman = []

    for oppIndex in self.getOpponents(gameState):
      oppPosition = gameState.getAgentState(oppIndex).getPosition()
      if gameState.getAgentState(oppIndex).isPacman and oppPosition != None:
        oppPacman.append([oppIndex, oppPosition])

    return oppPacman
  
  def historyOppPacman(self, gameState, histIndex, rangeVal):

    oppPacman = set()
    for i in range(histIndex, histIndex+rangeVal):
      if(len(self.observationHistory)>rangeVal):
        observation = self.observationHistory[-1 - i]
        for oppIndex in self.getOpponents(gameState):
          oppPosition = observation.getAgentState(oppIndex).getPosition()
          if observation.getAgentState(oppIndex).isPacman and oppPosition != None:
            oppPacman.add((oppIndex, oppPosition))

    return oppPacman


  def chooseAction(self, gameState):
    """
    Picks among actions randomly.
    """
    actions = gameState.getLegalActions(self.index)
    self.decay -= 1
    '''
    Find nearest food distance (called foodDistance)
    Check if the opponent's agent is a pacman and we can get its position
      -> Yes, calculate chaseDistance using mazeDistance
        -> If chaseDistance * 2 < foodDistance -> iterate through actions to get the suitable one (??? how to check)
      -> Else, go to the nearest food
    ''' 
    # closestFoodDistance = self.getClosestFoodDistance(gameState)
    oppPacmans = self.closestOppPacman(gameState)
    agentPos = gameState.getAgentPosition(self.index)
    grid = gameState.getWalls()

    if len(oppPacmans) > 0:
      minChaseDistance = float('inf')
      for [oppIndex, oppPosition] in oppPacmans:
        chaseDistance = self.getMazeDistance(gameState.getAgentState(self.index).getPosition(), oppPosition)
        minChaseDistance = min(minChaseDistance, chaseDistance)

      if minChaseDistance==1:
        self.setRandomDefPos(grid)
        self.decay = 4

      # print('should be chasing pacman')
      for action in actions:
        successor = self.getSuccessor(gameState, action)
        successorPos = successor.getAgentState(self.index).getPosition()
        if self.getMazeDistance(successorPos, oppPosition) < minChaseDistance and self.posIsSafe(grid, successorPos):
          # print('chasing pacman')
          return action
        
    elif histPacmans := self.historyOppPacman(gameState, 0, 3):
      minChaseDistance = float('inf')
      for (oppIndex, oppPosition) in histPacmans:
        chaseDistance = self.getMazeDistance(gameState.getAgentState(self.index).getPosition(), oppPosition)
        minChaseDistance = min(minChaseDistance, chaseDistance)

      # print('should be chasing pacman')
      for action in actions:
        successor = self.getSuccessor(gameState, action)
        successorPos = successor.getAgentState(self.index).getPosition()
        if self.getMazeDistance(successorPos, oppPosition) < minChaseDistance and self.posIsSafe(grid, successorPos):
          # print('chasing pacman')
          return action
    
    # elif opponentPos := [gameState.getAgentPosition(opp) for opp in self.getOpponents(gameState)if gameState.getAgentPosition(opp) is not None]:
    #   for action in actions:
    #       successor = self.getSuccessor(gameState, action)
    #       successorPos = successor.getAgentPosition(self.index)
    #       if(self.posIsSafe(grid, successorPos)):
    #         for oppPos in opponentPos:
    #           distToOpp = self.getMazeDistance(successorPos, oppPos)
    #           if distToOpp < self.getMazeDistance(agentPos, oppPos):
    #             return action
      #grid = capture.halfGrid(fullgrid, red=self.red)

    if not self.randomDefPos:
      self.setRandomDefPos(grid)

    # print("is in else")
    acceptableActions = []
    for action in actions:
      successor = self.getSuccessor(gameState, action)
      successorPos = successor.getAgentPosition(self.index)
      if(self.posIsSafe(grid, successorPos)):
        acceptableActions.append(action)
        distToRand = self.getMazeDistance(successorPos, self.randomDefPos)
        if distToRand < self.getMazeDistance(agentPos, self.randomDefPos):
          
          if distToRand==0:
            self.setRandomDefPos(grid)
          print('going to rand', self.randomDefPos, successorPos, grid.width)
          return action
    
    print("randomDefPos failed, retrying")
    self.setRandomDefPos(grid)

    print('random choice defense')
    return random.choice(acceptableActions)
  
  def posIsSafe(self, grid, pos):
    if self.red:
      return pos[0] < grid.width//2
    else:
      return pos[0] >= grid.width//2

  def setRandomDefPos(self, grid):
    randX = random.randrange(grid.width//2 - 3, grid.width//2)
    randY = random.randrange(grid.height//2, grid.height) if not self.randomDefPos or self.randomDefPos[1]<grid.height//2 else random.randrange(1, grid.height//2)
    while grid[randX][randY]:
      randX = random.randrange(grid.width//2 - 3, grid.width//2)
      randY = random.randrange(grid.height//2, grid.height) if not self.randomDefPos or self.randomDefPos[1]<grid.height//2 else random.randrange(1, grid.height//2)
    self.randomDefPos=(randX, randY)

  def getSuccessor(self, gameState, action):
    """
    Finds the next successor which is a grid position (location tuple).
    """
    successor = gameState.generateSuccessor(self.index, action)
    pos = successor.getAgentState(self.index).getPosition()
    if pos != nearestPoint(pos):
      # Only half a grid position was covered
      return successor.generateSuccessor(self.index, action)
    else:
      return successor
  


  # HELPER METHODS

def halfList(l, grid, red):
  halfway = grid.width // 2
  newList = []
  for x,y in l:
    if red and x < halfway: newList.append((x,y))
    elif not red and x >= halfway: newList.append((x,y))
  return newList