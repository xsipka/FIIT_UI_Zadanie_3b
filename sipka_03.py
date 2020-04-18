import random
import configparser as ConfigParser
import csv


# list of used constants................................................................................................

MEMORY_CELL_COUNT = 64              # length of an individual
STARTING_MEMORY_CELL_COUNT = 32     # part that will be filled when creating first generation
MAX_STEPS_COUNT = 500               # maximal amount of executed instructions
INDIVIDUAL_COUNT = 100              # number of individuals in every generation
GENERATION_COUNT = 1200             # number of generations

ELITARISM_RATE = 0.02               # part of the best individuals that will be transformed to the next generation
NEW_INDIVIDUALS_RATE = 0.15         # section of newly created individuals for next generation
SINGLE_CELL_MUTATION = 0.3          # chance of mutation for an individual obtained by crossover
MULTIPLE_CELL_MUTATION = 0.1        # chance of mutation of multiple memory cells


# list of used global variables.........................................................................................

# list of treasure locations
treasures = []

# map size
row_num = 0
col_num = 0

# starting location coordinates
row_start = 0
col_start = 0

# count average and best fitness for every generation
avg_fitness = []


# 1. map initialization and creation of first generation................................................................

# initializes starting and treasure locations and map size
def map_init():
    global treasures
    global row_num, col_num
    global row_start, col_start

    Config = ConfigParser.ConfigParser()
    Config.read("map_init.ini")

    row_num = Config.getint('Map', 'row_num')
    col_num = Config.getint('Map', 'col_num')

    row_start = Config.getint('Map', 'row_start')
    col_start = Config.getint('Map', 'col_start')

    treasure_num = Config.getint('Map', 'treasure_num')

    for i in range(treasure_num):
        x = Config.getint('Treasure_' + str(i + 1), 'row_num')
        y = Config.getint('Treasure_' + str(i + 1), 'col_num')
        treasures.append((x, y))

    return

# generates random data for current individual
def generate():
    steps = []

    for i in range(MEMORY_CELL_COUNT):
        steps.append(0)

    for i in range(STARTING_MEMORY_CELL_COUNT):
        steps[i] = random.randint(0, 255)

    return steps

# creates first generation of population with random data
def create_first_generation():
    first_gen = {0: {'fitness': 0, 'step_sequence': [], 'path': [], 'path_final': [],'found_treasures': []}}

    for i in range(INDIVIDUAL_COUNT):
        first_gen[i] = {}
        first_gen[i]['fitness'] = 0
        first_gen[i]['step_sequence'] = generate()
        first_gen[i]['path'] = []
        first_gen[i]['path_final'] = []
        first_gen[i]['found_treasures'] = []

    return first_gen


# 2. runs program for every individual, checks found treasures, calculates fitness......................................

# executes program sequence for current individual
def execute(individual):
    operation_counter = 0
    cell_index = 0
    steps_copy = individual['step_sequence'].copy()

    while check_cell_index(cell_index) and operation_counter < MAX_STEPS_COUNT:
        # takes first two bits from current memory cell
        operator = (bin(steps_copy[cell_index])[2:].zfill(8)[:2])
        # takes last six bits from current memory cell
        address = int((bin(steps_copy[cell_index])[2:].zfill(8)[2:]), 2)
        cell_index += 1
        operation_counter += 1

        #print("operation:", operator, cell_index - 1, address, individual[address])

        # increment
        if operator == "00":
            steps_copy[address] += 1
            #print("++ na address:", address, individual[address])
            # if value over the limit then nullify
            if steps_copy[address] == 256:
                steps_copy[address] = 0

        # decrement
        if operator == "01":
            steps_copy[address] -= 1
            #print("-- na address:", address, individual[address])
            # if value over the limit then maximise
            if steps_copy[address] == -1:
                steps_copy[address] = 255

        # jump
        if operator == "10":
            #print("jump na address:", address, individual[address], cell_index)
            cell_index = address

        # write
        if operator == "11":
            individual['path'].append(get_steps(steps_copy[address]))

    return

# checks if cell index has acceptable value
def check_cell_index(index):
    if index >= 0 and index < MEMORY_CELL_COUNT:
        return True
    else:
        return False

# get steps from memory cell
def get_steps(memory_cell):
    # takes last two bits from current memory cell
    direction = (bin(memory_cell)[2:].zfill(8)[6:])

    # right
    if direction == "11":
        return "P"
    # left
    if direction == "10":
        return "L"
    # down
    if direction == "01":
        return "D"
    # up
    if direction == "00":
        return "H"

# checks if any treasures are found
def found_treasures(individual):
    global treasures
    global row_num, col_num
    global row_start, col_start

    curr_row = row_start
    curr_col = col_start

    for direction in individual['path']:
        # goes in selected direction
        if direction == "H":
            curr_row -= 1
        if direction == "D":
            curr_row += 1
        if direction == "L":
            curr_col -= 1
        if direction == "P":
            curr_col += 1

        # if new coordinates are out of the map, then end function
        if check_coordinates(curr_row, curr_col) == False:
            return
        else:
            individual['path_final'].append(direction)

        # checks if there is some treasure on current coordinates
        for treasure_loc in treasures:
            if treasure_loc[0] == curr_row and treasure_loc[1] == curr_col:
                if treasure_loc not in individual['found_treasures']:
                    individual['found_treasures'].append(treasure_loc)
                    #print("trejšr was found: ", individual['found_treasures'])

        # if all treasures are found, then end function
        if len(treasures) == len(individual['found_treasures']):
            # print("All treasures found. Nice!")
            return

    return

# checks if current coordinates are in area
def check_coordinates(curr_row, curr_col):
    global row_num, col_num

    if curr_col >= 0 and curr_col < col_num and curr_row >= 0 and curr_row < row_num:
        return True
    else:
        return False

# calculates fitness for current individual
def calculate_fitness(individual):
    global row_num, col_num

    map_size = row_num * col_num
    treasures_num = len(individual['found_treasures'])
    path_length = len(individual['path_final'])
    path_fitness_val = path_length/map_size

    # if there is no path, fitness is zero
    if path_length == 0:
        individual['fitness'] = 0
        return

    # highest fitness value is for shorter paths with most found treasures
    if treasures_num > 0:
        # if path is shorter than map size
        if path_length/map_size < 1:
            individual['fitness'] = treasures_num + (1 - path_fitness_val)
        # if path is longer than map size
        else:
            # if path is too long, then divide it by 10 until less than zero
            while path_fitness_val >= 1:
                path_fitness_val /= 10
            # add a number of found treasures
            individual['fitness'] = treasures_num + (path_fitness_val/10)
        return

    # longer paths are better, higher potential of finding a treasure
    if treasures_num == 0:
        individual['fitness'] = path_length/map_size
        while individual['fitness'] >= 1:
            individual['fitness'] /= 10
        return


# 3. finds best individuals in generation, prints out generation summary................................................

# sorts individuals by fitness value
def sort_individuals(generation):
    sorted_list = []
    sorted_dict = sorted(generation.items(), reverse=True, key=lambda x: x[1]['fitness'])

    # creates and returns list of sorted keys of dictionary
    for i in range(INDIVIDUAL_COUNT):
        sorted_list.append(sorted_dict[i][0])

    return sorted_list

# prints out important data about current generation
def generation_summary(gen_num, generation, index_list):
    global avg_fitness

    fitness_sum = 0
    treasure_sum = 0
    path_sum = 0

    print("Generation ", str(gen_num) + "." )
    print("Best:  Found treasures:", len(generation[index_list[0]]['found_treasures']))
    print("       Fitness: {:.2f}".format(generation[index_list[0]]['fitness']))
    print("       Path length: ", len(generation[index_list[0]]['path_final']))

    for i in range(INDIVIDUAL_COUNT):
        treasure_sum += len(generation[i]['found_treasures'])
        fitness_sum += generation[i]['fitness']
        path_sum += len(generation[i]['path_final'])

    print("Avg treasures found: ", treasure_sum/INDIVIDUAL_COUNT, ", Avg fitness: ", round(fitness_sum/INDIVIDUAL_COUNT, 2),
          " Avg path length: ", path_sum/INDIVIDUAL_COUNT, "\n")

    avg_fitness.append(round(fitness_sum/INDIVIDUAL_COUNT, 2))
    return


# 4. creates new generation by mutation, crossover, elitarism and new random individuals................................

# creates new generation of population
def create_new_generation(current_gen, index_list):
    new_gen = {0: {'fitness': 0, 'step_sequence': [], 'path': [], 'path_final': [],'found_treasures': []}}
    top_individuals = int(ELITARISM_RATE * INDIVIDUAL_COUNT)
    new_individuals = int(NEW_INDIVIDUALS_RATE * INDIVIDUAL_COUNT)
    others = top_individuals + new_individuals
    parent_index = -1

    # takes the best individuals from current generation
    for i in range(top_individuals):
        new_gen[i] = {}
        new_gen[i] = create_individual(new_gen[i], current_gen[index_list[i]]['step_sequence'])

    # creates some new random individuals
    for i in range(top_individuals, top_individuals + new_individuals):
        new_gen[i] = {}
        new_gen[i] = create_individual(new_gen[i], generate())

    # gets the rest of the individuals by mutation and crossover
    while others < INDIVIDUAL_COUNT:
        new_gen[others] = {}
        # gets new individual by crossover
        parent_one = current_gen[index_list[parent_index]]
        parent_two = current_gen[index_list[others]]
        new_gen[others] = create_individual(new_gen[others], crossover(parent_one, parent_two))

        # if true then mutate one or multiple memory cells
        mutation_chance = random.random()
        if SINGLE_CELL_MUTATION > mutation_chance:
            # if true then mutate random number of memory cells
            if MULTIPLE_CELL_MUTATION > mutation_chance:
                to_mutate = random.randint(0, MEMORY_CELL_COUNT)
                for i in range(to_mutate):
                    mutation(new_gen[others])
            # if only first condition true then mutate one memory cell
            else:
                mutation(new_gen[others])

        parent_index += 1
        others += 1

    return new_gen

# create new individual
def create_individual(individual, step_sequence):

    individual['fitness'] = 0
    individual['step_sequence'] = step_sequence
    individual['path'] = []
    individual['path_final'] = []
    individual['found_treasures'] = []

    return individual

# makes a crossover between two parents
def crossover(parent_one, parent_two):
    steps = []

    for i in range(MEMORY_CELL_COUNT):
        if i % 2 == 0:
            steps.append(parent_one['step_sequence'][i])
        else:
            steps.append(parent_two['step_sequence'][i])

    return steps

# mutates random gene
def mutation(individual):
    rand_pos = random.randint(0, MEMORY_CELL_COUNT - 1)
    rand_val = random.randint(0, 255)

    individual['step_sequence'][rand_pos] = rand_val

    return


# 5. main program.......................................................................................................

# main function
def main():
    global avg_fitness

    map_init()
    current_gen = create_first_generation()
    best_copy = {}

    for gen in range(GENERATION_COUNT):
        for i in range(INDIVIDUAL_COUNT):
            # executes program for every individual
            execute(current_gen[i])
            # checks found treasures and calculate fitness
            found_treasures(current_gen[i])
            calculate_fitness(current_gen[i])

        # calculates fitness, prints generation summary and creates new generation
        sorted_index = sort_individuals(current_gen)
        generation_summary(gen, current_gen, sorted_index)
        best_copy = current_gen[sorted_index[0]].copy()
        current_gen = create_new_generation(current_gen, sorted_index)

    # prints the best individual
    print("The best:  Found treasures:", len(best_copy['found_treasures']))
    print("           Fitness: {:.2f}".format(best_copy['fitness']))
    print("           Path length: ", len(best_copy['path_final']))
    print("           Path : ", best_copy['path_final'],"\n")

    # writes info about fitness values into .cvs file
    with open('statistics.csv', mode='w') as stats_file:
        fieldnames = ['generation', 'avg_fitness']
        writer = csv.DictWriter(stats_file, fieldnames=fieldnames)
        writer.writeheader()

        for i in range(GENERATION_COUNT):
            writer.writerow({'generation': i, 'avg_fitness': avg_fitness[i]})


main()