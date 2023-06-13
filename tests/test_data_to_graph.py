import data_to_graph

data = [
    [1, 2, 3, 4, 5],
    [10, 9, 8, 7, 6],
    [11, 12, 13, 14, 15],
]

users = ["user1", "user2", "user3"]

timestamps = ["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-04", "2020-01-05"]

data_to_graph.data_to_graph(timestamps, data, users, "test", "d", "test.png")

