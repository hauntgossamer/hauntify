import random, time
t = time.time()
testlist = [f"test song {i}" for i in range(1, 1000)]
def shuffle(x):
    ceiling = random.randint(100, 100*len(x))
    while ceiling < x.index(x[-1]):
        ceiling = random.randint(100, 10000)

    procgen = [(dict(key=j, value=k)) for j,k in enumerate([(random.randint(100, ceiling)) for i in x])]
    procgen.pop(-1)
    
#     print(f"Procedural generation of random dictionaries looks like this: {procgen} \n \n")
    new_indexes =  [i["key"] for i in sorted(procgen, key=lambda d: d["value"])]
#     print(f"The list used to reassign indeces looks like this: \n {new_indexes} \n \n")
    new_list_of_dicts = []
    for i in new_indexes:
        new_list_of_dicts.append(dict(key=i, value=x[i]))
    print(new_list_of_dicts)
    shuffled_list = [i["value"] for i in new_list_of_dicts]
#     print(f"Provided list looked like this: \n {x} \n \n Shuffled list looks like this: \n {shuffled_list} \n")
    print(shuffled_list)
    return shuffled_list

shuffle(testlist)