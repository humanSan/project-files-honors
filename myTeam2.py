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
import numpy as np

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

    self.holdingFood = 0

    self.randomStartPos = None
    
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

  def chaseFood(self, actions, minFoodPos, gameState):
    distances = []
    for action in actions:
      successor = self.getSuccessor(gameState, action)
      successorPos = successor.getAgentPosition(self.index)
      distances.append((action, self.distancer.getDistance(successorPos, minFoodPos)))

    distances = sorted(distances, key=itemgetter(1)) # this is not the most efficient implementation, but will be useful if we choose to use a value function for each successor

    if(distances[0][1]==0): # If the chosen action gets a food (meaning the distance of the successor position is 0), we increment holdingFood to indicate that the agent now holds one more food.
      self.holdingFood+=1
    
    return distances[0][0]
  
  def goHome(self, actions, agentPos, gameState):
    closest_safe = self.closestSafeSpace(gameState, agentPos) # finds nearest home space (safe space)
    distances = []
    for action in actions: # finds action that gets us closer to the safe space
      successor = self.getSuccessor(gameState, action)
      successorPos = successor.getAgentPosition(self.index)
      nextDist = self.distancer.getDistance(successorPos, closest_safe[1])
      if nextDist < closest_safe[0]:
        if nextDist == 0:
          self.holdingFood=0
        # print("going home, no threat")
        return action

  def chooseAction(self, gameState):
    """
    Picks among actions randomly.
    """
    actions = gameState.getLegalActions(self.index)

    foodGrid = self.getFood(gameState)
    currentFood = foodGrid.asList()

    agentPos = gameState.getAgentState(self.index).getPosition() #current agent position

    # This code creates a "value matrix". The value matrix looks at how valuable a square is, where the value is the number of food surrounding a square. So for every square, we look at the number of food in neighboring spaces. For example, if a space has a food, and ALL it's neighbors (think 3x3 grid around a point) have a food, it's score is 9.
    foodMatrix = np.zeros((foodGrid.width, foodGrid.height))
    for x in range(foodGrid.width):
      for y in range(foodGrid.height):
          foodMatrix[x][y] = foodGrid[x][y]
    
    # print(type(foodGrid))
    # print(foodMatrix.shape)

    sum_matrix = neighborSum(foodMatrix, 3)

    # print(sum_matrix)

    # The following code produces a grids of 1 and 0 where 0 is a wall and 1 is not a wall. 
    wallGrid = gameState.getWalls()
    wallMatrix = np.zeros((wallGrid.width, wallGrid.height))
    for x in range(wallGrid.width):
        for y in range(wallGrid.height):
          wallMatrix[x][y] = wallGrid[x][y]

    notWallMatrix = np.logical_not(wallMatrix).astype(int)
    
    value_matrix = np.multiply(notWallMatrix, sum_matrix)

    #print(value_matrix) 
    # Value Matrix is currently unused, but we could use it later

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

    # This code creates 2 arrays, oppPacmans and oppTheirSide. oppPacmans has positions of enemy pacmans in our side. oppTheirSide has positions of opponents on their own side (meaning they are ghosts). It might be better to rename oppTheirSide as oppGhosts, but it works for now.
    if(self.red):
      oppPacmans = [opp for opp in opps if opp[1][0]<midpoint]
      oppTheirSide = [opp for opp in opps if opp[1][0]>=midpoint]
    else:
      oppPacmans = [opp for opp in opps if opp[1][0]>=midpoint]
      oppTheirSide = [opp for opp in opps if opp[1][0]<midpoint]

    """# if(opps):
    #   print("ourSide:", oppOurSide)
    #   print("theirSide:", oppTheirSide)"""

    
    # If there are enemy pacmans in our territory, we should chase after it unless it is too far away. Here, that threshold for being too far away is defined as (2d < f) where d is distance to pacman and f is distance to closest food. This means the closest food has to be twice as far away as the pacman for the agent to prefer chasing the pacman
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
          
    
    # Code to get nearest food and return home. After returning home it goes back for another food. The number of food to be collected before returning home can be changed by changing holdingFood < x.

    goHome = False # boolean to store whether agent should return home. used when agent is in enemy territory and encounters a ghost

    # successor = [(action, self.getSuccessor(gameState, action).getAgentPosition(self.index)) for action in actions]

    minFoodPos = None #position of nearest food
    minFoodDist = None #distance to nearest food
    for foodPos in currentFood:
      foodDist = self.distancer.getDistance(agentPos, foodPos)            

      if not minFoodPos or foodDist < minFoodDist:
        minFoodDist = self.distancer.getDistance(agentPos, foodPos)
        minFoodPos = foodPos

    # if agent already holds a certain number of food, return home immediately without trying to get more food. This decreases the risk of being attacked by a ghost while holding a lot of points.
    if(self.holdingFood < 2):      

      # print(actions)
      distFromFoodToHome = self.closestSafeSpace(gameState, minFoodPos)[0]# this gets the shortest path from the nearest food to our home territory

      # If we see a ghost, we see if we can eat the nearest food and return home quickly or not. If we can, then we will still eat the food. But if the ghost is nearer then the threshold, we go home. The threshold is set by the (minFoodDist+distFromFoodToHome) * 1.5). Changing 1.5 changes how close we are willing to get to the ghost. If we want to be safe and stay far away, increase it to 2.
      for opp in oppTheirSide:
          if self.distancer.getDistance(agentPos, opp[1]) < ((minFoodDist+distFromFoodToHome)*1.5):
            goHome = True

      
      if not goHome: # get the food
        return self.chaseFood(actions, minFoodPos, gameState)
    
    # If goHome has been set to true (only happens when we are near ghost but far from food), or if we already hold enough food past the threshold, we go home as quickly as possible
    if(goHome or self.holdingFood):

      if not oppTheirSide: # If we are not being chased by a ghost, we can go home easily, just take the shortest path home
        return self.goHome(actions, agentPos, gameState)

        """# distances = sorted(distances, key=itemgetter(1))

        # if(distances[0][1]==0):
        #   self.holdingFood=0

        # print("going home, no threat")
        # return distances[0][0]"""

      else:
        # if we are being chased by a ghost, we don't want to just go to the nearest home square, because the ghost might be on that path. Instead we want to take a path that avoids the ghost. So we do distHome - distGhost for every home space and every successor position. 
        walls = gameState.getWalls()
        gridList = walls.asList(key=False)
        # print(gameState.data)
        safeSpaces = halfList(l=gridList, grid=walls, red=self.red)
        # print(safeSpaces)
        best_score=None
        for safe_square in safeSpaces:
          for action in actions:
            # We iterate on every successor position because consider the case that we can go up or down. The ghost is up. The path to home going up is shorter than going down, but we still want to go down to avoid the ghost. So, we have to look at the distance to home from the successors, not our current position.

            successor = self.getSuccessor(gameState, action)
            successorPos = successor.getAgentPosition(self.index)

            # We want to go home while avoiding the ghost. So only consider actions that get us farther away from the ghosts. These actions are "acceptable actions"
            acceptableAction = True

            # minDistFromOpp holds the distance to the closest ghost. This is the most dangerous ghost, so we want to avoid this in our move calculation
            minDistFromOpp = None
            for opp in oppTheirSide:         
              distFromOpp = self.distancer.getDistance(successorPos, opp[1])
              currentDistFromOpp = self.distancer.getDistance(agentPos, opp[1])
              if distFromOpp < 6 and distFromOpp < currentDistFromOpp:
                acceptableAction = False
              
              if minDistFromOpp is None or distFromOpp < minDistFromOpp:
                minDistFromOpp = distFromOpp
              
            if acceptableAction:
              distToSafe = self.distancer.getDistance(successorPos, safe_square)
              score = distToSafe - minDistFromOpp

              # so we find the best score
              if not best_score or score < best_score[0]:
                best_score = (score, action, distToSafe)
              elif score == best_score[0] and distToSafe < self.getMazeDistance(agentPos, safe_square):
                  best_score = (score, action, distToSafe)
                  # This is for the case that 2 successors have the same best score. In that case we want whichever action will get us closer to home
        
        if best_score and best_score[2]==0:
          self.holdingFood=0
          
        if best_score:
          return best_score[1]
        

        # If nothing is returned by this point, this means that there is no way to get home without getting closer to the ghosts. In other words, we are cornered by both ghosts. So, we are most likely going to die. Here we just chase more food, but may not be best
        return self.goHome(actions, agentPos, gameState)
        
              

          

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
    
  def setRandomStartPos(self, grid):
    randX = random.randrange(grid.width//2 - 3, grid.width//2)
    randY = random.randrange(grid.height//2, grid.height) if not self.randomStartPos or self.randomStartPos[1]<grid.height//2 else random.randrange(1, grid.height//2)
    while grid[randX][randY]:
      randX = random.randrange(grid.width//2 - 3, grid.width//2)
      randY = random.randrange(grid.height//2, grid.height) if not self.randomStartPos or self.randomStartPos[1]<grid.height//2 else random.randrange(1, grid.height//2)
    self.randomStartPos=(randX, randY)

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
    
    self.pacman_last_seen = {}
    self.foodGridLast = None
    self.chasePos = None
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

    foodGrid = self.getFoodYouAreDefending(gameState)
    if self.foodGridLast is None: 
      self.foodGridLast = foodGrid

    pacmans_in_food = []

    for x in range(foodGrid.width):
      for y in range(foodGrid.height):
        if self.foodGridLast[x][y] ^ foodGrid[x][y]:
          pacmans_in_food.append(((x,y), self.distancer.getDistance(agentPos, (x,y))))
    
    if pacmans_in_food:
      pacmans_in_food = sorted(pacmans_in_food, key=itemgetter(1))
      self.chasePos = pacmans_in_food[0][0]
    
    self.foodGridLast = foodGrid
    print(pacmans_in_food)
    print(self.chasePos)

    if len(oppPacmans) > 0:
      minChaseDistance = float('inf')
      for [oppIndex, oppPosition] in oppPacmans:
        self.pacman_last_seen[oppIndex] = oppPosition
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
    
    elif self.chasePos:
      for action in actions:
        successor = self.getSuccessor(gameState, action)
        successorPos = successor.getAgentState(self.index).getPosition()
        if self.getMazeDistance(successorPos, self.chasePos) < self.getMazeDistance(agentPos, self.chasePos) and self.posIsSafe(grid, successorPos):
          # print('chasing pacman')

          if(successorPos == self.chasePos):
            self.chasePos = None
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
          #print('going to rand', self.randomDefPos, successorPos, grid.width)
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

def neighborSum(array, n):
    array = array.cumsum(1).cumsum(0)
    res = array.copy()
    res[:,n:] -= array[:,:-n]
    res[n:] -= array[:-n]
    res[n:,n:] += array[:-n,:-n]
    result = np.pad(res, ((0,1),(0,1)), mode='constant')[1:, 1:]
    return result
  
  # ^ This will do a n x n sum of neighboring squares (including its own square)
  # If we want only neighboring squares, we have to subtract the original matrix from it
  # This will include values for walls, if want to zero out all squares that are not walls, we need to get the Walls matrix (which is true where there's a wall). We can do np.logical_not(walls) so walls are now False. We do np.as_type(int) to make the False zeros, and then we multiply the matrices with np.multiply(). This makes all walls zero in the value matrix. Foods are left untouched.
  # We should add the power capsule value to the matrix as well. All squares near the power capsule (3x3 subgrid) get a bonus added in the value matrix (power_capsule_value)