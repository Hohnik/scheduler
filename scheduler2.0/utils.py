def calc_blocksizes(sws: int, blocks=[]) -> list:
    """
    Calculate the best possible combination of blocks.
    """
    if not sws:
        return blocks 

    if sws % 2 == 0:
        return calc_blocksizes(sws-2, blocks + [2])

    if sws >= 3:
        return calc_blocksizes(sws-3, blocks + [3])

    if sws == 1:
        return calc_blocksizes(sws-1, blocks + [1])