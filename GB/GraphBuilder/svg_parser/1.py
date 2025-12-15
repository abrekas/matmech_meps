import json


dicta = {}

with open('test.json', "r", encoding="utf-8") as file:
    dicta = json.load(file)

nodes = dicta["nodes"]
edges = dicta["edges"]
names = dicta["rooms"]

names_result = {}

nodes_dict = {}
result_dict = {}

result_dict_coords = {}

for node in nodes:
    result_dict[node["id"]] = []
    nodes_dict[node["id"]] = " ".join((str(int(node["x"])), str(int(node["y"]))))
    for edge in edges:
        if edge["from"] == node["id"]:
            result_dict[node["id"]].append(edge["to"])
        if edge["to"] == node["id"]:
            result_dict[node["id"]].append(edge["from"])

for des in result_dict.keys():
    result_dict_coords[nodes_dict[des]] = list(map(lambda x: nodes_dict[x], result_dict[des]))

for name in names:
    names_result[name["number"]] = nodes_dict[name["node_id"]]

with open("graph.json", "w", encoding='utf-8') as f:
    json.dump(result_dict_coords, f, ensure_ascii=False, indent=2)

with open("names.json", "w", encoding='utf-8') as f:
    json.dump(names_result, f, ensure_ascii=False, indent=2)

# Точка (563, 132)
print(result_dict_coords)