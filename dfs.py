from maze_config_creation import Maze, MazeConfig
import random


# binary location: 0bWSEN -> 1 wall 0 no wall
N, E, S, W = 1, 2, 4, 8
# directions: (row, col, opposite_dir)
DIRS = {N: (-1, 0, S), E: (0, 1, W), S: (1, 0, N), W: (0, -1, E)}


def maze_from_dfs(config: MazeConfig) -> Maze:
    maze = Maze(config)
    random.seed(maze.config.seed)
    visited: list[tuple[int, int]] = [config.entry]
    stack = [maze.config.entry]

    while stack:
        r, c = stack[-1]
        neighbors = [
            (bit, r + ir, c + ic, opp)
            for bit, (ir, ic, opp) in DIRS.items() if (
                0 <= r + ir < config.height and
                0 <= c + ic < config.width and
                maze.array[r + ir][c + ic] != 0b10000 and
                (r + ir, c + ic) not in visited
            )
        ]
        if neighbors:
            bit, nr, nc, opp = random.choice(neighbors)
            # we change the values of the cells (r,c) and (nr,nc)
            # because we removed a wall in-between
            maze.array[r][c] &= ~bit
            maze.array[nr][nc] &= ~opp
            visited.append((nr, nc))
            stack.append((nr, nc))
        else:
            stack.pop()

        # in case nonperfect, we remove all dead-ends
        if not config.perfect:
            for r in range(config.height):
                for c in range(config.width):
                    if maze.array[r][c] not in [7, 11, 13, 14]:
                        continue
                    # choose all wall sides
                    blocks = [
                        (bit, r + ir, c + ic, opp)
                        for bit, (ir, ic, opp) in DIRS.items() if (
                                maze.array[r][c] & bit and
                                0 <= r + ir < config.height and
                                0 <= c + ic < config.width and
                                maze.array[r + ir][c + ic] != 0b10000
                            )
                    ]
                    if not blocks:
                        continue
                    # check maybe a neighbor is also dead-end
                    # so we open just one wall
                    twins = [
                        x for x in blocks
                        if maze.array[x[1]][x[2]] in [7, 11, 13, 14]
                    ]
                    bit, nr, nc, opp = random.choice(twins or blocks)
                    maze.array[r][c] &= ~bit
                    maze.array[nr][nc] &= ~opp

    return maze
