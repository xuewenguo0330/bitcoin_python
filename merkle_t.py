import math
import hashlib
import json


class Node:
    def __init__(self, value: str, left_child=None, right_child=None):
        self.value = value
        self.left_child = left_child
        self.right_child = right_child


def compute_tree_depth(number_of_leaves: int) -> int:
    return math.ceil(math.log2(number_of_leaves))


def is_power_of_2(number_of_leaves: int) -> bool:
    return math.log2(number_of_leaves).is_integer()


def fill_set(list_of_nodes: list):
    current_number_of_leaves = len(list_of_nodes)
    if is_power_of_2(current_number_of_leaves):
        return list_of_nodes
    total_number_of_leaves = 2**compute_tree_depth(current_number_of_leaves)
    if current_number_of_leaves % 2 == 0:
        for i in range(current_number_of_leaves, total_number_of_leaves, 2):
            list_of_nodes = list_of_nodes + [list_of_nodes[-2], list_of_nodes[-1]]
    else:
        for i in range(current_number_of_leaves, total_number_of_leaves):
            list_of_nodes.append(list_of_nodes[-1])
    return list_of_nodes


def hash(block):
        # hashes a block
        # also make sure that the transactions are ordered otherwise we will have insonsistent hashes!
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

def build_merkle_tree(node_data):
    complete_set = fill_set(node_data)
    old_set_of_nodes = [Node(hash(data)) for data in complete_set]
    tree_depth = compute_tree_depth(len(old_set_of_nodes))

    for i in range(0, tree_depth):
        num_nodes = 2**(tree_depth-i)
        new_set_of_nodes = []
        for j in range(0, num_nodes, 2):
            child_node_0 = old_set_of_nodes[j]
            child_node_1 = old_set_of_nodes[j+1]
            new_node = Node(
                
                value=hash(f"{child_node_0.value}{child_node_1.value}"),
                left_child=child_node_0,
                right_child=child_node_1
            )
            new_set_of_nodes.append(new_node)
        old_set_of_nodes = new_set_of_nodes
    return new_set_of_nodes[0]


def get_path(node, k):
    if not node:
        return []
    if node.value == k:
        return [node.value]
    res = get_path(node.left_child, k)
    if res:
        return [node.value] + res
    res = get_path(node.right_child, k)
    if res:
        return [node.value] + res
    return []


def get_neighboor(node, parent, k):
    l = "l"
    r = "r"
    if not node:
        return None
    if node.value == k and parent != None:
        if parent.left_child.value == k:
            return parent.right_child.value, r
        else:
            return parent.left_child.value, l
    res = get_neighboor(node.left_child, node, k)
    if res:
        return res
    res = get_neighboor(node.right_child,node, k)
    if res:
        return res
    return None


def get_merkle_proof(node, k):
    path = get_path(node, k)
    if path:
        tab = path[1:]
        return [get_neighboor(node, None, p) for p in tab]
    else:
        return []


def check_merkle_proof(merkle_root_val, merkle_proof, transaction):
    if merkle_proof[-1][1] == "l":
        calculated_root = merkle_proof[-1][0] + hash(transaction)
    else:
        calculated_root = hash(transaction) + merkle_proof[-1][0]
    print(calculated_root)
    l = list(reversed(merkle_proof[:-1]))
    for val, d in l:
        if d == "l":
            calculated_root = val + hash(calculated_root) 
        else:
            calculated_root = hash(calculated_root) + val
        print(calculated_root)
    return hash(calculated_root) == merkle_root_val
