#! /usr/bin/python

import sys
import copy
import re

class Meal:
  def __init__(self, mealName, servingSize, ingredients):
    self.name = mealName
    self.servingSize = servingSize
    self.ingredients = ingredients
    self._calculateTotals()

  def _calculateTotals(self):
    carbGrams = 0
    protGrams = 0
    fatGrams = 0
    for ingredient in self.ingredients:
      carbGrams += ingredient.macros.carbGrams
      protGrams += ingredient.macros.protGrams
      fatGrams += ingredient.macros.fatGrams
    self.macros = Macros(carbGrams, protGrams, fatGrams)   

  def printIngredients(self):
    for ingredient in self.ingredients:
      print ingredient.toString()

  def printMeasurements(self):
    print self.macros.toStringAll()

  def printMeasurementsServing(self):
    servingMacros = self.getMacrosPerServing()
    if servingMacros is None:
      return
    print "Servings: " + str(self.servingSize)
    print "Measurements per serving:"
    print servingMacros.toStringAll()

  def getMacrosPerServing(self):
    if self.servingSize is None:
      print "Serving size unknown for " + self.name + ". Must specify."
      return None
    macroServing = copy.deepcopy(self.macros)
    macroServing.multiplyByFactor(float(1)/float(self.servingSize))
    return macroServing

class Unit:
  def __init__(self, quantity, unitType):
    self.quantity = quantity
    self.type = unitType

  def toString(self):
    return str(self.quantity) + " " + self.type

class Ingredient:
  def __init__(self, ingredientName, units):
    self.name = ingredientName
    self.units = units
    # macros added later

  def toString(self):
    return self.name + " | " + self.units.toString() + " | " + self.macros.toStringGramsMeasurements()

class DbEntry:
  def __init__(self, entryName, units, macros):
    self.name = entryName
    self.units = units
    self.macros = macros

class Macros:
  def __init__(self, carbGrams, protGrams, fatGrams):
    self.carbGrams = carbGrams
    self.protGrams = protGrams
    self.fatGrams = fatGrams

  def toStringAll(self):
    return self.toStringGramsMeasurements() + "\n" + \
           self.toStringCaloriesMeasurements() + "\n" + \
           self.toStringTotalCalories() + "\n" + \
           self.toStringRatioMeasurements()

  def toStringGramsMeasurements(self):
    return "Carb/prot/fat in grams: " + str(self.carbGrams) + "/" + str(self.protGrams) + "/" + str(self.fatGrams) 

  def toStringCaloriesMeasurements(self):
    return "Carb/prot/fat in calories: " + str(self.getCarbCalories()) + "/" + str(self.getProtCalories()) + "/" + str(self.getFatCalories())

  def toStringTotalCalories(self):
    return "Total calories: " + str(self.getTotalCal())

  def toStringRatioMeasurements(self):
    return "Carb/prot/fat macronutrient ratio: " + str(self.getCarbRatio()) + "/" + str(self.getProtRatio()) + "/" + str(self.getFatRatio())

  def multiplyByFactor(self, factor):
    self.carbGrams *= factor
    self.protGrams *= factor
    self.fatGrams *= factor

  def add(self, other):
    self.carbGrams += other.carbGrams
    self.protGrams += other.protGrams
    self.fatGrams += other.fatGrams

  def getCarbCalories(self):
    return self.carbGrams * 4

  def getProtCalories(self):
    return self.protGrams * 4

  def getFatCalories(self):
    return self.fatGrams * 9 

  def getTotalCal(self):
    return self.getCarbCalories() + self.getProtCalories() + self.getFatCalories()
    
  def getCarbRatio(self):
    return self.getCarbCalories() / self.getTotalCal()

  def getProtRatio(self):
    return self.getProtCalories() / self.getTotalCal()

  def getFatRatio(self):
    return self.getFatCalories() / self.getTotalCal()

##################################################################################
# True if the next line to be read would be an empty line
# Preserves file position if next line isn't the empty line, otherwise skips over
def atEmptyLine(inputFile):
    curPos = inputFile.tell()
    line = inputFile.readline().rstrip()
    line = re.sub(re.compile("\//.*"), "", line) # remove comment lines
    if len(line) is 0:
      return True
    inputFile.seek(0)
    inputFile.seek(curPos)
    return False
##################################################################

##################################################################
class EofCheck:
  def __init__(self, inputFile):
    self.inputFile = inputFile
    self.lastLinePos = self._getLastLinePos()

  def _getLastLinePos(self):
    for line in self.inputFile:
      self.linePos = self.inputFile.tell()
    self.inputFile.seek(0)
    return self.linePos

  def isAtEndOfFile(self):
    return self.inputFile.tell() >= self.lastLinePos
##################################################################

####################################
def parseUnit(unitStr):
  unitStr = unitStr.rstrip()
  quantityUnits, typeUnits = unitStr.split(" ")
  quantityUnits = float(quantityUnits)
  return Unit(quantityUnits, typeUnits)
####################################

####################################
def parseMacros(macroStr):
  carb, prot, fat = macroStr.split("/")
  return Macros(float(carb), float(prot), float(fat))
####################################

####################################
def parseIngredient(line) :
  substrings = line.split(" - ")

  # ingredient name
  name = substrings[0][2:].lower() # remove first two characters ('- ')
    
  # ingredient unit
  unit = parseUnit(substrings[1])

  # combine it all into ingredient
  return Ingredient(name, unit)
##########################################

##########################################
def parseDbEntry(line) :
  line = re.sub(re.compile("\//.*"), "", line) # remove trailing comments if present  
  substrings = line.split(" | ")

  # entry name
  name = substrings[0].lower()
    
  # entry unit
  units = parseUnit(substrings[1])

  # macros (in grams assumed)
  macros = parseMacros(substrings[2])

  return DbEntry(name, units, macros)
#########################################

#########################################
def parseServingSize(fullStr):
  split = fullStr.split(" - ")
  if len(split) is 2:
    split = split[1].split(" ")
    if len(split) is 2 and (split[1].lower() == "serving" or split[1].lower() == "servings"):
      return float(split[0])
  return None          
#########################################

#########################################
def parseMeal(mealFile, eof):

  while atEmptyLine(mealFile):
    if eof.isAtEndOfFile():
      return None
    continue

  recipeTitle = mealFile.readline().rstrip()
  servingSize = parseServingSize(recipeTitle)
        
  ingredients = []
  line = mealFile.readline()
  # Read in the ingredients
  while line and len(line.split()) > 1 and line.split()[0] in "-":
    line = re.sub(re.compile("\//.*"), "", line) # remove trailing comments if present
    ingredients.append(parseIngredient(line))
    line = mealFile.readline()
  # Read in the macros for the ingredients
  for ingredient in ingredients:
    if ingredient.name not in db:
      print "The macro ratios in grams for the ingredient, " + ingredient.name + " aren't available and need to be added."
      sys.exit(1)      
    ingredient.macros = copy.deepcopy(db[ingredient.name].macros)
    dbUnits = db[ingredient.name.lower()].units
    if ingredient.units.type != dbUnits.type:
      print "the units for " + ingredient.name + " differ with the database file. May need to convert to the same unit. Exiting for now."
      sys.exit(1)
    # multiply out the macros
    ingredient.macros.multiplyByFactor(ingredient.units.quantity / dbUnits.quantity)     

  # Create the meal
  return Meal(recipeTitle, servingSize, ingredients)

#########################################

#########################################
def yesNoPrompt(prompt):
  answer = raw_input(prompt)
  while answer != "y" and answer != "n":
    answer = raw_input(prompt)
  return answer == "y"
#########################################

# Read in db file
db = {}
with open("MacroDB", "r") as dbFile:
  for line in dbFile:
    if "---" in line:
      break # done
    entry = parseDbEntry(line)
    db[entry.name.lower()] = entry

# Read in the meal file
if len(sys.argv) < 2:
  print "Need to specify file name that has the recipes"
  sys.exit(1)

fileName = sys.argv[1]
with open(fileName, "r") as mealFile:
  meals = []
  eof = EofCheck(mealFile)
  while not eof.isAtEndOfFile():
    meal = parseMeal(mealFile, eof)
    if meal is None:
      continue # Probably end of file...
    print "\n\nThe meal/recipe, " + meal.name + ", has the following ingredients: "
    print "------------"
    meal.printIngredients() 
    print "------------"
    print "The meal's overall macros and calories are: "
    meal.printMeasurements()
    print "------------"
    if meal.servingSize is None:
      meal.servingSize = raw_input("Specify the desired serving amount: ")
    print "The meal has the following macro measurements per serving: "
    meal.printMeasurementsServing()
    meals.append(meal)
    print "------------"
   
  print "\n------------"
  if yesNoPrompt("Print aggregated measurement for all meals just measured (on a per serving basis)? [y/n]"):
    print "------------\n"
    aggregatedMacros = Macros(0,0,0)
    for meal in meals:
      aggregatedMacros.add(meal.getMacrosPerServing())
    print "-----------"
    print "Aggregated measurements (total macros when adding 1 serving measurement for all meals previously shown):"
    print aggregatedMacros.toStringAll()
    print "-----------"



