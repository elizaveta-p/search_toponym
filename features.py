def count_spn(c1, c2):
    delta_lan = abs(c1[0] - c2[0])
    delta_lon = abs(c1[1] - c2[1])
    return ','.join([str(delta_lan), str(delta_lon)])