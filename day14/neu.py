import numpy as np

from method_char_array import show_dict, test_with_char_array

input_file = "test_input.txt"
raw_input = np.genfromtxt(input_file, skip_header=2, dtype=str)

all_characters = np.unique(np.array([list(a) for a in raw_input[:, 0]]).flatten())
starting_polymer = open(input_file, "r").readline().rstrip()
one_step_ahead = {a: a[0] + b + a[1] for a, b in zip(raw_input[:, 0], raw_input[:, -1])}


def slicer(poly):
    return [poly[j:j + 2] for j in range(len(poly) - 1)]


def combine_slices(poly, slic):
    if poly == "":
        return slic
    else:
        return poly + slic[1:]


def query_the_wiki(pair, at_step):
    print(f"Checking {pair=} {at_step=}")
    if len(pair) > 2:
        if np.log2(at_step) % 1 != 0:
            closest_hop = 2**int(np.log2(at_step))
            print("Closest even step", closest_hop)
            res = calculate_from_parts(pair, closest_hop)
            print("##########################")
            return query_the_wiki(res, at_step-closest_hop)
        else:
            return calculate_from_parts(pair, at_step)
    else:
        if pair in wikipedia[at_step]:
            print(f"Recursive soln to {pair} at step {at_step} = {wikipedia[at_step][pair]}")
            return wikipedia[at_step][pair]
        else:
            half_age_status = query_the_wiki(pair, at_step // 2)
            print(f"{half_age_status=}")
            res = calculate_from_parts(half_age_status, at_step // 2)
            print(f"{res=}")
            print(f"Wikipedia updated {at_step=} for {pair}->{res}")
            wikipedia[at_step][pair] = res
            return res


def calculate_from_parts(poly, step):
    print(f"Calculating from parts {poly}")
    res = ""
    for sli in slicer(poly):
        out = query_the_wiki(sli, step)
        res = combine_slices(res, out)
    return res


total_steps = 10
hops = [2 ** x for x in range(int(np.log2(total_steps) + 1))]
wikipedia = {hop: {} for hop in hops}
wikipedia[1] = one_step_ahead
show_dict(wikipedia[1])

print(np.array(list(bin(total_steps)[2:]), dtype=int)[::-1] * np.array(hops, dtype=int))
output = query_the_wiki(starting_polymer, total_steps)

print("~~Check~~")
test_output = test_with_char_array(starting_polymer, {a: b for a, b in zip(raw_input[:, 0], raw_input[:, -1])},
                                   total_steps)

print(f"Test: {output == test_output}")
