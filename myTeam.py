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


from operator import itemgetter
from captureAgents import CaptureAgent
import random, time, util
from game import Directions
import game

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'DynamicAgent', second = 'DynamicAgent'):
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

# key: enemy index
# value: -1 if the enemy is not chaseable, otherwise the index of the agent that is chasing it
enemy_marked = {}

class DynamicAgent(CaptureAgent):

  def __init__(self, *args, **kwargs):

    super().__init__(*args, **kwargs)
    self.data = set()
    self.dictionary = {}
    self.holdingFood = 0

    

  def registerInitialState(self, gameState):
    global enemy_marked

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

    if len(enemy_marked) == 0:
      for oppIndex in self.getOpponents(gameState):
        enemy_marked[oppIndex] = -1


  # you can check if the opponent's agent is a pacman even when it is not close to our agents (but we don't know the exact position of their agents)
  def getClosestOppPacman(self, gameState):
    global enemy_marked
    oppPacman = []

    for oppIndex in self.getOpponents(gameState):
      oppPosition = gameState.getAgentState(oppIndex).getPosition()
      if gameState.getAgentState(oppIndex).isPacman and oppPosition != None:
        # only chase an enemy if you are already chasing it or nobody is already chasing it
        if enemy_marked[oppIndex] == self.index or enemy_marked[oppIndex] == -1:
          oppPacman.append([oppIndex, oppPosition])
        
      else:
        # unmark the enemy pacman (when they disappear(either by being eaten or going back to their home))
        enemy_marked[oppIndex] = -1

    return oppPacman
  
  def getSuccessor(self, gameState, action):
    """
    Finds the next successor which is a grid position (location tuple).
    """
    successor = gameState.generateSuccessor(self.index, action)
    pos = successor.getAgentState(self.index).getPosition()
    if pos != util.nearestPoint(pos):
      # Only half a grid position was covered
      return successor.generateSuccessor(self.index, action)
    else:
      return successor


  def getClosestFoodDistance(self, gameState):
    # cannot declare a global food variable since the food position can be changed
    food = self.getFood(gameState).asList()
    minFoodDistance = float('inf')
    minFoodPos = None
    for foodPos in food:
      foodDistance = self.getMazeDistance(gameState.getAgentState(self.index).getPosition(), foodPos)
      if foodDistance < minFoodDistance:
        minFoodDistance = foodDistance
        minFoodPos = foodPos
    return [minFoodPos, minFoodDistance]

  def chooseAction(self, gameState):

    actions = gameState.getLegalActions(self.index)
    agentPos = gameState.getAgentState(self.index).getPosition()

    '''
    Find nearest food distance (called foodDistance)
    Check if the opponent's agent is a pacman and we can get its position
      -> Yes, calculate chaseDistance using mazeDistance
        -> If chaseDistance * 2 < foodDistance -> iterate through actions to get the suitable one (??? how to check)
      -> Else, go to the nearest food
    ''' 
    [closestFoodPos, closestFoodDistance] = self.getClosestFoodDistance(gameState)
    oppPacmans = self.getClosestOppPacman(gameState)
    

    if len(oppPacmans) > 0:
      minChaseDistance = float('inf')
      for [oppIndex, oppPosition] in oppPacmans:
        chaseDistance = self.getMazeDistance(agentPos, oppPosition)
        minChaseDistance = min(minChaseDistance, chaseDistance)

      
      # chase the opponent
      if minChaseDistance * 2 < closestFoodDistance:
        # print("chase")
        for action in actions:
          successor = self.getSuccessor(gameState, action)
          succAgentPos = successor.getAgentState(self.index).getPosition()
          if self.getMazeDistance(succAgentPos, oppPosition) < chaseDistance:
            enemy_marked[oppIndex] = self.index
            return action
          

    # go to the nearest food 
    # INSERT YOUR GETTING FOOD FUNCTION HERE
    
    for action in actions:
      successor = self.getSuccessor(gameState, action)
      if self.getMazeDistance(agentPos, closestFoodPos) < closestFoodDistance:
        return action
      
    currentFood = self.getFood(gameState).asList()
    # oppGhostPresence = False
    if(self.holdingFood < 2):
      minFood = -1
      minFoodTile = None
      for foodPos in currentFood:
        if self.distancer.getDistance(agentPos, foodPos) < minFood or minFood<0:
          minFood = self.distancer.getDistance(agentPos, foodPos)
          minFoodTile = foodPos

      #print(actions)

      distances = []
      for action in actions:
        successor = self.getSuccessor(gameState, action)
        successorPos = successor.getAgentPosition(self.index)
        distances.append((action, self.distancer.getDistance(successorPos, minFoodTile)))

      distances = sorted(distances, key=itemgetter(1))

      if(distances[0][1]==0):
        self.holdingFood+=1
      return distances[0][0]
    else:
      walls = gameState.getWalls()
      gridList = walls.asList(key=False)
      #print(gameState.data)
      # do we have self.red or self.isRed?
      safeSpaces = halfList(l=gridList, grid=walls, red=self.red)
      #print(safeSpaces)
      closest_safe_space=None
      for safe_square in safeSpaces:
        if closest_safe_space==None or self.distancer.getDistance(agentPos, safe_square) < closest_safe_space[0]:
          closest_safe_space = (self.distancer.getDistance(agentPos, safe_square), safe_square)

      #print(closest_safe_space)
      distances = []
      for action in actions:
        successor = self.getSuccessor(gameState, action)
        successorPos = successor.getAgentPosition(self.index)
        distances.append((action, self.distancer.getDistance(successorPos, closest_safe_space[1])))

      distances = sorted(distances, key=itemgetter(1))

      if(distances[0][1]==0):
        self.holdingFood-=1
      return distances[0][0]


def halfList(l, grid, red):
  halfway = grid.width // 2
  newList = []
  for x,y in l:
    if red and x < halfway: newList.append((x,y))
    elif not red and x >= halfway: newList.append((x,y))
  return newList