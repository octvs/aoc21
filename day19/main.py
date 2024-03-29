#!/usr/bin/env python
import sys
import logging
import numpy as np


def parse_input(inp: str) -> dict[int, np.ndarray]:
    scans = {}
    report_blocks = [x.split("\n") for x in inp.split("\n\n")]
    for block in report_blocks:
        ind = int(block[0].split(" ")[2])
        logging.debug(f"Parser:New scanner is being read: {ind}")
        scans[ind] = np.array(
            [[int(i) for i in line.split(",")] for line in block[1:] if line != ""]
        )
        logging.debug(f"Parser:Read {len(scans[ind])} beacons.")
    logging.debug(f"Total beacons read: {sum([len(scans[sc]) for sc in scans])}")
    return scans


def euclidean_distance(p0, p1):
    return np.sqrt(np.sum(np.square(p0 - p1), axis=-1))


def manhattan_distance(p0, p1):
    return np.sum(np.abs(p0 - p1), axis=-1)


def invert_h(h):
    r, t = h[:-1, :-1], h[:-1, -1]
    return np.vstack(
        [np.hstack([r.T, np.reshape(-r.T @ t, (3, 1))]), np.array([0, 0, 0, 1])]
    )


def make_points_homogenous(p):
    return np.hstack([p, np.ones((len(p), 1))]).T


def create_distance_matrix(scan_data, metric=euclidean_distance):
    dst_mat = np.zeros((len(scan_data), len(scan_data)))
    for i, p in enumerate(scan_data):
        dst_mat[i, i:] = metric(p, scan_data[i:])
    return dst_mat


def pad_cols_if_necessary(dst0, dst1):
    if (n_cols0 := dst0.shape[1]) != (n_cols1 := dst1.shape[1]):
        target = max(n_cols0, n_cols1)
        dst0 = np.pad(dst0, ((0, 0), (0, target - n_cols0)))
        dst1 = np.pad(dst1, ((0, 0), (0, target - n_cols1)))
    return dst0, dst1


def map_common_points(dst0, dst1):
    logging.debug("Mapping common pts")
    dst0, dst1 = pad_cols_if_necessary(dst0, dst1)
    all_dst = np.vstack([dst0, dst1])
    vals, idxs, cnts = np.unique(all_dst, return_index=True, return_counts=True)
    vals, idxs = vals[cnts == 2], idxs[cnts == 2]

    # 12 beacons will have 66 overlaping distances, C(12,2)=66
    if len(vals) < 66:
        return None, None

    # TODO: change this part, doesn't look good
    map_mat = np.zeros((len(dst0), len(dst1)))
    for i in range(len(vals)):
        idx0 = idxs[i] // dst0.shape[1], idxs[i] % dst0.shape[1]
        idx1 = np.where(dst1 == vals[i])
        for ind in [(x, y) for y in idx1 for x in idx0]:
            map_mat[ind] += 1

    # The correct beacon will appear on all possible ambiguous pairs
    # 11 in case of 12 common points
    ind_src, ind_dst = np.where(map_mat >= 11)
    return ind_src, ind_dst


def solve_for_h(p0, p1):
    src, dst = (make_points_homogenous(p) for p in [p0, p1])
    right_inv_dst = dst.T @ np.linalg.inv(dst @ dst.T)
    return np.round(src @ right_inv_dst).astype(int)


def find_transformation_btw(data, ind0, ind1):
    dst_mat0 = create_distance_matrix(data[ind0])
    dst_mat1 = create_distance_matrix(data[ind1])
    ind_src, ind_dst = map_common_points(dst_mat0, dst_mat1)
    if ind_src is not None:
        logging.debug(f"Trying to solve H{ind0}_{ind1}")
        h_mat = solve_for_h(data[ind0][ind_src], data[ind1][ind_dst])
        return h_mat
    else:
        return None


def explore_transformations(h_dict):
    if len(h_dict) - 1 == len(h_dict[0]):
        logging.debug("Explorer:Populated the dict enough.")
        return h_dict
    for interm in list(h_dict[0].keys()):
        for dst in h_dict[interm].keys():
            if dst not in h_dict[0].keys() and dst != 0:
                logging.debug(f"Explorer:New link 0->({interm})->{dst}")
                h_dict[0][dst] = h_dict[0][interm] @ h_dict[interm][dst]
    logging.debug("Explorer:Recurring")
    return explore_transformations(h_dict)


def create_transformations_dict(scan_data):
    transformation_dict = {i: {} for i in scan_data.keys()}
    for ind_scanner0 in scan_data:
        for ind_scanner1 in range(ind_scanner0 + 1, max(scan_data) + 1):
            h_mat = find_transformation_btw(scan_data, ind_scanner0, ind_scanner1)
            if h_mat is None:
                continue
            transformation_dict[ind_scanner0][ind_scanner1] = h_mat
            transformation_dict[ind_scanner1][ind_scanner0] = invert_h(h_mat)

    explored_dict = explore_transformations(transformation_dict)
    explored_dict[0][0] = np.eye(4)
    return explored_dict


def part1(scanners, transformations):
    points = []
    for ind in scanners:
        beaconsi_0 = transformations[0][ind] @ make_points_homogenous(scanners[ind])
        beaconsi_0 = np.round(beaconsi_0[:-1].T).astype(int)
        points.append(beaconsi_0)
    points = np.vstack(points)
    print(f"Total scanned beacon count: {len(points)}")
    unique_points = np.unique(points, axis=0)
    print(f"Unique beacon count: {len(unique_points)}")


def part2(h_dict):
    scanners_0 = np.array([h_dict[0][i][:-1, -1] for i in h_dict[0]])
    manhattan_dsts = create_distance_matrix(scanners_0, manhattan_distance).astype(int)
    print(f"Maximum manhattan distance btw scanners: {np.max(manhattan_dsts)}")


def main():
    input_file = "input.txt"
    with open(f"day19/{input_file}", "r") as f:
        raw_input = f.read()

    scanners = parse_input(raw_input)
    transformations = create_transformations_dict(scanners)

    part1(scanners, transformations)
    part2(transformations)


def parse_args(args: list) -> list:
    if "--debug" in args:
        logging.basicConfig(level=logging.DEBUG)
        args.remove("--debug")
    return args


if __name__ == "__main__":
    parse_args(sys.argv)
    main()
