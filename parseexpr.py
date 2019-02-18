import ast
import logging
import re

logger = logging.getLogger()
handler = logging.StreamHandler()
logger.addHandler(handler)


class Handler:
    selection_pattern = re.compile("((\(.*?\))\?(\(.*?\)):(\(.*?\)))")
    substitute_dict = {
        "RET": "(close/delay(close,1)-1)",
        "DTM": "(open<=delay(open,1)?0:max((high-open),(open-delay(open,1))))",
        "DBM": "(open<=delay(open,1)?0:max((open-low),(open-delay(open,1))))",
        "TR": "MAX(MAX(HIGH-LOW,ABS(HIGH-DELAY(CLOSE,1))),ABS(LOW-DELAY(CLOSE,1)))".lower(),
        "HD": "(HIGH-DELAY(HIGH,1))".lower(),
        "LD": "(DELAY(LOW,1)-LOW)".lower(),
    }
    for key in substitute_dict.copy():
        substitute_dict[key.lower()] = substitute_dict[key]
    variable_dict = {
        "high": "d1_adjh",
        "open": "d1_adjo",
        "close": "d1_adjc",
        "low": "d1_adjl",
        "vwap": "d1_adjv",
        "volume": "d1_volm",
        "amount": "d1_amnt",
    }
    op_dict = {
        ast.Add: "+",
        ast.Sub: "-",
        ast.Mult: "*",
        ast.Div: "/",
        ast.And: "&",
        ast.Or: "|",
        ast.Lt: "<",
        ast.Gt: ">",
        ast.Pow: "**",
        ast.USub: "-"
    }

    def __init__(self):
        pass

    @classmethod
    def handle_sum(cls, args):
        if len(args) != 2:
            logger.warning("incorrect argument number")
            return "undefined"
        return "dt.ts_sum({0},{1})".format(args[0], args[1])

    @classmethod
    def handle_rank(cls, args):
        if len(args) > 1:
            logger.warning("incorrect argument number")
            return "undefined"
        return "dt.cs_rank({0})".format(args[0])

    @classmethod
    def handle_mean(cls, args):
        if len(args) != 2:
            logger.warning("incorrect argument number")
            return "undefined"
        return "dt.ts_mean({0},{1})".format(args[0], args[1])

    @classmethod
    def handle_delta(cls, args):
        if len(args) != 2:
            logger.warning("incorrect argument number")
            return "undefined"
        return "{0}.diff({1})".format(args[0], args[1])

    @classmethod
    def handle_corr(cls, args):
        if len(args) != 3:
            logger.warning("incorrect argument number")
            return "undefined"
        return "dt.ts_corr({0},{1})".format(args[0], args[1])

    @classmethod
    def handle_decaylinear(cls, args):
        if len(args) != 2:
            logger.warning("incorrect argument number")
            return "undefined"
        return "{0}.ewm(span={1})".format(args[0], args[1])


def parser(string: str):
    string = string.replace("^", "**")
    for key, item in Handler.substitute_dict.items():
        string = string.replace(key, item)
    return ast.parse(string).body[0]


def generator(data):
    sentences = recursive_generate(data)
    return sentences


def register_node(node, variable_dict, variable_number):
    if not isinstance(node, (ast.Num, ast.Name)):
        variable_dict[node] = "var_{}".format(variable_number)
        variable_number += 1
    elif isinstance(node, ast.Num):
        variable_dict[node] = str(node.n)
    elif isinstance(node, ast.Name):
        try:
            variable_dict[node] = Handler.variable_dict[node.id.lower()]
        except KeyError as e:
            logger.error("no value for {}".format(ast.dump(node)))
            variable_dict[node] = "undefined_".format(node.id)
    return variable_number


def recursive_generate(node, variable_dict={}, variable_number=0, sentences=[]):
    match_type = type(re.match("", ""))
    if isinstance(node, ast.Expr):
        recursive_generate(node.value, variable_dict, 0, sentences)
        return sentences
    elif isinstance(node, ast.BinOp):
        temp = ""
        op = Handler.op_dict[type(node.op)]
        if node not in variable_dict.keys():
            variable_dict[node] = "var_{}".format(variable_number)
        temp += (variable_dict[node] + "=")
        variable_number += 1
        variable_number = register_node(node.left, variable_dict, variable_number)
        temp += variable_dict[node.left] + op
        variable_number = register_node(node.right, variable_dict, variable_number)
        temp += variable_dict[node.right]
        sentences.append(temp)
        if not isinstance(node.left, (ast.Num, ast.Name)):
            variable_number += 1
            recursive_generate(node.left, variable_dict, variable_number, sentences)
        if not isinstance(node.right, (ast.Num, ast.Name)):
            variable_number += 1
            recursive_generate(node.right, variable_dict, variable_number, sentences)

    elif isinstance(node, ast.Call):
        temp = ""
        if node not in variable_dict.keys():
            variable_dict[node] = "var_{}".format(variable_number)
            variable_number += 1
        temp += (variable_dict[node] + "=")

        arg_names = []
        for arg in node.args:
            variable_number = register_node(arg, variable_dict, variable_number)
            arg_names.append(variable_dict[arg])
        rhs = getattr(Handler, "handle_{}".format(node.func.id.lower()))(arg_names)
        temp += rhs
        sentences.append(temp)
        for arg in node.args:
            if not isinstance(arg, (ast.Num, ast.Name)):
                variable_number += 1
                recursive_generate(arg, variable_dict, variable_number, sentences)

    elif isinstance(node, ast.Compare):
        temp = ""
        if node not in variable_dict.keys():
            variable_dict[node] = "var_{}".format(variable_number)
            variable_number += 1
        temp += (variable_dict[node] + "=")
        left = node.left
        variable_number = register_node(left, variable_dict, variable_number)
        right = node.comparators[0]
        variable_number = register_node(right, variable_dict, variable_number)
        op = Handler.op_dict[type(node.ops[0])]
        temp += (variable_dict[left] + op + variable_dict[right])
        sentences.append(temp)
        if not isinstance(left, (ast.Num, ast.Name)):
            variable_number += 1
            recursive_generate(left, variable_dict, variable_number, sentences)
        if not isinstance(right, (ast.Num, ast.Name)):
            variable_number += 1
            recursive_generate(right, variable_dict, variable_number, sentences)

    elif isinstance(node, ast.UnaryOp):
        temp = ""
        if node not in variable_dict.keys():
            variable_dict[node] = "var_{}".format(variable_number)
            variable_number += 1
        temp += (variable_dict[node] + "=")
        variable_number=register_node(node.operand,variable_dict,variable_number)
        temp+=Handler.op_dict[type(node.op)]
        temp+=variable_dict[node.operand]
        sentences.append(temp)
        if not isinstance(node.operand, (ast.Num, ast.Name)):
            variable_number += 1
            recursive_generate(node.operand, variable_dict, variable_number, sentences)

def pipeline(a:str):
    data=parser(a)
    sentences=generator(data)
    sentences.reverse()
    return sentences

if __name__ == "__main__":
    a = parser(
        "((rank(decaylinear(delta((close),2),8))-rank(decaylinear(corr(((vwap*0.3)+(open*0.7)),sum(mean(volume,180),37),14),12)))*-1)")
    print(ast.dump(a))
    data = generator(a)
    print(data)