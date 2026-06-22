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
import distanceCalculator
import layout

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'DefenseAgent', second = 'DynamicAgent'):
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

class CommonAgent(CaptureAgent):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    self.oppPowerTurns = -1
    self.ourPowerTurns = -1

    self.previousCapsulesDefend = None
    self.previousCapsulesAtk = None
    
    # self.chasePos = None
    self.scared = None
    self.oppScared = set()
    # MODIFIED class constructor to hold data variables
  
  # def safeChasePos(self, actions, position, gameState):
  #   distances = []
  #   for action in actions:
  #     successor = self.getSuccessor(gameState, action)
  #     successorPos = successor.getAgentPosition(self.index)
  #     distances.append((action, self.distancer.getDistance(successorPos, minFoodPos)))

  #   distances = sorted(distances, key=itemgetter(1)) # this is not the most efficient implementation, but will be useful if we choose to use a value function for each successor

  #   if(distances[0][1]==0): # If the chosen action gets a food (meaning the distance of the successor position is 0), we increment holdingFood to indicate that the agent now holds one more food.
  #     self.holdingFood+=1
    
  #   return distances[0][0]
#-------------
  # def safeChasePos(self, gameState, )
  #   if self.chasePos and self.getMazeDistance(self.chasePos, agentPos) * 1.5 < closestFoodDistance:
  #     for action in actions:
  #       successor = self.getSuccessor(gameState, action)
  #       successorPos = successor.getAgentState(self.index).getPosition()
  #       if self.getMazeDistance(successorPos, self.chasePos) < self.getMazeDistance(agentPos, self.chasePos) and self.posIsSafe(grid, successorPos):
  #         # print('chasing pacman')

  #         if(successorPos == self.chasePos):
  #           self.chasePos = None
  #         self.randomStartPos = None
  #         # print("chasing pacman cuz it ate food")
  #         return action

  def checkOppPower(self, gameState):
    if self.oppPowerTurns > 40:
      self.scared = False

    if self.oppPowerTurns >= 0:
      self.oppPowerTurns += 1

    currCapsules = self.getCapsulesYouAreDefending(gameState)
    if(self.previousCapsulesDefend is not None):
      for capsule in self.previousCapsulesDefend:
        if capsule not in currCapsules:
          self.oppPowerTurns = 0
          self.scared = True
    else:
      self.previousCapsulesDefend = self.getCapsulesYouAreDefending(gameState)

    self.previousCapsulesDefend = currCapsules
    if self.oppPowerTurns >= 0 and self.oppPowerTurns < 40:
      return True
    else:
      return False

  def checkOurPower(self, gameState):
    if self.ourPowerTurns > 40:
      self.oppScared = set()

    if self.ourPowerTurns >= 0:
      self.ourPowerTurns += 1

    currCapsules = self.getCapsules(gameState)
    if(self.previousCapsulesAtk is not None):
      for capsule in self.previousCapsulesAtk:
        if capsule not in currCapsules:
          self.ourPowerTurns = 0
          self.oppScared = set(self.getOpponents(gameState))
    else:
      self.previousCapsulesAtk = self.getCapsules(gameState)

    self.previousCapsulesAtk = currCapsules
    if self.ourPowerTurns >= 0 and self.ourPowerTurns < 40:
      return True
    else:
      return False
    
  def opponents(self, gameState):
    oppPacman = []

    for oppIndex in self.getOpponents(gameState):
      oppPosition = gameState.getAgentState(oppIndex).getPosition()
      if  oppPosition != None:
        oppPacman.append((oppIndex, oppPosition))

    return oppPacman


class DynamicAgent(CommonAgent):
  """
  A Dummy agent to serve as an example of the necessary agent structure.
  You should look at baselineTeam.py for more details about how to
  create an agent as this is the bare minimum.
  """

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    self.holdingFood = 0

    self.randomStartPos = None
    
    self.chasePos = None
    self.randomAtkPos=None
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

    fullgrid = gameState.getWalls()
    halfGrid = capture.halfGrid(fullgrid, red=self.red)

    # state_copy = gameState.deepcopy()
    layout_text = str(gameState.data.layout).split("\n")
    half_layout_text = []
    for line in layout_text:
      #print(line)
      wallBuffer = "".join(["%" for i in range(len(line)//2)])
      half_layout_text.append(line[:len(line)//2] + wallBuffer) if self.red else half_layout_text.append(wallBuffer + line[len(line)//2:])

    
    print("\n".join(half_layout_text))

    half_layout = layout.Layout(half_layout_text)

    #print(half_layout)
    
    self.half_dist = distanceCalculator.Distancer(half_layout)

    # comment this out to forgo maze distance computation and use manhattan distances
    self.half_dist.getMazeDistances()
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


  def getClosestFoodDistance(self, gameState):
    # cannot declare a global food variable since the food position can be changed
    food = self.getFood(gameState).asList()
    minFoodDistance = float('inf')
    for foodPos in food:
      foodDistance = self.getMazeDistance(gameState.getAgentState(self.index).getPosition(), foodPos)
      minFoodDistance = min(minFoodDistance, foodDistance)
    return minFoodDistance

  def pointToFood(self, gameState, point):
    # cannot declare a global food variable since the food position can be changed
    food = self.getFood(gameState).asList()
    minFoodDistance = float('inf')
    minFood = None
    for foodPos in food:
      foodDistance = self.getMazeDistance(point, foodPos)
      if minFood is None or foodDistance < minFoodDistance:
        minFood = foodPos
        minFoodDistance = foodDistance
    return (minFoodDistance, minFood)

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

  def setRandomAtkPos(self, grid, agentPos, gameState):

    meridian = grid.width//2
    gridlist = grid.asList(key = False)

    start = 1
    end = 0
    randomPosList = []
    if self.red:
      for i in gridlist:
        if i[0]>=meridian-start and i[0] < meridian-end and abs(i[1]-agentPos[1])>grid.height/3:
          randomPosList.append(i)
    else:
      for i in gridlist:
        if i[0]>=meridian+end and i[0] < meridian+start and abs(i[1]-agentPos[1])>grid.height/3:
          randomPosList.append(i)
    
    self.chasePos = random.choice(randomPosList)

  def goToRandom(self, actions, gameState):
    if not self.chasePos:
      self.setRandomAtkPos(gameState.getWalls(), gameState.getAgentPosition(self.index), gameState)

    for action in actions:
      successor = self.getSuccessor(gameState, action)
      successorPos = successor.getAgentPosition(self.index)
      agentPos = gameState.getAgentPosition(self.index)

      if self.posIsSafe(gameState.getWalls(), successorPos) and self.half_dist.getDistance(successorPos, self.chasePos) and self.half_dist.getDistance(successorPos, self.chasePos) < self.half_dist.getDistance(agentPos, self.chasePos):
        if successorPos == self.chasePos:
          self.chasePos = None
        
        # print('going to random defense:', self.randomDefPos, agentPos)
        return action
    return random.choice(actions)

  def chaseFood(self, actions, minFoodPos, gameState):
    distances = []
    for action in actions:
      successor = self.getSuccessor(gameState, action)
      successorPos = successor.getAgentPosition(self.index)
      distances.append((action, self.distancer.getDistance(successorPos, minFoodPos)))

    distances = sorted(distances, key=itemgetter(1)) # this is not the most efficient implementation, but will be useful if we choose to use a value function for each successor
    if distances:
      if(distances[0][1]==0): # If the chosen action gets a food (meaning the distance of the successor position is 0), we increment holdingFood to indicate that the agent now holds one more food.
        self.holdingFood+=1
      
      return distances[0][0]
    return random.choice(actions)

  def gotoHome(self, actions, target, gameState):
    distances = []
    for action in actions:
      successor = self.getSuccessor(gameState, action)
      successorPos = successor.getAgentPosition(self.index)
      distances.append((action, self.distancer.getDistance(successorPos, target)))

    distances = sorted(distances, key=itemgetter(1)) # this is not the most efficient implementation, but will be useful if we choose to use a value function for each successor
    if distances:
      if(distances[0][1]==0): # If the chosen action is home (meaning the distance of the successor position is 0), we reset holdingFood to indicate that we hold no food.
        self.holdingFood = 0
      
      return distances[0][0]
    return random.choice(actions)
  
  def goto(self, actions, target, gameState):
    distances = []
    for action in actions:
      successor = self.getSuccessor(gameState, action)
      successorPos = successor.getAgentPosition(self.index)
      distances.append((action, self.distancer.getDistance(successorPos, target)))

    distances = sorted(distances, key=itemgetter(1)) # this is not the most efficient implementation, but will be useful if we choose to use a value function for each successor
    if distances:
      return distances[0][0]
    return random.choice(actions)
  
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
    return random.choice(actions)

  def safeChasePos(self, actions, position, gameState):
    distances = []
    agentPos = gameState.getAgentPosition(self.index)
    for action in actions:
      successor = self.getSuccessor(gameState, action)
      successorPos = successor.getAgentState(self.index).getPosition()
      
      if self.posIsSafe(gameState.getWalls(), successorPos) and self.half_dist.getDistance(successorPos, position) < self.half_dist.getDistance(agentPos, position):

        if(successorPos == self.chasePos):
          print("chasePos reached", self.chasePos, successorPos)
          self.chasePos = None

        # print("chasing chasePos: food eaten or previous sighting", self.chasePos, successorPos)
        return action
    return random.choice(actions)

  def chooseAction(self, gameState):
    """
    Picks among actions randomly.
    """
    # print(self.oppScared)
    returnValue = None

    actions = gameState.getLegalActions(self.index)

    foodGrid = self.getFood(gameState)
    currentfood = foodGrid.asList()
    walls = gameState.getWalls()


    agentPos = gameState.getAgentState(self.index).getPosition() #current agent position
    powerStat = self.checkOurPower(gameState)

    capsules = self.getCapsules(gameState)
    sortedcapsules = []
    bestCapsule = None
    for capsule in capsules:
      sortedcapsules.append((capsule, self.getMazeDistance(agentPos, capsule)))
    if sortedcapsules:
      sortedcapsules.sort(key=itemgetter(1))
      bestCapsule = sortedcapsules[0][0]
    

    if(self.start == agentPos):
      self.scared = False
      self.holdingFood = 0
      self.ourPowerTurns = -1
    
    if(self.posIsSafe(walls, agentPos)):
      self.holdingFood = 0

    # # This code creates a "value matrix". The value matrix looks at how valuable a square is, where the value is the number of food surrounding a square. So for every square, we look at the number of food in neighboring spaces. For example, if a space has a food, and ALL it's neighbors (think 3x3 grid around a point) have a food, it's score is 9.
    # foodMatrix = np.zeros((foodGrid.width, foodGrid.height))
    # for x in range(foodGrid.width):
    #   for y in range(foodGrid.height):
    #       foodMatrix[x][y] = foodGrid[x][y]
    
    # # print(type(foodGrid))
    # # print(foodMatrix.shape)

    # sum_matrix = neighborSum(foodMatrix, 3)

    # # print(sum_matrix)

    # # The following code produces a grids of 1 and 0 where 0 is a wall and 1 is not a wall. 
    # walls = gameState.getWalls()
    # wallGrid = gameState.getWalls()
    # wallMatrix = np.zeros((wallGrid.width, wallGrid.height))
    # for x in range(wallGrid.width):
    #     for y in range(wallGrid.height):
    #       wallMatrix[x][y] = wallGrid[x][y]

    # notWallMatrix = np.logical_not(wallMatrix).astype(int)
    
    # value_matrix = np.multiply(notWallMatrix, sum_matrix)

    #print(value_matrix) 
    # Value Matrix is currently unused, but we could use it later

  # Code to get nearest food and return home. After returning home it goes back for another food. The number of food to be collected before returning home can be changed by changing holdingFood < x.
    minFoodPos = None #position of nearest food
    sortedfood = []
    for foodPos in currentfood:
      foodDist = self.distancer.getDistance(agentPos, foodPos)
      sortedfood.append((foodPos, foodDist))        

    if sortedfood:
      sortedfood.sort(key = itemgetter(1))
      minFoodPos = sortedfood[0][0]
    
    safemidline = self.getMeridian(walls, self.red)
    oppmidline = self.getMeridian(walls, not self.red)
    connectedmidline = [m for m in oppmidline if not walls[m[0]-1][m[1]]] if self.red else [m for m in oppmidline if not walls[m[0]+1][m[1]]]

    '''
    Find nearest food distance (called foodDistance)
    Check if the opponent's agent is a pacman and we can get its position
      -> Yes, calculate chaseDistance using mazeDistance
        -> If chaseDistance * 2 < foodDistance -> iterate through actions to get the suitable one (??? how to check)
      -> Else, go to the nearest food
    ''' 
    closestFoodDistance = self.getClosestFoodDistance(gameState)
    currentopps = self.opponents(self.getCurrentObservation())
    oppindices = [opp[0] for opp in currentopps]
    # oppdict = dict(currentopps) if currentopps else None
    # print("opps", opps)
    midpoint = gameState.getWalls().width//2

    # This code creates 2 arrays, oppPacmans and oppTheirSide. oppPacmans has positions of enemy pacmans in our side. oppTheirSide has positions of opponents on their own side (meaning they are ghosts). It might be better to rename oppTheirSide as oppGhosts, but it works for now.
    if(self.red):
      oppPacmans = [opp for opp in currentopps if opp[1][0]<midpoint]
      oppTheirSide = [opp for opp in currentopps if opp[1][0]>=midpoint]
    else:
      oppPacmans = [opp for opp in currentopps if opp[1][0]>=midpoint]
      oppTheirSide = [opp for opp in currentopps if opp[1][0]<midpoint]

    oppwatch = [opp for opp in currentopps if manhattanDistance(agentPos, opp[1]) < 6 and opp[0] not in self.oppScared]
    print("oppwatch", oppwatch)

    # We need a way to check if the opponent is scared. oppScared is set to True when power is first activated, and when turns run out it deactivates. But, what about when we kill the defender. It's scared state should deactivate, but how do we detect that. 
    
    # See if there is an opponent in previous opps that is not in current opps, but only for opps where the manhattan distance was 1 (<2) -> we do this because if manhat dist was 5 and it disappeared, it probably just left our sight
    previousstate = self.getPreviousObservation()
    if self.oppScared and previousstate:
      previousOpps = self.opponents(previousstate)
      previousAgentPos = previousstate.getAgentPosition(self.index)
      for opp in previousOpps:
        if manhattanDistance(opp[1], previousAgentPos) < 3 and opp[0] not in oppindices or (opp[0] in oppindices and abs(self.getMazeDistance(agentPos, opp[1]) - self.getMazeDistance(agentPos, gameState.getAgentState(opp[0]).getPosition())) > 2):
          self.debugDraw(agentPos, [0.5, 1, 0.2])
          print("We killed a ghost with power")
          if opp[0] in self.oppScared:
            self.oppScared.remove(opp[0])

    """# if(opps):
    #   print("ourSide:", oppOurSide)
    #   print("theirSide:", oppTheirSide)"""

    goHome = False # boolean to store whether agent should return home. used when agent is in enemy territory and encounters a ghost

    # CODE FOR CHASING AND USING POWER CAPSULE HERE:

    goodfoodstat = self.smartFood(connectedmidline, sortedfood, agentPos, oppwatch)
    goodfood = goodfoodstat[0]
    smartHomePos = self.smartHome(connectedmidline, agentPos, oppwatch)
    getPower = self.smartSeek(sortedcapsules, agentPos, oppwatch)
    print("goodfood", goodfoodstat)


    # if goodfoodstat[1] < 0 and bestCapsule and self.getMazeDistance(agentPos, goodfood) * 2.5 < self.getMazeDistance(agentPos, bestCapsule) and self.holdingFood < 2:
    #   self.chaseFood(actions, goodfood, gameState)

    if(self.holdingFood > 12 or not minFoodPos):
      goHome = True
    
    
    # if goodfoodstat[1] < 0:
    #     return self.chaseFood(actions, goodfood, gameState)

    if(self.posIsSafe(gameState.getWalls(), agentPos) and self.chasePos is not None):
      self.debugDraw(self.chasePos, [1,0.5,0.5])
      return self.safeChasePos(actions, self.chasePos, gameState)
    elif self.chasePos is not None:
      self.chasePos = None

    if self.holdingFood < 2:
      if not goHome and not powerStat and ((not oppwatch) or goodfoodstat[1] < 0):
        print("chasing food because it seems safe", goodfoodstat[1])
        return self.chaseFood(actions, goodfood, gameState)

    # if we have power, chase after food until we are low on time. If we are low on time,       

    if((not goHome) and powerStat and ((not oppwatch) or goodfoodstat[1] < 0) and 40 - self.ourPowerTurns > 10):
      print("chase food because we have power", oppwatch, goodfoodstat, self.oppScared)
      return self.chaseFood(actions, goodfood, gameState)
    
    # if(not goHome and powerStat and goodfoodstat[1] <= 0):
    #   self.chaseFood(actions, goodfood, gameState)
    
    # If we are low on time, but can reach the other power capsule (if it exists) then we get the other power capsule. If goHome has already been set that means we hold a lot of food already and we should just go home first so we can cash in our points
    # powerstat section may not be necessary
    if(not goHome and powerStat and ((not oppwatch) or getPower) and bestCapsule and 40 - self.ourPowerTurns > self.getMazeDistance(agentPos, bestCapsule)):
      return self.chaseFood(actions, getPower, gameState)
    
    # this is base case actually, where if we don't have power we chase after pellet
    if((not goHome) and getPower and ((not powerStat))):
      
      return self.chaseFood(actions, getPower, gameState)

    # All strategies with power pellet have failed, if we currently have power, let's go home
    if(powerStat):
      goHome = True
      # if smartHomePos:
      #   return self.gotoHome(actions, smartHomePos, gameState)
      # return self.goHome(actions, agentPos, gameState)
    

    #---------- defend against pacman
    # If there are enemy pacmans in our territory, we should chase after it unless it is too far away. Here, that threshold for being too far away is defined as (2d < f) where d is distance to pacman and f is distance to closest food. This means the closest food has to be twice as far away as the pacman for the agent to prefer chasing the pacman
    if oppPacmans and not self.checkOppPower(gameState) and self.posIsSafe(walls, agentPos):
      minChaseDistance = float('inf')
      minOppPosition = None
      for [oppIndex, oppPosition] in oppPacmans:
        chaseDistance = self.getMazeDistance(gameState.getAgentState(self.index).getPosition(), oppPosition)
        minChaseDistance = min(minChaseDistance, chaseDistance)
      
      # chase the opponent
      if self.posIsSafe(walls, agentPos) and minChaseDistance*2 < closestFoodDistance:
        for action in actions:
          successor = self.getSuccessor(gameState, action)
          if self.getMazeDistance(successor.getAgentState(self.index).getPosition(), oppPosition) < minChaseDistance:
            return action

    # if goodfood[1] < 0: #TODO
    #   return self.chaseFood(actions, goodfood, gameState)
        
    # if agent already holds a certain number of food, return home immediately without trying to get more food. This decreases the risk of being attacked by a ghost while holding a lot of points.
    # if(self.holdingFood < 4):      

      # print(actions)
      # distFromFoodToHome = self.closestSafeSpace(gameState, minFoodPos)[0]# this gets the shortest path from the nearest food to our home territory

      # This will be True under 3 cases, either there is no ghost nearby (under manHat distance 5), there is a ghost but the food is closer than the opponent, or there is no ghost visiable at all

      # If we see a ghost, we see if we can eat the nearest food and return home quickly or not. If we can, then we will still eat the food. But if the ghost is nearer then the threshold, we go home. The threshold is set by the (minFoodDist+distFromFoodToHome) * 1.5). Changing 1.5 changes how close we are willing to get to the ghost. If we want to be safe and stay far away, increase it to 2.

      # for opp in oppTheirSide:
      #   if self.distancer.getDistance(agentPos, opp[1]) < ((minFoodDist+distFromFoodToHome)*2.1) and manhattanDistance(opp[1], agentPos) < 5:
      #     self.chasePos = None
      #     goHome = True
      #     # If the ghost is close to us distance wise, AND the ghost can see us, we go home

      # if not goHome: # get the food
      #   return self.chaseFood(actions, minFoodPos, gameState)

      
      # if(self.posIsSafe(walls, agentPos)):
      #   self.chaseFood(actions, minFoodPos, gameState)
    if(self.posIsSafe(walls, agentPos) and oppTheirSide):
      probability = random.random()

      if probability <= 0.2: # go the mid position where the food is safe from opponent ghosts from that mid position
        midList = safemidline
        #self.debugDraw(safemidline, [1,0.5,0.5])
        best_mids = []
        if bestCapsule:
          for mid in midList:
            midfood = self.smartFood(connectedmidline, sortedcapsules, mid, oppTheirSide)[0]
            if midfood:
              best_mids.append((mid, self.getMazeDistance(mid, midfood)))
        else:
          for mid in midList:
            midfood = self.smartFood(connectedmidline, sortedfood, mid, oppTheirSide)[0]
            if midfood:
              best_mids.append((mid, self.getMazeDistance(mid, midfood)))
        
        if best_mids:
          best_mids.sort(key=itemgetter(1))
          self.chasePos = best_mids[0][0]
          return self.safeChasePos(actions, self.chasePos, gameState)
        else:
          return self.goToRandom(actions, gameState) 
      else:
        return self.goToRandom(actions, gameState) # go to random mid position with prob 0.5
    

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

        # goodhome = self.smartHome(connectedmidline, agentPos, oppwatch)
        if smartHomePos is not False:
          return self.gotoHome(actions, smartHomePos, gameState)

        # if we are being chased by a ghost, we don't want to just go to the nearest home square, because the ghost might be on that path. Instead we want to take a path that avoids the ghost. So we do distHome - distGhost for every home space and every successor position. 
        walls = gameState.getWalls()
        gridList = walls.asList(key=False)
        # print(gameState.data)
        safeSpaces = halfList(l=gridList, grid=walls, red=self.red)
        # print(safeSpaces)

        if(oppTheirSide):
          goodactions = []
          for action in actions:
            successor = self.getSuccessor(gameState, action)
            successorPos = successor.getAgentPosition(self.index)
            safe_action = True
            for opp in oppTheirSide:
              if self.getMazeDistance(successorPos, opp[1]) <= self.getMazeDistance(agentPos, opp[1]):
                safe_action = False

            oppPos = [opp[1] for opp in oppTheirSide]

            if safe_action and self.closestSafeSpace(gameState, successorPos)[0] < self.closestSafeSpace(gameState, agentPos)[0]:
              return action

            """start dfs"""
            if safe_action:
              
              explored = set()
              stack = [(successor, 0)]

              i=0
              while(stack or i<100):
                current = stack.pop()
                currentpos = current[0].getAgentPosition(self.index)
                # print("DFS", currentpos)
                if current[0] not in explored:
                  explored.add(current[0])
                  pathlength = current[1] + 1
                  if self.smartHome(connectedmidline, currentpos, oppwatch):
                    goodactions.append((action, pathlength))
                    break
                  else:
                
                    nextactions = current[0].getLegalActions(self.index)
                    
                    pathlength = current[1] + 1
                    for nexact in nextactions:
                      nextstate = self.getSuccessor(current[0], nexact)
                      nextpos = nextstate.getAgentPosition(self.index)
                      if nextpos not in oppPos and nextpos is not currentpos:
                        stack.append((nextstate, pathlength))

          print("DFS", goodactions)
          if goodactions:
            goodactions.sort(key=itemgetter(1))
            return goodactions[0][0]

          
        return self.goHome(actions, agentPos, gameState)


        # ------------------------------------ OLD CODE, NO LONGER NEEDED
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

    
    # This means we are in enemy territory, but we are holding no food -> this means all our other strategies have failed.
    if(not self.posIsSafe(walls, agentPos)):

      # if goodfoodstat[1] < 2: # this means the ghost can intercept us, but there's only a difference of 1 tile
      #   return self.chaseFood(actions, goodfood, gameState)
      
      if(smartHomePos):
        print("we should be going home")
        return self.gotoHome(actions, smartHomePos, gameState)

      # goHome = True      
      # for oppIndex, oppPosition in oppTheirSide:
      #   if(self.getMazeDistance(agentPos, oppPosition) < self.closestSafeSpace(gameState, agentPos)[0]):
      #     goHome = False
      
      # if goHome:
      if self.getMazeDistance(agentPos, minFoodPos) < 3:
        print("eating greedy")
        return self.chaseFood(actions, goodfood, gameState)

      return self.goHome(actions, agentPos, gameState)


    print("random choice dynamic")
    return self.chaseFood(actions, minFoodPos, gameState)

  
  def smartFood(self, safespaces, targetlist, currentpos, opps):
    self.debugClear()

    scoredlist = [] # store in form (position, score)

    for target, targetdist in targetlist:
      targetstate = True

      targetscore = None
      bestsafe = None

      agent_to_target = self.getMazeDistance(currentpos, target)
      # for opp in opps:
      #   opp_to_target = self.getMazeDistance(opp[1], target)
      #   if targetscore == None or agent_to_target - opp_to_target > targetscore:
      #     targetscore = agent_to_target - opp_to_target

      #   if opp_to_target <= agent_to_target:
      #     targetstate = False
      
      # bestsafestate = False
      # safespace = None
      for safe in safespaces:
        
        safestate = True
        target_to_safe = self.getMazeDistance(target, safe)
        agent_to_safe = self.getMazeDistance(currentpos, safe)
        safescore = -1000000
        for opp in opps:
          opp_to_safe = self.getMazeDistance(opp[1], safe)
          if opp_to_safe <= target_to_safe + agent_to_target:
            safestate = False
          if safescore == None or (agent_to_target + target_to_safe) - opp_to_safe > safescore:
            safescore = (agent_to_target + target_to_safe) - opp_to_safe

        if safestate:
          bestsafestate = True
          safespace = safe
          
        if bestsafe == None or safescore < bestsafe[1]:
          bestsafe = (safe, safescore)
          
      scoredlist.append((target, bestsafe[1], agent_to_target))

      # if targetstate and bestsafestate:
      #   self.debugDraw([target, safespace], [0,1,0])
      #   return target
    scoredlist.sort(key = itemgetter(1, 2))
    return scoredlist[0]
      
    return False

  # smartHome should take as input NOT OUR MIDLINE, but instead, the midline of the opponents that are connected to our side. This is because when we compare the distance between our agent and the opp, we want to see if the opp can reach the final square before we reach home. We don't want to check if the opp can reach our home before us, because we can kill our opp on home squares. it's just the opponent's squares that we are worried about. so we find the middle squares on the opp's side which connects to ourside, and for the ones we can reach faster than the ghost, we return the home square adjacent to it.
  def smartHome(self, safespaces, currentpos, opps):
    
    safetargets = []

    for target in safespaces:
      targetstate = True
      agent_to_target = self.getMazeDistance(currentpos, target)
      for opp in opps:
        opp_to_target = self.getMazeDistance(opp[1], target)
        if opp_to_target <= agent_to_target:
          targetstate = False
      
      # print("Smart Home:", target if targetstate else False)
      if targetstate == True:
        safetargets.append((target, agent_to_target))
    
    if safetargets:
      safetargets.sort(key=itemgetter(1))
      home = safetargets[0][0]
      self.debugDraw(home, [1,0,0])
      return (home[0]-1, home[1]) if self.red else (home[0]+1, home[1])
    
    return False
  

  def smartSeek(self, targetlist, currentpos, opps):
    
    for target, targetdist in targetlist:
      targetstate = True
      agent_to_target = self.getMazeDistance(currentpos, target)
      for opp in opps:
        opp_to_target = self.getMazeDistance(opp[1], target)
        if opp_to_target <= agent_to_target:
          targetstate = False
      
      # print("Smart Seek:", target if targetstate else False)
      if targetstate == True:
        self.debugDraw(target, [0,1,1])
        return target
          
    return False

  def getMeridian(self, grid, red):
    meridian = grid.width//2
    gridlist = grid.asList(key = False)

    midPosList = []
    if red:
      for i in gridlist:
        if i[0] == meridian-1:
          midPosList.append(i)
    else:
      for i in gridlist:
        if i[0] == meridian:
          midPosList.append(i)
    
    return midPosList

  def actionPos(self, gameState, action):
    successor = self.getSuccessor(gameState, action)
    successorPos = successor.getAgentPosition(self.index)
    return successorPos

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
  
  def posIsSafe(self, grid, pos):
    if self.red:
      return pos[0] < grid.width//2
    else:
      return pos[0] >= grid.width//2

class DefenseAgent(CommonAgent):
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
    self.ourFoodGridLast = None
    self.chasePos = None
    self.seenPositions = []

    # MODIFIED class constructor to hold data variables

  def registerInitialState(self, gameState):
    """
    This method handles the initial setup of the
    agent to populate useful fields (such as what team
    we're on).

    A distanceCalculator instance caches the maze distances
    between each pair of positions, so your agents can use:
    self.half_dist.getDistance(p1, p2)

    IMPORTANT: This method may run for at most 15 seconds.
    """

    '''
    Make sure you do not delete the following line. If you would like to
    use Manhattan distances instead of maze distances in order to save
    on initialization time, please take a look at
    CaptureAgent.registerInitialState in captureAgents.py.
    '''
    CaptureAgent.registerInitialState(self, gameState)

    fullgrid = gameState.getWalls()
    halfGrid = capture.halfGrid(fullgrid, red=self.red)

    # state_copy = gameState.deepcopy()
    layout_text = str(gameState.data.layout).split("\n")
    half_layout_text = []
    for line in layout_text:
      #print(line)
      wallBuffer = "".join(["%" for i in range(len(line)//2)])
      half_layout_text.append(line[:len(line)//2] + wallBuffer) if self.red else half_layout_text.append(wallBuffer + line[len(line)//2:])

    
    print("\n".join(half_layout_text))

    half_layout = layout.Layout(half_layout_text)

    #print(half_layout)
    
    self.half_dist = distanceCalculator.Distancer(half_layout)

    # comment this out to forgo maze distance computation and use manhattan distances
    self.half_dist.getMazeDistances()
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


  def chooseAction(self, gameState):
    self.debugClear()
    """
    Picks among actions randomly.
    """
    actions = gameState.getLegalActions(self.index)

    oppPacmans = self.closestOppPacman(gameState)
    agentPos = gameState.getAgentPosition(self.index)
    grid = gameState.getWalls()

    if(agentPos == self.start):
      self.scared = False

    ourFoodGrid = self.getFoodYouAreDefending(gameState)
    if self.ourFoodGridLast is None: 
      self.ourFoodGridLast = ourFoodGrid
    
    """The following code determines if there is a pacman that has eaten our food in the last timestep. If there is a pacman, the chase position is set, and our defender goes to the chase position."""
    pacmans_in_food = []

    for x in range(ourFoodGrid.width):
      for y in range(ourFoodGrid.height):
        if self.ourFoodGridLast[x][y] ^ ourFoodGrid[x][y]:
          pacmans_in_food.append(((x,y), self.half_dist.getDistance(agentPos, (x,y))))
          self.seenPositions.append((x,y))
    
    if pacmans_in_food:
      pacmans_in_food = sorted(pacmans_in_food, key=itemgetter(1))
      self.chasePos = pacmans_in_food[0][0]
    
    self.ourFoodGridLast = ourFoodGrid
    # print(pacmans_in_food)
    # print(self.chasePos)

    """Initializing some variables. opps stores all opponent positions and indices in form (index, position)"""
    opps = self.opponents(self.getCurrentObservation())
    midpoint = gameState.getWalls().width//2

    # print(agentPos, self.chasePos, self.randomDefPos)

    # oppPacmans = self.closestOppPacman(gameState)
    '''oppPacmans is list of opponent Pacmans. oppTheirSide is list of opponent ghosts that are on their side of the map'''
    if(self.red):
      oppPacmans = [opp for opp in opps if opp[1][0]<midpoint]
      oppTheirSide = [opp for opp in opps if opp[1][0]>=midpoint]
    else:
      oppPacmans = [opp for opp in opps if opp[1][0]>=midpoint]
      oppTheirSide = [opp for opp in opps if opp[1][0]<midpoint]
    
    # print(opps)

    '''we check if the opponent has eaten the power pellet'''
    oppPower = self.checkOppPower(gameState)
    if(oppPower):
      print("\topp has power")
      # for action in actions:
        # print("\t", self.actionPos(gameState, action))
        # print("\t", [opp for opp in oppPacmans])

    '''If we see a pacman, then we want to chase after it. HOWEVER, if the opponents have power active then we don't want to attack the pacman because we will die.'''
    if len(oppPacmans) > 0:
      minChaseDistance = None
      minOppPosition = None
      minAction = None
      minDist = None
      for [oppIndex, oppPosition] in oppPacmans:
        # self.seenPositions.append(oppPosition)
        # self.pacman_last_seen[oppIndex] = oppPosition
        chaseDistance = self.half_dist.getDistance(gameState.getAgentState(self.index).getPosition(), oppPosition)
        if minOppPosition is None or chaseDistance < minChaseDistance:
          minChaseDistance = chaseDistance
          minOppPosition = oppPosition

      self.randomDefPos = None
      self.chasePos = minOppPosition 
      '''This makes it so that if this pacman suddenly leaves our sight, our ghost will go to that position anyway. because ghost is faster than pacman, by the time we reach the pacman's old position we should be able to see the pacman, unless it has gone back home.'''
      
      '''Here, if the opponent power pellet is active, but they are far away from their home, its possible that their power pellet will run out before they reach their home. In that case we want to stay close to the enemy so that as soon as their power runs out, we can kill the pacman. But because the opp power is active, we do not want to directly attack it.'''
      oppDistToHome = self.distToMeridian(grid, minOppPosition)[0] + 1
      # print(oppDistToHome, 40-self.oppPowerTurns)

      if(self.scared and oppPower and oppDistToHome * 2 > 40 - self.oppPowerTurns):
        # print("oppPower but chase opp")
        for action in actions:
          successor = self.getSuccessor(gameState, action)
          successorPos = successor.getAgentState(self.index).getPosition()
          if(self.posIsSafe(grid, successorPos)):
            if minDist is None or self.half_dist.getDistance(successorPos, minOppPosition) < minDist:
              minDist = self.half_dist.getDistance(successorPos, minOppPosition)
              minAction = action

        # print('chasing visible pacman')
        if minDist is not 0:
          return minAction
        else:
          for action in actions:
            if(self.posIsSafe(grid, self.actionPos(gameState, action))):
              return action
            
      else:

        '''If power pellet is not active, or a lot of time remains for the opp's power, we chase the pacman. we might die if the power is active, but dying resets state and makes us able to kill pacman again, which is better if there is a lot of time left.'''
        for action in actions:
          successor = self.getSuccessor(gameState, action)
          successorPos = successor.getAgentState(self.index).getPosition()
          if(self.posIsSafe(grid, successorPos)):
            if minDist is None or self.half_dist.getDistance(successorPos, minOppPosition) < minDist:
              minDist = self.half_dist.getDistance(successorPos, minOppPosition)
              minAction = action

        # print('chasing visible pacman')
        return minAction
    
    if self.chasePos is not None:
      # print("chasePos is not None")
      for action in actions:
        successor = self.getSuccessor(gameState, action)
        successorPos = successor.getAgentState(self.index).getPosition()
        
        if self.posIsSafe(grid, successorPos) and self.half_dist.getDistance(successorPos, self.chasePos) < self.half_dist.getDistance(agentPos, self.chasePos):

          if(successorPos == self.chasePos):
            # print("chasePos reached", self.chasePos, successorPos)
            self.chasePos = None

          # print("chasing chasePos: food eaten or previous sighting", self.chasePos, successorPos)
          return action

    elif opponentPos := [(x[1], self.distToMeridian(grid, x[1])[0], self.distToMeridian(grid, x[1])[1]) for x in oppTheirSide if self.distToMeridian(grid, x[1])[0] < 3]:
      """This code allows defender to see ghosts on the other side. If there is a ghost, then that ghost might try to enter our side as pacman, so we can stay near it to deter it from entering. However this has the problem that it can cause defender to get stuck"""
      
      # print("defense sees ghost")
      # midList = self.getHomeMeridian(grid)
      closeMid = None
      print(closeMid)
      for oppPos, midDist, midPoint in opponentPos:
        if closeMid is None or self.getMazeDistance(agentPos, midPoint) < closeMid[0]:
          closeMid = (midDist, midPoint)

      # print("closest mid to opp", oppMid[1])

      for action in actions:
        successor = self.getSuccessor(gameState, action)
        successorPos = successor.getAgentState(self.index).getPosition()
        if(self.posIsSafe(grid, successorPos)):
          if self.half_dist.getDistance(successorPos, closeMid[1]) < self.half_dist.getDistance(agentPos, closeMid[1]) and self.posIsSafe(grid, successorPos):

            # print("mid defense", closeMid)
            return action

    """The code below is for a random restart. This is how the defender patrols our side of the map. It picks a random position near the edge, and goes to it. We do this if we don't see any pacman. If we see a pacman, or we detect pacman from the missing food, we go to it immediately."""
    # print("start random")
    return self.goToRandom(actions, gameState)
  
  
  # Function for random restart, allows defender to patrol our map
  def goToRandom(self, actions, gameState):
    if not self.randomDefPos:
      self.setRandomDefPos(gameState.getWalls(), gameState.getAgentPosition(self.index), gameState)

    for action in actions:
      successor = self.getSuccessor(gameState, action)
      successorPos = successor.getAgentPosition(self.index)
      agentPos = gameState.getAgentPosition(self.index)

      if self.posIsSafe(gameState.getWalls(), successorPos) and self.half_dist.getDistance(successorPos, self.randomDefPos) and self.half_dist.getDistance(successorPos, self.randomDefPos) < self.half_dist.getDistance(agentPos, self.randomDefPos):
        if successorPos == self.randomDefPos:
          self.randomDefPos = None
        
        # print('going to random defense:', self.randomDefPos, agentPos)
        return action
    
    # print("randomDefPos failed, retrying")
    self.setRandomDefPos(gameState.getWalls(), gameState.getAgentPosition(self.index), gameState)

    acceptableActions = []
    for action in actions:
      if self.posIsSafe(gameState.getWalls(), self.actionPos(gameState, action)):
        acceptableActions += [action]

    print('random choice defense')
    return random.choice(acceptableActions)

  def distToMeridian(self, grid, position):
    midList = self.getHomeMeridian(grid)
    minPoint = None
    minDist = None
    for mid in midList:
      if minPoint is None or self.getMazeDistance(position, mid) < minDist:
        minPoint = mid
        minDist = self.getMazeDistance(position, mid)
    return (minDist, minPoint)

  def getHomeMeridian(self, grid):
    meridian = grid.width//2
    gridlist = grid.asList(key = False)

    midPosList = []
    if self.red:
      for i in gridlist:
        if i[0] == meridian-1:
          midPosList.append(i)
    else:
      for i in gridlist:
        if i[0] == meridian:
          midPosList.append(i)
    
    return midPosList
    
  def actionPos(self, gameState, action):
    successor = self.getSuccessor(gameState, action)
    successorPos = successor.getAgentPosition(self.index)
    return successorPos

  def posIsSafe(self, grid, pos):
    if self.red:
      return pos[0] < grid.width//2
    else:
      return pos[0] >= grid.width//2

  def setRandomDefPos(self, grid, agentPos, gameState):

    meridian = grid.width//2
    gridlist = grid.asList(key = False)
    gridlist.extend(self.seenPositions)
    gridlist.extend(self.getFoodYouAreDefending(gameState))
    for i in range(2):
      gridlist.extend(self.getCapsulesYouAreDefending(gameState))
    start = 1
    end = 0
    randomPosList = []
    if self.red:
      for i in gridlist:
        if i[0]>=meridian-start and i[0] < meridian-end and abs(i[1]-agentPos[1])>grid.height/4:
          randomPosList.append(i)
    else:
      for i in gridlist:
        if i[0]>=meridian+end and i[0] < meridian+start and abs(i[1]-agentPos[1])>grid.height/4:
          randomPosList.append(i)
    
    
    self.randomDefPos = random.choice(randomPosList)


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
