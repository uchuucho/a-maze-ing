from maze_config_creation import MazeConfig, ConfigError, Maze
import sys


if __name__ == "__main__":
    print(sys.argv)
    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py config.txt")
        sys.exit(1)
    
    try:
        cfg = MazeConfig.create_maze_config(sys.argv[1])
        print(cfg)
    except ConfigError as e:
        print(e)
        sys.exit(1)
    
    print("=======================")
    maze = Maze(cfg)
    maze.__print_maze__()
