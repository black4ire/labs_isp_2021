#!/usr/bin/env python3
import logging


logging.basicConfig(level=logging.INFO, format="%(message)s\n")
logger = logging.getLogger(__name__)


def output_matrix(matrix):
    for index in range(5):
        logger.info(matrix[index])


def main():
    matrix = [
        [1, 0, 0, 0, 0],
        [1, 1, 0, 0, 0],
        [1, 1, 1, 0, 0],
        [1, 1, 1, 1, 0],
        [1, 1, 1, 1, 1],
    ]
    matrix_T = list(map(list, zip(*matrix)))

    output_matrix(matrix)
    logger.info("\n")
    output_matrix(matrix_T)


if __name__ == "__main__":
    main()
