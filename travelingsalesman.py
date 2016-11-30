import time, random, Tkinter, sys

# <editor-fold desc = "Tools">

def euclidean_distance(a, b):
    """
    Returns the Euclidean distance of two points.
    :param a: Cartesian coordinates of first point
    :param b: Cartesian coordinates of second point
    :return: distance from a to b
    """
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def generate_map(n, d = 2):
    """
    Generates a list of cities and a dictionary providing their Euclidean distances.
    :param n: number of cities
    :param d: dimension of map (most commonly 2)
    :return: list of cities represented by ordered tuples, dictionary providing distances between cities
    """
    cities = [tuple(random.random() for coordinate in range(d)) for city in range(n)]
    distance = dict()
    for a in cities:
        for b in cities:
            dist = euclidean_distance(a, b)
            distance[a, b] = dist
            distance[b, a] = dist
    return cities, distance


def draw_map(tour, pixels = 500):
    """
    Draws a 2D tour.
    :param tour: list of city locations in the order of the tour
    :param pixels: width and height of the image
    :return: NONE
    """
    master = Tkinter.Tk()
    canvas = Tkinter.Canvas(master, width = pixels, height = pixels)
    canvas.pack()
    for i in range(len(tour) - 1):
        a = pixels * tour[i][0]
        b = pixels * tour[i][1]
        c = pixels * tour[i + 1][0]
        d = pixels * tour[i + 1][1]
        canvas.create_line(a, b, c, d)
    a = pixels * tour[0][0]
    b = pixels * tour[0][1]
    c = pixels * tour[-1][0]
    d = pixels * tour[-1][1]
    canvas.create_line(a, b, c, d)
    Tkinter.mainloop()


def path_length(tour, distance):
    """
    :param tour: a list of cities in the order to be visited
    :param dist: dictionary containing distances between cities
    :return: length of the tour
    """
    length = distance[tour[0], tour[-1]]
    for i in range(len(tour) - 1):
        length += distance[tour[i], tour[i + 1]]
    return length


def swap(path, x, y):
    """
    Swaps two elements in a list
    """
    new_path = path[:]
    new_path[x] = path[y]
    new_path[y] = path[x]
    return new_path


def reverse(path, x, y):
    """
    Reverses the portion of path between indices x and y.
    """
    newpath = path[:]
    newpath[x:y] = path[x:y][::-1]
    return newpath

# </editor-fold>

# <editor-fold desc = "Algorithms">

def greedy_heuristic(cities, distance):
    """
    :param cities: list of Cartesian coordinates
    :param dist: dictionary containing distances
    :return: a "short" tour that visits each city then returns to the origin city
    """
    min_path = cities[:]
    min_len = path_length(min_path, distance)
    for city in cities:
        part_path = [city]
        dist = 0
        for i in range(len(cities) - 1):
            left_to_visit = [c for c in cities if not c in part_path]
            next_dist, next_city = min([(distance[city, c], c) for c in left_to_visit])
            part_path.append(next_city)
            dist += next_dist
        dist += distance[city, next_city]
        if dist < min_len:
            min_len = dist
            min_path = part_path
    return min_path, min_len


def random_search(cities, distance, timelimit = 1):
    """
    :param cities: list of Cartesian coordinates
    :param dist: dictionary containing distances
    :param timelimit: stop searching after this many seconds have elapsed
    :return: a "short" tour that visits each city then returns to the origin city
    """
    bestpath = cities
    bestdistance = 1.5 * len(cities)
    t = time.clock()
    while time.clock() - t < timelimit:
        newpath = cities[:]
        random.shuffle(newpath)
        newdist = path_length(newpath, distance)
        if newdist < bestdistance:
            bestdistance = newdist
            bestpath = newpath
    return bestpath, bestdistance


# TODO: n = 15, seed = 'hello', this doesn't find shortest path
# specifically: 3.32241679079 vs 3.32209034898
def backtracking_with_pruning(cities, distance, part_path = [], part_len = 0, min_path = [], min_len = 0):
    # TODO: refine lower_bound (both times)
    if not part_len:
        part_path = cities[0:1]
        part_len = 0
    if not min_len:
        min_path = cities[:]
        min_len = path_length(min_path, distance)
    if len(part_path) == len(cities):
        tour_len = part_len + distance[part_path[0], part_path[-1]]
        if tour_len < min_len:
            min_path = part_path
            min_len = tour_len
        return min_path, min_len
    else:
        left_to_visit = [city for city in cities if not city in part_path]
        remaining_distances = []
        for x in left_to_visit:
            for y in left_to_visit:
                if not x == y:
                    remaining_distances.append(distance[x, y])
        remaining_distances = sorted(remaining_distances)
        lower_bound = part_len + sum(remaining_distances[:len(cities) - len(part_path) + 1])
        if lower_bound < min_len:
            sorted_cities = sorted([(distance[part_path[-1], x], x) for x in left_to_visit])
            for next_distance, next_city in sorted_cities:
                lower_bound = part_len + next_distance + sum(remaining_distances[:len(cities) - len(part_path)])
                if lower_bound < min_len: #TODO: CHANGING min_len TO 10**6 FIXED THE PROBLEM
                    new_part_path = part_path + [next_city]
                    new_part_len = part_len + distance[part_path[-1], next_city]
                    tour, tour_len = \
                        backtracking_with_pruning(cities, distance, new_part_path, new_part_len, min_path, min_len)
                    if tour_len < lower_bound:
                        print('DANGER WILL ROBINSON', round(lower_bound, 2), round(tour_len, 2))
                    if tour_len < min_len:
                        min_path, min_len = tour, tour_len
        return min_path, min_len


# TODO: weird behavior note - applying greedy_heuristic before local_search makes latter do nothing (IF n > 30).
def local_search(cities, distance):
    stuck = False
    n = len(cities)
    # min_path, min_len = cities, 1.5 * len(cities)
    min_path, min_len = random_search(cities, distance)
    # min_path, min_len = greedy_heuristic(cities, distance)
    while not stuck:
        stuck = True
        for x in range(n - 1):
            for y in range(x + 1, n):
                for method in [swap, reverse]:
                    new_path = method(min_path, x, y)
                    new_length = path_length(new_path, distance)
                    if new_length < min_len:
                        min_path, min_len = new_path, new_length
                        stuck = False
    return min_path, min_len


def simulated_annealing(cities, distance, method, iteration_length, temp_coefficient, decrement):
    return "NOT DONE YET"


def backtracking(cities, distance, part_path = [], part_len = 0, min_path = [], min_len = 0):
    if not part_len:
        part_path = cities[0:1]
        part_len = 0
    if not min_len:
        min_path = cities[:]
        min_len = path_length(min_path, distance)
    if len(part_path) == len(cities):
        tour_len = part_len + distance[part_path[0], part_path[-1]]
        if tour_len < min_len:
            min_path = part_path
            min_len = tour_len
        return min_path, min_len
    else:
        left_to_visit = [city for city in cities if not city in part_path]
        for next_city in left_to_visit:
            new_part_path = part_path + [next_city]
            new_part_len = part_len + distance[part_path[-1], next_city]
            tour, tour_len = \
                backtracking_with_pruning(cities, distance, new_part_path, new_part_len, min_path, min_len)
            if tour_len < min_len:
                min_path, min_len = tour, tour_len
        return min_path, min_len

# TODO: Make something of this.
def matrix_stuff(cities, distance):
    n = len(cities)
    array = [[0 for y in range(n)] for x in range(n)]
    for x in range(n):
        for y in range(n):
            array[x][y] = euclidean_distance(cities[x], cities[y])
    for row in array:
        print(map(lambda x: round(x, 2), row))
    return [], 0

# </editor-fold>

# <editor-fold desc = "Main">

def main(n, seed = 'hello'):
    random.seed(seed)
    cities, distance = generate_map(n, 2)
    algorithms = [greedy_heuristic, random_search, local_search, matrix_stuff, backtracking_with_pruning,
                  backtracking, simulated_annealing][4:6]
    print('Working on n = ' + str(n) + ' cities:')
    for algorithm in algorithms:
        t = time.clock()
        tour, length = algorithm(cities, distance)
        t = time.clock() - t
        message = 'Algorithm ' + algorithm.__name__ + ' found a path of length '
        message += str(length) + ' in ' + str(t) + ' seconds.'
        print(message)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        main(15)

# </editor-fold>
