# import pytest

from slither.core.cfg.node import Node, NodeType
from slither.core.declarations import (
    Function,
    Contract,
)
from slither.slithir.operations import (
    Return,
)


def test_with_explicit_return(slither_from_source) -> None:
    source = """
        contract Contract {
            function foo(int x) public returns (int y) {
                if(x > 0) {
                    return x;
                } else {
                    y = x * -1;
                }
            }
        }
        """
    with slither_from_source(source) as slither:
        c: Contract = slither.get_contract_from_name("Contract")[0]
        f: Function = c.functions[0]
        node_if: Node = f.nodes[1]
        node_true = node_if.son_true
        node_false = node_if.son_false
        assert node_true.type == NodeType.RETURN
        assert isinstance(node_true.irs[0], Return)
        assert node_true.irs[0].values[0] == f.get_local_variable_from_name("x")
        assert len(node_true.sons) == 0
        node_end_if = node_false.sons[0]
        assert node_end_if.type == NodeType.ENDIF
        assert node_end_if.sons[0].type == NodeType.RETURN
        node_ret = node_end_if.sons[0]
        assert isinstance(node_ret.irs[0], Return)
        assert node_ret.irs[0].values[0] == f.get_local_variable_from_name("y")


def test_return_multiple_with_struct(slither_from_source) -> None:
    source = """
        struct St {
            uint256 value;
        }
        
        contract Contract {
            function foo(St memory x) public returns (St memory y, uint256 z) {
                z = x.value;
                y = St({value: z + 1});
            }
        }
        """
    with slither_from_source(source) as slither:
        c: Contract = slither.get_contract_from_name("Contract")[0]
        f: Function = c.functions[0]
        assert len(f.nodes) == 4
        node = f.nodes[3]
        assert node.type == NodeType.RETURN
        assert isinstance(node_true.irs[0], Return)
        assert node_true.irs[0].values[0] == f.get_local_variable_from_name("y")
        assert node_true.irs[0].values[1] == f.get_local_variable_from_name("z")


def test_nested_ifs_with_loop(slither_from_source) -> None:
    source = """
        contract Contract {
            function foo(uint a) public returns (uint x) {
                x = a;
                if(a == 1) {
                    return a;
                } else {
                    for (uint i = 0; i < 10; i++) {
                        if (x > 10) {
                            if (a < 0) {
                                x = 10 * x;
                            } else {
                                throw;
                            }
                        } else {
                            x++;
                        }
                    }
                }
            }
        }
        """
    with slither_from_source(source) as slither:
        c: Contract = slither.get_contract_from_name("Contract")[0]
        f: Function = c.functions[0]
        node_if = f.nodes[2]
        assert node_if.son_true.type == NodeType.RETURN
        node_explicit = node_if.son_true
        assert isinstance(node_explicit.irs[0], Return)
        assert node_explicit.irs[0].values[0] == f.get_local_variable_from_name("a")
        node_end_if = f.nodes[16]
        assert node_end_if.type == NodeType.ENDIF
        assert node_end_if.sons[0].type == NodeType.RETURN
        node_implicit = node_end_if.sons[0]
        assert isinstance(node_implicit.irs[0], Return)
        assert node_implicit.irs[0].values[0] == f.get_local_variable_from_name("x")
        node_throw = f.nodes[11]
        assert node_throw.type == NodeType.THROW
        assert len(node_throw.sons) == 0


def test_issue_1846_ternary_in_ternary(slither_from_source):
    source = """
        contract Contract {
            function foo(uint x) public returns (uint y) {
                y = x > 0 ? x > 1 ? 2 : 3 : 4;
            }
        }
        """
    with slither_from_source(source) as slither:
        c: Contract = slither.get_contract_from_name("Contract")[0]
        f = c.functions[0]
        node_end_if = f.nodes[3]
        assert node_end_if.type == NodeType.ENDIF
        assert len(node_end_if.sons) == 1
        node_ret = node_end_if.sons[0]
        assert node_ret.type == NodeType.RETURN
        assert isinstance(node_ret.irs[0], Return)
        assert node_ret.irs[0].values[0] == f.get_local_variable_from_name("y")
